"""Private per-WeChat-user preferences with atomic compare-and-swap revisions."""
import json,re,sqlite3,time,uuid
from contextlib import contextmanager
from pathlib import Path

TYPES={'voice','graphic','product','tutorial','story','offer'}
GOALS={'structure','emotion','selling','conversion','trust','visual'}
PRESETS={'structure','emotion','benefit','offer','evidence','visual'}
FIELDS={'customTemplates','typeDefaults','typeGoals','goals','goalOverrides','materialOverrides','materialType','mode','preset','overrides'}
class Conflict(Exception):pass

def validate(value):
    def require(ok):
        if not ok:raise ValueError('模板同步数据格式无效')
    def text(raw,limit,empty=False):return isinstance(raw,str) and len(raw)<=limit and (empty or bool(raw.strip()))
    def goals(raw):return isinstance(raw,list) and len(raw)<=6 and all(isinstance(key,str) and key in GOALS for key in raw) and len(raw)==len(set(raw))
    def mapping(raw,keys,validator,limit=200):return isinstance(raw,dict) and len(raw)<=limit and all(isinstance(key,str) and key not in ('__proto__','constructor','prototype') and (key in keys if keys else bool(re.fullmatch('[A-Za-z0-9_-]{1,80}',key))) and validator(item) for key,item in raw.items())
    require(isinstance(value,dict) and set(value)==FIELDS)
    rows=value['customTemplates'];require(isinstance(rows,list) and len(rows)<=20)
    ids=set(PRESETS)
    for row in rows:
        require(isinstance(row,dict) and set(row)=={'id','name','description','materialType','sections','dimensions','steps','version','goalIds','custom'})
        ident=row['id'];require(isinstance(ident,str) and bool(re.fullmatch('custom-[a-z0-9]{8,40}',ident)) and ident not in ids);ids.add(ident)
        require(text(row['name'],32) and text(row['description'],160,True) and isinstance(row['materialType'],str) and row['materialType'] in TYPES and row['custom'] is True)
        require(type(row['version']) is int and 1<=row['version']<=9999 and goals(row['goalIds']))
        sections=row['sections'];require(isinstance(sections,list) and 1<=len(sections)<=12)
        keys=[]
        for section in sections:
            require(isinstance(section,dict) and set(section)=={'key','title','question'})
            key=section['key'];require(isinstance(key,str) and bool(re.fullmatch('[a-z][a-z0-9_-]{0,40}',key)) and key not in keys)
            require(text(section['title'],40) and text(section['question'],240));keys.append(key)
        require(row['dimensions']==keys and isinstance(row['steps'],list) and len(row['steps'])<=12 and all(text(step,240) for step in row['steps']))
    require(value['mode'] in ('auto','manual') and isinstance(value['preset'],str) and value['preset'] in ids and isinstance(value['materialType'],str) and value['materialType'] in TYPES|{'auto'} and goals(value['goals']))
    require(mapping(value['typeDefaults'],TYPES,lambda key:isinstance(key,str) and key in ids,6))
    require(mapping(value['typeGoals'],TYPES,goals,6) and mapping(value['goalOverrides'],None,goals))
    require(mapping(value['materialOverrides'],None,lambda key:isinstance(key,str) and key in TYPES))
    require(mapping(value['overrides'],None,lambda key:isinstance(key,str) and key in ids|{'auto'}))
    require(len(json.dumps(value,ensure_ascii=False).encode())<=524288)
    return value

class Store:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS analysis_preferences (user_id TEXT PRIMARY KEY, revision TEXT NOT NULL, preferences TEXT NOT NULL, updated_at REAL NOT NULL)')
        self.path.chmod(0o600)
    @contextmanager
    def db(self):
        connection=sqlite3.connect(self.path,timeout=10)
        try:
            with connection:yield connection
        finally:connection.close()
    def read(self,user):
        with self.db() as db:row=db.execute('SELECT revision,preferences,updated_at FROM analysis_preferences WHERE user_id=?',(user,)).fetchone()
        return {'revision':row[0],'preferences':json.loads(row[1]),'updatedAt':row[2]} if row else {'revision':'none','preferences':None,'updatedAt':None}
    def write(self,user,expected,value):
        value=validate(value)
        if not isinstance(expected,str) or not re.fullmatch('none|[a-f0-9]{32}',expected):raise ValueError('同步版本无效')
        revision=uuid.uuid4().hex;now=time.time()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT revision FROM analysis_preferences WHERE user_id=?',(user,)).fetchone()
            if (old[0] if old else 'none')!=expected:raise Conflict()
            db.execute('INSERT INTO analysis_preferences VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET revision=excluded.revision,preferences=excluded.preferences,updated_at=excluded.updated_at',(user,revision,json.dumps(value,ensure_ascii=False),now))
        return {'revision':revision,'preferences':value,'updatedAt':now}
