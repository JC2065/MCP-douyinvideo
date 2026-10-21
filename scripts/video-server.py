"""Local demo renderer. pip install pillow imageio-ffmpeg; python scripts/video-server.py"""
import json
import html
import os
import re
import subprocess
import tempfile
import threading
import time
import uuid
import tomllib
import hashlib
import ipaddress
import math
import shutil
import sys
import base64
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
import imageio_ffmpeg
import importlib.util
_plan_spec=importlib.util.spec_from_file_location('analysis_plan',Path(__file__).with_name('analysis-plan.py'));_plan_module=importlib.util.module_from_spec(_plan_spec);_plan_spec.loader.exec_module(_plan_module)
_boundary_spec=importlib.util.spec_from_file_location('content_boundaries',Path(__file__).with_name('content-boundaries.py'));_boundary_module=importlib.util.module_from_spec(_boundary_spec);_boundary_spec.loader.exec_module(_boundary_module)
_prefs_spec=importlib.util.spec_from_file_location('analysis_preferences',Path(__file__).with_name('analysis-preferences.py'));_prefs_module=importlib.util.module_from_spec(_prefs_spec);_prefs_spec.loader.exec_module(_prefs_module)
_understand_spec=importlib.util.spec_from_file_location('content_understanding',Path(__file__).with_name('content-understanding.py'));_understand_module=importlib.util.module_from_spec(_understand_spec);_understand_spec.loader.exec_module(_understand_module)
_mcp_spec=importlib.util.spec_from_file_location('youai_mcp_gateway',Path(__file__).with_name('mcp-gateway.py'));_mcp_module=importlib.util.module_from_spec(_mcp_spec);_mcp_spec.loader.exec_module(_mcp_module)
_archive_spec=importlib.util.spec_from_file_location('youai_asset_archive',Path(__file__).with_name('asset-archive.py'));_archive_module=importlib.util.module_from_spec(_archive_spec);_archive_spec.loader.exec_module(_archive_module)

ROOT = Path(os.environ.get('YOUAI_RENDER_ROOT',str(Path(tempfile.gettempdir()) / 'youai-generated-videos')))
ROOT.mkdir(parents=True,exist_ok=True)
REFERENCE_ROOT = ROOT / 'references'
REFERENCE_ROOT.mkdir(exist_ok=True)
TOOL_ROOT = Path(os.environ.get('YOUAI_TOOL_ASSET_ROOT','E:/data/codexYOUAI-data/creation-tools'))
TOOL_ROOT.mkdir(parents=True,exist_ok=True)
ASSET_ROOT = Path(os.environ.get('YOUAI_ASSET_ROOT','E:/data/codexYOUAI-data/video-assets'))
ASSET_ROOT.mkdir(parents=True,exist_ok=True)
ANALYSIS_PREFERENCES=_prefs_module.Store(ASSET_ROOT/'analysis/preferences.sqlite')
ARCHIVE=_archive_module.ArchiveManager(ASSET_ROOT,os.environ.get('YOUAI_FEISHU_CONFIG','E:/data/codexYOUAI-data/credentials/feishu-matrix.json'),os.environ.get('YOUAI_FEISHU_STATE','E:/data/codexYOUAI-data/feishu-matrix-unified-state.json'))
_ledger_spec=importlib.util.spec_from_file_location('youai_asset_ledger',Path(__file__).with_name('asset-ledger.py'));_ledger_module=importlib.util.module_from_spec(_ledger_spec);_ledger_spec.loader.exec_module(_ledger_module)
# 长期资产：每一步都同步到飞书多维表格（用户 / 素材库 / 理解卡 / 拆解库 / 方法卡 / 作品库 / 数据回流）
MCP_GATEWAY=_mcp_module.Gateway(ASSET_ROOT/'mcp',os.environ.get('YOUAI_MCP_UPSTREAM','http://dtk-api-1:8000/mcp/'))
MCP_DOWNLOAD_TOOL={'name':'download_video','title':'下载抖音作品（服务器托管链接）',
    'description':'解析抖音分享链接或分享口令，由有AI服务器下载无水印视频（图文作品合成为幻灯片视频），返回作品信息和 30 分钟内有效的下载链接。链接无需 Referer 或登录，可直接用浏览器或 curl 下载。每次调用计入每日额度。',
    'inputSchema':{'type':'object','properties':{'url':{'type':'string','description':'抖音分享链接，或包含链接的整段分享文案'}},'required':['url']}}

def mcp_download(arguments):
    value=str(arguments.get('url') or '').strip()[:2000]
    if not value:raise _mcp_module.ToolError('请提供抖音分享链接')
    cfg=MCP_GATEWAY.config() or {}
    try:result=acquire_reference(value,parser_config={'baseUrl':os.environ.get('YOUAI_REFERENCE_PARSER_URL',''),'token':cfg.get('dtkKey','')},comments=False)
    except ReferenceAcquireError as error:raise _mcp_module.ToolError(str(error)) from None
    except ValueError as error:raise _mcp_module.ToolError(str(error) or '解析失败') from None
    asset=result.get('asset') or {};media=asset.get('media') or {};source=result.get('source') or {};stats=source.get('stats') or {};author=source.get('author') or {}
    link,expires=MCP_GATEWAY.file_link(os.environ.get('YOUAI_MCP_PUBLIC_BASE','https://youai888.top/youai'),asset['sha256'])
    return {'downloadUrl':link,'expiresAt':time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(expires+8*3600))+' 北京时间',
            'kind':result.get('kind') or source.get('kind') or 'video','imageCount':source.get('imageCount') or 0,
            'contentId':source.get('contentId') or result.get('videoId') or '','description':source.get('description') or result.get('description') or '',
            'hashtags':source.get('hashtags') or [],'author':{'nickname':author.get('nickname') or '','followerCount':author.get('followerCount')},
            'stats':{'likes':stats.get('digg_count'),'comments':stats.get('comment_count'),'collects':stats.get('collect_count'),'shares':stats.get('share_count')},
            'video':{'durationSeconds':media.get('durationSeconds'),'width':media.get('width'),'height':media.get('height'),'hasAudio':media.get('hasAudio'),'sizeBytes':asset.get('sizeBytes'),'sha256':asset['sha256']},
            'note':'图文作品已按每张 %s 秒合成为视频' % GALLERY_SECONDS if (result.get('kind')=='gallery') else ''}

MCP_GATEWAY.register(MCP_DOWNLOAD_TOOL,mcp_download)
LEDGER=_ledger_module.Ledger(ASSET_ROOT/'ledger',os.environ.get('YOUAI_FEISHU_CONFIG','E:/data/codexYOUAI-data/credentials/feishu-matrix.json'),os.environ.get('YOUAI_FEISHU_LEDGER_STATE',str(ASSET_ROOT/'ledger'/'feishu-tables.json')),ffmpeg=imageio_ffmpeg.get_ffmpeg_exe())
def ledger_safe(action,*args,**kwargs):
    try:return action(*args,**kwargs)
    except Exception as error:print(json.dumps({'event':'ledger.enqueue.failed','error':str(error)[:160]},ensure_ascii=False),file=sys.stderr,flush=True)
def ledger_metric(user,wid,day,source,values):ledger_safe(LEDGER.metric,user,wid,day,source,values)
def ledger_user(user):
    if not user or not AUTH:return
    ledger_safe(lambda:LEDGER.user(user,AUTH.profile(user),AUTH.phone(user) if hasattr(AUTH,'phone') else ''))
_auth_spec=importlib.util.spec_from_file_location('youai_wechat_auth',Path(__file__).with_name('wechat-auth.py'));_auth_module=importlib.util.module_from_spec(_auth_spec);_auth_spec.loader.exec_module(_auth_module)
AUTH=_auth_module.WechatAuth(os.environ['YOUAI_WECHAT_CONFIG'],ASSET_ROOT/'auth/sessions.sqlite') if os.environ.get('YOUAI_WECHAT_CONFIG') else None
REFERENCE_RELAY_STATE = Path(os.environ.get('YOUAI_REFERENCE_RELAY_STATE','E:/data/codexYOUAI-data/reference-relay.json'))
REFERENCE_RELAY_CREDENTIALS = Path(os.environ.get('YOUAI_REFERENCE_RELAY_CREDENTIALS','E:/data/codexYOUAI-data/.youai-reference-relay.env'))
JOBS = {}
ANALYSIS_JOBS = {}
LOCK = threading.Lock()
PALETTES = {'温柔治愈': ('#e5eef9', '#20344c'), '清爽直接': ('#f7f9fc', '#152b43'), '活力明亮': ('#fff0c9', '#603c19')}
DOUYIN_URL = re.compile(r"https://(?:v\.)?douyin\.com/[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]+", re.I)
_link_spec=importlib.util.spec_from_file_location('link_platform',Path(__file__).with_name('link-platform.py'));_link_module=importlib.util.module_from_spec(_link_spec);_link_spec.loader.exec_module(_link_module)
_comments_spec=importlib.util.spec_from_file_location('top_comments',Path(__file__).with_name('top-comments.py'));_comments_module=importlib.util.module_from_spec(_comments_spec);_comments_spec.loader.exec_module(_comments_module)
QIANWEN_CONFIG = Path(os.environ.get('YOUAI_MPT_CONFIG', Path.home() / 'MoneyPrinterTurbo' / 'config.toml'))
POST_LIMITS = {'/references/glance':32*1024,'/references/peek':16*1024,'/replica/check':4*1024,'/replica/jobs':9*1024*1024,'/replica/status':4*1024,'/reference/deep-watch':32*1024,'/reference/chat':32*1024,'/reference/brief':32*1024,'/works/image':32*1024, '/works/text':32*1024, '/jobs':64*1024, '/references/analyze':32*1024, '/references/acquire':16*1024, '/references/read':8*1024, '/references/config/check':8*1024, '/tools/run':16*1024}

def update_job(job_id, **changes):
    job = dict(JOBS.get(job_id) or {})
    job.update(changes)
    JOBS[job_id] = job

def job_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return None
    result = dict(job)
    started = result.get('startedAt')
    if started:
        result['elapsedSeconds'] = max(0, int(time.time() - started))
    return result

def validate(data):
    idea = data.get('idea', '')
    if not isinstance(idea, str) or not 1 <= len(idea.strip()) <= 160:
        raise ValueError('点子需为 1–160 字')
    duration = data.get('duration')
    if isinstance(duration, bool) or not isinstance(duration, int) or not 2 <= duration <= 30 or data.get('mood') not in PALETTES:
        raise ValueError('不支持的时长或风格')
    visual_style = data.get('visualStyle', '纯文字画面')
    if visual_style not in ('AI 生成画面', '纯文字画面'):
        raise ValueError('不支持的画面形式')
    source = data.get('source') if isinstance(data.get('source'), dict) else {}
    storyboard=data.get('storyboard') if isinstance(data.get('storyboard'),dict) else None
    if source and (not storyboard or storyboard.get('status')!='approved'):raise ValueError('请先确认分镜草案')
    shots=storyboard.get('shots') if storyboard else []
    if storyboard and (not 1<=len(shots)<=12 or any(not isinstance(item,dict) or not str(item.get('narration') or '').strip() or not str(item.get('visual') or '').strip() or len(str(item.get('narration')))>240 or len(str(item.get('visual')))>240 for item in shots)):raise ValueError('分镜内容无效，请返回修改')
    raw_generation=data.get('generation') if isinstance(data.get('generation'),dict) else {}
    defaults=video_defaults();generation={'mode':raw_generation.get('mode','all-purpose'),'resolution':raw_generation.get('resolution',defaults['resolution']),'ratio':raw_generation.get('ratio','9:16'),'audio':raw_generation.get('audio',True),'promptExtend':raw_generation.get('promptExtend',True),'watermark':raw_generation.get('watermark',defaults['watermark']),'smartDuration':raw_generation.get('smartDuration',False)}
    if generation['mode'] not in ('all-purpose','first-last-frame') or generation['resolution'] not in ('480P','720P','1080P') or generation['ratio'] not in ('adaptive','21:9','16:9','4:3','1:1','3:4','9:16') or any(not isinstance(generation[key],bool) for key in ('audio','promptExtend','watermark','smartDuration')):raise ValueError('视频生成参数无效')
    if generation['mode']=='first-last-frame' and source.get('type')!='douyin':raise ValueError('首尾帧模式需要已验证的参考原片')
    if generation['mode']=='all-purpose' and (storyboard or {}).get('referenceMode')=='reference-video' and not generation['smartDuration']:
        input_duration=float(((((source.get('reference') or {}).get('analysis') or {}).get('summary') or {}).get('durationSeconds')) or 0)
        if input_duration+duration>30:raise ValueError(f'高度参考原片与成片总时长不能超过 30 秒；当前最多可生成 {max(2,int(30-input_duration))} 秒')
    analysis_plan=_plan_module.validate(data.get('analysisPlan'))
    boundaries=_boundary_module.validate(data.get('contentBoundaries'))
    if boundaries!=_boundary_module.validate((storyboard or {}).get('contentBoundaries')):raise ValueError('内容边界已改变，请重新确认分镜')
    if analysis_plan and _plan_module.validate((storyboard or {}).get('analysisPlan'))!=analysis_plan:raise ValueError('拆解方案已改变，请重新确认分镜')
    preference=data.get('aiPreference') or ''
    if not isinstance(preference,str) or len(preference)>500:raise ValueError('AI个人偏好无效')
    return dict(idea=idea.strip(), duration=data['duration'], mood=data['mood'], visualStyle=visual_style,generation=generation,analysisPlan=analysis_plan,contentBoundaries=boundaries,
                goal=str(data.get('goal') or '吸引看完')[:120],audience=str(data.get('audience') or '泛兴趣用户')[:120],hookStyle=str(data.get('hookStyle') or '先给结果')[:120],tone=str(data.get('tone') or '自然真实')[:120],cta=str(data.get('cta') or '看完即可')[:120],mustInclude=str(data.get('mustInclude') or '')[:120],avoid=str(data.get('avoid') or '')[:120],aiPreference=preference[:500],creativeIntent=str(data.get('creativeIntent') or '')[:1000],referenceNotes=str(data.get('referenceNotes') or '')[:1000],storyboard=storyboard,source=source)

def video_defaults():
    # Admin console defaults apply only when an (older) client omits the field.
    try:return PLATFORM.config()['video']
    except Exception:return {'resolution':'720P','watermark':False}

def qianwen_settings():
    return PLATFORM.video_settings()

def legacy_video_settings():
    """Credential file / environment values; never raises so the console can show status."""
    values = {}
    try:
        if QIANWEN_CONFIG.exists():
            with QIANWEN_CONFIG.open('rb') as stream:
                values = tomllib.load(stream)
            values = values.get('app', values)
    except (OSError, ValueError):
        values = {}
    key = os.environ.get('YOUAI_QIANWEN_API_KEY') or values.get('qianwen_video_api_key') or ''
    return {'key': key, 'keySource': '环境变量' if os.environ.get('YOUAI_QIANWEN_API_KEY') else '凭据文件',
            'url': (os.environ.get('YOUAI_QIANWEN_BASE_URL') or values.get('qianwen_video_base_url') or 'https://maas.qianwenaiapi.com/api/v1').rstrip('/'),
            'model': os.environ.get('YOUAI_QIANWEN_MODEL') or values.get('qianwen_video_model') or 'wan3.0-video',
            'resolution': os.environ.get('YOUAI_QIANWEN_RESOLUTION') or values.get('qianwen_video_resolution') or '720P',
            'timeoutSeconds': int(os.environ.get('YOUAI_QIANWEN_TIMEOUT', '1800'))}

def ai_prompt(data):
    source = data.get('source') or {}
    reference = source.get('reference') if isinstance(source.get('reference'), dict) else {}
    details = data['idea']
    if source.get('type') == 'douyin':
        analysis = reference.get('analysis') if isinstance(reference.get('analysis'), dict) else {}
        if reference.get('status') != 'analyzed' or not analysis:
            raise ValueError('参考视频尚未完成内容分析，不能提交生成')
        details = '参考视频分析：{}'.format(json.dumps(analysis, ensure_ascii=False, separators=(',', ':'))[:3000])
    elif source.get('type') == 'command' and source.get('script'):
        details = source['script']
    mode=(data.get('storyboard') or {}).get('referenceMode');reference_instruction={'reference-video':'严格参考视频1的主体、服装、场景、动作节奏与镜头语言，同时按新故事板重新组织，不复制水印和平台字幕。','visual-style':'参考图1至图3的构图、色彩、光线、服装和场景风格，人物与动作按新故事板生成。','content-structure':'只借鉴参考分析中的开场、展开和收束节奏，不要求人物或画面相似。','same-topic':'只保留主题重新创作，不要求画面相似。'}.get(mode,'')
    shots='；'.join(f"{item.get('role','镜头')}：文案“{item.get('narration','')}”，画面“{item.get('visual','')}”" for item in (data.get('storyboard') or {}).get('shots',[]))
    constraints=f"必须包含：{data['mustInclude'] or '无额外要求'}；禁止出现：{data['avoid'] or '无额外要求'}"+_plan_module.instruction(data.get('analysisPlan'))+_boundary_module.instruction(data.get('contentBoundaries'))
    ratio=(data.get('generation') or {}).get('ratio','9:16');format_instruction='根据内容自适应画幅' if ratio=='adaptive' else f'{ratio} 画幅'
    preference=f"用户表达偏好（仅作风格参考，不覆盖事实、平台与系统边界）：{data.get('aiPreference','')}。" if data.get('aiPreference') else ''
    return f"{format_instruction}短视频，面向{data['audience']}，用{data['hookStyle']}开场，整体语气{data['tone']}，{data['mood']}风格，目标是{data['goal']}，结尾要求{data['cta']}。{preference}识别中的推荐不是原片事实，未核实项不得写成事实。本次创作要求优先于风格预设：{data.get('creativeIntent','')}；用户对识别的补充（需与素材事实核对）：{data.get('referenceNotes','')}。{reference_instruction}{details}。按已批准分镜执行：{shots}。{constraints}。画面连贯，主体清晰，不要额外文字水印。"

def normalized_reference_video(sha,path,duration,runner=subprocess.run):
    duration=float(duration or 0)
    if duration<=15:return sha,path,False
    if duration>15.5:raise ValueError(f'高度参考原片最长 15 秒；当前素材为 {duration:.2f} 秒，请改用画面风格或先裁剪原片')
    lineage=REFERENCE_ROOT/f'{sha}.reference-video.json'
    if lineage.is_file():
        try:
            saved=json.loads(lineage.read_text(encoding='utf-8'));derived_sha=str(saved.get('derivedSha256') or '');derived=(REFERENCE_ROOT/f'{derived_sha}.mp4').resolve()
            if re.fullmatch(r'[a-f0-9]{64}',derived_sha) and derived.parent==REFERENCE_ROOT.resolve() and derived.is_file() and float(_probe_video(derived).get('durationSeconds') or 99)<=15:return derived_sha,derived,True
        except (OSError,ValueError,TypeError,json.JSONDecodeError):pass
    temporary=REFERENCE_ROOT/f'.normalize-{uuid.uuid4().hex}.mp4'
    try:
        result=runner([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-i',str(path),'-t','14.9','-map','0:v:0','-map','0:a?','-c:v','libx264','-preset','fast','-crf','20','-c:a','aac','-b:a','128k','-movflags','+faststart',str(temporary)],capture_output=True,timeout=180)
        if result.returncode or not temporary.is_file() or temporary.stat().st_size<1024:raise ValueError('参考原片自动规范化失败，请改用画面风格或手动裁剪')
        media=_probe_video(temporary)
        if float(media.get('durationSeconds') or 99)>15:raise ValueError('参考原片规范化后仍超过 15 秒，请手动裁剪')
        derived_sha=hashlib.sha256(temporary.read_bytes()).hexdigest();derived=REFERENCE_ROOT/f'{derived_sha}.mp4'
        if derived.exists():temporary.unlink()
        else:temporary.replace(derived)
        lineage.write_text(json.dumps({'version':'reference-video-normalization-v1','sourceSha256':sha,'sourceDurationSeconds':round(duration,3),'derivedSha256':derived_sha,'derivedDurationSeconds':media.get('durationSeconds'),'trimmedToSeconds':14.9},ensure_ascii=False,indent=2),encoding='utf-8')
        return derived_sha,derived,True
    finally:temporary.unlink(missing_ok=True)

def generation_reference_media(data,runner=subprocess.run):
    source=data.get('source') or {};reference=source.get('reference') if isinstance(source.get('reference'),dict) else {};mode=(data.get('storyboard') or {}).get('referenceMode');generation=data.get('generation') or {}
    if generation.get('mode')=='first-last-frame':
        sha=str((reference.get('asset') or {}).get('sha256') or '');path=(REFERENCE_ROOT/f'{sha}.mp4').resolve()
        if not re.fullmatch(r'[a-f0-9]{64}',sha) or path.parent!=REFERENCE_ROOT.resolve() or not path.is_file():raise ValueError('首尾帧模式需要已验证的参考原片')
        duration=float((((reference.get('analysis') or {}).get('summary') or {}).get('durationSeconds')) or 0);items=[];folder=REFERENCE_ROOT/f'.provider-boundaries-{uuid.uuid4().hex}';folder.mkdir()
        try:
            for kind,second in (('first_frame',0),('last_frame',max(0,duration-.05))):
                frame=folder/f'{kind}.jpg';result=runner([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-ss',str(second),'-i',str(path),'-frames:v','1','-vf','scale=720:-2',str(frame)],capture_output=True,timeout=45)
                if result.returncode or not frame.exists():raise ValueError('无法从参考原片准备首尾帧')
                items.append({'type':kind,'url':'data:image/jpeg;base64,'+base64.b64encode(frame.read_bytes()).decode()})
            return items
        finally:shutil.rmtree(folder,ignore_errors=True)
    if source.get('type')!='douyin' or mode not in ('reference-video','visual-style'):return []
    sha=str((reference.get('asset') or {}).get('sha256') or '')
    path=(REFERENCE_ROOT/f'{sha}.mp4').resolve()
    if not re.fullmatch(r'[a-f0-9]{64}',sha) or path.parent!=REFERENCE_ROOT.resolve() or not path.is_file():raise ValueError('高度参考需要已验证的参考原片，请重新获取视频')
    if mode=='reference-video':
        duration=float((((reference.get('analysis') or {}).get('summary') or {}).get('durationSeconds')) or 0)
        media_sha,_,_=normalized_reference_video(sha,path,duration,runner)
        return [{'type':'reference_video','url':signed_reference_video_url(media_sha,user=data.get('_userId'))}]
    analysis=reference.get('analysis') or {};times=((analysis.get('visual') or {}).get('evidenceTimes') or [0])[:3];items=[];folder=REFERENCE_ROOT/f'.provider-frames-{uuid.uuid4().hex}';folder.mkdir()
    try:
        for index,second in enumerate(times):
            frame=folder/f'{index}.jpg';result=runner([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-ss',str(float(second)),'-i',str(path),'-frames:v','1','-vf','scale=720:-2',str(frame)],capture_output=True,timeout=45)
            if not result.returncode and frame.exists():items.append({'type':'reference_image','url':'data:image/jpeg;base64,'+base64.b64encode(frame.read_bytes()).decode()})
        if not items:raise ValueError('无法准备画面风格参考帧，请重新分析原视频')
        return items
    finally:shutil.rmtree(folder,ignore_errors=True)

def signed_reference_video_url(sha,now=None,user=None):
    base,secret=reference_relay_settings()
    parsed=urlparse(base)
    if AUTH and user and parsed.scheme=='https' and parsed.netloc:return base+AUTH.signed_url(user,f'/reference-assets/{sha}.mp4')
    if parsed.scheme!='https' or not parsed.netloc or not secret:
        raise ValueError('高度参考原片需要配置模型可访问的 HTTPS 素材地址；当前请选择“画面风格”')
    expires=int(now if now is not None else time.time())+1800
    signature=hmac.new(secret.encode(),f'{sha}:{expires}'.encode(),hashlib.sha256).hexdigest()
    return f'{base}/reference-assets/{sha}.mp4?expires={expires}&signature={quote(signature)}'

def verified_reference_video(path_value,now=None):
    parsed=urlparse(path_value);match=re.fullmatch(r'/reference-assets/([a-f0-9]{64})\.mp4',parsed.path)
    query=parse_qs(parsed.query);expires=str((query.get('expires') or [''])[0]);signature=str((query.get('signature') or [''])[0]);_,secret=reference_relay_settings()
    if not match or not expires.isdigit() or int(expires)<int(now if now is not None else time.time()) or not secret:return None
    expected=hmac.new(secret.encode(),f'{match[1]}:{expires}'.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,expected):return None
    file=(REFERENCE_ROOT/f'{match[1]}.mp4').resolve()
    return file if file.parent==REFERENCE_ROOT.resolve() and file.is_file() else None

def reference_relay_settings():
    base=os.environ.get('YOUAI_PUBLIC_ASSET_BASE_URL','').strip().rstrip('/');secret=os.environ.get('YOUAI_REFERENCE_MEDIA_SECRET','').strip()
    if REFERENCE_RELAY_CREDENTIALS.exists() and not secret:
        for line in REFERENCE_RELAY_CREDENTIALS.read_text(encoding='utf-8-sig').splitlines():
            key,separator,value=line.partition('=')
            if separator and key.strip()=='YOUAI_REFERENCE_MEDIA_SECRET':secret=value.strip()
    if REFERENCE_RELAY_STATE.exists() and not base:
        try:base=str(json.loads(REFERENCE_RELAY_STATE.read_text(encoding='utf-8-sig')).get('publicBaseUrl') or '').strip().rstrip('/')
        except (OSError,ValueError,TypeError):base=''
    return base,secret

def reference_relay_status(opener=urlopen):
    base,secret=reference_relay_settings();parsed=urlparse(base)
    if parsed.scheme!='https' or not parsed.netloc or (not secret and not AUTH):return {'ready':False,'message':'高度参考通道尚未就绪'}
    try:
        with opener(Request(base+'/health',headers={'User-Agent':'YOUAI/1.0'}),timeout=8) as response:ready=response.status==200
    except Exception:ready=False
    return {'ready':ready,'message':'高度参考原片可用' if ready else '高度参考通道正在恢复，请稍后重试'}

def persist_run_assets(job_id,data,provider,provider_task=None,runner=subprocess.run,opener=urlopen):
    folder=ASSET_ROOT/'runs'/job_id;folder.mkdir(parents=True,exist_ok=True)
    output=ROOT/job_id/'video.mp4';final=folder/'final.mp4';shutil.copy2(output,final)
    final_sha=hashlib.sha256(final.read_bytes()).hexdigest();reference=(data.get('source') or {}).get('reference') or {};asset=reference.get('asset') or {};analysis=reference.get('analysis') or {}
    source_sha=str(asset.get('sha256') or analysis.get('assetSha256') or '');source_path=REFERENCE_ROOT/f'{source_sha}.mp4';source_uri=''
    keyframes=[]
    if re.fullmatch(r'[a-f0-9]{64}',source_sha) and source_path.exists():
        sources=ASSET_ROOT/'sources';sources.mkdir(exist_ok=True);saved_source=sources/f'{source_sha}.mp4'
        if not saved_source.exists():shutil.copy2(source_path,saved_source)
        source_uri=str(saved_source)
        frames=ASSET_ROOT/'keyframes'/source_sha;frames.mkdir(parents=True,exist_ok=True)
        times=((analysis.get('visual') or {}).get('evidenceTimes') or [])[:7]
        for index,second in enumerate(times):
            target=frames/f'{index:02d}-{float(second):.2f}s.jpg'
            if not target.exists():runner([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-ss',str(second),'-i',str(saved_source),'-frames:v','1','-vf','scale=480:-2',str(target)],capture_output=True,timeout=45)
            if target.exists():keyframes.append(str(target))
    safe_request=json.loads(json.dumps(data,ensure_ascii=False));prompt=ai_prompt(data) if data['visualStyle']=='AI 生成画面' else '纯文字画面按批准故事板逐段合成'
    (folder/'analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2),encoding='utf-8');(folder/f"storyboard.v{data['storyboard'].get('version',1)}.json").write_text(json.dumps(data['storyboard'],ensure_ascii=False,indent=2),encoding='utf-8');(folder/'request.json').write_text(json.dumps(safe_request,ensure_ascii=False,indent=2),encoding='utf-8');(folder/'prompt.txt').write_text(prompt,encoding='utf-8')
    generation_settings={**(data.get('generation') or {}),'duration':-1 if (data.get('generation') or {}).get('smartDuration') else data.get('duration')}
    manifest={'version':'video-asset-bundle-v1','runId':job_id,'createdAt':time.time(),'source':{'type':(data.get('source') or {}).get('type'),'sha256':source_sha,'storageUri':source_uri},'analysis':{'available':bool(analysis),'path':str(folder/'analysis.json'),'keyframes':keyframes,'payload':analysis},'communication':{key:data.get(key) for key in ('goal','audience','hookStyle','tone','cta','mustInclude','avoid')},'storyboard':{'version':data['storyboard'].get('version',1),'status':data['storyboard'].get('status'),'referenceMode':data['storyboard'].get('referenceMode','same-topic'),'path':str(folder/f"storyboard.v{data['storyboard'].get('version',1)}.json"),'shots':data['storyboard'].get('shots',[])},'generation':{'provider':provider,'model':qianwen_settings()['model'] if provider=='qianwen' else 'local-text-renderer','settings':generation_settings,'providerTaskId':provider_task,'requestPath':str(folder/'request.json'),'promptPath':str(folder/'prompt.txt'),'estimatedCostCny':None,'actualCostCny':None},'final':{'sha256':final_sha,'storageUri':str(final),'sizeBytes':final.stat().st_size},'lineage':{'sourceSha256':source_sha,'analysisVersion':analysis.get('version'),'storyboardVersion':data['storyboard'].get('version',1),'generationJobId':job_id},'limitations':['当前整片 Provider 只返回最终视频，没有逐镜头候选文件']}
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    backend=os.environ.get('YOUAI_BACKEND_URL','http://127.0.0.1:8080').rstrip('/');user=data.get('_userId') or os.environ.get('YOUAI_ASSET_USER_ID','00000000-0000-4000-8000-000000000001')
    try:
        saved=json_request(f'{backend}/api/v1/video-runs',headers={'Content-Type':'application/json','X-Youai-User-Id':user},payload=manifest,opener=opener,timeout=10);manifest['database']=saved
    except Exception as error:manifest['database']={'status':'pending','error':str(error)[:120]}
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    if ARCHIVE.root==ASSET_ROOT.resolve():
        try:ARCHIVE.enqueue(job_id)
        except Exception:pass
    return manifest

def json_request(url, *, headers, payload=None, opener=urlopen, timeout=30):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    request = Request(url, data=body, headers=headers, method='POST' if payload is not None else 'GET')
    try:
        with opener(request, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as error:
        try:document=json.loads(error.read().decode('utf-8'))
        except Exception:document={}
        raise ApiResponseError(error.code,document) from None

def public_asset_manifest(run_id,manifest):
    source=manifest.get('source') or {};analysis=manifest.get('analysis') or {};storyboard=manifest.get('storyboard') or {};generation=manifest.get('generation') or {};final=manifest.get('final') or {};folder=ASSET_ROOT/'runs'/run_id
    prompt_file=folder/'prompt.txt';prompt=prompt_file.read_text(encoding='utf-8')[:3000] if prompt_file.exists() else ''
    frames=analysis.get('keyframes') if isinstance(analysis.get('keyframes'),list) else []
    return {'version':manifest.get('version'),'runId':run_id,'createdAt':manifest.get('createdAt'),'source':{'type':source.get('type'),'sha256':source.get('sha256'),'available':bool(source.get('storageUri')),'url':f'/asset-runs/{run_id}/source.mp4' if source.get('storageUri') else ''},'analysis':{'available':bool(analysis.get('available')),'keyframeCount':len(frames),'keyframes':[f'/asset-runs/{run_id}/keyframes/{index}.jpg' for index in range(len(frames))],'summary':((analysis.get('payload') or {}).get('summary') if isinstance(analysis.get('payload'),dict) else {})},'communication':manifest.get('communication') or {},'storyboard':{'version':storyboard.get('version'),'status':storyboard.get('status'),'referenceMode':storyboard.get('referenceMode'),'shots':storyboard.get('shots') or []},'generation':{'provider':generation.get('provider'),'model':generation.get('model'),'settings':generation.get('settings') or {},'providerTaskId':generation.get('providerTaskId'),'prompt':prompt,'estimatedCostCny':generation.get('estimatedCostCny'),'actualCostCny':generation.get('actualCostCny')},'final':{'sha256':final.get('sha256'),'sizeBytes':final.get('sizeBytes'),'url':f'/assets/{run_id}/final.mp4'},'lineage':manifest.get('lineage') or {},'database':{'status':(manifest.get('database') or {}).get('status','pending')},'limitations':manifest.get('limitations') or []}

def asset_preview_file(run_id,kind,index=None):
    manifest_file=ASSET_ROOT/'runs'/run_id/'manifest.json'
    if not manifest_file.exists():return None
    manifest=json.loads(manifest_file.read_text(encoding='utf-8'))
    if kind=='source':candidate=Path(str((manifest.get('source') or {}).get('storageUri') or ''))
    else:
        frames=(manifest.get('analysis') or {}).get('keyframes') or []
        if index is None or index<0 or index>=len(frames):return None
        candidate=Path(str(frames[index]))
    try:
        resolved=candidate.resolve();root=(ASSET_ROOT/('sources' if kind=='source' else 'keyframes')).resolve()
        return resolved if resolved.is_file() and resolved.is_relative_to(root) else None
    except (OSError,ValueError):return None

class ApiResponseError(RuntimeError):
    def __init__(self,status,payload):
        super().__init__('上游接口请求失败');self.status=status;self.payload=payload if isinstance(payload,dict) else {}

class ReferenceAcquireError(ValueError):
    def __init__(self,message,code='reference_failed',action='upload'):
        super().__init__(message);self.code=code;self.action=action

def generate_qianwen(job_id, data, opener=urlopen, sleeper=time.sleep):
    settings = qianwen_settings()
    update_job(job_id, phase='submitting', message='正在向 AI 视频模型提交任务')
    headers = {'Authorization':f"Bearer {settings['key']}", 'Content-Type':'application/json', 'X-DashScope-Async':'enable'}
    media=generation_reference_media(data);provider_input={'prompt':ai_prompt(data)}
    if media:provider_input['media']=media
    created = json_request(f"{settings['base']}/services/aigc/video-generation/video-synthesis", headers=headers, payload={
        'model':settings['model'], 'input':provider_input,
        'parameters':{'resolution':data['generation']['resolution'], 'ratio':data['generation']['ratio'], 'watermark':data['generation']['watermark'], 'duration':-1 if data['generation']['smartDuration'] else data['duration'], 'audio':data['generation']['audio'], 'prompt_extend':data['generation']['promptExtend']},
    }, opener=opener)
    task_id = (created.get('output') or {}).get('task_id')
    if not task_id:
        raise RuntimeError(created.get('message') or '第三方未返回任务编号')
    update_job(job_id, status='rendering', phase='queued', message='任务已提交，正在等待模型开始生成', provider='qianwen', providerTaskId=task_id)
    poll_headers = {'Authorization':headers['Authorization'], 'Content-Type':'application/json'}
    deadline = time.monotonic() + int(settings.get('timeout') or 1800)
    while time.monotonic() < deadline:
        result = json_request(f"{settings['base']}/tasks/{task_id}", headers=poll_headers, opener=opener)
        output = result.get('output') or {}
        status = output.get('task_status')
        if status == 'SUCCEEDED':
            video_url = output.get('video_url')
            if not video_url:
                raise RuntimeError('第三方任务成功但没有返回视频地址')
            update_job(job_id, phase='downloading', message='AI 画面已生成，正在下载成片')
            folder = ROOT / job_id
            folder.mkdir(exist_ok=True)
            with opener(Request(video_url, headers={'User-Agent':'YOUAI/1.0'}), timeout=120) as response:
                (folder / 'video.mp4').write_bytes(response.read())
            return task_id
        if status == 'FAILED':
            raise RuntimeError(result.get('message') or output.get('message') or '第三方视频生成失败')
        if status == 'RUNNING':
            update_job(job_id, phase='generating', message='AI 正在生成画面，这一步通常需要几分钟')
        else:
            update_job(job_id, phase='queued', message='任务正在模型队列中等待处理')
        sleeper(10)
    raise TimeoutError('第三方视频生成超时')

def segments(idea):
    # Preserve every character; split long clauses to keep text readable.
    parts = re.findall(r'[^，。！？；\n]+[，。！？；\n]*|[，。！？；\n]+', idea)
    return [part[i:i+42] for part in parts for i in range(0, len(part), 42)]

def reference_url(value):
    match = DOUYIN_URL.search(value if isinstance(value, str) else '')
    if not match:
        raise ValueError('请粘贴有效的抖音分享链接')
    return match.group(0).rstrip('.,;!?，。；！？、）》】')

def identify_reference(value, opener=urlopen):
    url = reference_url(value)
    request = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    })
    with opener(request, timeout=15) as response:
        resolved = response.geturl()
        content = response.read(1024 * 1024).decode('utf-8', errors='replace')
    host = (urlparse(resolved).hostname or '').lower()
    video_id = re.search(r'/(?:share/)?video/(\d+)', resolved)
    if not host.endswith(('douyin.com', 'iesdouyin.com')) or not video_id:
        raise ValueError('链接没有跳转到可识别的抖音视频')
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.I | re.S)
    desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', content, re.I)
    title = html.unescape(re.sub(r'\s+', ' ', title_match.group(1)).strip()) if title_match else ''
    description = html.unescape(desc_match.group(1).strip()) if desc_match else ''
    if not content or (not title and not description):
        raise ValueError('视频页面没有返回可读取的内容')
    return {'status':'identified', 'videoId':video_id.group(1), 'title':title or description[:80], 'description':description[:300], 'resolvedUrl':resolved}

def _media_urls(value):
    found=[]
    def visit(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key.lower() in ('url','play_url','download_url','video_url','playaddr','play_addr') and isinstance(child, str) and child.startswith(('http://','https://')):
                    found.append(child)
                visit(child)
        elif isinstance(item, list):
            for child in item:visit(child)
    visit(value)
    return list(dict.fromkeys(found))

def _video_media_urls(document):
    data=document.get('data') if isinstance(document,dict) and isinstance(document.get('data'),dict) else document
    media=data.get('media') if isinstance(data,dict) and isinstance(data.get('media'),dict) else {}
    candidates=[]
    for item in [media.get('video'),*(media.get('streams') if isinstance(media.get('streams'),list) else [])]:
        if not isinstance(item,dict):continue
        for value in [item.get('url'),*(item.get('urls') if isinstance(item.get('urls'),list) else [])]:
            if isinstance(value,str) and value.startswith(('http://','https://')):candidates.append(value)
    return list(dict.fromkeys(candidates)) or _media_urls(document)

def _first_field(value,names):
    if isinstance(value,dict):
        for name in names:
            found=value.get(name)
            if isinstance(found,(str,int)) and str(found).strip():return str(found).strip()
        for child in value.values():
            found=_first_field(child,names)
            if found:return found
    elif isinstance(value,list):
        for child in value:
            found=_first_field(child,names)
            if found:return found
    return ''

def _parser_failure(error):
    payload=error.payload;failure=payload.get('error') if isinstance(payload.get('error'),dict) else payload
    code=str(failure.get('code') or '');details=failure.get('details') if isinstance(failure.get('details'),dict) else {}
    if code=='INVALID_URL' and details.get('reason')=='short_link_dead_end':
        return ReferenceAcquireError('这条抖音短链已失效并跳转到首页，请在抖音重新复制分享链接，或上传原视频','short_link_expired','replace_or_upload')
    if error.status in (401,403):return ReferenceAcquireError('参考解析凭据已失效，请到“我的”的工具接口管理中重新检测','parser_auth','configure')
    return ReferenceAcquireError('参考解析服务暂时未能解析这条链接，请稍后重试或上传原视频','parser_failed','retry_or_upload')

def _safe_media_url(value):
    parsed=urlparse(value)
    if parsed.scheme!='https' or not parsed.hostname:raise ValueError('素材下载地址必须使用 HTTPS')
    host=parsed.hostname.lower()
    if host=='localhost' or host.endswith(('.localhost','.local')):raise ValueError('素材下载地址不允许指向本机或内网')
    try:
        address=ipaddress.ip_address(host)
        if not address.is_global:raise ValueError('素材下载地址不允许指向本机或内网')
    except ValueError as error:
        if '不允许' in str(error):raise
    return value

def _probe_video(path, runner=subprocess.run):
    result=runner([imageio_ffmpeg.get_ffmpeg_exe(),'-v','info','-i',str(path),'-map','0:v:0','-frames:v','1','-f','null','-'],capture_output=True,timeout=30)
    if result.returncode:
        raise ValueError('取得的文件不是可解码视频')
    info=result.stderr.decode('utf-8',errors='replace')
    video=re.search(r'Video:\s*([^,]+).*?(\d{2,5})x(\d{2,5})',info,re.I)
    duration=re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)',info)
    if not video:raise ValueError('取得的文件没有视频画面')
    seconds=None if not duration else int(duration[1])*3600+int(duration[2])*60+float(duration[3])
    return {'codec':video[1].strip(),'width':int(video[2]),'height':int(video[3]),'durationSeconds':seconds,'hasAudio':bool(re.search(r'Audio:',info,re.I))}

def persist_analysis(job_id):
    directory=REFERENCE_ROOT/'jobs';directory.mkdir(exist_ok=True)
    target=directory/f'{job_id}.json';temp=directory/f'.{job_id}.{uuid.uuid4().hex}.tmp'
    temp.write_text(json.dumps(ANALYSIS_JOBS[job_id],ensure_ascii=False),encoding='utf-8');temp.replace(target)

def analysis_status(job_id):
    job=ANALYSIS_JOBS.get(job_id)
    if not job and re.fullmatch('[a-f0-9]{32}',job_id):
        try:job=json.loads((REFERENCE_ROOT/'jobs'/f'{job_id}.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):pass
        if job and job.get('status')=='running':job.update(status='failed',error='服务已重启，请重新提交拆解',phase='failed')
    if not job:return None
    result=dict(job);started=result.get('startedAt')
    # 完成后用完成时刻算用时（以前按查询时刻算，隔一阵再打开会显示上千秒）
    if started:result['elapsedSeconds']=max(0,int((result.get('finishedAt') or time.time())-started))
    return result

def _reference_asset(reference):
    asset=reference.get('asset') if isinstance(reference,dict) and isinstance(reference.get('asset'),dict) else {}
    sha=str(asset.get('sha256') or '');path=Path(str(asset.get('storagePath') or '')).resolve()
    if not re.fullmatch(r'[a-f0-9]{64}',sha) or path.parent!=REFERENCE_ROOT.resolve() or path.name!=f'{sha}.mp4' or not path.is_file():raise ValueError('参考视频资产无效或已丢失，请重新获取')
    return sha,path,asset

_config_spec=importlib.util.spec_from_file_location('client_config',Path(__file__).with_name('client-config.py'))
_config_module=importlib.util.module_from_spec(_config_spec)
_config_spec.loader.exec_module(_config_module)
_ai_spec=importlib.util.spec_from_file_location('inspiration_ai',Path(__file__).with_name('inspiration-ai.py'))
_ai_module=importlib.util.module_from_spec(_ai_spec);_ai_spec.loader.exec_module(_ai_module)
INSPIRATION_AI=_ai_module.Gateway(Path(os.environ.get('YOUAI_ADMIN_ROOT',str(ROOT.parent/'admin')))/'inspiration-ai')
_text_spec=importlib.util.spec_from_file_location('text_works',Path(__file__).with_name('text-works.py'));_text_module=importlib.util.module_from_spec(_text_spec);_text_spec.loader.exec_module(_text_module)
_platform_spec=importlib.util.spec_from_file_location('platform_config',Path(__file__).with_name('platform-config.py'))
_platform_module=importlib.util.module_from_spec(_platform_spec);_platform_spec.loader.exec_module(_platform_module)

def service_status():
    """Presence-only status of server configuration; never returns secrets or full private paths."""
    def present(name):return bool(os.environ.get(name)) and Path(os.environ[name]).exists()
    whisper=os.environ.get('YOUAI_WHISPER_MODEL','tiny')
    return [
        {'name':'微信登录','ok':AUTH is not None,'detail':'已配置' if AUTH is not None else '未配置 YOUAI_WECHAT_CONFIG'},
        {'name':'飞书资产归档','ok':present('YOUAI_FEISHU_CONFIG'),'detail':'凭据文件已挂载' if present('YOUAI_FEISHU_CONFIG') else '未找到飞书凭据文件'},
        {'name':'热点数据源','ok':bool(os.environ.get('YOUAI_HOTSPOT_API')),'detail':'DailyHot 已配置' if os.environ.get('YOUAI_HOTSPOT_API') else '未配置'},
        {'name':'业务数据库 API','ok':bool(os.environ.get('YOUAI_BACKEND_URL')),'detail':'已配置' if os.environ.get('YOUAI_BACKEND_URL') else '使用默认本机地址'},
        {'name':'参考解析服务','ok':bool(os.environ.get('YOUAI_REFERENCE_PARSER_URL')),'detail':'已配置' if os.environ.get('YOUAI_REFERENCE_PARSER_URL') else '未配置'},
        {'name':'语音转写模型','ok':Path(whisper).is_dir() or whisper in ('tiny','base','small'),'detail':'faster-whisper '+Path(whisper).name+'（本机CPU）'},
        {'name':'公网素材地址','ok':bool(os.environ.get('YOUAI_PUBLIC_ASSET_BASE_URL')),'detail':os.environ.get('YOUAI_PUBLIC_ASSET_BASE_URL') or '未配置'},
    ]

PLATFORM=_platform_module.Platform(Path(os.environ.get('YOUAI_ADMIN_ROOT',str(ROOT.parent/'admin')))/'platform',
    legacy={'qwen-domestic':lambda:dict(INSPIRATION_AI.legacy_profile(),keySource=INSPIRATION_AI.key_source()),
            'wan-video':legacy_video_settings,
            'reference-parser':lambda:{'url':os.environ.get('YOUAI_REFERENCE_PARSER_URL',''),'key':os.environ.get('YOUAI_REFERENCE_PARSER_KEY',''),'keySource':'环境变量'},
            'image-gen':lambda:{'url':os.environ.get('YOUAI_IMAGE_BASE_URL',''),'key':os.environ.get('YOUAI_IMAGE_API_KEY',''),'model':os.environ.get('YOUAI_IMAGE_MODEL',''),'keySource':'环境变量'}},
    environment=service_status)
INSPIRATION_AI.resolver=PLATFORM
_image_spec=importlib.util.spec_from_file_location('image_works',Path(__file__).with_name('image-works.py'));_image_module=importlib.util.module_from_spec(_image_spec);_image_spec.loader.exec_module(_image_module)
IMAGE_WORKS=_image_module.ImageWorks(ASSET_ROOT/'images',PLATFORM.image_settings)
TEXT_WORKS=_text_module.TextWorks(ASSET_ROOT/'auth/text-works.sqlite',INSPIRATION_AI.profile,INSPIRATION_AI)
_watch_spec=importlib.util.spec_from_file_location('hotspot_watch',Path(__file__).with_name('hotspot-watch.py'))
_watch_module=importlib.util.module_from_spec(_watch_spec);_watch_spec.loader.exec_module(_watch_module)
HOTSPOT_WATCH=_watch_module.Watches(ASSET_ROOT/'auth/hotspot-watch.sqlite')
HOTSPOT_SEARCH=_watch_module.Search()
_topic_spec=importlib.util.spec_from_file_location('topic_chat',Path(__file__).with_name('topic-chat.py'))
_topic_module=importlib.util.module_from_spec(_topic_spec);_topic_spec.loader.exec_module(_topic_module)
TOPIC_CHAT=_topic_module.TopicChat(ASSET_ROOT/'auth/topic-chat.sqlite',INSPIRATION_AI)

def topic_owned_history(user):
    result=[]
    with AUTH.db() as db:rows=db.execute("SELECT resource FROM resources WHERE user_id=? AND resource LIKE 'run:%' ORDER BY rowid DESC LIMIT 20",(user,)).fetchall()
    for (resource,) in rows:
        ident=resource[4:]
        if not re.fullmatch('[a-f0-9]{32}',ident):continue
        try:
            value=json.loads((ASSET_ROOT/'runs'/ident/'request.json').read_text(encoding='utf-8'))
            result.append({k:str(value.get(k,''))[:200] for k in ('title','idea','goal','audience','tone')})
        except (OSError,ValueError):continue
    return result

def owned_runs(user):
    """Structured fields of the user's saved works for the long-term profile (newest 50)."""
    result=[]
    if not AUTH:return result
    with AUTH.db() as db:rows=db.execute("SELECT resource FROM resources WHERE user_id=? AND resource LIKE 'run:%' ORDER BY rowid DESC LIMIT 50",(user,)).fetchall()
    for (resource,) in rows:
        ident=resource[4:]
        if not re.fullmatch('[a-f0-9]{32}',ident):continue
        path=ASSET_ROOT/'runs'/ident/'request.json'
        try:
            value=json.loads(path.read_text(encoding='utf-8'))
            result.append({'audience':value.get('audience'),'tone':value.get('tone'),'goal':value.get('goal'),'at':path.stat().st_mtime})
        except (OSError,ValueError):continue
    return result

_profile_spec=importlib.util.spec_from_file_location('user_profile',Path(__file__).with_name('user-profile.py'))
_profile_module=importlib.util.module_from_spec(_profile_spec);_profile_spec.loader.exec_module(_profile_module)
PROFILES=_profile_module.Profiles(ASSET_ROOT/'auth/user-profile.sqlite',settings=PLATFORM.personalization,owned_runs=owned_runs)
_watchflow_spec=importlib.util.spec_from_file_location('watch_flow',Path(__file__).with_name('watch-flow.py'));_watchflow_module=importlib.util.module_from_spec(_watchflow_spec);_watchflow_spec.loader.exec_module(_watchflow_module)
USAGE=_watchflow_module.usage.UsageLedger(Path(os.environ.get('YOUAI_ADMIN_ROOT',str(ROOT.parent/'admin')))/'usage.sqlite',lambda:PLATFORM.config()['videoUnderstanding'])
INSPIRATION_AI.usage_ledger=USAGE
WATCH_FLOW=_watchflow_module.WatchFlow(ASSET_ROOT/'watch',INSPIRATION_AI,lambda:PLATFORM.config()['videoUnderstanding'],USAGE)
_replica_spec=importlib.util.spec_from_file_location('replica',Path(__file__).with_name('replica.py'));_replica_module=importlib.util.module_from_spec(_replica_spec);_replica_spec.loader.exec_module(_replica_module)
REPLICA=_replica_module.Replica(ASSET_ROOT/'replica')


_summary_spec=importlib.util.spec_from_file_location('hotspot_summary',Path(__file__).with_name('hotspot-summary.py'))
_summary_module=importlib.util.module_from_spec(_summary_spec);_summary_spec.loader.exec_module(_summary_module)
_summary_module.GATEWAY=INSPIRATION_AI
_hotspot_spec=importlib.util.spec_from_file_location('hotspot_feed',Path(__file__).with_name('hotspot-feed.py'))
_hotspot_module=importlib.util.module_from_spec(_hotspot_spec)
_hotspot_spec.loader.exec_module(_hotspot_module)
_content_spec=importlib.util.spec_from_file_location('hotspot_content',Path(__file__).with_name('hotspot-content.py'))
_content_module=importlib.util.module_from_spec(_content_spec)
_content_spec.loader.exec_module(_content_module)
_admin_spec=importlib.util.spec_from_file_location('admin_console',Path(__file__).with_name('admin-console.py'))
_admin_module=importlib.util.module_from_spec(_admin_spec);_admin_spec.loader.exec_module(_admin_module)

def admin_tasks():
    rows=[]
    for kind,store in [('视频生成',JOBS),('内容分析',ANALYSIS_JOBS)]:
        for key,value in list(store.items())[-50:]:
            rows.append({'id':key,'kind':kind,'status':value.get('status','unknown'),
                         'startedAt':value.get('startedAt',0),
                         'error': '处理失败；请核对服务日志' if value.get('status')=='failed' else ''})
    return sorted(rows,key=lambda row:row['startedAt'],reverse=True)[:50]

ADMIN=_admin_module.Console(os.environ.get('YOUAI_ADMIN_ROOT',str(ROOT.parent/'admin')),
    os.environ.get('YOUAI_ADMIN_AUTH',str(ROOT.parent/'admin-auth.json')),
    os.environ.get('YOUAI_CLIENT_CONFIG',str(ROOT.parent/'admin/client-config.json')),
    _hotspot_module.snapshot,_content_module.content,admin_tasks,INSPIRATION_AI,PLATFORM)

_board_spec=importlib.util.spec_from_file_location('creation_board',Path(__file__).with_name('creation-board.py'));_board_module=importlib.util.module_from_spec(_board_spec);_board_spec.loader.exec_module(_board_module)
BOARD_FONT=next((f for f in (os.environ.get('YOUAI_BOARD_FONT',''),'/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/wqy/wqy-microhei.ttc') if f and Path(f).is_file()),None)
def _board_reference(user,sha):
    try:return AUTH.reference(user,sha) if AUTH else None
    except Exception:return None
def _board_acquire(user,url):
    reference=acquire_reference(url)
    if AUTH:AUTH.remember(user,reference)
    return reference
def _board_analyze(user,reference):
    value,_=analyze_reference(reference,user=user)
    if AUTH:AUTH.claim(user,'reference:'+reference['asset']['sha256'],{**reference,'status':'analyzed','analysis':value})
    return value
def parse_public(url):
    """Public counters of a Douyin post via the parser only (no media download)."""
    parser,key=_parser_settings(None);headers={'Content-Type':'application/json','User-Agent':'YOUAI/1.0'}
    if key:headers['Authorization']=f'Bearer {key}'
    return _link_module.source_meta(json_request(f'{parser}/api/v1/parse?wait=30',headers=headers,payload={'url':reference_url(url)},timeout=60))
def _board_signal(user,payload):
    try:PROFILES.signal(user,payload)
    except Exception:pass
BOARD=_board_module.Board(ASSET_ROOT/'board',INSPIRATION_AI,PLATFORM.board_settings,resolve_reference=_board_reference,acquire=_board_acquire,analyze=_board_analyze,
    parse_stats=parse_public,notify=(AUTH.notify if AUTH else None),profile_signal=_board_signal,font=BOARD_FONT)
ADMIN.board=BOARD
ADMIN.auth=AUTH
if AUTH:BOARD.is_trial=AUTH.is_trial
USAGE.extra=BOARD.spend_credit
BOARD.on_metric=ledger_metric
WATCH_FLOW.review_hook=(BOARD.needs_review,BOARD.reviewed)
def _board_ticker():
    while True:
        time.sleep(600)
        try:BOARD.tick()
        except Exception as error:print(json.dumps({'event':'board.tick.failed','error':type(error).__name__}),file=sys.stderr,flush=True)

ASR_LOCK = threading.Lock()
ASR_MODEL = None
ASR_MODELS = {}

def _transcribe_reference(path, model='tiny'):
    global ASR_MODEL
    if not ASR_LOCK.acquire(timeout=5):
        return {'status':'unavailable','text':'','segments':[],'note':'语音识别繁忙，请稍后重试'}
    try:
        from faster_whisper import WhisperModel
        if model not in ('tiny','base','small'):raise ValueError('unsupported ASR model')
        fallback=os.environ.get('YOUAI_WHISPER_MODEL','/opt/whisper/tiny') if model=='tiny' else '/opt/whisper/'+model
        model_path=os.environ.get('YOUAI_WHISPER_'+model.upper()+'_MODEL', fallback)
        if model not in ASR_MODELS:
            ASR_MODELS[model]=WhisperModel(model_path,device='cpu',compute_type='int8',cpu_threads=2,num_workers=1,local_files_only=True)
        ASR_MODEL=ASR_MODELS[model]
        segments,info=ASR_MODEL.transcribe(str(path),beam_size=1,vad_filter=True,language='zh')
        rows=[{'start':round(item.start,2),'end':round(item.end,2),'text':item.text.strip(),'confidence':round(max(.05,min(.99,math.exp(item.avg_logprob))),2)} for item in segments if item.text.strip()]
        confidence=round(sum(item['confidence'] for item in rows)/len(rows),2) if rows else 0
        return {'status':'available' if rows else 'silent','language':getattr(info,'language',None),'text':' '.join(item['text'] for item in rows),'confidence':confidence,'segments':rows,'note':'自动语音转写需用户校对后再作为最终文案'}
    except Exception as error:
        print(json.dumps({'event':'asr.failed','type':type(error).__name__}),flush=True)
        return {'status':'unavailable','language':None,'text':'','segments':[],'note':'语音识别暂时不可用，请稍后重试'}
    finally:
        ASR_LOCK.release()

FRAME_SAMPLING = {
    'smart': {'label':'智能','interval':3.0,'minimum':4,'maximum':10},
    'sparse': {'label':'精简','interval':6.0,'minimum':3,'maximum':6},
    'standard': {'label':'正常','interval':3.0,'minimum':5,'maximum':10},
    'detailed': {'label':'精细','interval':2.0,'minimum':8,'maximum':16},
    'ultra': {'label':'超细','interval':1.0,'minimum':12,'maximum':24},
}

def frame_sampling_plan(duration, mode='smart'):
    mode=str(mode or 'smart').strip().lower()
    if mode not in FRAME_SAMPLING:raise ValueError('代表帧采样档位无效')
    profile=FRAME_SAMPLING[mode];duration=max(.1,float(duration));count=max(profile['minimum'],math.floor(duration/profile['interval']+.5)+1);count=min(profile['maximum'],count)
    times=[round(duration*(index+.5)/count,3) for index in range(count)]
    return {'mode':mode,'label':profile['label'],'intervalSeconds':profile['interval'],'targetCount':count,'times':times}

def _extract_analysis_frame(path, second, target, runner=subprocess.run):
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();attempts=[
        [ffmpeg,'-y','-ss',f'{second:.3f}','-i',str(path),'-frames:v','1','-vf','scale=320:-2',str(target)],
        [ffmpeg,'-y','-i',str(path),'-ss',f'{max(0,second-.25):.3f}','-frames:v','1','-vf','scale=320:-2',str(target)],
    ];last=''
    for command in attempts:
        target.unlink(missing_ok=True)
        result=runner(command,capture_output=True,timeout=45)
        if result.returncode==0 and target.is_file() and target.stat().st_size>0:return True,''
        raw=getattr(result,'stderr',b'') or b'';last=raw.decode('utf-8','replace')[-240:].replace('\r',' ').replace('\n',' ')
    return False,last

def analyze_reference_legacy(reference, runner=subprocess.run, transcriber=_transcribe_reference, progress=lambda *_:None, sampling='smart', understander=None):
    understander=understander or (lambda frames,transcript,duration:_understand_module.understand(INSPIRATION_AI,frames,transcript,duration))
    try:understanding_revision=INSPIRATION_AI.scene('reference_understanding')['revision']
    except Exception:understanding_revision='unavailable'
    sha,path,asset=_reference_asset(reference);plan=frame_sampling_plan(((asset.get('media') or {}).get('durationSeconds') or .1),sampling);cache=REFERENCE_ROOT/f"{sha}.analysis.{plan['mode']}.json"
    if cache.exists():
        saved=json.loads(cache.read_text(encoding='utf-8'))
        if saved.get('version')=='reference-analysis-v1' and saved.get('analyzerVersion')=='content-evidence-3' and saved.get('understandingRevision')==understanding_revision and saved.get('understanding',{}).get('status')=='ready' and (saved.get('sampling') or {}).get('targetCount')==plan['targetCount'] and saved.get('audio',{}).get('transcript',{}).get('status')!='unavailable':
            saved['sampling']['label']=plan['label']
            return saved,True
    media=asset.get('media') if isinstance(asset.get('media'),dict) else {};duration=max(0.1,float(media.get('durationSeconds') or 0.1))
    frame_dir=REFERENCE_ROOT/f'.frames-{uuid.uuid4().hex}';frame_dir.mkdir();frames=[];failures=[]
    try:
        progress('extracting',f"正在按{plan['label']}档抽取 {plan['targetCount']} 张代表帧")
        for index,second in enumerate(plan['times']):
            target=frame_dir/f'{index:02d}.jpg';ok,detail=_extract_analysis_frame(path,second,target,runner)
            if not ok:
                failures.append({'time':second,'detail':detail});continue
            with Image.open(target) as opened:frames.append((second,opened.convert('RGB').copy()))
        required=min(3,plan['targetCount'])
        if len(frames)<required:
            print(json.dumps({'event':'reference.frames.failed','sha256':sha[:12],'sampling':plan['mode'],'targetCount':plan['targetCount'],'successCount':len(frames),'failures':failures},ensure_ascii=False),file=sys.stderr,flush=True)
            raise ValueError(f"代表帧仅成功 {len(frames)}/{plan['targetCount']} 张，至少需要 {required} 张，请重试或改用精简采样")
        brightness=[round(ImageStat.Stat(image.convert('L')).mean[0],1) for _,image in frames];changes=[]
        for (_,before),(_,after) in zip(frames,frames[1:]):
            diff=ImageChops.difference(before.resize((160,160)),after.resize((160,160)));changes.append(round(sum(ImageStat.Stat(diff).mean)/3,1))
        cuts=[round(frames[i+1][0],2) for i,value in enumerate(changes) if value>=18]
        progress('transcribing','正在识别音轨中的可核验文案');transcript=transcriber(path) if media.get('hasAudio',True) else {'status':'silent','language':None,'text':'','segments':[]}
        progress('understanding','正在结合代表帧与音轨理解内容并推荐创作方向')
        try:understanding=understander(frames,transcript,duration)
        except Exception as error:
            print(json.dumps({'event':'reference.understanding.failed','asset':sha[:12],'code':getattr(error,'code','invalid_response')},ensure_ascii=False),file=sys.stderr,flush=True)
            code=getattr(error,'code','invalid_response')
            message={'model':'视觉模型不存在或未开通，请在管理中台检查作品拆解模型','auth':'视觉模型凭据无效或无权限','quota':'视觉模型限流或额度不足','timeout':'视觉模型响应超时，请稍后重试','not_configured':'视觉模型连接尚未配置','invalid_response':'视觉模型未返回可核验的画面结构，请重试'}.get(code,'视觉模型调用未完成，请检查连接后重试')
            understanding={'status':'unavailable','errorCode':code,'error':message,'overview':'','facts':[],'segments':[],'recommendations':{},'uncertainties':['画面内容识别未完成，请重试或补充你看到的内容；抽帧和语音结果仍可查看']}
        progress('structuring','正在整理识别依据和创作建议')
        structure=[{'start':r['start'],'end':r['end'],'role':r['description'],'evidence':'结合时间戳代表帧与音轨，待用户核对'} for r in understanding.get('segments',[])]
        orientation='竖屏' if int(media.get('height') or 0)>int(media.get('width') or 0) else '横屏或方形';pace='未判断（画面变化不等于剪辑或音乐节奏）'
        transcript_confidence=float(transcript.get('confidence') or 0);overall=None
        sampling_summary={key:value for key,value in plan.items() if key!='times'};sampling_summary.update(successCount=len(frames),failureCount=len(failures))
        analysis={'version':'reference-analysis-v1','analyzerVersion':'content-evidence-3','understanding':understanding,'understandingRevision':understanding_revision,'assetSha256':sha,'sampling':sampling_summary,'summary':{'durationSeconds':round(duration,2),'orientation':orientation,'pace':pace,'detectedSpeech':transcript.get('text','')[:300] or '未取得可核验语音文案'},'hook':{'window':'0–3 秒','evidence':'使用开场代表帧与前三秒音轨作为钩子证据','confidence':0},'structure':structure,'shots':{'representativeFrameCount':len(frames),'detectedChangeCount':len(cuts),'changeTimes':cuts,'averageChangeScore':round(sum(changes)/len(changes),1) if changes else 0},'visual':{'orientation':orientation,'averageBrightness':round(sum(brightness)/len(brightness),1),'brightnessRange':[min(brightness),max(brightness)],'evidenceTimes':[round(second,2) for second,_ in frames]},'audio':{'present':bool(media.get('hasAudio',True)),'transcript':transcript},'reusableStrategies':[r['value']+'：'+r['reason'] for r in understanding.get('recommendations',{}).get('video',[])],'confidence':{'overall':overall,'visual':None,'transcript':transcript_confidence},'limitations':['自动识别与语音转写需要用户核对','多模态模型仅查看选中的代表帧，未覆盖画面不推断','没有数据证明原视频的播放或转化效果']+([f"有 {len(failures)} 个采样点解码失败，已使用其余代表帧完成分析"] if failures else [])}
        cache.write_text(json.dumps(analysis,ensure_ascii=False,indent=2),encoding='utf-8');return analysis,False
    finally:
        for item in frame_dir.glob('*'):item.unlink(missing_ok=True)
        frame_dir.rmdir()

def deep_reference(user,reference):
    sha,path,asset=_reference_asset(reference);cfg=PLATFORM.config()['videoUnderstanding'];duration=min(float(asset['media'].get('durationSeconds') or .1),cfg['maxAnalyzeSeconds'])
    def video():
        # Always clip; the provider must never receive more than the configured interval.
        target=REFERENCE_ROOT/(sha+'.deep.'+str(cfg['maxAnalyzeSeconds'])+'.mp4')
        result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-t',str(duration),'-i',str(path),'-vf','scale=640:-2','-c:v','libx264','-preset','ultrafast','-crf','28','-c:a','aac',str(target)],capture_output=True,timeout=180)
        if result.returncode!=0:raise ValueError('深度观看素材准备失败')
        if target.stat().st_size<=10*1024*1024:return 'data:video/mp4;base64,'+__import__('base64').b64encode(target.read_bytes()).decode()
        digest=hashlib.sha256(target.read_bytes()).hexdigest();stored=REFERENCE_ROOT/(digest+'.mp4')
        if not stored.exists():shutil.copyfile(target,stored)
        AUTH.claim(user,'reference:'+digest)
        return os.environ.get('YOUAI_PUBLIC_ASSET_BASE_URL','').rstrip('/')+AUTH.signed_url(user,'/reference-assets/'+digest+'.mp4',ttl=300)
    return WATCH_FLOW.deep_watch(user,sha,video,duration)

def reference_preview(user,reference,runner=subprocess.run):
    """A small 360p copy of the reference for the user to watch beside generated outputs; made once per reference and reused."""
    sha,path,_=_reference_asset(reference)
    marker=REFERENCE_ROOT/(sha+'.preview')
    digest=marker.read_text(encoding='utf-8').strip() if marker.is_file() else ''
    if not (re.fullmatch('[a-f0-9]{64}',digest) and (REFERENCE_ROOT/(digest+'.mp4')).is_file()):
        tmp=REFERENCE_ROOT/(sha+'.preview.tmp.mp4')
        result=runner([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-i',str(path),'-vf',"scale='if(gt(iw,ih),-2,360)':'if(gt(iw,ih),360,-2)'",'-r','24',
                       '-c:v','libx264','-preset','veryfast','-crf','32','-maxrate','600k','-bufsize','1200k','-c:a','aac','-b:a','48k','-ac','1','-movflags','+faststart',str(tmp)],capture_output=True,timeout=180)
        if getattr(result,'returncode',1)!=0 or not tmp.is_file() or tmp.stat().st_size==0:
            tmp.unlink(missing_ok=True);raise ValueError('原视频预览生成失败，请稍后再试')
        if tmp.stat().st_size>=path.stat().st_size:
            digest=sha;tmp.unlink(missing_ok=True)
        else:
            digest=hashlib.sha256(tmp.read_bytes()).hexdigest();stored=REFERENCE_ROOT/(digest+'.mp4')
            if stored.exists():tmp.unlink(missing_ok=True)
            else:tmp.replace(stored)
        marker.write_text(digest,encoding='utf-8')
    if AUTH and digest!=sha:AUTH.claim(user,'reference:'+digest)
    return {'url':'/reference-assets/'+digest+'.mp4','bytes':(REFERENCE_ROOT/(digest+'.mp4')).stat().st_size}

def analyze_reference(reference,runner=subprocess.run,transcriber=_transcribe_reference,progress=lambda *_:None,sampling='smart',user=''):
    sha,path,asset=_reference_asset(reference)
    if transcriber is _transcribe_reference:
        model=PLATFORM.config()['videoUnderstanding']['asrModel']
        transcriber=lambda audio:_transcribe_reference(audio,model=model)
    value,reused=WATCH_FLOW.watch(user,sha,path,asset.get('media') or {},transcriber,progress,post=reference.get('source') if isinstance(reference.get('source'),dict) else None)
    cfg=PLATFORM.config()['videoUnderstanding'];card=value['understanding']
    if cfg['autoDeepWatch'] and card.get('status')=='ready' and card.get('confidence',0)<cfg['deepWatchThreshold']:
        try:value={**value,'understanding':deep_reference(user,reference)}
        except Exception:pass  # Keep standard results on unavailable optional upgrade.
    return value,reused

def analysis_worker(job_id,reference,sampling='smart',user=''):
    def progress(phase,message):
        ANALYSIS_JOBS[job_id].update(phase=phase,message=message);persist_analysis(job_id)
    try:
        analysis,reused=analyze_reference(reference,progress=progress,sampling=sampling,user=user);analyzed={**reference,'status':'analyzed','analysis':analysis}
        ANALYSIS_JOBS[job_id].update(status='done',phase='done',message='内容分析完成',reference=analyzed,reused=reused,finishedAt=time.time())
        ledger_safe(LEDGER.card,(reference.get('asset') or {}).get('sha256'),analysis,reference.get('description') or reference.get('title') or '')
    except Exception as error:ANALYSIS_JOBS[job_id].update(status='failed',phase='failed',message='内容分析失败',error='内容分析失败，请重试',finishedAt=time.time())
    finally:persist_analysis(job_id)

def _parser_settings(config=None):
    config=config if isinstance(config,dict) else {}
    base=str(config.get('baseUrl') or os.environ.get('YOUAI_REFERENCE_PARSER_URL') or '').strip().rstrip('/')
    token=str(config.get('token') or PLATFORM.parser_token() or os.environ.get('YOUAI_REFERENCE_PARSER_KEY') or '').strip()
    if not base:raise ValueError('尚未配置素材解析服务，请到“我的”的工具接口管理中配置')
    parsed=urlparse(base)
    loopback=parsed.hostname in ('127.0.0.1','localhost','::1')
    internal_http_hosts={item.strip().lower() for item in os.environ.get('YOUAI_REFERENCE_PARSER_INTERNAL_HTTP_HOSTS','').split(',') if item.strip()}
    internal_http=parsed.scheme=='http' and parsed.hostname and parsed.hostname.lower() in internal_http_hosts
    if parsed.scheme not in (('https','http') if loopback or internal_http else ('https',)) or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:raise ValueError('素材解析服务必须是有效的 HTTPS 地址；本机回环或明确允许的容器内网主机可使用 HTTP 地址')
    if len(base)>500 or len(token)>2000 or '\r' in token or '\n' in token:raise ValueError('素材解析服务配置无效')
    return base,token

def check_parser(config,opener=urlopen):
    base,token=_parser_settings(config);headers={'User-Agent':'YOUAI/1.0'}
    if token:headers['Authorization']=f'Bearer {token}'
    document=json_request(f'{base}/openapi.json',headers=headers,opener=opener,timeout=15)
    paths=document.get('paths') if isinstance(document,dict) else None
    if not isinstance(paths,dict) or '/api/v1/parse' not in paths:raise ValueError('接口不是受支持的参考解析服务')
    return {'status':'ready','service':'douyin-tiktok-download-api-v5'}

def receive_reference_upload(stream,length,content_type,runner=subprocess.run):
    """Store a user-uploaded original video (multipart/form-data, single file field) like an acquired one."""
    limit=int(os.environ.get('YOUAI_REFERENCE_MAX_BYTES',str(200*1024*1024)))
    match=re.search(r'boundary="?([^";]{1,200})"?',content_type or '')
    if not match:raise ValueError('上传格式无效，请重试')
    if length<=0:raise ValueError('上传内容为空')
    if length>limit+64*1024:raise ValueError('原视频超过 200MB，请压缩后上传')
    boundary=match[1].encode();REFERENCE_ROOT.mkdir(parents=True,exist_ok=True)
    raw=REFERENCE_ROOT/f'.{uuid.uuid4().hex}.upload';temp=REFERENCE_ROOT/f'.{uuid.uuid4().hex}.download'
    try:
        remaining=length
        with raw.open('wb') as target:
            while remaining:
                chunk=stream.read(min(1024*1024,remaining))
                if not chunk:raise ValueError('上传中断，请重试')
                target.write(chunk);remaining-=len(chunk)
        with raw.open('rb') as source:
            head=source.read(64*1024);source.seek(max(0,length-64*1024));tail=source.read()
            header_end=head.find(b'\r\n\r\n')
            if not head.startswith(b'--'+boundary) or header_end<0 or b'filename=' not in head[:header_end]:raise ValueError('上传格式无效，请重试')
            closing=tail.rfind(b'\r\n--'+boundary)
            if closing<0:raise ValueError('上传不完整，请重试')
            start=header_end+4;end=max(0,length-64*1024)+closing
            if end-start<1024:raise ValueError('视频文件为空或不完整')
            digest=hashlib.sha256();source.seek(start);left=end-start
            with temp.open('wb') as target:
                while left:
                    chunk=source.read(min(1024*1024,left));digest.update(chunk);target.write(chunk);left-=len(chunk)
        media=_probe_video(temp,runner)
        sha=digest.hexdigest();stored=REFERENCE_ROOT/f'{sha}.mp4'
        if stored.exists():temp.unlink()
        else:temp.replace(stored)
        return {'status':'acquired','platform':'upload','needsUpload':False,'title':'上传的原视频','description':'','videoId':'','resolvedUrl':'','source':{'platform':'upload'},'asset':{'sha256':sha,'sizeBytes':end-start,'storagePath':str(stored),'media':media}}
    finally:
        raw.unlink(missing_ok=True);temp.unlink(missing_ok=True)

GALLERY_SECONDS=3.0
GALLERY_MAX_IMAGES=20

def _gallery_image_urls(document):
    """图文作品: one list of candidate URLs per image, in order; empty when the post has a real video."""
    data=document.get('data') if isinstance(document,dict) and isinstance(document.get('data'),dict) else document
    media=data.get('media') if isinstance(data,dict) and isinstance(data.get('media'),dict) else {}
    if isinstance(media.get('video'),dict) and (media['video'].get('url') or media['video'].get('urls')):return []
    groups=[]
    for image in media.get('images') if isinstance(media.get('images'),list) else []:
        if not isinstance(image,dict):continue
        urls=[u for u in [image.get('url'),*(image.get('urls') if isinstance(image.get('urls'),list) else [])] if isinstance(u,str) and u.startswith('https://')]
        if urls:groups.append(list(dict.fromkeys(urls)))
    return groups[:GALLERY_MAX_IMAGES]

def _build_gallery(groups, target, opener=urlopen, runner=subprocess.run):
    """Download every image and turn the post into a silent slideshow so frames, OCR, understanding and composing work unchanged."""
    from PIL import Image
    with tempfile.TemporaryDirectory(prefix='gallery-') as root:
        files=[]
        for index,urls in enumerate(groups):
            for url in urls:
                try:
                    request=Request(_safe_media_url(url),headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.douyin.com/','Accept':'image/*'})
                    with opener(request,timeout=60) as response:data=response.read(15*1024*1024+1)
                    if len(data)>15*1024*1024 or len(data)<512:continue
                    path=Path(root)/f'{index:02d}.jpg'
                    with Image.open(__import__('io').BytesIO(data)) as image:image.convert('RGB').save(path,'JPEG',quality=92)
                    files.append(path);break
                except Exception:continue
        if not files:raise ValueError('图文作品的图片下载失败')
        with Image.open(files[0]) as first:w,h=first.size
        height=int(round(1080*h/w/2)*2) if w else 1440;height=max(720,min(1920,height))
        command=[imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y']
        for file in files:command+=['-loop','1','-t',str(GALLERY_SECONDS),'-i',str(file)]
        chains=''.join(f'[{i}:v]scale=1080:{height}:force_original_aspect_ratio=decrease,pad=1080:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=25[v{i}];' for i in range(len(files)))
        command+=['-filter_complex',chains+''.join(f'[v{i}]' for i in range(len(files)))+f'concat=n={len(files)}:v=1:a=0[out]','-map','[out]','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-an','-f','mp4',str(target)]
        result=runner(command,capture_output=True,timeout=180)
        if result.returncode or not Path(target).exists():raise ValueError('图文作品转换失败')
    return len(files)

_PARSE_CACHE={};_PARSE_LOCK=threading.Lock()
def _parse_link(url,parser,headers,opener=urlopen):
    """Platform parse with a 3-minute in-memory cache, so the quick peek and the full acquire share one parse call."""
    cache_key=(url,parser)
    with _PARSE_LOCK:
        hit=_PARSE_CACHE.get(cache_key)
        if hit and time.time()-hit[0]<180:return hit[1]
    try:parsed=json_request(f'{parser}/api/v1/parse?wait=30',headers=headers,payload={'url':url},opener=opener,timeout=60)
    except ApiResponseError as error:raise _parser_failure(error) from None
    with _PARSE_LOCK:
        for k in [k for k,v in _PARSE_CACHE.items() if time.time()-v[0]>=180]:_PARSE_CACHE.pop(k,None)
        _PARSE_CACHE[cache_key]=(time.time(),parsed)
    return parsed

def _cover_url(parsed):
    data=parsed.get('data') if isinstance(parsed,dict) and isinstance(parsed.get('data'),dict) else (parsed if isinstance(parsed,dict) else {})
    media=data.get('media') if isinstance(data.get('media'),dict) else {}
    for group in ('covers','images'):
        for item in media.get(group) or []:
            value=item.get('url') if isinstance(item,dict) else item
            if isinstance(value,str) and value.startswith('https://'):return value
    return ''

def peek_reference(value,user='',opener=urlopen,parser_config=None):
    """大致内容的最快版本：只解析链接 + 看封面和文案（约 2–3 秒），不等视频下载。"""
    found=_link_module.detect(value)
    if found['platform'] not in ('douyin','none'):raise ValueError(found['message'])
    url=reference_url(value);parser,key=_parser_settings(parser_config)
    headers={'Content-Type':'application/json','User-Agent':'YOUAI/1.0'}
    if key:headers['Authorization']=f'Bearer {key}'
    parsed=_parse_link(url,parser,headers,opener)
    content_id=_first_field(parsed,('aweme_id','content_id','video_id'));title=_first_field(parsed,('desc','title'))
    cover=_cover_url(parsed)
    if not content_id or not cover:return {'status':'unavailable','overview':'','type':'','tags':[],'confidence':0}
    request=Request(_safe_media_url(cover),headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.douyin.com/'})
    with opener(request,timeout=6) as response:data=response.read(3*1024*1024+1)
    if len(data)>3*1024*1024:return {'status':'unavailable','overview':'','type':'','tags':[],'confidence':0}
    from PIL import Image as _Image
    import io as _io
    with _Image.open(_io.BytesIO(data)) as image:
        image=image.convert('RGB');image.thumbnail((540,540))
        result=WATCH_FLOW.peek(user,content_id,image.copy(),title)
    return {**result,'title':title[:120],'contentId':content_id}

def acquire_reference(value, opener=urlopen, runner=subprocess.run, parser_config=None, comments=True):
    found=_link_module.detect(value)
    if found['platform'] not in ('douyin','none'):raise ReferenceAcquireError(found['message'],'unsupported_platform','upload')
    url=reference_url(value)
    try:parser,key=_parser_settings(parser_config)
    except ValueError as error:raise ReferenceAcquireError(str(error),'parser_config','configure') from None
    headers={'Content-Type':'application/json','User-Agent':'YOUAI/1.0'}
    if key:headers['Authorization']=f'Bearer {key}'
    parsed=_parse_link(url,parser,headers,opener)
    gallery=_gallery_image_urls(parsed)
    urls=[] if gallery else _video_media_urls(parsed)
    if not urls and not gallery:raise ValueError('素材解析服务没有返回可下载的视频，请上传原视频')
    video_id=_first_field(parsed,('aweme_id','content_id','video_id'));title=_first_field(parsed,('desc','title'))
    identified={'status':'identified','platform':'douyin','videoId':video_id,'title':title[:120],'description':title[:300],'resolvedUrl':url,'source':_link_module.source_meta(parsed,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))}
    # 热评和视频下载同时进行（以前是先等评论 5 秒左右再下载）。
    comment_box={'rows':[]}
    def _load_comments():
        try:comment_box['rows']=_comments_module.fetch(ASSET_ROOT/'top-comments',identified['source'].get('contentId'),
            lambda path,timeout:json_request(parser+path,headers=headers,opener=opener,timeout=timeout),
            (identified['source'].get('author') or {}).get('uid',''))
        except Exception:comment_box['rows']=[]
    comment_thread=threading.Thread(target=_load_comments,daemon=True)
    if comments:comment_thread.start()
    def _with_comments(result):
        if comments:comment_thread.join(timeout=10)
        result['comments']=comment_box['rows'];return result
    limit=int(os.environ.get('YOUAI_REFERENCE_MAX_BYTES',str(200*1024*1024)))
    temp=REFERENCE_ROOT/f'.{uuid.uuid4().hex}.download'
    digest=None;size=0;media=None;last_error=None
    if gallery:
        try:
            count=_build_gallery(gallery,temp,opener,runner)
            data=temp.read_bytes();sha=hashlib.sha256(data).hexdigest();stored=REFERENCE_ROOT/f'{sha}.mp4'
            media=_probe_video(temp,runner)
            if stored.exists():temp.unlink()
            else:temp.replace(stored)
            identified['source']={**identified['source'],'kind':'gallery','imageCount':count}
            return _with_comments({**identified,'status':'acquired','needsUpload':False,'kind':'gallery','gallery':{'imageCount':count,'secondsPerImage':GALLERY_SECONDS},
                    'asset':{'sha256':sha,'sizeBytes':len(data),'storagePath':str(stored),'media':media}})
        except ValueError as error:
            temp.unlink(missing_ok=True);raise ReferenceAcquireError(str(error)+'，请重试或上传截图','media_download_failed','retry_or_upload') from None
        except Exception as error:
            temp.unlink(missing_ok=True);raise ReferenceAcquireError('图文作品处理失败，请重试','media_download_failed','retry_or_upload') from error
    try:
        for candidate in urls:
            temp.unlink(missing_ok=True);digest=hashlib.sha256();size=0
            try:
                media_url=_safe_media_url(candidate)
                request=Request(media_url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.douyin.com/','Accept':'video/mp4,video/*;q=0.9,*/*;q=0.1'})
                with opener(request,timeout=120) as response,temp.open('wb') as target:
                    while True:
                        chunk=response.read(1024*1024)
                        if not chunk:break
                        size+=len(chunk)
                        if size>limit:raise ValueError('参考视频超过 200MB，请压缩后上传')
                        digest.update(chunk);target.write(chunk)
                if size<1024:raise ValueError('取得的视频文件为空或不完整')
                media=_probe_video(temp,runner);break
            except ValueError as error:
                if '超过 200MB' in str(error):raise
                last_error=error
            except Exception as error:last_error=error
        if media is None:
            raise ReferenceAcquireError('平台已解析视频，但媒体下载受限，请重试或上传原视频','media_download_failed','retry_or_upload') from last_error
        sha=digest.hexdigest();stored=REFERENCE_ROOT/f'{sha}.mp4'
        if stored.exists():temp.unlink()
        else:temp.replace(stored)
        return _with_comments({**identified,'status':'acquired','needsUpload':False,'asset':{'sha256':sha,'sizeBytes':size,'storagePath':str(stored),'media':media}})
    except Exception:
        temp.unlink(missing_ok=True);raise

CREATION_TOOL_IDS={'download','transcript','audio','eraser','cover'}

def run_creation_tool(tool,value,parser_config=None,runner=subprocess.run,transcriber=_transcribe_reference,cache_scope=''):
    if tool not in CREATION_TOOL_IDS:raise ValueError('不支持的创作工具')
    if _config_module.client_config()['tools'].get(tool,{}).get('maintenance'):raise ValueError('该工具正在维护，请稍后重试')
    url=reference_url(value);index_dir=TOOL_ROOT/'url-index';index_dir.mkdir(exist_ok=True);index_file=index_dir/f'{hashlib.sha256((url+"|"+cache_scope if cache_scope else url).encode()).hexdigest()}.json';reference=None
    source_reused=False
    if index_file.exists():
        try:
            candidate=json.loads(index_file.read_text(encoding='utf-8'));_reference_asset(candidate);reference=candidate;source_reused=True
        except (ValueError,TypeError,OSError,json.JSONDecodeError):pass
    if reference is None:
        reference=acquire_reference(url,runner=runner,parser_config=parser_config);index_file.write_text(json.dumps(reference,ensure_ascii=False,indent=2),encoding='utf-8')
    sha,path,asset=_reference_asset(reference);folder=TOOL_ROOT/sha;folder.mkdir(parents=True,exist_ok=True)
    common={'status':'done','tool':tool,'sha256':sha,'title':reference.get('title') or '抖音视频','media':asset.get('media') or {},'sourceReused':source_reused,'reused':source_reused}
    if tool in ('download','eraser'):
        return {**common,'kind':'video','assetUrl':f'/tool-assets/{sha}/source.mp4','message':'已取得平台解析返回的无水印原片' if tool=='eraser' else '视频已解析并保存'}
    if tool=='transcript':
        target=folder/'transcript.json';transcript={}
        if target.exists():
            try:transcript=json.loads(target.read_text(encoding='utf-8'))
            except (OSError,json.JSONDecodeError):pass
        if not isinstance(transcript,dict) or transcript.get('status') not in ('available','silent'):
            transcript=transcriber(path);common['reused']=False
            if transcript.get('status') not in ('available','silent'):
                raise ValueError(transcript.get('note') or '语音识别暂时不可用，请稍后重试')
            target.write_text(json.dumps(transcript,ensure_ascii=False,indent=2),encoding='utf-8')
        return {**common,'kind':'text','transcript':transcript,'message':'文案已提取，请校对后使用'}
    if tool=='audio':
        target=folder/'audio.mp3'
        if not target.exists():
            result=runner([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-v','error','-i',str(path),'-vn','-ac','2','-ar','44100','-b:a','192k',str(target)],capture_output=True,timeout=120)
            if result.returncode or not target.exists():raise ValueError('音频提取失败，原视频可能没有可用音轨')
            common['reused']=False
        return {**common,'kind':'audio','assetUrl':f'/tool-assets/{sha}/audio.mp3','message':'音频已提取为 MP3'}
    target=folder/'cover.jpg'
    if not target.exists():
        result=runner([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-v','error','-i',str(path),'-vf','thumbnail=100,scale=720:-2','-frames:v','1',str(target)],capture_output=True,timeout=120)
        if result.returncode or not target.exists():raise ValueError('封面提取失败，请重试')
        common['reused']=False
    return {**common,'kind':'image','assetUrl':f'/tool-assets/{sha}/cover.jpg','message':'已选择具有代表性的清晰画面'}

def creation_tool_asset(sha,name):
    if not re.fullmatch(r'[a-f0-9]{64}',sha):return None,None
    if name=='source.mp4':path=REFERENCE_ROOT/f'{sha}.mp4';mime='video/mp4'
    elif name=='audio.mp3':path=TOOL_ROOT/sha/name;mime='audio/mpeg'
    elif name=='cover.jpg':path=TOOL_ROOT/sha/name;mime='image/jpeg'
    else:return None,None
    expected=(REFERENCE_ROOT if name=='source.mp4' else TOOL_ROOT/sha).resolve()
    resolved=path.resolve()
    return (resolved,mime) if resolved.parent==expected and resolved.is_file() else (None,None)

# Compatibility name for callers that only need URL identification.
read_reference=identify_reference

def render(job_id, data):
    folder = ROOT / job_id
    folder.mkdir()
    font_path = os.environ.get('YOUAI_VIDEO_FONT', 'C:/Windows/Fonts/msyh.ttc')
    font = ImageFont.truetype(font_path, 30)
    small = ImageFont.truetype(font_path, 14)
    parts = [str(item.get('narration')).strip() for item in (data.get('storyboard') or {}).get('shots',[]) if str(item.get('narration') or '').strip()] or segments(data['idea'])
    listing = []
    for index, text in enumerate(parts):
        bg, ink = PALETTES[data['mood']]
        image = Image.new('RGB', (360, 640), bg)
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((20, 130, 340, 500), radius=28, fill='#ffffff')
        lines, line = [], ''
        for char in text:
            if draw.textlength(line + char, font=font) > 270 and line:
                lines.append(line)
                line = ''
            line += char
        if line:
            lines.append(line)
        y = 315 - len(lines) * 23
        for line in lines:
            draw.text((180, y), line, font=font, fill=ink, anchor='mt')
            y += 46
        draw.text((180, 560), f'{index+1:02d} / {len(parts):02d}', font=small, fill=ink, anchor='mt')
        image.save(folder / f'{index}.png')
        listing.extend([f"file '{index}.png'", f"duration {data['duration']/len(parts):.6f}"])
    listing.append(f"file '{len(parts)-1}.png'")
    (folder / 'frames.txt').write_text('\n'.join(listing), encoding='utf-8')
    output = folder / 'video.mp4'
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(folder/'frames.txt'), '-vf', 'fps=24,tpad=stop_mode=clone:stop_duration=30,scale=380:676,crop=360:640:x=10+8*sin(t/3):y=18,format=yuv420p', '-r', '24', '-t', str(data['duration']), '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '24', '-movflags', '+faststart', str(output)], check=True, timeout=120, capture_output=True)
    return output

def worker(job_id, data):
    try:
        provider_task = generate_qianwen(job_id, data) if data['visualStyle'] == 'AI 生成画面' else None
        if provider_task:
            manifest=persist_run_assets(job_id,data,'qianwen',provider_task);update_job(job_id, status='done', phase='done', message='成片与资产包已准备好', url=f'/assets/{job_id}/final.mp4',assetUrl=f'/asset-runs/{job_id}',assetStatus=(manifest.get('database') or {}).get('status','saved'), provider='qianwen', providerTaskId=provider_task)
        else:
            update_job(job_id, phase='rendering', message='正在本机合成纯文字画面', provider='local-text')
            render(job_id, data)
            manifest=persist_run_assets(job_id,data,'local-text');update_job(job_id, status='done', phase='done', message='成片与资产包已准备好', url=f'/assets/{job_id}/final.mp4',assetUrl=f'/asset-runs/{job_id}',assetStatus=(manifest.get('database') or {}).get('status','saved'), provider='local-text')
    except Exception as error:
        update_job(job_id, status='failed', phase='failed', message='生成未完成', error=str(error)[:180] or '视频生成失败')
    finally:
        LOCK.release()

_idea_spec=importlib.util.spec_from_file_location('idea_box',Path(__file__).with_name('idea-box.py'));_idea_module=importlib.util.module_from_spec(_idea_spec);_idea_spec.loader.exec_module(_idea_module)
_screen_spec=importlib.util.spec_from_file_location('screen_text_ideas',Path(__file__).with_name('screen-text.py'));_screen_module=importlib.util.module_from_spec(_screen_spec);_screen_spec.loader.exec_module(_screen_module)
def _idea_ocr(path):
    if not _screen_module.available():return []
    from PIL import Image
    with Image.open(path) as image:return _screen_module.lines(image.convert('RGB'))
IDEAS=_idea_module.IdeaBox(ASSET_ROOT/'ideas',INSPIRATION_AI,ocr=_idea_ocr,asr=lambda path:_transcribe_reference(path),detect=_link_module.detect)
def read_multipart_file(stream,length,content_type,limit):
    """Small single-file multipart body read fully into memory (fragment screenshots and voice)."""
    match=re.search(r'boundary="?([^";]{1,200})"?',content_type or '')
    if not match or not 0<length<=limit+64*1024:raise _idea_module.IdeaError('上传内容无效或过大')
    body=stream.read(length);boundary=b'--'+match[1].encode()
    for part in body.split(boundary)[1:]:
        head,sep,data=part.partition(b'\r\n\r\n')
        if sep and b'filename=' in head:
            if data.endswith(b'\r\n'):data=data[:-2]
            return data
    raise _idea_module.IdeaError('没有收到文件')

def trial_client(headers):
    """WeChat sets Referer servicewechat.com/<appid>/<version>/page-frame.html; version is 0 for develop/trial builds and devtools in the simulator."""
    match=re.fullmatch(r'https://servicewechat\.com/wx[0-9a-f]{16}/(\d+|devtools)/page-frame\.html',headers.get('Referer','') or '')
    return bool(match) and match[1] in ('0','devtools')

class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):
        print(json.dumps({'event':'video.http','method':self.command,'path':urlparse(getattr(self,'path','')).path,'status':str(args[1]) if len(args)>1 else ''}),file=sys.stderr,flush=True)
    def guard(self):
        self.original_path=self.path;self.path=urlparse(self.path).path;self.user_id=None
        if not AUTH or self.path in ('/health','/auth/login','/client-config','/hotspots','/hotspots/search') or re.fullmatch(r'/hotspot-content/(douyin|weibo|toutiao|kuaishou)-[a-f0-9]{20}',self.path):return True
        header=self.headers.get('Authorization','')
        self.user_id=AUTH.user(header[7:]) if header.startswith('Bearer ') else None
        is_media=self.path.endswith(('.mp4','.mp3','.jpg','.png')) and AUTH.resource(self.path)
        if not self.user_id and is_media:self.user_id=AUTH.media_user(self.original_path)
        if not self.user_id:self.reply(401,{'error':'请重新登录'});return False
        resource=AUTH.resource(self.path)
        if resource and not AUTH.owns(self.user_id,resource):self.reply(403,{'error':'资产不属于当前账号'});return False
        if self.path not in ('/auth/me','/auth/phone','/auth/logout','/auth/trial') and not AUTH.bound(self.user_id):
            self.reply(403,{'error':'请先授权手机号','code':'PHONE_REQUIRED'});return False
        return True
    def signed(self,value):
        if isinstance(value,dict):return {key:self.signed(item) for key,item in value.items()}
        if isinstance(value,list):return [self.signed(item) for item in value]
        if isinstance(value,str) and value.startswith('/') and urlparse(value).path.endswith(('.mp4','.mp3','.jpg','.png')) and AUTH.resource(value) and AUTH.owns(self.user_id,AUTH.resource(value)):
            return AUTH.signed_url(self.user_id,value)
        return value
    def reply(self, status, data):
        if AUTH and getattr(self,'user_id',None) and status==200:
            if self.path in ('/references/acquire','/references/upload') or self.path.startswith('/reference-analyses/'):AUTH.remember(self.user_id,data)
            if self.path=='/tools/run' and isinstance(data,dict) and re.fullmatch('[a-f0-9]{64}',str(data.get('sha256',''))):AUTH.claim(self.user_id,'tool:'+data['sha256'])
            data=self.signed(data)
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def board_reference(self,payload):
        sha=((payload.get('reference') or {}).get('asset') or {}).get('sha256') if isinstance(payload.get('reference'),dict) else None
        reference=AUTH.reference(self.user_id,sha) if AUTH else payload.get('reference')
        if not isinstance(reference,dict):raise ValueError('参考视频不存在，请重新获取')
        return reference
    def voice_transcribe(self):
        """Voice input for chat boxes: transcribe locally and return text; the audio is deleted and nothing is stored."""
        if not AUTH or not self.user_id:return self.reply(401,{'error':'请登录后继续'})
        try:
            data=read_multipart_file(self.rfile,int(self.headers.get('Content-Length','0') or 0),self.headers.get('Content-Type',''),_idea_module.MAX_VOICE_BYTES)
            if len(data)<64:raise _idea_module.IdeaError('录音为空，请再说一次')
            temp=ASSET_ROOT/'ideas'/('.%s.voice'%uuid.uuid4().hex);temp.parent.mkdir(parents=True,exist_ok=True);temp.write_bytes(data)
            try:result=_transcribe_reference(temp)
            finally:temp.unlink(missing_ok=True)
        except _idea_module.IdeaError as error:return self.reply(422,{'error':str(error)})
        except (ValueError,TypeError):return self.reply(400,{'error':'录音上传无效'})
        if result.get('status')=='unavailable':return self.reply(503,{'error':result.get('note') or '语音识别暂不可用，请先打字'})
        text=re.sub(r'\s+',' ',result.get('text') or '').strip()[:1000]
        if not text:return self.reply(422,{'error':'没听清，请靠近一点再说一次'})
        return self.reply(200,{'text':text})
    def ideas_post(self):
        if not AUTH or not self.user_id:return self.reply(401,{'error':'请登录后继续'})
        user=self.user_id
        try:
            if self.path=='/ideas/media':
                query=parse_qs(urlparse(self.original_path).query)
                kind=query.get('kind',[''])[0]
                data=read_multipart_file(self.rfile,int(self.headers.get('Content-Length','0') or 0),self.headers.get('Content-Type',''),_idea_module.MAX_IMAGE_BYTES)
                fragment=IDEAS.add_media(user,kind,data,query.get('clientId',[None])[0])
                if fragment.get('image'):AUTH.claim(user,'idea:'+fragment['id'])
                return self.reply(200,fragment)
            length=int(self.headers.get('Content-Length','0') or 0)
            if not 2<=length<=8192:raise _idea_module.IdeaError('请求内容无效')
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload,dict):raise _idea_module.IdeaError('请求内容无效')
            if self.path=='/ideas':return self.reply(200,IDEAS.add_text(user,payload))
            if self.path=='/ideas/sync':
                rows=payload.get('items') if set(payload)=={'items'} and isinstance(payload.get('items'),list) else None
                if rows is None or len(rows)>50:raise _idea_module.IdeaError('同步内容无效')
                saved=[]
                for item in rows:
                    try:saved.append(IDEAS.add_text(user,item))
                    except _idea_module.IdeaError as error:
                        if error.code=='quota':break
                return self.reply(200,{'saved':len(saved),'rows':saved})
            match=re.fullmatch(r'/ideas/([a-f0-9]{32})/(status|delete)',self.path)
            if match:
                ident,action=match.groups()
                if action=='delete':return self.reply(200,IDEAS.delete(user,ident))
                return self.reply(200,IDEAS.set_status(user,ident,payload.get('status')))
            return self.reply(404,{'error':'接口不存在'})
        except _idea_module.IdeaError as error:return self.reply(404 if error.code=='missing' else 429 if error.code=='quota' else 422,{'error':str(error),'code':error.code})
        except (ValueError,TypeError):return self.reply(400,{'error':'请求内容无效'})
        except Exception as error:
            print(json.dumps({'event':'ideas.failed','type':type(error).__name__}),file=sys.stderr,flush=True)
            return self.reply(503,{'error':'碎片箱暂时不可用，请稍后重试'})
    def board_post(self):
        if not AUTH or not self.user_id:return self.reply(401,{'error':'请登录后继续'})
        limit=6*1024*1024 if self.path.endswith('/screenshot') else 64*1024
        try:length=int(self.headers.get('Content-Length','0'))
        except (TypeError,ValueError):return self.reply(400,{'error':'请求内容无效'})
        if not 0<length<=limit:return self.reply(413 if length>limit else 400,{'error':'请求内容无效或过大'})
        try:payload=json.loads(self.rfile.read(length))
        except ValueError:return self.reply(400,{'error':'请求 JSON 无法解析，请重试'})
        if not isinstance(payload,dict):return self.reply(400,{'error':'请求内容必须是对象'})
        user,path=self.user_id,self.path;ident=payload.get('id')
        try:
            if path=='/board/session':return self.reply(200,BOARD.start(user,self.board_reference(payload),payload.get('glance')))
            if path=='/board/quota/request':return self.reply(200,BOARD.request_quota(user,payload.get('amount'),payload.get('reason','')))
            if path=='/board/refresh':return self.reply(200,BOARD.refresh(user,ident))
            if path=='/board/answer':
                key=payload.get('key')
                return self.reply(200,(BOARD.answer_followup if str(key).startswith('followup') else BOARD.answer)(user,ident,key,payload.get('value')))
            if path=='/board/followups':return self.reply(200,BOARD.followups(user,ident,payload.get('stage')))
            if path=='/board/interview':return self.reply(200,BOARD.interview(user,ident,payload.get('message','')))
            if path=='/board/confirm':return self.reply(200,BOARD.confirm(user,ident,payload))
            if path=='/board/rewatch':return self.reply(200,BOARD.rewatch(user,ident,payload.get('start'),payload.get('end')))
            if path=='/board/breakdown':
                result=BOARD.breakdown(user,ident);self.ledger_board(user,ident);return self.reply(200,result)
            if path=='/board/adjust':
                result=BOARD.adjust(user,ident,payload.get('message'),payload.get('save') is True);self.ledger_board(user,ident);return self.reply(200,result)
            if path=='/board/output/text':
                result=BOARD.text_work(user,ident,payload.get('instruction',''));self.ledger_board(user,ident,'text');return self.reply(200,result)
            if path=='/board/preview':return self.reply(200,reference_preview(user,BOARD._reference(user,BOARD.session(user,ident))))
            if path=='/board/output/package':
                result=BOARD.package(user,ident,payload.get('conditions',''));self.ledger_board(user,ident,'package');return self.reply(200,result)
            if path=='/board/compose':
                clips=[]
                for sha in payload.get('clips',[])[:8] if isinstance(payload.get('clips'),list) else []:
                    clips.append(Path(AUTH.reference(user,sha)['asset']['storagePath']))
                job=BOARD.compose(user,ident,payload,clips)
                AUTH.claim(user,'board:'+job['id'])
                return self.reply(200,job)
            if path=='/board/variants':
                clips=[Path(AUTH.reference(user,sha)['asset']['storagePath']) for sha in (payload.get('clips',[])[:8] if isinstance(payload.get('clips'),list) else [])]
                job=BOARD.variants(user,ident,payload,clips)
                for item in job.get('items',[]):AUTH.claim(user,'board:'+item['id'])
                return self.reply(200,job)
            if path=='/board/plans':
                action=payload.get('action')
                if action=='chat':return self.reply(200,BOARD.chat_plan(user,payload.get('message'),payload.get('baseId')))
                if action=='save':return self.reply(200,BOARD.save_plan(user,payload.get('plan') or {},ident=payload.get('planId')))
                if action=='fork':return self.reply(200,BOARD.fork_plan(user,payload.get('planId')))
                if action=='rollback':return self.reply(200,BOARD.rollback_plan(user,payload.get('planId'),payload.get('version')))
                if action=='delete':return self.reply(200,BOARD.delete_plan(user,payload.get('planId')))
                if action=='induce':return self.reply(200,BOARD.induce(user,payload.get('urls')))
                return self.reply(400,{'error':'方案操作无效'})
            if path=='/board/works':return self.reply(200,BOARD.create_work(user,ident,payload))
            if path=='/board/monitors':return self.reply(200,BOARD.add_monitor(user,payload.get('url'),payload.get('role') or 'benchmark'))
            match=re.fullmatch(r'/board/works/([a-f0-9]{32})/(link|subscribe|screenshot|metrics|refresh|remove|role)',path)
            if match:
                wid,action=match.groups()
                if action=='link':return self.reply(200,BOARD.link_work(user,wid,payload.get('url')))
                if action=='subscribe':return self.reply(200,BOARD.subscribe(user,wid,payload.get('accepted')))
                if action=='screenshot':return self.reply(200,BOARD.read_screenshot(user,wid,payload.get('image')))
                if action=='refresh':return self.reply(200,BOARD.refresh_work(user,wid))
                if action=='remove':return self.reply(200,BOARD.remove_work(user,wid))
                if action=='role':return self.reply(200,BOARD.set_role(user,wid,payload.get('role')))
                return self.reply(200,BOARD.save_metrics(user,wid,payload.get('day'),payload.get('values')))
            return self.reply(404,{'error':'Not found'})
        except _auth_module.LoginError as error:return self.reply(403,{'error':str(error)})
        except _board_module.BoardError as error:return self.reply(422,{'error':str(error),'code':error.code})
        except _watchflow_module.usage.UsageLimit as error:return self.reply(429,{'error':str(error)})
        except ValueError as error:return self.reply(422,{'error':str(error)})
        except Exception as error:
            print(json.dumps({'event':'board.failed','path':path,'error':type(error).__name__,'code':getattr(error,'code','')}),file=sys.stderr,flush=True)
            code=getattr(error,'code','')
            return self.reply(503,{'error':'AI 服务暂时不可用，请稍后重试' if code else '创作板块暂时不可用，请稍后重试'})
    def ledger_board(self,user,ident,output=None):
        def run():
            session=BOARD.session(user,ident);title=str(((session.get('source') or {}).get('description')) or '')[:200]
            LEDGER.breakdown(user,session,title)
            out=(session.get('outputs') or {}).get(output) if output else None
            if isinstance(out,dict):
                if output=='text':
                    body='\n'.join([*('大标题：'+str(x.get('text','')) for x in out.get('screenTitles') or [] if isinstance(x,dict)),*(str(l.get('text','')) for l in out.get('lines') or [] if isinstance(l,dict)),
                                     *('标题'+str(n+1)+'：'+str(t) for n,t in enumerate(out.get('titles') or [])),'封面大字：'+str(out.get('cover') or ''),' '.join('#'+str(h) for h in out.get('hashtags') or [])])
                    LEDGER.work(user,ident+':text','文字作品',session,(out.get('titles') or [title])[0] if (out.get('titles') or [title]) else title,body)
                else:
                    body='\n'.join(f"{s.get('start')}–{s.get('end')}秒 · {s.get('shot','')}｜手机：{s.get('phone','')}｜动作：{s.get('action','')}"+(f"｜台词：{s.get('line')}" if s.get('line') else '') for s in out.get('shots') or [] if isinstance(s,dict))
                    body+='\n\n口播：'+str(out.get('script') or '')+'\n清单：'+'、'.join(str(c) for c in out.get('checklist') or [])
                    LEDGER.work(user,ident+':package','创作包',session,title,body)
        ledger_safe(run)
    def board_get(self):
        if not AUTH or not self.user_id:return self.reply(401,{'error':'请登录后继续'})
        user,path=self.user_id,self.path
        try:
            if path=='/board/plans':return self.reply(200,BOARD.plans(user))
            if path=='/board/works':return self.reply(200,{'rows':BOARD.works(user)})
            if path=='/board/history':return self.reply(200,{'rows':BOARD.history(user)})
            if path=='/board/credits':return self.reply(200,BOARD.credits(user))
            if path=='/board/quota':return self.reply(200,BOARD.quota_status(user))
            match=re.fullmatch(r'/board/(works|jobs|session)/([a-f0-9]{32})',path)
            if match:
                kind,ident=match.groups()
                if kind=='works':return self.reply(200,BOARD.work_view(user,ident))
                if kind=='jobs':return self.reply(200,BOARD.job(user,ident))
                return self.reply(200,BOARD.public(BOARD.session(user,ident)))
            return self.reply(404,{'error':'Not found'})
        except _board_module.BoardError as error:return self.reply(422 if error.code!='missing' else 404,{'error':str(error),'code':error.code})
    def mcp(self):
        """Remote MCP for outside AI clients: own token, daily cap, then relay to dtk's MCP (see mcp-gateway.py)."""
        def plain(status,data,extra=()):
            body=json.dumps(data,ensure_ascii=False).encode();self.send_response(status)
            for k,v in (('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(body))),('Cache-Control','no-store'))+tuple(extra):self.send_header(k,v)
            self.end_headers();self.wfile.write(body)
        if not MCP_GATEWAY.authorized(self.headers.get('Authorization','')):
            return plain(401,{'error':'MCP 访问令牌无效'},(('WWW-Authenticate','Bearer realm="youai-mcp"'),))
        body=b''
        if self.command=='POST':
            length=int(self.headers.get('Content-Length') or 0)
            if length<=0 or length>_mcp_module.MAX_BODY:return plain(413,{'error':'请求过大'})
            body=self.rfile.read(length)
            billable=MCP_GATEWAY.billable(body)
            if billable and not MCP_GATEWAY.charge(len(billable)):
                refusal=MCP_GATEWAY.refusal(body)
                if not refusal:return plain(429,{'error':'今日 MCP 额度已用完'})
                self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(refusal)))
                if self.headers.get('Mcp-Session-Id'):self.send_header('Mcp-Session-Id',self.headers.get('Mcp-Session-Id'))
                self.end_headers();self.wfile.write(refusal);return
            local=MCP_GATEWAY.local_call(body)
            if local is not None:
                self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(local)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(local);return
        status,headers,chunks=MCP_GATEWAY.relay(self.command,{k:self.headers.get(k) for k in _mcp_module.FORWARD_HEADERS},body)
        if self.command=='POST' and status==200 and MCP_GATEWAY.is_list(body):
            data=MCP_GATEWAY.augment_list(b''.join(chunks),dict(headers).get('Content-Type',''))
            self.send_response(200)
            for k,v in headers:self.send_header(k,v)
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        self.send_response(status)
        for k,v in headers:self.send_header(k,v)
        self.send_header('X-Accel-Buffering','no');self.send_header('Connection','close');self.end_headers()
        try:
            for chunk in chunks:self.wfile.write(chunk);self.wfile.flush()
        except (BrokenPipeError,ConnectionResetError):pass
    def do_DELETE(self):
        if urlparse(self.path).path=='/mcp':return self.mcp()
        self.send_response(405);self.send_header('Content-Length','0');self.end_headers()
    def do_POST(self):
        if urlparse(self.path).path=='/mcp':return self.mcp()
        if ADMIN.handle(self):return
        if not self.guard():return
        if self.path.startswith('/board/'):return self.board_post()
        if self.path=='/ideas' or self.path.startswith('/ideas/'):return self.ideas_post()
        if self.path=='/voice/transcribe':return self.voice_transcribe()
        if self.path=='/references/upload':
            try:length=int(self.headers.get('Content-Length','0'))
            except (TypeError,ValueError):return self.reply(400,{'error':'上传内容无效'})
            try:return self.reply(200,receive_reference_upload(self.rfile,length,self.headers.get('Content-Type','')))
            except ValueError as error:return self.reply(422,{'status':'failed','error':str(error)})
            except Exception:return self.reply(500,{'status':'failed','error':'原视频保存失败，请重试'})
        if self.path=='/auth/profile':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=2048:raise ValueError('资料过长')
                return self.reply(200,AUTH.update_profile(self.user_id,json.loads(self.rfile.read(length))))
            except (ValueError,TypeError) as e:return self.reply(400,{'error':str(e) if isinstance(e,_auth_module.LoginError) else '资料请求无效'})
        if self.path=='/task-interest':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录并绑定手机号'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=128:raise ValueError()
                payload=json.loads(self.rfile.read(length))
                if payload!={}:raise ValueError()
                return self.reply(200,ADMIN.task_interest(self.user_id))
            except (ValueError,TypeError):return self.reply(400,{'error':'请求无效'})
        if self.path=='/auth/trial':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'微信账号服务暂不可用'})
            if not trial_client(self.headers):return self.reply(403,{'error':'测试账号只能在体验版或开发版中生成'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=64 or json.loads(self.rfile.read(length))!={}:raise ValueError()
                return self.reply(200,AUTH.create_trial(self.user_id))
            except _auth_module.LoginError as error:return self.reply(422,{'error':str(error)})
            except (ValueError,TypeError):return self.reply(400,{'error':'请求无效'})
        if self.path=='/auth/phone':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'微信账号服务暂不可用'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=4096:raise ValueError()
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict) or set(payload)!={'code'}:raise ValueError()
                profile=AUTH.bind_phone(self.user_id,payload['code']);ledger_user(self.user_id)
                return self.reply(200,profile)
            except _auth_module.LoginError as error:return self.reply(422,{'error':str(error)})
            except (ValueError,TypeError):return self.reply(400,{'error':'手机号授权请求无效'})
            except Exception:return self.reply(503,{'error':'手机号授权暂时不可用'})
        if self.path in ('/hotspot-watch','/hotspot-watch/remove'):
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录微信账号'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=1024:raise ValueError()
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict) or set(payload)!={'keyword'}:raise ValueError()
                term=payload['keyword']
                if self.path.endswith('/remove'):HOTSPOT_WATCH.remove(self.user_id,term)
                else:HOTSPOT_WATCH.add(self.user_id,term)
                HOTSPOT_WATCH.sample(_hotspot_module.snapshot())
                return self.reply(200,HOTSPOT_WATCH.view(self.user_id,term))
            except (ValueError,TypeError) as e:return self.reply(400,{'error':str(e) or '关注关键词无效'})
            except Exception:return self.reply(503,{'error':'关注保存暂不可用，请重试'})
        if self.path in ('/topics/chat','/topics/chat/clear'):
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录微信账号'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=8192:raise ValueError()
                payload=json.loads(self.rfile.read(length))
                if self.path.endswith('/clear'):
                    if payload!={}:raise ValueError()
                    return self.reply(200,TOPIC_CHAT.clear(self.user_id))
                prefs=ANALYSIS_PREFERENCES.read(self.user_id).get('preferences') or {}
                prefs={k:prefs.get(k) for k in ('preset','goals','materialType')}
                return self.reply(200,TOPIC_CHAT.chat(self.user_id,payload,_hotspot_module.snapshot(),topic_owned_history(self.user_id),prefs,profile=PROFILES.text(self.user_id),settings=PLATFORM.personalization(),
                    fragments=lambda focus,user=self.user_id:IDEAS.for_ta(user,focus=focus),surfaced=lambda ids,user=self.user_id:IDEAS.surfaced(user,ids)))
            except (ValueError,TypeError):return self.reply(400,{'error':'选题对话请求无效'})
            except _topic_module.ChatError as error:return self.reply(503,{'error':str(error)})
            except Exception:return self.reply(503,{'error':'AI选题暂不可用，请稍后重试'})
        if self.path in ('/profile/signal','/profile/remove','/profile/settings','/profile/clear'):
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录微信账号'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=4096:raise ValueError('请求内容无效')
                payload=json.loads(self.rfile.read(length))
                if self.path=='/profile/signal':return self.reply(200,PROFILES.signal(self.user_id,payload))
                if self.path=='/profile/remove':return self.reply(200,PROFILES.remove(self.user_id,payload))
                if self.path=='/profile/settings':return self.reply(200,PROFILES.set_enabled(self.user_id,payload))
                if payload!={}:raise ValueError('请求内容无效')
                return self.reply(200,PROFILES.clear(self.user_id))
            except json.JSONDecodeError:return self.reply(400,{'error':'请求内容无效'})
            except (ValueError,TypeError) as e:return self.reply(400,{'error':str(e) if isinstance(e,ValueError) and str(e) else '请求内容无效'})
        if self.path=='/hotspots/summary':
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=2048:raise ValueError()
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict) or set(payload) not in ({'platform'},{'platform','preference'}):raise ValueError()
                preference=payload.get('preference','')
                if not isinstance(preference,str) or len(preference)>500:raise ValueError()
                return self.reply(200,_summary_module.summarize(payload['platform'],_hotspot_module.snapshot(),self.user_id,preference=preference))
            except ValueError:return self.reply(400,{'error':'热点总结请求无效'})
            except _summary_module.Unavailable as error:return self.reply(503,{'error':str(error)})
            except Exception:return self.reply(503,{'error':'AI热点总结暂不可用，请稍后重试'})
        if self.path=='/analysis-preferences':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'微信账号同步暂不可用'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 2<=length<=524288:raise ValueError('模板内容过大，请精简后同步')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict) or set(payload)!={'expectedRevision','preferences'}:raise ValueError('模板同步请求无效')
                return self.reply(200,ANALYSIS_PREFERENCES.write(self.user_id,payload['expectedRevision'],payload['preferences']))
            except _prefs_module.Conflict:return self.reply(409,{'error':'云端已有新版本，本机修改已保留'})
            except (ValueError,TypeError):return self.reply(400,{'error':'模板同步数据无效或过大，请检查模板'})
            except Exception:return self.reply(503,{'error':'模板云同步暂不可用，本机修改已保留'})
        if self.path=='/auth/logout':
            header=self.headers.get('Authorization','')
            if not AUTH or not header.startswith('Bearer '):return self.reply(401,{'error':'请重新登录'})
            AUTH.revoke(header[7:]);return self.reply(200,{'status':'signed_out'})
        if self.path=='/auth/login':
            if not AUTH:return self.reply(503,{'error':'服务端微信登录尚未配置'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 1<=length<=4096:raise ValueError('登录请求大小无效')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict) or not set(payload)<={'code','trial'}:raise ValueError('登录请求无效')
                return self.reply(200,AUTH.login(payload.get('code'),payload.get('trial') if trial_client(self.headers) else None))
            except _auth_module.LoginError as error:return self.reply(401,{'error':str(error)})
            except (ValueError,TypeError):return self.reply(400,{'error':'登录请求无效'})
            except Exception:return self.reply(503,{'error':'微信登录暂时不可用'})
        feedback_action=re.fullmatch(r'/asset-runs/([a-f0-9]{32})/feedback',self.path)
        if feedback_action:
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<1 or length>4096:raise ValueError('反馈内容超出限制')
                payload=json.loads(self.rfile.read(length).decode('utf-8'))
                return self.reply(200,ARCHIVE.feedback(feedback_action[1],payload))
            except (ValueError,RuntimeError):return self.reply(422,{'error':'反馈内容无效'})
        archive_action=re.fullmatch(r'/asset-runs/([a-f0-9]{32})/(archive|restore)',self.path)
        if archive_action:
            try:
                run_id,action=archive_action.groups()
                if action=='archive':ARCHIVE.enqueue(run_id);return self.reply(200,ARCHIVE.status(run_id))
                return self.reply(200,ARCHIVE.restore(run_id))
            except (ValueError,RuntimeError) as error:return self.reply(422,{'error':str(error)})
            except Exception:return self.reply(500,{'error':'资产恢复失败，请检查归档状态'})
        if self.path not in POST_LIMITS:
            return self.reply(404, {'error':'Not found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except (ValueError,TypeError):
            return self.reply(400, {'error':'请求内容无效'})
        if length<=0:return self.reply(400,{'error':'请求内容无效'})
        if length>POST_LIMITS[self.path]:return self.reply(413,{'error':f'请求内容超过该接口 {POST_LIMITS[self.path]//1024} KB 上限，请减少内容后重试'})
        try:payload=json.loads(self.rfile.read(length))
        except (ValueError,TypeError):return self.reply(400,{'error':'请求 JSON 无法解析，请重试'})
        if not isinstance(payload,dict):return self.reply(400,{'error':'请求内容必须是对象'})
        if AUTH and self.user_id:
            try:
                if 'reference' in payload:
                    sha=(payload['reference'].get('asset') or {}).get('sha256') if isinstance(payload['reference'],dict) else None
                    payload['reference']=AUTH.reference(self.user_id,sha)
                source=payload.get('source')
                if isinstance(source,dict) and source.get('reference'):
                    sha=(source['reference'].get('asset') or {}).get('sha256') if isinstance(source['reference'],dict) else None
                    source['reference']=AUTH.reference(self.user_id,sha)
            except _auth_module.LoginError as error:return self.reply(403,{'error':str(error)})
        if self.path in ('/replica/check','/replica/jobs','/replica/status'):
            # Bring-your-own-key replica: the key in this payload is used for this request only.
            if not AUTH or not self.user_id:return self.reply(401,{'error':'请登录后继续'})
            try:
                if self.path=='/replica/check':return self.reply(200,REPLICA.check(payload))
                if self.path=='/replica/status':return self.reply(200,REPLICA.status(self.user_id,payload.get('id'),payload))
                _reference_asset(payload.get('reference') or {})
                job=REPLICA.create(self.user_id,payload.get('reference'),payload);AUTH.claim(self.user_id,'replica:'+job['id'])
                return self.reply(200,job)
            except _replica_module.ReplicaError as error:return self.reply(422,{'error':str(error),'code':error.code})
            except ValueError as error:return self.reply(422,{'error':str(error)})
            except Exception:
                print(json.dumps({'event':'replica.failed','path':self.path}),file=sys.stderr,flush=True)
                return self.reply(503,{'error':'1:1 复刻暂不可用，请稍后重试'})
        if self.path in ('/reference/deep-watch','/reference/chat','/reference/brief'):
            if not AUTH or not self.user_id:return self.reply(401,{'error':'请登录后继续'})
            try:
                reference=payload.get('reference') or {};sha,path,asset=_reference_asset(reference)
                card=(reference.get('analysis') or {}).get('understanding') or {}
                if self.path.endswith('deep-watch'):
                    card=deep_reference(self.user_id,reference);reference={**reference,'analysis':{**reference.get('analysis',{}),'understanding':card}}
                    return self.reply(200,{'reference':reference})
                if self.path.endswith('chat'):
                    return self.reply(200,WATCH_FLOW.chat(self.user_id,sha,card,payload.get('message',''),payload.get('requestId'),PROFILES.text(self.user_id)))
                return self.reply(200,WATCH_FLOW.confirm(self.user_id,sha,payload.get('brief')))
            except ValueError as error:return self.reply(422,{'error':str(error)})
            except Exception:return self.reply(503,{'error':'观看对话暂不可用，本地结果已保留'})
        if self.path in ('/jobs','/works/text','/works/image'):
            source=payload.get('source') or {};reference=source.get('reference') or {};analysis=reference.get('analysis') or {}
            if str(analysis.get('analyzerVersion') or '').startswith('content-watch-'):
                output={'/jobs':'video','/works/text':'text','/works/image':'image'}[self.path]
                try:
                    brief=WATCH_FLOW.confirmed(self.user_id,(reference.get('asset') or {}).get('sha256'),payload.get('briefId'),output)
                    payload.update(goal=brief['goal'],creativeIntent=brief['notes'],mustInclude='；'.join(brief['keep']),avoid='；'.join(brief['change']))
                except ValueError as error:return self.reply(422,{'error':str(error)})
        if self.path == '/works/image':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录并绑定手机号'})
            try:
                boundaries=_boundary_module.validate(payload.get('contentBoundaries'))
                result=IMAGE_WORKS.create(self.user_id,payload,_boundary_module.instruction(boundaries))
                AUTH.claim(self.user_id,'image:'+result['id'])
                return self.reply(200,result)
            except ValueError as error:return self.reply(400,{'error':str(error)})
            except _image_module.Busy as error:return self.reply(429,{'error':str(error)})
            except _image_module.Unavailable as error:return self.reply(503,{'error':str(error)})
        if self.path == '/works/text':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录并绑定手机号'})
            try:
                boundaries=_boundary_module.validate(payload.get('contentBoundaries'))
                return self.reply(200,TEXT_WORKS.create(self.user_id,payload,_boundary_module.instruction(boundaries)))
            except ValueError as error:return self.reply(400,{'error':str(error)})
            except _text_module.Busy as error:return self.reply(429,{'error':str(error)})
            except _text_module.Unavailable as error:return self.reply(503,{'error':str(error)})
        if self.path == '/references/read':
            try:
                return self.reply(200, read_reference(payload.get('url', '')))
            except ValueError as error:
                return self.reply(422, {'status':'failed', 'error':str(error)})
            except Exception:
                return self.reply(502, {'status':'failed', 'error':'暂时无法连接抖音视频，请稍后重试'})
        if self.path == '/references/acquire':
            try:
                result=acquire_reference(payload.get('url',''),parser_config=payload.get('parser'))
                if result.get('status')=='acquired':
                    ledger_user(self.user_id);peeked=ledger_safe(WATCH_FLOW.peek_cached,(result.get('source') or {}).get('contentId'))
                    ledger_safe(LEDGER.source,self.user_id or '',result,peeked)
                return self.reply(200 if result.get('status')=='acquired' else 409,result)
            except ReferenceAcquireError as error:
                return self.reply(422,{'status':'failed','needsUpload':True,'error':str(error),'errorCode':error.code,'recoveryAction':error.action})
            except ValueError as error:
                return self.reply(422,{'status':'failed','needsUpload':True,'error':str(error)})
            except Exception as error:
                print(json.dumps({'event':'reference.acquire.failed','errorType':type(error).__name__,'message':str(error)[:160]},ensure_ascii=False),file=sys.stderr,flush=True)
                return self.reply(502,{'status':'failed','needsUpload':True,'error':'参考视频获取失败，请上传原视频'})
        if self.path == '/references/peek':
            try:return self.reply(200,peek_reference(payload.get('url',''),self.user_id or '',parser_config=payload.get('parser')))
            except Exception:return self.reply(200,{'status':'unavailable','overview':'','type':'','tags':[],'confidence':0})
        if self.path == '/references/config/check':
            try:return self.reply(200,check_parser(payload.get('parser')))
            except ValueError as error:return self.reply(422,{'status':'failed','error':str(error)})
            except Exception:return self.reply(502,{'status':'failed','error':'解析服务连接失败，请检查地址、凭据或服务状态'})
        if self.path == '/references/glance':
            try:
                sha,path,asset=_reference_asset(payload.get('reference') or {})
                return self.reply(200,WATCH_FLOW.glance(self.user_id or '',sha,path,asset.get('media') or {}))
            except ValueError as error:return self.reply(422,{'error':str(error)})
            except Exception:return self.reply(200,{'status':'unavailable','overview':'','type':'','tags':[],'confidence':0})
        if self.path == '/references/analyze':
            try:_reference_asset(payload.get('reference'))
            except ValueError as error:return self.reply(422,{'status':'failed','error':str(error)})
            sampling=str(payload.get('sampling') or 'smart').strip().lower()
            if sampling not in FRAME_SAMPLING:return self.reply(422,{'status':'failed','error':'代表帧采样档位无效'})
            job_id=uuid.uuid4().hex;ANALYSIS_JOBS[job_id]={'status':'running','phase':'queued','message':'内容分析任务已创建','startedAt':time.time()}
            if AUTH and self.user_id:AUTH.claim(self.user_id,'analysis:'+job_id)
            persist_analysis(job_id)
            threading.Thread(target=analysis_worker,args=(job_id,payload['reference'],sampling,self.user_id or ''),daemon=True).start()
            return self.reply(200,{'id':job_id})
        if self.path == '/tools/run':
            try:return self.reply(200,run_creation_tool(str(payload.get('tool') or ''),payload.get('url',''),payload.get('parser'),cache_scope=self.user_id or ''))
            except ReferenceAcquireError as error:return self.reply(422,{'status':'failed','error':str(error),'errorCode':error.code,'recoveryAction':error.action})
            except ValueError as error:return self.reply(422,{'status':'failed','error':str(error)})
            except Exception as error:
                print(json.dumps({'event':'creation-tool.failed','tool':str(payload.get('tool'))[:20],'errorType':type(error).__name__,'message':str(error)[:160]},ensure_ascii=False),file=sys.stderr,flush=True)
                return self.reply(502,{'status':'failed','error':'工具处理失败，请稍后重试'})
        try:
            data = validate(payload)
        except ValueError as error:
            return self.reply(400, {'error':str(error)})
        except (TypeError,AttributeError):
            return self.reply(400, {'error':'请检查点子、风格和 2–30 秒时长'})
        if not LOCK.acquire(blocking=False):
            return self.reply(429, {'error':'正在合成另一个视频，请稍后重试'})
        job_id = uuid.uuid4().hex
        if AUTH and self.user_id:
            try:AUTH.claim(self.user_id,'run:'+job_id);data['_userId']=self.user_id
            except Exception:
                LOCK.release();return self.reply(503,{'error':'任务归属暂时无法保存，请重试'})
        JOBS[job_id] = {'status':'rendering', 'phase':'starting', 'message':'正在创建视频任务', 'startedAt':time.time()}
        threading.Thread(target=worker, args=(job_id, data), daemon=True).start()
        self.reply(200, {'id':job_id})

    def mcp_file(self):
        match=re.fullmatch(r'/mcp/files/([a-f0-9]{64})\.mp4',urlparse(self.path).path);query=parse_qs(urlparse(self.path).query)
        file=REFERENCE_ROOT/(match[1]+'.mp4') if match else None
        if not file or not file.is_file() or not MCP_GATEWAY.file_allowed(match[1],(query.get('e') or [''])[0],(query.get('s') or [''])[0]):
            return self.reply(403,{'error':'下载链接无效或已过期，请重新调用 download_video'})
        return self.send_file(file,'video/mp4',True)
    def do_GET(self):
        if urlparse(self.path).path=='/mcp':return self.mcp()
        if urlparse(self.path).path.startswith('/mcp/files/'):return self.mcp_file()
        if ADMIN.handle(self):return
        if not self.guard():return
        if self.path.startswith('/board/'):return self.board_get()
        if self.path=='/ideas':
            status=parse_qs(urlparse(self.original_path).query).get('status',[None])[0]
            return self.reply(200,IDEAS.list(self.user_id,status))
        idea_media=re.fullmatch(r'/idea-media/([a-f0-9]{32})\.jpg',self.path)
        if idea_media:
            file=IDEAS.media_path(idea_media[1])
            return self.send_file(file,'image/jpeg') if file else self.reply(404,{'error':'图片不存在'})
        board_media=re.fullmatch(r'/board-media/([a-f0-9]{32})\.mp4',self.path)
        if board_media:
            file=BOARD.media(board_media[1])
            return self.send_video(file) if file else self.reply(404,{'error':'视频不存在'})
        if self.path=='/replica/jobs':return self.reply(200,{'jobs':[REPLICA.public(j) for j in REPLICA.jobs(self.user_id)[:20]]})
        replica_match=re.fullmatch(r'/replica-media/([a-f0-9]{32})\.mp4',self.path)
        if replica_match:
            file=REPLICA.media(replica_match[1])
            return self.send_video(file) if file else self.reply(404,{'error':'视频不存在'})
        if self.path=='/analysis-preferences':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'微信账号同步暂不可用'})
            try:return self.reply(200,ANALYSIS_PREFERENCES.read(self.user_id))
            except Exception:return self.reply(503,{'error':'模板云同步暂不可用'})
        if self.path=='/client-config':return self.reply(200,_config_module.client_config())
        if self.path=='/hotspots':return self.reply(200,_hotspot_module.snapshot())
        if self.path=='/hotspots/search':
            try:
                term=parse_qs(urlparse(self.original_path).query).get('q',[''])[0]
                return self.reply(200,HOTSPOT_SEARCH.query(term,_hotspot_module.snapshot(),_content_module.fetch))
            except (ValueError,TypeError):return self.reply(400,{'error':'请输入1–40字关键词'})
            except Exception:return self.reply(503,{'error':'搜索暂不可用，请稍后重试'})
        if self.path=='/hotspot-watch':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录微信账号'})
            try:
                term=parse_qs(urlparse(self.original_path).query).get('q',[''])[0]
                if term:term=_watch_module.keyword(term)
                return self.reply(200,HOTSPOT_WATCH.view(self.user_id,term))
            except ValueError:return self.reply(400,{'error':'关注关键词无效'})
            except Exception:return self.reply(503,{'error':'关注记录暂不可用'})
        content_match=re.fullmatch(r'/hotspot-content/((?:douyin|weibo|toutiao|kuaishou)-[a-f0-9]{20})',self.path)
        if content_match:return self.reply(200,_content_module.content(content_match[1],_hotspot_module.snapshot()['rows'],retry=urlparse(self.original_path).query=='retry=1'))
        if self.path=='/profile':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录微信账号'})
            return self.reply(200,PROFILES.view(self.user_id))
        if self.path=='/auth/me':
            header=self.headers.get('Authorization','')
            user=AUTH.user(header[7:]) if AUTH and header.startswith('Bearer ') else None
            return self.reply(200,AUTH.profile(user)) if user else self.reply(401,{'error':'请重新登录'})
        archive_status=re.fullmatch(r'/asset-runs/([a-f0-9]{32})/archive',self.path)
        if archive_status:return self.reply(200,ARCHIVE.status(archive_status[1]))
        if self.path=='/creative-assets':
            if not AUTH or not self.user_id:return self.reply(503,{'error':'请先登录'})
            videos=[]
            with AUTH.db() as db:owned=db.execute("SELECT resource FROM resources WHERE user_id=? AND resource LIKE 'run:%' ORDER BY rowid DESC LIMIT 100",(self.user_id,)).fetchall()
            for (resource,) in owned:
                ident=resource[4:]
                if not re.fullmatch('[a-f0-9]{32}',ident):continue
                try:
                    folder=ASSET_ROOT/'runs'/ident;manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'));request=json.loads((folder/'request.json').read_text(encoding='utf-8'))
                    videos.append({'id':ident,'title':str(request.get('idea') or request.get('title') or '我的视频作品')[:80],'time':float(manifest['createdAt'])*1000,'url':f'/assets/{ident}/final.mp4','assetUrl':f'/asset-runs/{ident}','sourceType':(request.get('source') or {}).get('type','idea')})
                except (OSError,ValueError,TypeError,KeyError):continue
            with TOPIC_CHAT.db() as db:turns=db.execute('SELECT request_id,message,response,created FROM turns WHERE user_id=? ORDER BY created DESC LIMIT 100',(self.user_id,)).fetchall()
            chats=[]
            for ident,message,response,created in turns:
                try:
                    value=json.loads(response);reply=value.get('reply','');reply+=''.join('\n\n'+str(t.get('title',''))+'\n'+str(t.get('angle','')) for t in value.get('topics',[]) if isinstance(t,dict))
                except (ValueError,AttributeError):continue
                chats.append({'id':ident,'title':message[:40] or 'AI主动选题推荐','text':('我：'+message+'\n' if message else '')+'ta：'+reply,'time':created*1000})
            try:breakdowns=BOARD.history(self.user_id)
            except Exception:breakdowns=[]
            try:replicas=[REPLICA.public(j) for j in REPLICA.jobs(self.user_id)[:20]]
            except Exception:replicas=[]
            return self.reply(200,{'videos':videos,'texts':TEXT_WORKS.list(self.user_id),'images':IMAGE_WORKS.list(self.user_id),'chats':chats,'breakdowns':breakdowns,'replicas':replicas})
        image_work=re.fullmatch(r'/works/image/([a-f0-9]{32})',self.path)
        image_asset=re.fullmatch(r'/image-assets/([a-f0-9]{32})\.png',self.path)
        if self.path=='/works/image':return self.reply(200,{'rows':IMAGE_WORKS.list(self.user_id)})
        if image_work:
            result=IMAGE_WORKS.poll(self.user_id,image_work[1])
            return self.reply(200,result) if result else self.reply(404,{'error':'图片作品不存在'})
        if image_asset:
            result=IMAGE_WORKS.get(self.user_id,image_asset[1]);file=IMAGE_WORKS.root/(image_asset[1]+'.png')
            return self.send_file(file,'image/png') if result and result['status']=='done' and file.exists() else self.reply(404,{'error':'图片作品不存在'})
        text_work=re.fullmatch(r'/works/text/([a-f0-9]{32})',self.path)
        if self.path=='/works/text':return self.reply(200,{'rows':TEXT_WORKS.list(self.user_id)})
        if text_work:
            result=TEXT_WORKS.get(self.user_id,text_work[1])
            return self.reply(200,result) if result else self.reply(404,{'error':'文字作品不存在'})
        if self.path == '/health':
            return self.reply(200, {'status':'ok', 'engines':['qianwen-video','local-text-renderer']})
        if re.fullmatch(r'/jobs/[a-f0-9]{32}', self.path):
            job = job_status(self.path.rsplit('/',1)[1])
            return self.reply(200 if job else 404, job or {'error':'任务不存在'})
        if re.fullmatch(r'/reference-analyses/[a-f0-9]{32}',self.path):
            job=analysis_status(self.path.rsplit('/',1)[1])
            return self.reply(200 if job else 404,job or {'error':'分析任务不存在'})
        if self.path=='/reference-relay/status':
            return self.reply(200,reference_relay_status())
        tool_match=re.fullmatch(r'/tool-assets/([a-f0-9]{64})/(source\.mp4|audio\.mp3|cover\.jpg)',urlparse(self.path).path)
        if tool_match:
            file,mime=creation_tool_asset(tool_match[1],tool_match[2])
            return self.send_file(file,mime,tool_match[2].endswith(('.mp4','.mp3'))) if file else self.reply(404,{'error':'工具资产不存在'})
        if urlparse(self.path).path.startswith('/reference-assets/'):
            if AUTH and self.user_id:
                match=re.fullmatch(r'/reference-assets/([a-f0-9]{64})\.mp4',self.path)
                file=REFERENCE_ROOT/f'{match[1]}.mp4' if match else None
                if file and not file.is_file():file=None
            else:file=verified_reference_video(getattr(self,'original_path',self.path))
            return self.send_file(file,'video/mp4',True) if file else self.reply(403,{'error':'参考素材地址无效或已过期'})
        asset_match=re.fullmatch(r'/asset-runs/([a-f0-9]{32})',self.path)
        if asset_match:
            manifest=ASSET_ROOT/'runs'/asset_match[1]/'manifest.json'
            return self.reply(200,public_asset_manifest(asset_match[1],json.loads(manifest.read_text(encoding='utf-8')))) if manifest.exists() else self.reply(404,{'error':'资产包不存在'})
        source_match=re.fullmatch(r'/asset-runs/([a-f0-9]{32})/source\.mp4',self.path)
        if source_match:
            file=asset_preview_file(source_match[1],'source')
            return self.send_file(file,'video/mp4',True) if file else self.reply(404,{'error':'参考原片不存在'})
        frame_match=re.fullmatch(r'/asset-runs/([a-f0-9]{32})/keyframes/(\d+)\.jpg',self.path)
        if frame_match:
            file=asset_preview_file(frame_match[1],'keyframe',int(frame_match[2]))
            return self.send_file(file,'image/jpeg') if file else self.reply(404,{'error':'代表帧不存在'})
        durable_match=re.fullmatch(r'/assets/([a-f0-9]{32})/final\.mp4',self.path)
        if durable_match:
            file=ASSET_ROOT/'runs'/durable_match[1]/'final.mp4'
            if not file.exists():return self.reply(404,{'error':'视频不存在'})
            return self.send_video(file)
        match = re.fullmatch(r'/media/([a-f0-9]{32})\.mp4', self.path)
        if not match:
            return self.reply(404, {'error':'Not found'})
        file = ROOT / match[1] / 'video.mp4'
        if not file.exists():
            return self.reply(404, {'error':'视频不存在'})
        return self.send_video(file)

    def send_video(self,file):
        return self.send_file(file,'video/mp4',True)

    def send_file(self,file,content_type,range_support=False):
        size = file.stat().st_size
        start, end = 0, size-1
        requested = self.headers.get('Range') if range_support else None
        if requested:
            m = re.fullmatch(r'bytes=(\d+)-(\d*)', requested)
            if not m:
                return self.reply(416, {'error':'Unsupported range'})
            start, end = int(m[1]), min(int(m[2]) if m[2] else end, end)
            if start > end:
                return self.reply(416, {'error':'Invalid range'})
        self.send_response(206 if requested else 200)
        self.send_header('Content-Type',content_type)
        if range_support:self.send_header('Accept-Ranges','bytes')
        self.send_header('Content-Length',str(end-start+1))
        if requested:
            self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        with file.open('rb') as source:
            source.seek(start)
            self.wfile.write(source.read(end-start+1))

if __name__ == '__main__':
    IMAGE_WORKS.start()
    ARCHIVE.start();LEDGER.start()
    _hotspot_module.start()
    HOTSPOT_WATCH.start(_hotspot_module.snapshot)
    host=os.environ.get('YOUAI_VIDEO_HOST','127.0.0.1');port=int(os.environ.get('YOUAI_VIDEO_PORT','8765'))
    print(f'YOUAI video service: http://{host}:{port}', flush=True)
    threading.Thread(target=_board_ticker,daemon=True).start()
    threading.Thread(target=BOARD.backfill_methods,daemon=True).start()  # 方法卡复用：历史拆解一次性回填
    ThreadingHTTPServer((host,port),Handler).serve_forever()
