"""Versioned inspiration AI routing and redacted per-scene observations."""
import hashlib,json,os,re,secrets,sqlite3,threading,time,socket
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
SCENES={'ta_opening':'TA主动推荐','ta_chat':'与TA继续对话','hotspot_summary':'热点总结','text_works':'文字作品生成','reference_understanding':'旧版参考理解（仅兼容）','video_watch':'视频观看理解','video_glance':'视频快看（大致内容）','board_breakdown':'按方案拆解','board_plan':'拆解方案生成/归纳','board_interview':'分层问询与对话','board_output':'文字作品与创作包','data_screenshot':'后台截图识别数据','video_watch_deep':'深度观看','video_chat':'拆解对话','idea_note':'灵感碎片轻反馈'}
DEFAULTS={'hotspot_summary':(35,900),'text_works':(40,1800),'reference_understanding':(40,3500),'video_watch':(60,4000),'video_glance':(20,200),'board_breakdown':(40,3500),'board_plan':(40,1800),'board_interview':(30,600),'board_output':(40,3500),'data_screenshot':(30,400),'video_watch_deep':(90,1500),'video_chat':(40,600),'idea_note':(20,200)}
ERRORS={'disabled':'该AI功能已暂停','not_configured':'模型连接或凭据尚未配置','auth':'模型凭据无效或无权限','quota':'模型限流或额度不足','model':'模型不存在或未开通','timeout':'模型请求超时','network':'模型网络连接失败','request':'模型或请求参数不受支持','content_filter':'内容未通过模型服务审核，请调整表达后重试','upstream':'模型接口暂不可用','invalid_response':'模型返回格式不符合要求','config':'AI配置无效，请联系管理员'}
class AIError(RuntimeError):
 def __init__(self,code):self.code=code;super().__init__(ERRORS[code])
class Conflict(Exception):pass
class Gateway:
 Error=AIError
 def __init__(self,root,resolver=None):
  self.usage_ledger=None;self.resolver=resolver;self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.lock=threading.RLock()
  with self.db() as db:db.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,at REAL,scene TEXT,kind TEXT,ok INTEGER,code TEXT,http_status INTEGER,latency_ms INTEGER,revision TEXT,model TEXT,tokens INTEGER)')
 @contextmanager
 def db(self):
  db=sqlite3.connect(self.root/'calls.sqlite',timeout=10)
  try:
   with db:yield db
  finally:db.close()
 def legacy_profile(self):
  try:value=json.loads(Path(os.environ.get('YOUAI_HOTSPOT_AI_CONFIG','/credentials/hotspot-ai.json')).read_text(encoding='utf-8-sig'))
  except (OSError,ValueError):value={}
  return {'url':os.environ.get('YOUAI_HOTSPOT_AI_URL') or value.get('url',''),'key':os.environ.get('YOUAI_HOTSPOT_AI_KEY') or value.get('key',''),'model':os.environ.get('YOUAI_HOTSPOT_AI_MODEL') or value.get('model','qwen3.8-max')}
 def key_source(self):
  return '环境变量' if os.environ.get('YOUAI_HOTSPOT_AI_KEY') else '凭据文件'
 def profile(self,connection='qwen-domestic'):
  if self.resolver:
   value=self.resolver.resolve(connection)
   if value is None:raise AIError('not_configured')
   return value
  if connection!='qwen-domestic':raise AIError('not_configured')
  return self.legacy_profile()
 def connection_ids(self):
  return self.resolver.chat_connections() if self.resolver else ['qwen-domestic']
 def default_scene(self,k):
  timeout,tokens=DEFAULTS.get(k,(40,1600))
  return {'enabled':True,'connection':'qwen-domestic','model':'qwen3-vl-plus' if k=='reference_understanding' else 'qwen3.8-omni-flash' if k=='video_watch_deep' else 'qwen3.8-flash' if k in ('video_watch','video_chat','video_glance') or k.startswith('board_') or k in ('data_screenshot','idea_note') else self.legacy_profile()['model'],'timeoutSeconds':timeout,'maxTokens':tokens,'instruction':''}
 def merged(self,scenes):
  # Configurations saved before a scene existed keep working: missing scenes use defaults.
  return {k:(scenes[k] if isinstance(scenes,dict) and k in scenes else self.default_scene(k)) for k in SCENES}
 def config(self):
  with self.lock:
   try:
    value=json.loads((self.root/'config.json').read_text(encoding='utf-8'));value['scenes']=self.merged(value.get('scenes'));return value
   except FileNotFoundError:
    scenes={k:self.default_scene(k) for k in SCENES}
    return {'revision':hashlib.sha256(json.dumps(scenes,sort_keys=True).encode()).hexdigest()[:32],'scenes':scenes,'publishedAt':None}
   except (OSError,ValueError):raise AIError('config') from None
 def scene(self,ident):
  if ident not in SCENES:raise AIError('config')
  config=self.config();value=dict(config['scenes'][ident],revision=config['revision'])
  if not value['enabled']:raise AIError('disabled')
  return value
 def write(self,path,value):
  path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_name(path.name+'.'+secrets.token_hex(8)+'.tmp')
  try:
   with temp.open('x',encoding='utf-8') as f:os.chmod(temp,0o600);json.dump(value,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
   temp.replace(path)
  finally:temp.unlink(missing_ok=True)
 def publish(self,payload):
  if not isinstance(payload,dict) or set(payload) not in ({'expectedRevision','scenes'},{'expectedRevision','rollback'}):raise ValueError('AI配置请求无效')
  with self.lock:
   old=self.config()
   if payload['expectedRevision']!=old['revision']:raise Conflict()
   if 'rollback' in payload:
    ident=payload['rollback']
    if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('版本不存在')
    try:scenes=self.merged(json.loads((self.root/'versions'/f'{ident}.json').read_text())['scenes'])
    except (OSError,ValueError):raise ValueError('版本不存在') from None
   else:scenes=payload['scenes']
   if not isinstance(scenes,dict) or set(scenes)!=set(SCENES):raise ValueError('必须配置全部AI调用场景')
   allowed=set(self.connection_ids())
   for scene_id,v in scenes.items():
    if not isinstance(v,dict) or set(v)!={'enabled','connection','model','timeoutSeconds','maxTokens','instruction'}:raise ValueError('AI配置字段无效')
    if type(v['enabled']) is not bool or v['connection'] not in allowed or not isinstance(v['model'],str) or not re.fullmatch('[A-Za-z0-9._:-]{1,80}',v['model']):raise ValueError('连接或模型无效')
    if type(v['timeoutSeconds']) is not int or not 5<=v['timeoutSeconds']<=(120 if scene_id in ('video_watch','video_watch_deep') else 40) or type(v['maxTokens']) is not int or not 32<=v['maxTokens']<=4096:raise ValueError('超时为5–120秒，输出上限为32–4096 Token')
    if not isinstance(v['instruction'],str) or len(v['instruction'])>1000:raise ValueError('补充提示词最多1000字')
   new={'revision':secrets.token_hex(16),'scenes':scenes,'publishedAt':int(time.time())}
   self.write(self.root/'versions'/f"{old['revision']}.json",old);self.write(self.root/'versions'/f"{new['revision']}.json",new);self.write(self.root/'config.json',new)
   for path in sorted((self.root/'versions').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[50:]:path.unlink()
   return self.dashboard()
 def record(self,scene,kind,ok,code,status,elapsed,cfg,tokens=0):
  with self.db() as db:
   db.execute('INSERT INTO events(at,scene,kind,ok,code,http_status,latency_ms,revision,model,tokens) VALUES(?,?,?,?,?,?,?,?,?,?)',(time.time(),scene,kind,int(ok),code,status,int(elapsed*1000),cfg.get('revision',''),cfg.get('model',''),tokens))
   db.execute('DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 1000)')
 def input_bound(self,messages):
  total=0
  for message in messages:
   value=message.get('content','')
   if isinstance(value,str):total+=len(value.encode())
   elif isinstance(value,list):
    for part in value:
     if part.get('type')=='text':total+=len(str(part.get('text','')).encode())
     elif part.get('type')=='image_url':total+=2048
     elif part.get('type')=='video_url':total+=self.usage_ledger.settings()['maxAnalyzeSeconds']*1024
  return max(100,total)
 def complete(self,ident,messages,opener=urlopen,json_mode=False,probe=False,user_id='',asset=''):
  reservation=None;began=time.monotonic();cfg={};status=None;kind='probe' if probe else 'business'
  try:
   cfg=self.scene(ident);profile=self.profile(cfg.get('connection','qwen-domestic'));url=urlsplit(profile['url'])
   if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or not profile['key']:raise AIError('not_configured')
   messages=[dict(m) for m in messages]
   if cfg['instruction'] and not probe:messages.append({'role':'system','content':'管理员补充风格要求（不改变事实核验、账号权限与输出JSON约束）：'+cfg['instruction']})
   payload={'model':cfg['model'],'messages':messages,'max_tokens':32 if probe else cfg['maxTokens']}
   if cfg['model'].startswith(('qwen3.8-','qwen3-vl-')):payload['enable_thinking']=False
   if ident=='video_watch_deep':payload['modalities']=['text']
   if json_mode:payload['response_format']={'type':'json_object'}
   if self.usage_ledger:
    reservation=self.usage_ledger.reserve(user_id,asset,ident,cfg['model'],self.input_bound(messages),32 if probe else cfg['maxTokens'])
   request=Request(profile['url'],data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+profile['key'],'Content-Type':'application/json'},method='POST')
   try:
    with opener(request,timeout=cfg['timeoutSeconds']) as response:raw=response.read(65537)
    status=200
   except HTTPError as e:
    status=e.code
    if e.code==400:
     try:filtered=json.loads(e.read(4096)).get('error',{}).get('code')=='data_inspection_failed'
     except Exception:filtered=False
     if filtered:raise AIError('content_filter') from None
    raise AIError('auth' if e.code in (401,403) else 'quota' if e.code==429 else 'model' if e.code==404 else 'request' if e.code==400 else 'upstream') from None
   except (TimeoutError,socket.timeout):raise AIError('timeout') from None
   except URLError as e:raise AIError('timeout' if isinstance(e.reason,(TimeoutError,socket.timeout)) else 'network') from None
   except Exception:raise AIError('network') from None
   try:
    if len(raw)>65536:raise ValueError()
    value=json.loads(raw);content=value['choices'][0]['message']['content']
    if not isinstance(content,str) or not content.strip():raise ValueError()
    if json_mode:
     structured=json.loads(content)
     if not isinstance(structured,dict) or not isinstance(structured.get('reply'),str) or not structured['reply'].strip() or not isinstance(structured.get('topics'),list) or not 1<=len(structured['topics'])<=3:raise ValueError()
     for topic in structured['topics']:
      if not isinstance(topic,dict) or not all(isinstance(topic.get(k),str) and topic[k].strip() for k in ('title','angle')):raise ValueError()
    usage=value.get('usage') or {};tokens=usage.get('total_tokens',0)
    if type(tokens) is not int:tokens=0
   except Exception:raise AIError('invalid_response') from None
   if self.usage_ledger and reservation:self.usage_ledger.settle(reservation,value.get('usage') or {})
   self.record(ident,kind,True,'',status,time.monotonic()-began,cfg,tokens);return value
  except AIError as e:
   if self.usage_ledger and reservation:self.usage_ledger.settle(reservation,{},e.code)
   self.record(ident,kind,False,e.code,status,time.monotonic()-began,cfg);raise
 def probe_connection(self,connection,opener=urlopen):
  if connection not in self.connection_ids():raise ValueError('连接不存在')
  began=time.monotonic();status=None;profile=self.profile(connection);cfg={'revision':'connection','model':profile.get('model','')}
  try:
   url=urlsplit(profile.get('url',''))
   if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or not profile.get('key'):raise AIError('not_configured')
   payload={'model':profile['model'],'messages':[{'role':'user','content':'只回复：OK'}],'max_tokens':32}
   if profile['model'].startswith('qwen3.8-'):payload['enable_thinking']=False
   request=Request(profile['url'],data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+profile['key'],'Content-Type':'application/json'},method='POST')
   try:
    with opener(request,timeout=20) as response:response.read(65537)
    status=200
   except HTTPError as e:
    status=e.code
    if e.code==400:
     try:filtered=json.loads(e.read(4096)).get('error',{}).get('code')=='data_inspection_failed'
     except Exception:filtered=False
     if filtered:raise AIError('content_filter') from None
    raise AIError('auth' if e.code in (401,403) else 'quota' if e.code==429 else 'model' if e.code==404 else 'request' if e.code==400 else 'upstream') from None
   except (TimeoutError,socket.timeout):raise AIError('timeout') from None
   except URLError as e:raise AIError('timeout' if isinstance(e.reason,(TimeoutError,socket.timeout)) else 'network') from None
   except Exception:raise AIError('network') from None
   self.record('connection:'+connection,'probe',True,'',status,time.monotonic()-began,cfg);return {'ok':True,'message':'连接检测成功','latencyMs':int((time.monotonic()-began)*1000)}
  except AIError as e:
   self.record('connection:'+connection,'probe',False,e.code,status,time.monotonic()-began,cfg);return {'ok':False,'message':str(e),'code':e.code,'httpStatus':status}
 def probe(self,ident,opener=urlopen):
  self.complete(ident,[{'role':'user','content':'只回复：OK'}],probe=True,opener=opener)
  return self.dashboard()
 def connection_rows(self,parsed,profile):
  rows=[{'id':'qwen-domestic','name':'现有国内千问连接','endpoint':('https://'+parsed.hostname+parsed.path) if parsed.scheme=='https' and parsed.hostname else '未配置','credentialConfigured':bool(profile['key'] or (self.resolver and self.resolver.secret('qwen-domestic')))}]
  if self.resolver:
   for row in self.resolver.config()['connections']:rows.append({'id':row['id'],'name':row['name'],'endpoint':row['endpoint'],'credentialConfigured':bool(self.resolver.secret(row['id']))})
  return rows
 def scenes_using(self):
  return sorted({v['connection'] for v in self.config()['scenes'].values()})
 def dashboard(self):
  config=self.config();profile=self.legacy_profile();parsed=urlsplit(profile['url']);rows=[]
  with self.db() as db:
   for key,name in SCENES.items():
    latest={}
    for kind in ('business','probe'):
     row=db.execute('SELECT at,ok,code,http_status,latency_ms,revision,model,tokens FROM events WHERE scene=? AND kind=? ORDER BY id DESC LIMIT 1',(key,kind)).fetchone()
     latest[kind]=dict(zip(('at','ok','code','httpStatus','latencyMs','revision','model','tokens'),row)) if row else None
     if latest[kind]:latest[kind]['message']='接口调用成功' if row[1] else ERRORS.get(row[2],'调用失败')
    counts=db.execute('SELECT count(*),sum(CASE WHEN ok=0 THEN 1 ELSE 0 END) FROM events WHERE scene=? AND kind=?',(key,'business')).fetchone()
    rows.append({'id':key,'name':name,'config':config['scenes'][key],'lastBusiness':latest['business'],'lastProbe':latest['probe'],'calls':counts[0],'failures':counts[1] or 0})
   recent=[]
   for row in db.execute('SELECT at,scene,kind,ok,code,http_status,latency_ms,revision,model,tokens FROM events ORDER BY id DESC LIMIT 30'):
    event=dict(zip(('at','scene','kind','ok','code','httpStatus','latencyMs','revision','model','tokens'),row));event['message']='接口调用成功' if event['ok'] else ERRORS.get(event['code'],'调用失败');recent.append(event)
  versions=[]
  for path in (self.root/'versions').glob('*.json'):
   try:v=json.loads(path.read_text());versions.append({'revision':v['revision'],'publishedAt':v.get('publishedAt')})
   except (OSError,ValueError):pass
  return {'recentCalls':recent,'revision':config['revision'],'scenes':config['scenes'],'rows':rows,'connections':self.connection_rows(parsed,profile),'versions':sorted(versions,key=lambda v:v['publishedAt'] or 0,reverse=True)[:20],'notice':'统计最近1000次模型请求；业务调用与手动检测分开。未调用不代表故障，连接检测不代表完整业务成功。'}
