"""长期资产台账：把爆款拆解链路的每一步（用户、素材、理解、拆解、方法、作品、数据）同步到飞书多维表格。

数据先写本机 SQLite 发件箱（outbox），再由后台线程投递飞书；飞书不可用时按指数退避重试，不阻塞用户。
素材附件：封面 + 中段两张 + 结尾一张共 4 张截图，以及整段视频的低清压缩版（方便核对）。
飞书里「我的评分 / 标签 / 运营备注」等列归人工维护，系统只写自己的列，不会覆盖。
"""
import hashlib, json, re, sqlite3, subprocess, threading, time, uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

T, NUM, DATE, URL, FILE = 1, 2, 5, 15, 17
TABLES = [
    ('users', '用户', [('用户ID', T), ('昵称', T), ('手机号', T), ('手机号(脱敏)', T), ('体验账号', T), ('首次使用', DATE), ('最近活跃', DATE),
                      ('拆解视频数', NUM), ('作品数', NUM), ('运营备注', T)]),
    ('sources', '素材库', [('素材ID', T), ('标题文案', T), ('平台', T), ('链接', URL), ('作品编号', T), ('话题', T), ('作者', T), ('作者粉丝数', NUM),
                         ('点赞', NUM), ('评论', NUM), ('收藏', NUM), ('分享', NUM), ('发布时间', DATE), ('时长秒', NUM), ('图文', T),
                         ('大致内容', T), ('截图', FILE), ('低清视频', FILE), ('提交用户', T), ('提交次数', NUM), ('首次入库', DATE), ('最近提交', DATE),
                         ('我的评分', NUM), ('我的标签', T), ('运营备注', T)]),
    ('cards', '理解卡', [('理解ID', T), ('素材ID', T), ('标题文案', T), ('类型', T), ('标签', T), ('概述', T), ('逐段画面', T), ('屏幕文字', T),
                       ('语音转写', T), ('吸引力来源', T), ('状态', T), ('生成时间', DATE)]),
    ('breakdowns', '拆解库', [('拆解ID', T), ('素材ID', T), ('用户ID', T), ('标题文案', T), ('方案', T), ('为什么火', T), ('复刻难度', NUM), ('难度说明', T),
                            ('传播驱动', T), ('账号角色', T), ('最该学', T), ('评论区打法', T), ('评论权重', T), ('用户纠正', T), ('全部字段', T),
                            ('拆解时间', DATE), ('我的评分', NUM), ('运营备注', T)]),
    ('methods', '方法卡', [('方法ID', T), ('方法', T), ('可学程度', T), ('学法', T), ('出现次数', NUM), ('来源素材', T), ('最近出现', DATE),
                         ('用过次数', NUM), ('效果评价', T), ('运营备注', T)]),
    ('works', '作品库', [('作品ID', T), ('用户ID', T), ('来源拆解ID', T), ('素材ID', T), ('类型', T), ('标题', T), ('正文', T), ('发布链接', URL),
                       ('生成时间', DATE), ('运营备注', T)]),
    ('metrics', '数据回流', [('记录ID', T), ('作品ID', T), ('用户ID', T), ('日期', DATE), ('来源', T), ('播放', NUM), ('点赞', NUM), ('评论', NUM),
                          ('收藏', NUM), ('分享', NUM), ('完播率', NUM), ('采集时间', DATE)]),
]
KEYS = {t: fields[0][0] for t, _, fields in TABLES}
PLAN_META = [('拆解ID', T), ('用户ID', T), ('素材ID', T), ('标题文案', T), ('方案版本', NUM), ('为什么火', T), ('用户纠正', T), ('拆解时间', DATE), ('我的评分', NUM), ('优化备注', T)]


def key_field(table):
    return '拆解ID' if table.startswith('plan:') else KEYS[table]
SYSTEM_SKIP = {'我的评分', '我的标签', '运营备注', '用过次数', '效果评价', '优化备注'}  # 人工维护的列，系统不写


def text(value, limit=2000):
    value = '' if value is None else str(value)
    return value[:limit]


def ms(seconds):
    try:
        return int(float(seconds) * 1000)
    except (TypeError, ValueError):
        return None


def when(value):
    """Epoch seconds/ms or ISO time → Feishu date (ms)."""
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit()):
        n = float(value)
        return int(n if n > 1e11 else n * 1000) if n > 0 else None
    if isinstance(value, str) and value.strip():
        import datetime
        try:
            return int(datetime.datetime.fromisoformat(value.strip().replace('Z', '+00:00')).timestamp() * 1000)
        except ValueError:
            return None
    return None


class FeishuBase:
    """Minimal bitable client: tenant token, table/field bootstrap, upsert by stable key, attachment upload."""
    def __init__(self, config, opener=urlopen):
        self.config = config; self.opener = opener; self.token = ''; self.expires = 0

    def auth(self):
        if time.time() < self.expires:
            return
        body = json.dumps({'app_id': self.config['appId'], 'app_secret': self.config['appSecret']}).encode()
        with self.opener(Request('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', data=body, headers={'Content-Type': 'application/json'}), timeout=20) as r:
            data = json.load(r)
        if data.get('code') != 0:
            raise RuntimeError(f"飞书鉴权失败 code={data.get('code')}")
        self.token = data['tenant_access_token']; self.expires = time.time() + max(0, data.get('expire', 0) - 60)

    def call(self, method, path, body=None, raw=None, content_type=None):
        self.auth()
        headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': content_type or 'application/json'}
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        try:
            with self.opener(Request('https://open.feishu.cn/open-apis' + path, data=data, headers=headers, method=method), timeout=120) as r:
                result = json.load(r)
        except HTTPError as e:
            try:
                detail = json.loads(e.read()); code = detail.get('code'); msg = str(detail.get('msg') or '')[:120]
            except Exception:
                code, msg = 'unknown', ''
            raise RuntimeError(f'飞书接口失败 HTTP={e.code} code={code} {msg}') from None
        if result.get('code') != 0:
            raise RuntimeError(f"飞书接口失败 code={result.get('code')} {path.split('?')[0]}")
        return result.get('data') or {}

    def list(self, path):
        rows, page = [], ''
        while True:
            data = self.call('GET', path + ('&' if '?' in path else '?') + 'page_size=100' + ('&page_token=' + page if page else ''))
            rows += data.get('items') or []
            if not data.get('has_more'):
                return rows
            page = data.get('page_token') or ''
            if not page:
                return rows

    def ensure(self, state):
        """Create missing tables/fields (never deletes or renames). Returns {key: {'id':..., 'fields': {...}}}."""
        prefix = '/bitable/v1/apps/' + self.config['baseToken']
        existing = {t['name']: t['table_id'] for t in self.list(prefix + '/tables')}
        for key, name, fields in TABLES:
            table_id = (state.get(key) or {}).get('id') or existing.get(name)
            if not table_id:
                table_id = self.call('POST', prefix + '/tables', {'table': {'name': name, 'default_view_name': '全部', 'fields': [{'field_name': fields[0][0], 'type': fields[0][1]}]}})['table_id']
            have = {f['field_name']: f for f in self.list(prefix + '/tables/' + table_id + '/fields')}
            for field, kind in fields:
                if field in have:
                    if have[field].get('type') != kind:
                        raise RuntimeError(f'字段类型冲突：{name}/{field}，请人工处理')
                    continue
                self.call('POST', prefix + '/tables/' + table_id + '/fields', {'field_name': field, 'type': kind})
            state[key] = {'id': table_id, 'name': name}
        return state

    def ensure_plan(self, state, plan_id, name, labels):
        """用户自定义拆解方案：在飞书里单独建一张「拆解库·方案名」表，方案的每个字段一列，方便逐项优化。"""
        plans = state.setdefault('plans', {}); entry = plans.get(plan_id) or {}
        prefix = '/bitable/v1/apps/' + self.config['baseToken']
        if not entry.get('id'):
            title = '拆解库·仅本次调整' if plan_id == 'once' else ('拆解库·' + re.sub(r'[\\/:*?"<>|\[\]]', '', name or '自定义方案'))[:40] + '·' + plan_id[-4:]
            existing = {t['name']: t['table_id'] for t in self.list(prefix + '/tables')}
            entry = {'id': existing.get(title) or self.call('POST', prefix + '/tables', {'table': {'name': title, 'default_view_name': '全部', 'fields': [{'field_name': '拆解ID', 'type': T}]}})['table_id'], 'name': title, 'fields': []}
        have = set(entry.get('fields') or [])
        wanted = [(f, k) for f, k in PLAN_META] + [(label, T) for label in labels if label not in dict(PLAN_META)]
        missing = [(f, k) for f, k in wanted if f not in have]
        if missing:
            current = {f['field_name'] for f in self.list(prefix + '/tables/' + entry['id'] + '/fields')}
            for f, k in missing:
                if f not in current:
                    self.call('POST', prefix + '/tables/' + entry['id'] + '/fields', {'field_name': f, 'type': k})
            entry['fields'] = sorted(have | {f for f, _ in wanted})
        plans[plan_id] = entry
        return entry['id']

    def upsert(self, table_id, key_field, fields):
        prefix = f"/bitable/v1/apps/{self.config['baseToken']}/tables/{table_id}/records"
        found = self.call('POST', prefix + '/search', {'filter': {'conjunction': 'and', 'conditions': [{'field_name': key_field, 'operator': 'is', 'value': [fields[key_field]]}]}, 'page_size': 2}).get('items', [])
        if found:
            return self.call('PUT', prefix + '/' + found[0]['record_id'], {'fields': fields})['record']['record_id']
        # 飞书要求 client_token 是 UUIDv4 格式：用稳定哈希造一个 v4 形状的值，重试时不会重复建行
        raw = bytearray(hashlib.sha256((prefix + '|' + str(fields[key_field])).encode()).digest()[:16]); raw[6] = (raw[6] & 0x0F) | 0x40; raw[8] = (raw[8] & 0x3F) | 0x80
        token = str(uuid.UUID(bytes=bytes(raw)))
        return self.call('POST', prefix + '?client_token=' + token, {'fields': fields})['record']['record_id']

    def attach(self, path, name, kind):
        data = Path(path).read_bytes(); boundary = 'youai' + uuid.uuid4().hex; body = b''
        parts = {'file_name': name, 'parent_type': 'bitable_image' if kind == 'image' else 'bitable_file', 'parent_node': self.config['baseToken'], 'size': str(len(data))}
        for k, v in parts.items():
            body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode() + data + f'\r\n--{boundary}--\r\n'.encode()
        return self.call('POST', '/drive/v1/medias/upload_all', raw=body, content_type='multipart/form-data; boundary=' + boundary)['file_token']


class Ledger:
    def __init__(self, root, config_path, state_path, ffmpeg=None, client_factory=None, runner=subprocess.run, clock=time.time):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.config_path = Path(config_path) if config_path else None; self.state_path = Path(state_path) if state_path else None
        self.ffmpeg = ffmpeg; self.runner = runner; self.clock = clock
        self.client_factory = client_factory or (lambda cfg: FeishuBase(cfg)); self._client = None; self.lock = threading.Lock(); self.wake = threading.Event()
        with self.db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY,tbl TEXT,key TEXT,fields TEXT,media TEXT,status TEXT,attempts INTEGER DEFAULT 0,next REAL DEFAULT 0,error TEXT DEFAULT '',created REAL,updated REAL);
            CREATE INDEX IF NOT EXISTS outbox_due ON outbox(status,next);
            CREATE TABLE IF NOT EXISTS uploads(path TEXT PRIMARY KEY,sha TEXT,token TEXT);
            CREATE TABLE IF NOT EXISTS methods(id TEXT PRIMARY KEY,name TEXT,level TEXT,how TEXT,sources TEXT,count INTEGER,last REAL);
            CREATE TABLE IF NOT EXISTS sources(sha TEXT PRIMARY KEY,users TEXT,count INTEGER,first REAL);''')

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.root / 'ledger.sqlite', timeout=30)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    # ---------- enqueue (merges pending updates of the same record) ----------
    def put(self, table, fields, media=None):
        key = text(fields.get(key_field(table)), 200)
        if not key:
            return None
        ident = hashlib.sha256((table + '|' + key).encode()).hexdigest()[:32]; now = self.clock()
        with self.lock, self.db() as db:
            row = db.execute('SELECT fields,media,status FROM outbox WHERE id=?', (ident,)).fetchone()
            merged = {**(json.loads(row[0]) if row else {}), **{k: v for k, v in fields.items() if v is not None and v != ''}}
            merged_media = {**(json.loads(row[1]) if row and row[1] else {}), **(media or {})}
            db.execute('INSERT OR REPLACE INTO outbox VALUES(?,?,?,?,?,?,?,?,?,?,?)', (ident, table, key, json.dumps(merged, ensure_ascii=False), json.dumps(merged_media, ensure_ascii=False),
                                                                                    'pending', 0, 0, '', now, now))
        self.wake.set()
        return ident

    # ---------- the chain ----------
    def user(self, user_id, profile=None, phone='', counts=None):
        p = profile or {}
        self.put('users', {'用户ID': user_id, '昵称': text(p.get('nickname'), 60), '手机号': phone, '手机号(脱敏)': text(p.get('phoneMasked'), 40),
                           '体验账号': '是' if p.get('trial') else '否', '最近活跃': ms(self.clock()), **(counts or {})})

    def source(self, user_id, reference, glance=None):
        asset = reference.get('asset') if isinstance(reference.get('asset'), dict) else {}
        sha = asset.get('sha256')
        if not sha:
            return None
        src = reference.get('source') if isinstance(reference.get('source'), dict) else {}
        author = src.get('author') if isinstance(src.get('author'), dict) else {}
        stats = src.get('stats') if isinstance(src.get('stats'), dict) else {}
        media = asset.get('media') if isinstance(asset.get('media'), dict) else {}
        with self.lock, self.db() as db:
            row = db.execute('SELECT users,count,first FROM sources WHERE sha=?', (sha,)).fetchone()
            users = json.loads(row[0]) if row else []
            if user_id and user_id not in users:
                users.append(user_id)
            count = (row[1] if row else 0) + 1; first = row[2] if row else self.clock()
            db.execute('INSERT OR REPLACE INTO sources VALUES(?,?,?,?)', (sha, json.dumps(users[-50:]), count, first))
        link = reference.get('resolvedUrl') or reference.get('url') or ''
        created = src.get('createdAt') or src.get('createTime')
        fields = {'素材ID': sha, '标题文案': text(reference.get('description') or reference.get('title'), 500), '平台': '抖音' if reference.get('platform', 'douyin') == 'douyin' else text(reference.get('platform'), 20),
                  '链接': {'link': link, 'text': text(reference.get('title') or link, 80)} if str(link).startswith('http') else None,
                  '作品编号': text(src.get('contentId'), 40), '话题': ' '.join('#' + str(h) for h in (src.get('hashtags') or [])[:12]),
                  '作者': text(author.get('nickname'), 60), '作者粉丝数': author.get('followerCount') if isinstance(author.get('followerCount'), int) else None,
                  '点赞': stats.get('digg_count'), '评论': stats.get('comment_count'), '收藏': stats.get('collect_count'), '分享': stats.get('share_count'),
                  '发布时间': when(created),
                  '时长秒': media.get('durationSeconds'), '图文': '是' if src.get('kind') == 'gallery' else '否',
                  '大致内容': text((glance or {}).get('overview'), 200), '提交用户': ', '.join(users[-20:]), '提交次数': count,
                  '首次入库': ms(first), '最近提交': ms(self.clock())}
        files = {'path': asset.get('storagePath') or '', 'cover': src.get('coverUrl') or reference.get('coverUrl') or '', 'duration': media.get('durationSeconds') or 0}
        return self.put('sources', fields, {'source': files})

    def card(self, sha, analysis, title=''):
        u = analysis.get('understanding') if isinstance(analysis.get('understanding'), dict) else {}
        if not sha or not u:
            return None
        timeline = '\n'.join(f"{r.get('start')}–{r.get('end')}秒 {r.get('what', '')}" for r in (u.get('timeline') or []) if isinstance(r, dict))
        screen = ' / '.join(str(i.get('text', '')) for i in ((analysis.get('screenText') or {}).get('items') or [])[:40] if isinstance(i, dict))
        shares = '　'.join(f"{s.get('label')} {s.get('percent')}%" for s in (u.get('valueShares') or []) if isinstance(s, dict))
        return self.put('cards', {'理解ID': sha, '素材ID': sha, '标题文案': text(title, 200), '类型': text(u.get('type'), 60), '标签': ' '.join('#' + str(t) for t in (u.get('tags') or [])),
                                  '概述': text(u.get('overview'), 1000), '逐段画面': text(timeline, 4000), '屏幕文字': text(screen, 3000),
                                  '语音转写': text(((analysis.get('audio') or {}).get('transcript') or {}).get('text'), 4000), '吸引力来源': shares,
                                  '状态': {'ready': '已识别', 'local_only': '额度用完未识别', 'unavailable': '未识别'}.get(u.get('status'), text(u.get('status'), 20)), '生成时间': ms(self.clock())})

    def breakdown(self, user_id, session, title=''):
        bd = session.get('breakdown') if isinstance(session.get('breakdown'), dict) else {}
        if not bd.get('fields'):
            return None
        ins = bd.get('insight') or {}; sha = session.get('asset') or ''
        def value_text(v):
            if isinstance(v, list):
                return '\n'.join(('· ' + str(r.get('item', '')) + (f"（{r.get('level')}）" if r.get('level') else '') + (f" 学法：{r.get('how')}" if r.get('how') else '')) if isinstance(r, dict) and 'item' in r
                                 else (f"{r.get('start')}–{r.get('end')}秒 {r.get('text', '')}" if isinstance(r, dict) else str(r)) for r in v)
            if isinstance(v, dict):
                return f"{v.get('score', '')}/10 {v.get('reason', '')}".strip()
            return text(v, 2000)
        all_fields = '\n\n'.join(f"【{f.get('label')}】\n{value_text(f.get('value'))}" for f in bd['fields'] if isinstance(f, dict))
        learn = next((f.get('value') for f in bd['fields'] if f.get('key') == 'learnable' and isinstance(f.get('value'), list)), [])
        best = next((r for r in learn if isinstance(r, dict) and r.get('level') == '高'), learn[0] if learn and isinstance(learn[0], dict) else {})
        diff = ins.get('difficulty') or {}; stats = ins.get('commentStats') or {}
        corrections = '\n'.join(str(c.get('text', '')) for c in (session.get('corrections') or []) if isinstance(c, dict))
        if session.get('statement'):
            corrections = (corrections + '\n' + str(session['statement'])).strip()
        ident = self.put('breakdowns', {'拆解ID': session.get('id'), '素材ID': sha, '用户ID': user_id, '标题文案': text(title, 200), '方案': text(bd.get('planName'), 40),
                                        '为什么火': text(ins.get('why'), 300), '复刻难度': diff.get('score'), '难度说明': text(diff.get('reason'), 200),
                                        '传播驱动': text(ins.get('driver'), 20), '账号角色': text(ins.get('accountRole'), 20), '最该学': text(best.get('item'), 100),
                                        '评论区打法': text(ins.get('commentPlay'), 300), '评论权重': text(stats.get('shape'), 20) + (f"（{stats.get('read')} 条）" if stats.get('read') else ''),
                                        '用户纠正': text(corrections, 1500), '全部字段': text(all_fields, 20000), '拆解时间': ms(self.clock())})
        for row in learn:
            if isinstance(row, dict) and row.get('item'):
                self.method(row, sha, title)
        plan_id = str(bd.get('planId') or session.get('planId') or '')
        if plan_id and not plan_id.startswith('builtin-'):
            labels = [str(f.get('label'))[:60] for f in bd['fields'] if isinstance(f, dict) and f.get('label')]
            row = {'拆解ID': session.get('id'), '用户ID': user_id, '素材ID': sha, '标题文案': text(title, 200), '方案版本': bd.get('version'),
                   '为什么火': text(ins.get('why'), 300), '用户纠正': text(corrections, 1500), '拆解时间': ms(self.clock())}
            for f in bd['fields']:
                if isinstance(f, dict) and f.get('label') and str(f['label'])[:60] not in row:
                    row[str(f['label'])[:60]] = text(value_text(f.get('value')), 5000)
            # 「仅本次」临时调整的方案统一进一张「拆解库·仅本次调整」，避免每次调整都新建一张表
            once = plan_id.startswith('once-')
            if once:
                row['方案'] = text(bd.get('planName'), 40); adj = session.get('adjustments') if isinstance(session.get('adjustments'), list) else []; row['调整说明'] = text('\n'.join(str(x.get('message', '')) for x in adj if isinstance(x, dict)), 1000)
            self.put('plan:' + ('once' if once else plan_id), row, {'plan': {'name': '仅本次调整' if once else text(bd.get('planName'), 30), 'labels': (['方案', '调整说明'] if once else []) + labels}})
        return ident

    def method(self, row, sha, title=''):
        name = re.sub(r'\s+', '', str(row.get('item')))[:40]
        ident = hashlib.sha256(name.encode()).hexdigest()[:16]
        with self.lock, self.db() as db:
            old = db.execute('SELECT sources,count FROM methods WHERE id=?', (ident,)).fetchone()
            sources = json.loads(old[0]) if old else []
            label = text(title, 30) or sha[:8]
            if sha and sha not in [s[0] for s in sources]:
                sources.append([sha, label])
            count = len(sources) or ((old[1] if old else 0) + 1)
            db.execute('INSERT OR REPLACE INTO methods VALUES(?,?,?,?,?,?,?)', (ident, name, text(row.get('level'), 4), text(row.get('how'), 300), json.dumps(sources[-100:], ensure_ascii=False), count, self.clock()))
        return self.put('methods', {'方法ID': ident, '方法': name, '可学程度': text(row.get('level'), 4), '学法': text(row.get('how'), 300), '出现次数': count,
                                    '来源素材': '\n'.join(s[1] for s in sources[-30:]), '最近出现': ms(self.clock())})

    def work(self, user_id, ident, kind, session=None, title='', body='', link=''):
        session = session or {}
        return self.put('works', {'作品ID': ident, '用户ID': user_id, '来源拆解ID': session.get('id'), '素材ID': session.get('asset'), '类型': kind,
                                  '标题': text(title, 200), '正文': text(body, 20000), '发布链接': {'link': link, 'text': link[:80]} if str(link).startswith('http') else None,
                                  '生成时间': ms(self.clock())})

    def metric(self, user_id, work_id, day, source, values):
        v = values or {}
        return self.put('metrics', {'记录ID': f'{work_id}|{day}|{source}', '作品ID': work_id, '用户ID': user_id, '日期': ms(int(day) * 86400) if str(day).isdigit() else None,
                                    '来源': {'public': '公开数据', 'backend': '后台截图'}.get(source, text(source, 20)), '播放': v.get('play'), '点赞': v.get('likes'),
                                    '评论': v.get('comments'), '收藏': v.get('collects'), '分享': v.get('shares'), '完播率': v.get('completion'), '采集时间': ms(self.clock())})

    # ---------- media: cover + 2 middle + end screenshots, and a low-res copy ----------
    def prepare_media(self, sha, spec):
        folder = self.root / 'media' / sha[:2] / sha; folder.mkdir(parents=True, exist_ok=True)
        path = Path(spec.get('path') or ''); shots, video = [], None
        if spec.get('cover'):
            target = folder / '0-cover.jpg'
            if not target.exists():
                try:
                    with urlopen(Request(spec['cover'], headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.douyin.com/'}), timeout=15) as r:
                        data = r.read(5 * 1024 * 1024)
                    target.write_bytes(data)
                except Exception:
                    pass
            if target.exists():
                shots.append(target)
        if self.ffmpeg and path.exists():
            duration = float(spec.get('duration') or 0)
            points = [('1-mid1', duration / 3), ('2-mid2', duration * 2 / 3), ('3-end', max(0, duration - 0.6))] if duration > 1 else [('1-first', 0)]
            if not spec.get('cover'):
                points = [('0-first', 0.2)] + points
            for name, second in points:
                target = folder / f'{name}.jpg'
                if not target.exists():
                    self.runner([self.ffmpeg, '-v', 'error', '-y', '-ss', f'{second:.2f}', '-i', str(path), '-frames:v', '1', '-vf', 'scale=720:-2', str(target)], capture_output=True, timeout=60)
                if target.exists():
                    shots.append(target)
            low = folder / 'low.mp4'
            if not low.exists():
                tmp = folder / 'low.tmp.mp4'
                self.runner([self.ffmpeg, '-v', 'error', '-y', '-i', str(path), '-vf', "scale='if(gt(iw,ih),-2,360)':'if(gt(iw,ih),360,-2)'", '-r', '24',
                             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-maxrate', '600k', '-bufsize', '1200k',
                             '-c:a', 'aac', '-b:a', '48k', '-ac', '1', '-movflags', '+faststart', str(tmp)], capture_output=True, timeout=600)
                if tmp.exists() and tmp.stat().st_size > 0:
                    tmp.replace(low)
            if low.exists() and low.stat().st_size <= 19 * 1024 * 1024:
                video = low
        return shots[:4], video

    # ---------- delivery ----------
    def client(self):
        if self._client is None:
            if not self.config_path or not self.config_path.exists():
                raise RuntimeError('飞书配置不存在')
            cfg = json.loads(self.config_path.read_text(encoding='utf-8-sig'))['management']
            client = self.client_factory(cfg)
            state = {}
            if self.state_path and self.state_path.exists():
                state = json.loads(self.state_path.read_text(encoding='utf-8'))
            state = client.ensure(state)
            if self.state_path:
                self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')
            client.tables = state; self._client = client
        return self._client

    def upload_once(self, client, path, kind):
        path = Path(path); sha = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.db() as db:
            row = db.execute('SELECT token FROM uploads WHERE path=? AND sha=?', (str(path), sha)).fetchone()
        if row:
            return row[0]
        token = client.attach(path, path.parent.name[:12] + '-' + path.name, kind)
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO uploads VALUES(?,?,?)', (str(path), sha, token))
        return token

    def deliver(self, row):
        ident, table, key, fields, media = row
        fields = {k: v for k, v in json.loads(fields).items() if k not in SYSTEM_SKIP and v is not None}
        media = json.loads(media or '{}'); client = self.client()
        if media.get('source'):
            shots, video = self.prepare_media(key, media['source'])
            if shots:
                fields['截图'] = [{'file_token': self.upload_once(client, p, 'image')} for p in shots]
            if video:
                fields['低清视频'] = [{'file_token': self.upload_once(client, video, 'file')}]
        if table.startswith('plan:'):
            meta = media.get('plan') or {}
            table_id = client.ensure_plan(client.tables, table[5:], meta.get('name') or '自定义方案', meta.get('labels') or [])
            if self.state_path:
                self.state_path.write_text(json.dumps(client.tables, ensure_ascii=False, indent=1), encoding='utf-8')
            client.upsert(table_id, '拆解ID', fields)
            return
        client.upsert(client.tables[table]['id'], KEYS[table], fields)

    def tick(self, limit=20):
        now = self.clock(); done = 0
        with self.db() as db:
            rows = db.execute("SELECT id,tbl,key,fields,media FROM outbox WHERE status='pending' AND next<=? ORDER BY created LIMIT ?", (now, limit)).fetchall()
        for row in rows:
            try:
                self.deliver(row)
                with self.db() as db:
                    db.execute("UPDATE outbox SET status='done',error='',updated=? WHERE id=? AND fields=?", (self.clock(), row[0], row[3]))
                done += 1
            except Exception as error:
                with self.db() as db:
                    attempts = (db.execute('SELECT attempts FROM outbox WHERE id=?', (row[0],)).fetchone() or [0])[0] + 1
                    db.execute("UPDATE outbox SET attempts=?,next=?,error=?,updated=? WHERE id=?", (attempts, self.clock() + min(3600, 30 * 2 ** min(attempts, 7)), text(error, 300), self.clock(), row[0]))
                if '配置不存在' in str(error) or '鉴权' in str(error):
                    self._client = None
                    break
        return done

    def status(self):
        with self.db() as db:
            rows = db.execute('SELECT tbl,status,count(*) FROM outbox GROUP BY tbl,status').fetchall()
            failing = db.execute("SELECT tbl,key,attempts,error FROM outbox WHERE status='pending' AND attempts>0 ORDER BY updated DESC LIMIT 10").fetchall()
        return {'counts': [{'table': t, 'status': s, 'count': c} for t, s, c in rows], 'failing': [{'table': t, 'key': k, 'attempts': a, 'error': e} for t, k, a, e in failing]}

    def start(self):
        def loop():
            while True:
                busy = False
                try:
                    busy = self.tick() >= 20  # 一批满了说明还有积压，马上接着发
                except Exception:
                    pass
                if not busy:
                    self.wake.wait(timeout=15); self.wake.clear()
        threading.Thread(target=loop, daemon=True, name='asset-ledger').start()
