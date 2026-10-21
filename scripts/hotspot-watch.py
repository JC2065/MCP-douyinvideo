"""Private keyword watch lists and measured per-platform ranks; public source search."""
import json,re,sqlite3,threading,time
from pathlib import Path
from contextlib import contextmanager
PLATFORMS=('微博','抖音','今日头条','快手')
def keyword(value):
 if not isinstance(value,str) or not 1<=len(value.strip())<=40 or any(ord(c)<32 for c in value):raise ValueError('请输入1–40字关键词')
 return value.strip()
class Watches:
 def __init__(self,path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.lock=threading.RLock()
  with self.db() as db:
   db.execute('CREATE TABLE IF NOT EXISTS terms(user_id TEXT,term TEXT,created REAL,PRIMARY KEY(user_id,term))')
   db.execute('CREATE TABLE IF NOT EXISTS observations(user_id TEXT,term TEXT,platform TEXT,at REAL,status TEXT,rank INTEGER,topic_id TEXT,title TEXT,PRIMARY KEY(user_id,term,platform,at))')
 @contextmanager
 def db(self):
  db=sqlite3.connect(self.path,timeout=15)
  try:
   with db:yield db
  finally:db.close()
 def add(self,user,term):
  term=keyword(term)
  with self.lock,self.db() as db:
   count=db.execute('SELECT count(*) FROM terms WHERE user_id=?',(user,)).fetchone()[0]
   exists=db.execute('SELECT 1 FROM terms WHERE user_id=? AND term=?',(user,term)).fetchone()
   if not exists and count>=20:raise ValueError('最多关注20个关键词，请先取消一个')
   db.execute('INSERT INTO terms VALUES(?,?,?) ON CONFLICT(user_id,term) DO UPDATE SET created=excluded.created',(user,term,time.time()))
  return term
 def remove(self,user,term):
  term=keyword(term)
  with self.lock,self.db() as db:
   db.execute('DELETE FROM terms WHERE user_id=? AND term=?',(user,term));db.execute('DELETE FROM observations WHERE user_id=? AND term=?',(user,term))
 def sample(self,feed):
  now=time.time()
  with self.lock,self.db() as db:
   terms=db.execute('SELECT user_id,term FROM terms').fetchall()
   for user,term in terms:
    for platform in PLATFORMS:
     source=next((s for s in feed.get('sources',{}).values() if s.get('platform')==platform),{})
     at=source.get('attemptedAt') or source.get('fetchedAt') or 0
     if not isinstance(at,(int,float)) or at<=0:continue
     fresh=source.get('status')=='fresh'
     rows=[r for r in feed.get('rows',[]) if r.get('platform')==platform and term.casefold() in str(r.get('title','')).casefold()]
     best=min(rows,key=lambda r:r['rank']) if rows and fresh else None
     status='ranked' if best else 'not_ranked' if fresh else 'unknown'
     db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?,?,?)',(user,term,platform,at,status,best['rank'] if best else None,best['id'] if best else '',best['title'] if best else ''))
   db.execute('DELETE FROM observations WHERE at<?',(now-7*86400,))
 def view(self,user,term=''):
  with self.db() as db:
   terms=[r[0] for r in db.execute('SELECT term FROM terms WHERE user_id=? ORDER BY created DESC',(user,))]
   if term and term not in terms:return {'keywords':terms,'keyword':term,'observations':[]}
   selected=term or (terms[0] if terms else '');observations=[]
   for platform in PLATFORMS:
    rows=db.execute('SELECT at,status,rank,topic_id,title FROM observations WHERE user_id=? AND term=? AND platform=? ORDER BY at DESC LIMIT 8',(user,selected,platform)).fetchall()
    if not rows:observations.append({'platform':platform,'status':'unknown','rank':None,'title':'','rankChange':None,'trail':[]});continue
    latest=rows[0];previous=rows[1] if len(rows)>1 else None
    change=previous[2]-latest[2] if previous and latest[1]==previous[1]=='ranked' and latest[3]==previous[3] and 0<latest[0]-previous[0]<=1800 else None
    observations.append({'platform':platform,'at':latest[0],'status':latest[1],'rank':latest[2],'title':latest[4],'rankChange':change,'trail':[{'at':r[0],'status':r[1],'rank':r[2]} for r in reversed(rows)]})
  return {'keywords':terms,'keyword':selected,'observations':observations,'notice':'仅监测已采集的平台榜单前50项；未入采集榜不代表全网没有热度。每10分钟采样，保存7天。'}
 def start(self,snapshot):
  def run():
   while True:
    try:self.sample(snapshot())
    except Exception:pass
    time.sleep(600)
  threading.Thread(target=run,daemon=True).start()
class Search:
 def __init__(self):self.cache={};self.lock=threading.Lock();self.slots=threading.BoundedSemaphore(2)
 def query(self,term,feed,retrieve):
  term=keyword(term);now=time.time()
  ranked=[r for r in feed.get('rows',[]) if term.casefold() in str(r.get('title','')).casefold()]
  with self.lock:cached=self.cache.get(term)
  if cached and cached[0]>now:items=cached[1];status=cached[2]
  elif not self.slots.acquire(blocking=False):items=[];status='busy'
  else:
   try:
    try:items=retrieve(term)[:6];status='ready' if items else 'empty'
    except Exception:items=[];status='unavailable'
    with self.lock:
     if len(self.cache)>100:self.cache.clear()
     self.cache[term]=(now+(300 if status=='ready' else 30),items,status)
   finally:self.slots.release()
  return {'keyword':term,'ranked':ranked,'items':items,'searchStatus':status,'notice':'相关网页为检索结果，不代表平台上榜；榜位仅来自已采集的真实热榜。'}
