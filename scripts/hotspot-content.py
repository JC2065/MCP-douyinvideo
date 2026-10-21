"""On-demand source excerpts. No model-generated news and no arbitrary URL fetching."""
import concurrent.futures
import hashlib
import html
import json
import re
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

POOL = concurrent.futures.ThreadPoolExecutor(max_workers=2)
LOCK = threading.Lock()
JOBS = {}
ROOT = Path('/data/hotspots/content')
TTL = 1800
SEARCH_VERSION = 2

def clean(text):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', '', text or ''))).strip()

def relevant(topic, title, excerpt):
    text = re.sub(r'[^\w]', '', topic).lower()
    target = re.sub(r'[^\w]', '', title + excerpt).lower()
    if not text or not target: return False
    if text in target: return True
    pairs = {text[i:i+2] for i in range(len(text)-1)}
    return len(pairs & {target[i:i+2] for i in range(len(target)-1)}) >= max(3, len(pairs)*0.35)

def parse_rss(raw, topic):
    root = ET.fromstring(raw)
    items = []
    seen = set()
    for item in root.findall('.//item'):
        title = clean(item.findtext('title'))[:200]
        excerpt = clean(item.findtext('description'))[:1200]
        url = item.findtext('link', '').strip()[:2000]
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username or parsed.password:
            continue
        if url in seen or not title or not excerpt or not relevant(topic,title,excerpt): continue
        seen.add(url)
        items.append({'id':hashlib.sha256(url.encode()).hexdigest()[:16], 'title':title,
                      'excerpt':excerpt, 'url':url, 'source':parsed.hostname,
                      'publishedAt':clean(item.findtext('pubDate'))[:80],
                      'contentType':'网页检索摘录',
                      'isVideo':parsed.hostname in ('www.douyin.com','douyin.com') and bool(re.fullmatch(r'/video/\d+/?',parsed.path))})
        if len(items)==6: break
    return items

def request_bytes(url):
    request = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(request,timeout=8) as response:
        raw = response.read(1_000_001)
    if len(raw)>1_000_000: raise ValueError('response too large')
    return raw

def queries(topic, tokenize=None):
    if tokenize is None:
        try:
            import jieba
            tokenize=jieba.lcut
        except ImportError:
            tokenize=lambda value:[value]
    # Preserve all words: dropping words can change the subject of a headline.
    split=' '.join(word.strip() for word in tokenize(topic) if word.strip())
    return [('www.bing.com',topic),('www.bing.com',split),('cn.bing.com',split)]

def fetch(topic, reader=request_bytes, tokenize=None):
    valid_responses=0
    seen=set()
    for host,query in queries(topic,tokenize):
        url='https://'+host+'/search?format=rss&count=10&setlang=zh-hans&q='+urllib.parse.quote(query)
        if url in seen: continue
        seen.add(url)
        try:
            items=parse_rss(reader(url),topic)
            valid_responses+=1
            if items:return items
        except Exception: continue
    if not valid_responses:raise RuntimeError('content search unavailable')
    return []

def run(row, retrieve=fetch):
    ident = row['id']
    now = time.time()
    try:
        items = retrieve(row['title'])
        value = {'status':'ready' if items else 'empty','topicId':ident,'title':row['title'],
                 'retrievedAt':now,'items':items,'sourceUrl':row.get('url',''),'searchVersion':SEARCH_VERSION,
                 'notice':'以下为相关来源摘录，请核对原文和报道日期。' if items else '暂未找到匹配的报道或视频，可重试或复制原平台链接查看。'}
    except Exception:
        value = {'status':'error','topicId':ident,'retrievedAt':now,'items':[],'searchVersion':SEARCH_VERSION,
                 'notice':'内容检索暂不可用，请稍后重试或复制原平台链接。'}
    try:
        ROOT.mkdir(parents=True,exist_ok=True)
        target = ROOT/(ident+'.json')
        temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
        temporary.replace(target)
        files = sorted(ROOT.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
        for path in files[300:]: path.unlink(missing_ok=True)
    except OSError: pass
    with LOCK: JOBS[ident] = value

def content(ident, rows, retry=False):
    row = next((r for r in rows if r['id']==ident),None)
    if not row: return {'status':'expired','items':[],'notice':'该话题已离开当前榜单，请返回刷新。'}
    with LOCK:
        value = JOBS.get(ident)
        if value and value['status']=='pending': return dict(value)
        if not value:
            try: value=json.loads((ROOT/(ident+'.json')).read_text(encoding='utf-8'))
            except (OSError,ValueError): pass
        lifetime = TTL if value and value.get('status')=='ready' else 120
        if value and value.get('status')!='ready' and value.get('searchVersion')!=SEARCH_VERSION: value=None
        if value and time.time()-value.get('retrievedAt',0)<lifetime and not (retry and value.get('status') in ('empty','error')): return value
        if sum(v.get('status')=='pending' for v in JOBS.values())>=2:
            return {'status':'busy','items':[],'notice':'正在获取其他话题，请稍后重试。'}
        for key in list(JOBS):
            if JOBS[key].get('status')!='pending' and time.time()-JOBS[key].get('retrievedAt',0)>TTL:
                del JOBS[key]
        value={'status':'pending','topicId':ident,'items':[],'notice':'正在查找相关来源…'}
        JOBS[ident]=value
        POOL.submit(run,dict(row))
        return dict(value)
