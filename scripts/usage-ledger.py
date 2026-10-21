"""Durable, shared cost reservations. Prices are CNY per million tokens."""
import json,sqlite3,time,uuid,datetime
from pathlib import Path
from contextlib import contextmanager

class UsageLimit(ValueError):pass
class UsageLedger:
    def __init__(self,path,settings,clock=time.time):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.settings=settings;self.clock=clock
        with self.db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY,day TEXT,at REAL,user TEXT,asset TEXT,scene TEXT,model TEXT,reserved REAL,cost REAL,prompt INTEGER,completion INTEGER,cached INTEGER,cache_hit INTEGER,status TEXT);
            CREATE TABLE IF NOT EXISTS videos(day TEXT,user TEXT,asset TEXT,PRIMARY KEY(day,user,asset));''')
        self.path.chmod(0o600)
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=30);db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()
    def day(self):return datetime.datetime.fromtimestamp(self.clock(),datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    def reserve(self,user,asset,scene,model,input_tokens,output_tokens):
        cfg=self.settings();prices=cfg['prices'].get(model,{'in':10,'out':30})
        estimate=(input_tokens*prices['in']+output_tokens*prices['out'])/1e6
        ident=uuid.uuid4().hex;day=self.day()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            total=db.execute('SELECT COALESCE(SUM(COALESCE(cost,reserved)),0) FROM calls WHERE day=?',(day,)).fetchone()[0]
            if total+estimate>cfg['dailyBudgetYuan']:raise UsageLimit('今日 AI 观看额度已用完（全站预算）')
            if scene=='video_watch':
                exists=db.execute('SELECT 1 FROM videos WHERE day=? AND user=? AND asset=?',(day,user,asset)).fetchone()
                used=db.execute('SELECT COUNT(*) FROM videos WHERE day=? AND user=?',(day,user)).fetchone()[0]
                if not exists and used>=cfg['perUserDailyVideos'] and not (getattr(self,'extra',None) and self.extra(user)):raise UsageLimit('今日 AI 观看额度已用完（个人额度）；回传作品数据可获得额外次数')
                db.execute('INSERT OR IGNORE INTO videos VALUES(?,?,?)',(day,user,asset))
            db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,NULL,0,0,0,0,?)',(ident,day,self.clock(),user,asset,scene,model,estimate,'reserved'))
        return ident
    def settle(self,ident,usage,status='ok'):
        usage=usage if isinstance(usage,dict) else {}
        def number(v):return max(0,int(v)) if type(v) in (int,float) else 0
        prompt=number(usage.get('prompt_tokens'));completion=number(usage.get('completion_tokens'));cached=number((usage.get('prompt_tokens_details') or {}).get('cached_tokens'))
        with self.db() as db:
            row=db.execute('SELECT model,reserved FROM calls WHERE id=?',(ident,)).fetchone()
            prices=self.settings()['prices'].get(row['model'],{'in':10,'out':30})
            # Missing usage and ambiguous transport failures retain the reservation.
            cost=(prompt*prices['in']+completion*prices['out'])/1e6 if 'prompt_tokens' in usage else None
            db.execute('UPDATE calls SET cost=?,prompt=?,completion=?,cached=?,status=? WHERE id=?',(cost,prompt,completion,cached,status,ident))
    def cache_hit(self,user,asset,scene,model):
        with self.db() as db:db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?,0,0,0,0,0,1,?)',(uuid.uuid4().hex,self.day(),self.clock(),user,asset,scene,model,'cache'))
    def overview(self):
        today=self.day();since=self.clock()-7*86400
        with self.db() as db:
            def aggregate(where,args):
                row=db.execute('SELECT COUNT(*) requests,COALESCE(SUM(1-cache_hit),0) calls,COALESCE(SUM(cache_hit),0) cacheHits,COALESCE(SUM(prompt+completion),0) tokens,COALESCE(SUM(COALESCE(cost,reserved)),0) estimatedYuan FROM calls WHERE '+where,args).fetchone();return dict(row)
            return {'today':aggregate('day=?',(today,)),'sevenDays':aggregate('at>=?',(since,)),'currency':'CNY','estimated':True}
