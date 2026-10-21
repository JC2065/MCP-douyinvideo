"""Platform configuration centre for the admin console.

Covers model connections, write-only secrets, video provider settings, service
status and the three versioned workflow definitions (requirements, analysis,
production).  Secrets are accepted but never returned: only "configured", the
source and the last four characters are exposed.  Every write is atomic,
versioned and protected by expectedRevision; rollbacks create new versions.
"""
import copy
import hashlib
import ipaddress
import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit
import importlib.util

_spec = importlib.util.spec_from_file_location('user_profile_rules', Path(__file__).with_name('user-profile.py'))
_profile_rules = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_profile_rules)
PERSONALIZATION_DEFAULT = _profile_rules.DEFAULTS


class PlatformError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


BUILTIN = {
    'qwen-domestic': {'name': '国内千问（文本模型）', 'kind': 'chat'},
    'wan-video': {'name': '千问 Wan（视频生成）', 'kind': 'video'},
    'reference-parser': {'name': '抖音参考解析服务', 'kind': 'parser'},
    'image-gen': {'name': '图片生成（图文作品）', 'kind': 'image'},
}
IMAGE_DEFAULT = {'baseUrl': 'https://dashscope.aliyuncs.com/api/v1', 'model': 'wan2.6-t2i'}
WATCH_DEFAULT = {'maxAnalyzeSeconds':90,'maxFrames':32,'frameShortSide':360,'deepWatchThreshold':0.4,'autoDeepWatch':False,'chatMaxTurns':4,'perUserDailyVideos':10,'dailyBudgetYuan':20,'promptVersion':'watch-v1','glanceRatio':10,'ocr':True,'asrModel':'small','prices':{'qwen3.8-flash':{'in':1.12,'out':3.29},'qwen3.8-omni-flash':{'in':7.0,'out':21.0},'qwen3-vl-plus':{'in':1.4,'out':11.2}}}

BOARD_DEFAULT = {'countdownSeconds':8,'autoConfidence':0.7,'rewatchLimit':2,'interviewTurns':6,'attemptWindowDays':7,'similarityThreshold':0.6,
                 'maxPlanFields':12,'reviewVotes':3,'rewardPerMetrics':1,'streakUnlock':3,'predictMinWorks':5,'subscribeTemplateId':'','composeMaxSeconds':90}
BOARD_LIMITS = {'countdownSeconds':(3,30),'rewatchLimit':(0,5),'interviewTurns':(2,12),'attemptWindowDays':(1,30),'maxPlanFields':(3,12),'reviewVotes':(2,20),
                'rewardPerMetrics':(0,20),'streakUnlock':(1,30),'predictMinWorks':(3,200),'composeMaxSeconds':(10,180)}

def validate_board(value):
    if not isinstance(value,dict) or set(value)!=set(BOARD_DEFAULT):raise ValueError('创作板块配置字段无效')
    for k,(lo,hi) in BOARD_LIMITS.items():
        if type(value[k]) is not int or not lo<=value[k]<=hi:raise ValueError(k+'超出范围')
    for k in ('autoConfidence','similarityThreshold'):
        if type(value[k]) not in (int,float) or not 0<=value[k]<=1:raise ValueError(k+'超出范围')
    if not isinstance(value['subscribeTemplateId'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{0,64}',value['subscribeTemplateId']):raise ValueError('订阅消息模板ID无效')

def validate_watch(value):
    if not isinstance(value,dict) or set(value)!=set(WATCH_DEFAULT):raise ValueError('视频观看配置字段无效')
    for k,lo,hi in [('maxAnalyzeSeconds',30,300),('maxFrames',8,48),('frameShortSide',240,768),('chatMaxTurns',1,4),('perUserDailyVideos',0,10000)]:
        if type(value[k]) is not int or not lo<=value[k]<=hi:raise ValueError(k+'超出范围')
    for k,lo,hi in [('deepWatchThreshold',0,1),('dailyBudgetYuan',0,100000)]:
        if type(value[k]) not in (int,float) or not lo<=value[k]<=hi:raise ValueError(k+'超出范围')
    if type(value['glanceRatio']) is not int or not 5<=value['glanceRatio']<=20:raise ValueError('glanceRatio超出范围')
    if value['asrModel'] not in ('tiny','base','small'):raise ValueError('语音转写模型无效')
    if type(value['ocr']) is not bool:raise ValueError('OCR开关无效')
    if type(value['autoDeepWatch']) is not bool or not isinstance(value['promptVersion'],str) or not re.fullmatch('[a-zA-Z0-9._-]{1,40}',value['promptVersion']):raise ValueError('观看版本或升级开关无效')
    if not isinstance(value['prices'],dict) or not 1<=len(value['prices'])<=100:raise ValueError('模型单价无效')
    for model,rates in value['prices'].items():
        if not isinstance(model,str) or not MODEL_ID.fullmatch(model) or not isinstance(rates,dict) or set(rates)!={'in','out'} or any(type(v) not in (int,float) or not 0<=v<=10000 for v in rates.values()):raise ValueError('模型单价无效')

MAX_CUSTOM = 8
RESOLUTIONS = ('480P', '720P', '1080P')
MODEL_ID = re.compile(r'[A-Za-z0-9._:/-]{1,80}')
CONNECTION_ID = re.compile(r'[a-z][a-z0-9-]{2,30}')

# Mirrors web/admin-workflows/model.js so the preview and production rules agree.
CAPABILITIES = {'input': '输入采集', 'skill': 'Skill协作', 'review': '用户确认', 'evidence': '证据提取',
                'generate': '作品生成', 'package': '作品编排', 'archive': '资产归档'}
STAGES = {'requirements': '确认需求设计', 'analysis': '作品拆解', 'production': '作品产出'}


def _step(ident, title, capability, required=False):
    return {'id': ident, 'title': title, 'capability': capability, 'required': required}


DEFAULT_FLOWS = {
    'requirements': [_step('input', '接收灵感 / 热点 / 口令', 'input', True),
                     _step('clarify', '确认目标、受众、平台与时长', 'skill'),
                     _step('brief', '形成主题、风格和交付清单', 'skill'),
                     _step('confirm', '用户确认需求简报', 'review', True)],
    'analysis': [_step('source', '选择素材与拆解模板', 'input', True),
                 _step('evidence', '提取画面、语音与来源证据', 'evidence', True),
                 _step('analyze', '按目标拆解结构、卖点和镜头', 'skill'),
                 _step('reuse', '提炼可复用方法与原创方向', 'skill'),
                 _step('confirm', '用户确认拆解方案', 'review', True)],
    'production': [_step('brief', '读取已确认简报与拆解快照', 'input', True),
                   _step('script', '生成脚本、分镜与素材清单', 'skill'),
                   _step('confirm', '确认分镜与费用上限', 'review', True),
                   _step('generate', '生成文字 / 图片 / 视频', 'generate', True),
                   _step('package', '匹配音乐、字幕与标题', 'package'),
                   _step('review', '预览并确认作品', 'review', True),
                   _step('archive', '归集资产与飞书归档事件', 'archive', True)],
}

BOARDS = [
    {'id': 'hotspots', 'name': '热点推荐', 'desc': '来源采集、榜单与AI总结'},
    {'id': 'tools', 'name': '创作工具调用', 'desc': '工具开关、视频生成与转写'},
    {'id': 'data', 'name': '数据积累（飞书）', 'desc': '资产归档与飞书配置状态'},
    {'id': 'requirements', 'name': '确认需求设计', 'desc': '把想法整理成可确认的创作简报', 'flow': True},
    {'id': 'analysis', 'name': '作品拆解', 'desc': '基于素材证据提炼结构与方法', 'flow': True},
    {'id': 'production', 'name': '作品产出', 'desc': '从确认方案到可追踪的作品资产', 'flow': True},
]


def validate_steps(stage, steps):
    """Return a list of Chinese error messages; empty means valid."""
    if stage not in DEFAULT_FLOWS:
        return ['未知流程']
    if not isinstance(steps, list) or not 1 <= len(steps) <= 12:
        return ['流程需要1–12个步骤']
    errors, seen = [], set()
    for row in steps:
        if not isinstance(row, dict) or set(row) != {'id', 'title', 'capability', 'required'}:
            errors.append('步骤只能包含 id、title、capability、required，不能携带代码或调用地址')
            continue
        if not isinstance(row['id'], str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', row['id']) or row['id'] in seen:
            errors.append('步骤ID重复或无效')
            continue
        seen.add(row['id'])
        if row['capability'] not in CAPABILITIES:
            errors.append('不支持的能力：' + str(row['capability'])[:40])
        if not isinstance(row['title'], str) or not row['title'].strip() or len(row['title']) > 80:
            errors.append('步骤标题需1–80字')
        if type(row['required']) is not bool:
            errors.append('必需标记必须为布尔值')
    if errors:
        return errors
    for required in (s for s in DEFAULT_FLOWS[stage] if s['required']):
        row = next((s for s in steps if s['id'] == required['id']), None)
        if not row or row['capability'] != required['capability'] or not row['required']:
            errors.append('必须保留：' + required['title'])
    order = [s['id'] for s in steps]
    if stage == 'production' and not errors:
        if not order.index('confirm') < order.index('generate') < order.index('review') < order.index('archive'):
            errors.append('必须先确认分镜与费用，再生成，再验收归档')
    if stage != 'production' and steps[-1]['id'] != 'confirm':
        errors.append('流程必须以用户确认为终点')
    return errors


def diff_steps(before, after):
    old = {s['id']: s for s in before}
    new = {s['id']: s for s in after}
    rows = []
    for ident in new:
        if ident not in old:
            rows.append('新增步骤：' + new[ident]['title'])
        elif new[ident]['title'] != old[ident]['title']:
            rows.append('改名：' + old[ident]['title'] + ' → ' + new[ident]['title'])
    for ident in old:
        if ident not in new:
            rows.append('移除步骤：' + old[ident]['title'])
    common_old = [i for i in old if i in new]
    common_new = [i for i in new if i in old]
    if common_old != common_new:
        rows.append('调整顺序')
    return rows


def _public_https(url):
    if not isinstance(url, str) or len(url) > 300:
        return False
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        return False
    host = parts.hostname.lower()
    if host == 'localhost' or host.endswith('.localhost') or host.endswith('.internal') or '.' not in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False  # literal IPs are refused to avoid pointing the server at private networks
    except ValueError:
        return True


class Platform:
    def __init__(self, root, legacy=None, environment=None):
        """legacy: {connection_id: callable -> {'url','key','model','keySource', ...}}"""
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.legacy = legacy or {}
        self.environment = environment or (lambda: [])
        self.lock = threading.RLock()

    # ---------- storage helpers ----------
    def _write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + '.' + secrets.token_hex(8) + '.tmp')
        try:
            with temp.open('x', encoding='utf-8') as stream:
                os.chmod(temp, 0o600)
                json.dump(value, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)

    def _read(self, path, default=None):
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return copy.deepcopy(default)
        except (OSError, ValueError):
            raise PlatformError(503, '配置文件损坏，请检查服务器数据目录') from None

    def _keep(self, folder, limit=50):
        rows = sorted(folder.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in rows[limit:]:
            path.unlink(missing_ok=True)

    # ---------- secrets (write-only) ----------
    def _vault(self):
        return self._read(self.root / 'secrets.json', {})

    def secret(self, ref):
        entry = self._vault().get(ref)
        return entry.get('value', '') if isinstance(entry, dict) else ''

    def set_secret(self, payload):
        if not isinstance(payload, dict) or set(payload) not in ({'ref', 'value'}, {'ref', 'clear'}):
            raise PlatformError(400, '密钥请求字段无效')
        ref = payload['ref']
        if not isinstance(ref, str) or ref not in self._connection_ids():
            raise PlatformError(400, '连接不存在')
        with self.lock:
            vault = self._vault()
            if 'clear' in payload:
                if payload['clear'] is not True:
                    raise PlatformError(400, '密钥请求字段无效')
                vault.pop(ref, None)
                event = 'secret_clear'
            else:
                value = payload['value']
                if not isinstance(value, str) or not 8 <= len(value) <= 512 or re.search(r'[\s\x00-\x1f\x7f]', value):
                    raise PlatformError(400, '密钥需为8–512位且不含空白字符')
                vault[ref] = {'value': value, 'updatedAt': int(time.time())}
                event = 'secret_set'
            self._write(self.root / 'secrets.json', vault)
        return self.overview(), event, ref

    def _secret_status(self, ref, legacy_key='', legacy_source=''):
        entry = self._vault().get(ref)
        if isinstance(entry, dict) and entry.get('value'):
            return {'configured': True, 'source': '中台写入', 'last4': entry['value'][-4:], 'updatedAt': entry.get('updatedAt')}
        if legacy_key:
            return {'configured': True, 'source': legacy_source or '服务器凭据', 'last4': legacy_key[-4:], 'updatedAt': None}
        return {'configured': False, 'source': '', 'last4': '', 'updatedAt': None}

    # ---------- versioned platform config ----------
    def _default_config(self):
        video = self._legacy('wan-video')
        value = {'connections': [],
                 'video': {'model': video.get('model') or 'wan3.0-video',
                           'resolution': video.get('resolution') if video.get('resolution') in RESOLUTIONS else '720P',
                           'watermark': False,  # matches the server default before the console existed
                           'timeoutSeconds': int(video.get('timeoutSeconds') or 1800)},
                 'image': self._legacy_image(),
                 'personalization': copy.deepcopy(PERSONALIZATION_DEFAULT), 'videoUnderstanding':copy.deepcopy(WATCH_DEFAULT),'creationBoard':copy.deepcopy(BOARD_DEFAULT)}
        value['revision'] = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:32]
        value['publishedAt'] = None
        return value

    def _legacy_image(self):
        legacy = self._legacy('image-gen')
        return {'baseUrl': legacy.get('url') or IMAGE_DEFAULT['baseUrl'], 'model': legacy.get('model') or IMAGE_DEFAULT['model']}

    def config(self):
        with self.lock:
            value = self._read(self.root / 'config.json')
            if not value:
                return self._default_config()
            value.setdefault('image', self._legacy_image())  # configs published before image support
            value.setdefault('personalization', copy.deepcopy(PERSONALIZATION_DEFAULT))
            value['videoUnderstanding']={**copy.deepcopy(WATCH_DEFAULT),**(value.get('videoUnderstanding') or {})}  # new keys get defaults
            value['creationBoard']={**copy.deepcopy(BOARD_DEFAULT),**(value.get('creationBoard') or {})}
            return value

    def _legacy(self, ident):
        try:
            value = self.legacy[ident]() if ident in self.legacy else {}
        except Exception:
            value = {}
        return value if isinstance(value, dict) else {}

    def _connection_ids(self):
        return list(BUILTIN) + [c['id'] for c in self.config()['connections']]

    def chat_connections(self):
        return ['qwen-domestic'] + [c['id'] for c in self.config()['connections']]

    def resolve(self, ident):
        """Server-side only: return {'url','key','model'} for a chat connection, or None."""
        if ident == 'qwen-domestic':
            legacy = self._legacy(ident)
            return {'url': legacy.get('url', ''), 'key': self.secret(ident) or legacy.get('key', ''), 'model': legacy.get('model', '')}
        row = next((c for c in self.config()['connections'] if c['id'] == ident), None)
        if not row:
            return None
        return {'url': row['endpoint'], 'key': self.secret(ident), 'model': row['defaultModel']}

    def video_settings(self):
        """Server-side settings for the Wan provider (includes the key)."""
        legacy = self._legacy('wan-video')
        video = self.config()['video']
        key = self.secret('wan-video') or legacy.get('key', '')
        if not key:
            raise RuntimeError('未配置千问视频 API Key')
        return {'key': key, 'base': (legacy.get('url') or 'https://maas.qianwenaiapi.com/api/v1').rstrip('/'),
                'model': video['model'], 'resolution': video['resolution'], 'watermark': video['watermark'],
                'timeout': video['timeoutSeconds']}

    def image_settings(self):
        """Server-side settings for the image provider (includes the key)."""
        legacy = self._legacy('image-gen')
        key = self.secret('image-gen') or legacy.get('key', '')
        if not key:
            raise RuntimeError('未配置图片生成 API Key')
        image = self.config()['image']
        return {'key': key, 'base': image['baseUrl'].rstrip('/'), 'model': image['model']}

    def board_settings(self):
        return copy.deepcopy(self.config()['creationBoard'])

    def personalization(self):
        return copy.deepcopy(self.config()['personalization'])

    def parser_token(self):
        return self.secret('reference-parser')

    def _validate_config(self, value):
        if not isinstance(value, dict) or set(value) != {'connections', 'video', 'image', 'personalization', 'videoUnderstanding', 'creationBoard'}:
            raise PlatformError(400, '平台配置字段无效')
        try:
            _profile_rules.validate_settings(value['personalization'])
            validate_watch(value['videoUnderstanding'])
            validate_board(value['creationBoard'])
        except ValueError as error:
            raise PlatformError(400, str(error)) from None
        image = value['image']
        if not isinstance(image, dict) or set(image) != {'baseUrl', 'model'}:
            raise PlatformError(400, '图片生成配置字段无效')
        if not _public_https(image['baseUrl']):
            raise PlatformError(400, '图片接口地址必须是公网 HTTPS 地址')
        if not isinstance(image['model'], str) or not MODEL_ID.fullmatch(image['model']):
            raise PlatformError(400, '图片模型ID无效')
        connections = value['connections']
        if not isinstance(connections, list) or len(connections) > MAX_CUSTOM:
            raise PlatformError(400, '自定义模型连接最多%d个' % MAX_CUSTOM)
        seen = set()
        for row in connections:
            if not isinstance(row, dict) or set(row) != {'id', 'name', 'endpoint', 'defaultModel'}:
                raise PlatformError(400, '模型连接字段无效')
            if not isinstance(row['id'], str) or not CONNECTION_ID.fullmatch(row['id']) or row['id'] in BUILTIN or row['id'] in seen:
                raise PlatformError(400, '连接ID需为3–31位小写字母、数字或短横线，且不能重复')
            seen.add(row['id'])
            if not isinstance(row['name'], str) or not 1 <= len(row['name'].strip()) <= 30:
                raise PlatformError(400, '连接名称需1–30字')
            if not _public_https(row['endpoint']):
                raise PlatformError(400, '接口地址必须是公网 HTTPS 地址（不接受 IP、本机或内网主机名）')
            if not isinstance(row['defaultModel'], str) or not MODEL_ID.fullmatch(row['defaultModel']):
                raise PlatformError(400, '默认模型ID无效')
        video = value['video']
        if not isinstance(video, dict) or set(video) != {'model', 'resolution', 'watermark', 'timeoutSeconds'}:
            raise PlatformError(400, '视频生成配置字段无效')
        if not isinstance(video['model'], str) or not MODEL_ID.fullmatch(video['model']):
            raise PlatformError(400, '视频模型ID无效')
        if video['resolution'] not in RESOLUTIONS:
            raise PlatformError(400, '默认分辨率只能是480P、720P或1080P')
        if type(video['watermark']) is not bool:
            raise PlatformError(400, '水印设置必须为布尔值')
        if type(video['timeoutSeconds']) is not int or not 60 <= video['timeoutSeconds'] <= 3600:
            raise PlatformError(400, '视频任务等待上限为60–3600秒')

    def publish(self, payload, in_use=()):
        base = {'expectedRevision', 'connections', 'video'}
        if not isinstance(payload, dict) or not (set(payload) == {'expectedRevision', 'rollback'} or base <= set(payload) <= base | {'image', 'personalization','videoUnderstanding','creationBoard'}):
            raise PlatformError(400, '平台配置请求无效')
        with self.lock:
            old = self.config()
            if payload['expectedRevision'] != old['revision']:
                raise PlatformError(409, '平台配置已有新版本，请刷新后重试')
            if 'rollback' in payload:
                ident = payload['rollback']
                if not isinstance(ident, str) or not re.fullmatch(r'[a-f0-9]{32}', ident):
                    raise PlatformError(404, '配置版本不存在')
                saved = self._read(self.root / 'versions' / (ident + '.json'))
                if not saved:
                    raise PlatformError(404, '配置版本不存在')
                body, event = {'connections': saved['connections'], 'video': saved['video'], 'image': saved.get('image') or old['image'],
                               'personalization': saved.get('personalization') or old['personalization'],'videoUnderstanding':saved.get('videoUnderstanding',old['videoUnderstanding']),'creationBoard':{**BOARD_DEFAULT,**saved.get('creationBoard',old['creationBoard'])}}, 'platform_rollback'
            else:
                body, event = {'connections': payload['connections'], 'video': payload['video'], 'image': payload.get('image', old['image']),
                               'personalization': payload.get('personalization', old['personalization']),'videoUnderstanding':payload.get('videoUnderstanding',old['videoUnderstanding']),'creationBoard':payload.get('creationBoard',old['creationBoard'])}, 'platform_publish'
            self._validate_config(body)
            removed = {c['id'] for c in old['connections']} - {c['id'] for c in body['connections']}
            busy = sorted(removed & set(in_use))
            if busy:
                raise PlatformError(400, '连接仍被AI场景使用，请先改用其他连接：' + '、'.join(busy))
            new = dict(body, revision=secrets.token_hex(16), publishedAt=int(time.time()))
            self._write(self.root / 'versions' / (old['revision'] + '.json'), old)
            self._write(self.root / 'versions' / (new['revision'] + '.json'), new)
            self._write(self.root / 'config.json', new)
            self._keep(self.root / 'versions')
            vault = self._vault()
            if any(ref in vault for ref in removed):
                for ref in removed:
                    vault.pop(ref, None)
                self._write(self.root / 'secrets.json', vault)
        return self.overview(), event, new['revision']

    def versions(self):
        rows = []
        for path in (self.root / 'versions').glob('*.json'):
            try:
                value = json.loads(path.read_text(encoding='utf-8'))
                rows.append({'revision': value['revision'], 'publishedAt': value.get('publishedAt'),
                             'connections': len(value.get('connections', [])), 'videoModel': value.get('video', {}).get('model')})
            except (OSError, ValueError, KeyError):
                pass
        return sorted(rows, key=lambda r: r['publishedAt'] or 0, reverse=True)[:20]

    def overview(self):
        config = self.config()
        rows = []
        for ident, meta in BUILTIN.items():
            legacy = self._legacy(ident)
            url = config['image']['baseUrl'] if ident == 'image-gen' else legacy.get('url', '')
            parts = urlsplit(url) if isinstance(url, str) else None
            endpoint = (parts.scheme + '://' + parts.hostname + (':%d' % parts.port if parts.port else '') + parts.path) if parts and parts.scheme in ('http', 'https') and parts.hostname else '未配置'
            rows.append({'id': ident, 'name': meta['name'], 'kind': meta['kind'], 'builtin': True, 'endpoint': endpoint,
                         'defaultModel': config['image']['model'] if ident == 'image-gen' else legacy.get('model', ''),
                         'credential': self._secret_status(ident, legacy.get('key', ''), legacy.get('keySource', ''))})
        for row in config['connections']:
            rows.append(dict(row, kind='chat', builtin=False, credential=self._secret_status(row['id'])))
        return {'revision': config['revision'], 'publishedAt': config.get('publishedAt'),
                'connections': rows, 'custom': copy.deepcopy(config['connections']), 'video': config['video'], 'image': config['image'], 'personalization': config['personalization'], 'videoUnderstanding':config['videoUnderstanding'],'creationBoard':config['creationBoard'],
                'resolutions': list(RESOLUTIONS), 'services': self.environment(), 'versions': self.versions(),
                'notice': '密钥只写不读：保存后只显示来源与末4位。中台写入的密钥优先于服务器凭据文件和环境变量；清除后恢复使用服务器凭据。'}

    # ---------- workflows ----------
    def _workflow(self, stage):
        value = self._read(self.root / 'workflows' / (stage + '.json'))
        if value:
            return value
        steps = copy.deepcopy(DEFAULT_FLOWS[stage])
        seed = hashlib.sha256(json.dumps(steps, sort_keys=True).encode()).hexdigest()[:32]
        return {'stage': stage, 'revision': seed,
                'published': {'version': 'default-v1', 'steps': steps, 'publishedAt': None}, 'draft': None}

    def workflows(self):
        rows = []
        for stage, name in STAGES.items():
            value = self._workflow(stage)
            draft = value['draft']
            history = []
            for path in (self.root / 'workflows' / stage).glob('*.json'):
                try:
                    saved = json.loads(path.read_text(encoding='utf-8'))
                    history.append({'version': saved['version'], 'publishedAt': saved.get('publishedAt'), 'steps': len(saved['steps'])})
                except (OSError, ValueError, KeyError):
                    pass
            rows.append({'stage': stage, 'name': name, 'revision': value['revision'], 'published': value['published'],
                         'draft': draft, 'defaults': copy.deepcopy(DEFAULT_FLOWS[stage]),
                         'diff': diff_steps(value['published']['steps'], draft['steps']) if draft else [],
                         'errors': validate_steps(stage, draft['steps']) if draft else [],
                         'versions': sorted(history, key=lambda r: r['publishedAt'] or 0, reverse=True)[:20]})
        return {'boards': BOARDS, 'capabilities': CAPABILITIES, 'workflows': rows,
                'notice': '流程定义由管理员发布，小程序固定组件渲染尚未上线（需客户端版本审核）。发布只改变数据，不下发代码或调用地址。'}

    def workflow_action(self, stage, action, payload):
        if stage not in STAGES:
            raise PlatformError(404, '流程不存在')
        if action == 'validate':
            if not isinstance(payload, dict) or set(payload) != {'steps'}:
                raise PlatformError(400, '校验请求字段无效')
            return {'errors': validate_steps(stage, payload['steps'])}, None, None
        with self.lock:
            value = self._workflow(stage)
            if not isinstance(payload, dict) or payload.get('expectedRevision') != value['revision']:
                raise PlatformError(409, '流程已有新版本，请刷新后重试')
            now = int(time.time())
            if action == 'draft':
                if set(payload) == {'expectedRevision', 'discard'} and payload['discard'] is True:
                    value['draft'] = None
                    event, ref = 'workflow_draft_discard', stage
                elif set(payload) == {'expectedRevision', 'steps'}:
                    # Drafts may break ordering rules (shown as errors, publish blocked) but never structure.
                    structural = [e for e in validate_steps(stage, payload['steps']) if not e.startswith(('必须', '流程必须'))]
                    if structural:
                        raise PlatformError(400, structural[0])
                    value['draft'] = {'steps': payload['steps'], 'updatedAt': now}
                    event, ref = 'workflow_draft', stage
                else:
                    raise PlatformError(400, '草案请求字段无效')
            elif action == 'publish':
                if set(payload) != {'expectedRevision'} or not value['draft']:
                    raise PlatformError(400, '没有可发布的草案')
                errors = validate_steps(stage, value['draft']['steps'])
                if errors:
                    raise PlatformError(400, '草案未通过校验：' + errors[0])
                version = stage + '-' + secrets.token_hex(6)
                published = {'version': version, 'steps': value['draft']['steps'], 'publishedAt': now}
                self._write(self.root / 'workflows' / stage / (version + '.json'), published)
                self._keep(self.root / 'workflows' / stage)
                value['published'], value['draft'] = published, None
                event, ref = 'workflow_publish', version
            elif action == 'rollback':
                target = payload.get('version')
                if set(payload) != {'expectedRevision', 'version'} or not isinstance(target, str) or not re.fullmatch(r'[a-z]+-[a-f0-9]{12}|default-v1', target):
                    raise PlatformError(400, '回滚版本无效')
                steps = copy.deepcopy(DEFAULT_FLOWS[stage]) if target == 'default-v1' else (self._read(self.root / 'workflows' / stage / (target + '.json')) or {}).get('steps')
                if not steps:
                    raise PlatformError(404, '流程版本不存在')
                version = stage + '-' + secrets.token_hex(6)
                published = {'version': version, 'steps': steps, 'publishedAt': now, 'restoredFrom': target}
                self._write(self.root / 'workflows' / stage / (version + '.json'), published)
                self._keep(self.root / 'workflows' / stage)
                value['published'], value['draft'] = published, None
                event, ref = 'workflow_rollback', version
            else:
                raise PlatformError(404, '管理接口不存在')
            value['revision'] = secrets.token_hex(16)
            self._write(self.root / 'workflows' / (stage + '.json'), value)
        return self.workflows(), event, ref

    def effective(self, stage):
        """Read-only published definition for future client use (no user overrides yet)."""
        if stage not in STAGES:
            raise PlatformError(404, '流程不存在')
        value = self._workflow(stage)
        return {'stage': stage, 'version': value['published']['version'], 'steps': value['published']['steps']}
