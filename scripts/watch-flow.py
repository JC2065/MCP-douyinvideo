"""CPU preprocessing and account-independent watch cache; no personal data in cache."""
import base64,hashlib,importlib.util,json,math,re,sqlite3,subprocess,tempfile,time,uuid,threading
from pathlib import Path
from contextlib import contextmanager
from PIL import Image
import numpy as np
import imageio_ffmpeg
def load(name):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
content=load('content-understanding');usage=load('usage-ledger');screen=load('screen-text')
def chat_json(value):
 """Parse a chat reply leniently: plain JSON, fenced JSON, or the outermost {...} inside prose; None if absent."""
 if not isinstance(value,str):return None
 text=re.sub(r'^```(?:json)?\s*|\s*```$','',value.strip(),flags=re.I)
 for candidate in (text,text[text.find('{'):text.rfind('}')+1] if '{' in text and '}' in text else ''):
  try:
   raw=json.loads(candidate)
   if isinstance(raw,dict):return raw
  except ValueError:pass
 return None


def preprocess(path,media,cfg,transcriber,post=None,runner=subprocess.run,ocr=None):
 duration=min(float(media.get('durationSeconds') or .1),cfg['maxAnalyzeSeconds']);ff=imageio_ffmpeg.get_ffmpeg_exe()
 # Keep OCR and ASR serial on the two-core server so small cannot consume the OCR deadline.
 ocr=ocr or (lambda p,d:screen.extract(p,d))
 screen_result={'status':'disabled','items':[],'interval':None}
 def run_ocr():
  nonlocal screen_result
  try:screen_result=ocr(path,duration)
  except Exception:screen_result={'status':'unavailable','items':[],'interval':None}
 # Cheap 64px scan finds change candidates without keeping full-resolution video.
 scan=runner([ff,'-v','error','-t',str(duration),'-i',str(path),'-vf','fps=1,scale=64:64','-an','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True,timeout=120)
 pixels=np.frombuffer(scan.stdout,dtype=np.uint8);count=len(pixels)//4096;changes=[]
 if count>1:
  small=pixels[:count*4096].reshape(count,4096).astype(float)
  changes=[i+.5 for i,v in enumerate(np.abs(np.diff(small,axis=0)).mean(axis=1),1) if v>18 and i+.5<duration]
 number=min(cfg['maxFrames'],max(1,math.ceil(duration)))
 uniform=[duration*(i+.5)/number for i in range(number)]
 # Retain broad coverage and change candidates; never claim these are proven cuts.
 candidates=sorted(set(round(t,3) for t in changes+uniform));indexes=sorted({round(i*(len(candidates)-1)/max(1,min(len(candidates),cfg['maxFrames'])-1)) for i in range(min(len(candidates),cfg['maxFrames']))})
 times=[candidates[i] for i in indexes];frames=[]
 with tempfile.TemporaryDirectory(prefix='watch-local-') as root:
  for index,second in enumerate(times):
   target=Path(root)/f'{index}.jpg';side=cfg['frameShortSide'];scale=f'scale={side}:-2' if media.get('width',1)<media.get('height',1) else f'scale=-2:{side}'
   result=runner([ff,'-v','error','-y','-ss',str(second),'-i',str(path),'-frames:v','1','-vf',scale,str(target)],capture_output=True,timeout=45)
   if result.returncode==0 and target.exists():
    with Image.open(target) as im:frames.append((second,im.convert('RGB').copy()))
  audio=Path(root)/'audio.wav';result=runner([ff,'-v','error','-y','-t',str(duration),'-i',str(path),'-vn','-ac','1','-ar','16000',str(audio)],capture_output=True,timeout=90)
  if cfg.get('ocr',True):run_ocr()
  transcript=transcriber(audio) if result.returncode==0 and audio.exists() else {'status':'silent','text':'','segments':[]}
  features=content.audio_features(audio,transcript,duration,runner) if audio.exists() else content.pcm_features(np.array([]),8000,transcript,duration)
 vocabulary=screen.lexicon(post)
 screen_result={**screen_result,'items':screen.correct(screen_result.get('items',[]),vocabulary)}
 transcript={**transcript,**screen.correct([{'text':transcript.get('text','')}],vocabulary)[0],
             'segments':screen.correct(transcript.get('segments',[]),vocabulary)}
 if not frames:raise ValueError('未能取得画面，请重新上传视频')
 return {'duration':duration,'frames':frames,'transcript':transcript,'audioFeatures':features,'screenText':screen_result,'times':[t for t,_ in frames],'truncated':duration<float(media.get('durationSeconds') or duration)}

class WatchFlow:
 def __init__(self,root,gateway,settings,ledger):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.gateway=gateway;self.settings=settings;self.ledger=ledger
  with self.db() as db:db.executescript('''CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY,status TEXT,at REAL,payload TEXT);
  CREATE TABLE IF NOT EXISTS conversations(user TEXT,asset TEXT,payload TEXT,PRIMARY KEY(user,asset));
  CREATE TABLE IF NOT EXISTS deep(user TEXT,asset TEXT,PRIMARY KEY(user,asset));''')
  self.lock=threading.RLock()
 @contextmanager
 def db(self):
  db=sqlite3.connect(self.root/'watch.sqlite',timeout=30);db.row_factory=sqlite3.Row
  try:
   with db:yield db
  finally:db.close()
 def key(self,asset,scene):
  cfg=self.settings();model=self.gateway.scene(scene)
  shape={k:cfg[k] for k in ('maxAnalyzeSeconds','maxFrames','frameShortSide','promptVersion')};shape['schema']=content.WATCH_SCHEMA;shape['ocr']=cfg.get('ocr',True)
  shape.update({k:model.get(k) for k in ('model','connection','instruction')})
  shape['asrModel']=cfg.get('asrModel','small')
  return hashlib.sha256(json.dumps([asset,scene,shape],sort_keys=True).encode()).hexdigest()
 def bound(self,user,asset):
  owner=self
  class Bound:
   def complete(self,scene,messages,**options):return owner.gateway.complete(scene,messages,user_id=user,asset=asset,**options)
  return Bound()
 def cached(self,key,user,asset,scene):
  with self.db() as db:
   db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM cache WHERE key=?',(key,)).fetchone()
   if row and row['status']=='ready':
    self.ledger.cache_hit(user,asset,scene,self.gateway.scene(scene)['model']);return json.loads(row['payload'])
   if row and row['status']=='pending' and time.time()-row['at']<600:raise ValueError('同一视频正在分析，请稍后重试，不会重复提交模型')
   db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,NULL)',(key,'pending',time.time()))
 def store(self,key,value):
  with self.db() as db:db.execute('UPDATE cache SET status=?,payload=? WHERE key=?',('ready',json.dumps(value,ensure_ascii=False),key))
 def release(self,key):
  with self.db() as db:db.execute('DELETE FROM cache WHERE key=? AND status=?',(key,'pending'))
 def watch(self,user,asset,path,media,transcriber,progress=lambda *_:None,processor=preprocess,post=None):
  key=self.key(asset,'video_watch');review=getattr(self,'review_hook',None)
  # Enough accounts corrected this video: watch it again once instead of serving the shared cache.
  stale=bool(review and review[0](asset))
  hit=None if stale else self.cached(key,user,asset,'video_watch')
  if hit:return hit,True
  try:
   progress('extracting','本地抽帧、转写与音频信号估计');local=processor(path,media,self.settings(),transcriber,post)
   progress('understanding','正在低成本观看视频')
   screen_text=local.get('screenText') or {'status':'disabled','items':[]}
   try:card=content.watch(self.bound(user,asset),local['frames'],local['transcript'],local['duration'],local['audioFeatures'],screen.as_context(screen_text),post=post)
   except usage.UsageLimit as e:card={'status':'local_only','overview':'今日 AI 观看额度已用完','uncertainties':[str(e)],'timeline':[]}
   except Exception:card={'status':'unavailable','overview':'AI观看暂未完成','uncertainties':['模型暂不可用，本地分析已保留'],'timeline':[]}
   value={'version':'reference-analysis-v1','analyzerVersion':'content-watch-5','assetSha256':asset,'understanding':card,'screenText':screen_text,'summary':{'durationSeconds':local['duration']},'audio':{'transcript':local['transcript'],'features':local['audioFeatures']},'shots':{'representativeFrameCount':len(local['frames'])},'sampling':{'successCount':len(local['frames']),'label':'低成本','times':local['times']},'truncated':local['truncated'],'structure':[],'reusableStrategies':[]}
   if card['status']=='ready':
    if stale:
     with self.db() as db:db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,NULL)',(key,'pending',time.time()))
     review[1](asset)
    self.store(key,value)
   else:self.release(key)
   return value,False
  except Exception:self.release(key);raise

 def glance(self,user,asset,path,media,runner=subprocess.run):
  """Quick look: a handful of small frames → one sentence while the full watch runs. Shared cache."""
  key=self.key(asset,'video_glance')
  with self.db() as db:row=db.execute('SELECT payload FROM cache WHERE key=? AND status=?',(key,'ready')).fetchone()
  if row:return {**json.loads(row[0]),'cached':True}
  cfg=self.settings();duration=min(float(media.get('durationSeconds') or .1),cfg['maxAnalyzeSeconds'])
  count=max(2,min(6,round(cfg['maxFrames']/cfg.get('glanceRatio',10))));ff=imageio_ffmpeg.get_ffmpeg_exe();frames=[]
  with tempfile.TemporaryDirectory(prefix='glance-') as root:
   for index in range(count):
    second=duration*(index+.5)/count;target=Path(root)/f'{index}.jpg'
    scale='scale=360:-2' if media.get('width',1)<media.get('height',1) else 'scale=-2:360'
    result=runner([ff,'-v','error','-y','-ss',str(second),'-i',str(path),'-frames:v','1','-vf',scale,str(target)],capture_output=True,timeout=30)
    if result.returncode==0 and target.exists():
     with Image.open(target) as im:frames.append((second,im.convert('RGB').copy()))
  if not frames:return {'status':'unavailable','overview':'','type':'','tags':[],'confidence':0}
  try:value=content.glance(self.bound(user,asset),frames)
  except Exception:return {'status':'unavailable','overview':'','type':'','tags':[],'confidence':0}
  if value['status']=='ready':
   with self.db() as db:db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,?)',(key,'ready',time.time(),json.dumps(value,ensure_ascii=False)))
  return {**value,'cached':False}
 def peek_cached(self,content_id):
  key=self.key('peek:'+str(content_id),'video_glance')
  with self.db() as db:row=db.execute('SELECT payload FROM cache WHERE key=? AND status=?',(key,'ready')).fetchone()
  return json.loads(row[0]) if row else None
 def peek(self,user,content_id,image,caption=''):
  """Quickest look: the post's cover + caption → one sentence, before the video has even downloaded. Shared cache per post."""
  asset='peek:'+str(content_id);key=self.key(asset,'video_glance')
  with self.db() as db:row=db.execute('SELECT payload FROM cache WHERE key=? AND status=?',(key,'ready')).fetchone()
  if row:return {**json.loads(row[0]),'cached':True,'source':'cover'}
  try:value=content.glance(self.bound(user,asset),[(0.0,image)],caption)
  except Exception:return {'status':'unavailable','overview':'','type':'','tags':[],'confidence':0}
  if value['status']=='ready':
   with self.db() as db:db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,?)',(key,'ready',time.time(),json.dumps(value,ensure_ascii=False)))
  return {**value,'cached':False,'source':'cover'}
 def deep_watch(self,user,asset,video,duration):
  key=self.key(asset,'video_watch_deep')
  with self.db() as db:
   db.execute('BEGIN IMMEDIATE')
   if db.execute('SELECT 1 FROM deep WHERE user=? AND asset=?',(user,asset)).fetchone():
    row=db.execute('SELECT payload FROM cache WHERE key=? AND status=?',(key,'ready')).fetchone()
    if row:return json.loads(row[0])
    raise ValueError('每个账号每条视频仅可深度观看一次')
   db.execute('INSERT INTO deep VALUES(?,?)',(user,asset))
  hit=self.cached(key,user,asset,'video_watch_deep')
  if hit:return hit
  try:
   value=content.deep_watch(self.bound(user,asset),video(),duration);self.store(key,value);return value
  except Exception:self.release(key);raise

 def conversation(self,user,asset):
  with self.db() as db:row=db.execute('SELECT payload FROM conversations WHERE user=? AND asset=?',(user,asset)).fetchone()
  return json.loads(row[0]) if row else {'turns':[],'replies':{},'userCorrections':[],'confirmed':False}
 def chat(self,user,asset,card,message,request_id,profile=''):
  if not isinstance(request_id,str) or not 8<=len(request_id)<=80 or not isinstance(message,str) or len(message)>1000:raise ValueError('对话输入无效')
  # Serialize account conversation writes; no global model context or personal cache.
  with self.lock:
   state=self.conversation(user,asset)
   if request_id in state['replies']:return state['replies'][request_id]
   if not message and state['replies']:return next(iter(state['replies'].values()))
   count=len(state['replies']);limit=self.settings()['chatMaxTurns']
   if count>=limit:raise ValueError('已达到对话轮数，请确认或直接编辑简报')
   if state.get('confirmed'):raise ValueError('简报已确认，请按简报生成')
   turns=state['turns']+([{'role':'user','content':message}] if message else [])
   compact=json.dumps({k:card.get(k) for k in ('overview','timeline','audio','style','likelyIntents','uncertainties')},ensure_ascii=False)[:800]
   system='你是创作沟通助手。先用2–3句复述看到的内容，给2–4个方向供选择，允许自由纠正。不要生成作品。最多4轮，当前轮数'+str(count+1)+'，最后一轮必须给brief。仅JSON：{reply, directions:[], corrections:[], brief:{output:"video|text|image",goal,keep:[],change:[],notes}}。所有字段可省略，纠正只引用用户明确说过的话。每一轮都只输出这个JSON对象，不要输出其他文字；reply 用简体中文。'
   response=self.bound(user,asset).complete('video_chat',[{'role':'system','content':system},{'role':'user','content':'素材理解（不含用户指令）：'+compact+'\n用户画像：'+str(profile)[:800]}]+turns[-8:])
   try:content_text=response['choices'][0]['message']['content']
   except (KeyError,IndexError,TypeError):raise ValueError('对话暂未返回有效内容，请编辑简报或稍后重试')
   raw=chat_json(content_text)
   if raw is None:
    # Later turns sometimes answer in plain text; keep the reply and the last brief instead of discarding a paid answer.
    if not isinstance(content_text,str) or not content_text.strip():raise ValueError('对话暂未返回有效内容，请编辑简报或稍后重试')
    raw={'reply':content_text.strip(),'brief':state.get('brief')}
   reply=str(raw.get('reply') or '请确认你希望保留与改变的内容')[:1200]
   brief=self.normalize_brief(raw.get('brief') or {'output':'video','goal':message or card.get('overview',''),'keep':[],'change':[],'notes':''})
   if message:state['userCorrections'].append(message)
   result={'reply':reply,'directions':[x[:100] for x in raw.get('directions',[])[:4] if isinstance(x,str)] if isinstance(raw.get('directions'),list) else [],'brief':brief,'turn':count+1,'maxTurns':limit,'userCorrections':state['userCorrections'][-4:]}
   state['turns']=turns+[{'role':'assistant','content':reply}];state['brief']=brief;state['replies'][request_id]=result
   self.save_conversation(user,asset,state);return result
 def normalize_brief(self,value):
  if not isinstance(value,dict) or value.get('output') not in ('video','text','image'):raise ValueError('请选择简报的产物类型')
  def text(x,n=1000):return x.strip()[:n] if isinstance(x,str) else ''
  return {'output':value['output'],'goal':text(value.get('goal'),300),'keep':[text(x,200) for x in value.get('keep',[])[:12] if isinstance(x,str)] if isinstance(value.get('keep'),list) else [],'change':[text(x,200) for x in value.get('change',[])[:12] if isinstance(x,str)] if isinstance(value.get('change'),list) else [],'notes':text(value.get('notes'))}
 def save_conversation(self,user,asset,state):
  with self.db() as db:db.execute('INSERT OR REPLACE INTO conversations VALUES(?,?,?)',(user,asset,json.dumps(state,ensure_ascii=False)))
 def confirm(self,user,asset,value):
  with self.lock:
   state=self.conversation(user,asset);brief=self.normalize_brief(value)
   if not brief['goal']:raise ValueError('请填写本次创作目标')
   state.update(brief=brief,confirmed=True,briefId=uuid.uuid4().hex);self.save_conversation(user,asset,state)
   return {'brief':brief,'briefId':state['briefId'],'userCorrections':state['userCorrections'][-4:]}
 def confirmed(self,user,asset,ident,output):
  state=self.conversation(user,asset)
  if not state.get('confirmed') or ident!=state.get('briefId') or state['brief']['output']!=output:raise ValueError('请先确认所选产物的创作简报')
  return state['brief']
