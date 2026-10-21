"""Public comment evidence: persist only text, counters and author-reply flag."""
import importlib.util
import json
import re
import sqlite3
import time
from pathlib import Path

spec=importlib.util.spec_from_file_location('links',Path(__file__).with_name('link-platform.py'))
links=importlib.util.module_from_spec(spec);spec.loader.exec_module(links)


def sanitize(items, author_uid=''):
    rows=[]
    for item in items[:20] if isinstance(items,list) else []:
        if not isinstance(item,dict):continue
        value=links.strip_contacts(item.get('text'))[0]
        value=re.sub(r'@[^\s，。:：]+','[用户]',value).strip()[:80]
        if not value:continue
        author=item.get('author') if isinstance(item.get('author'),dict) else {}
        is_author=item.get('isAuthorReply') is True or item.get('is_author') is True
        if author_uid:is_author=is_author or author_uid in [str(author.get(k) or '') for k in ('uid','sec_uid','id')]
        number=lambda v:min(v,10**12) if type(v) is int and v>=0 else 0
        rows.append({'text':value,'likes':number(item.get('likes',item.get('digg_count'))),
                     'replies':number(item.get('replies',item.get('reply_count'))),'isAuthorReply':is_author})
    return sorted(rows,key=lambda row:(-row['likes'],-row['replies']))


REPLY_WEIGHT=3  # 一条回复比一个赞更费力，代表真在讨论


def weigh(rows):
    """Rank comments by heat (likes + 3×replies) and say how much each one weighs, so judgements lean on what the audience
    actually backed instead of whichever comment happens to come first. Returns (rows, stats)."""
    rows=[dict(r) for r in rows if isinstance(r,dict)][:20]
    for r in rows:r['heat']=r.get('likes',0)+REPLY_WEIGHT*r.get('replies',0)
    rows.sort(key=lambda r:(-r['heat'],-r.get('likes',0)))
    total=sum(r['heat'] for r in rows);likes=sum(r.get('likes',0) for r in rows);replies=sum(r.get('replies',0) for r in rows)
    for r in rows:
        share=r['heat']/total if total else 0;r['share']=round(share,3)
        if r['heat']<3 or share<0.02:r['kind']='长尾'
        elif r.get('replies',0)>=3 and r.get('replies',0)>=r.get('likes',0)*0.3:r['kind']='讨论'
        elif r.get('likes',0)>=10:r['kind']='共识'
        else:r['kind']='普通'
    top1=rows[0]['share'] if rows and total else 0;top3=round(sum(r['share'] for r in rows[:3]),3) if total else 0
    shape='没有评论' if not rows else '互动太少' if total<20 else '单条主导' if top1>=0.5 else '头部集中' if top3>=0.7 else '分散'
    stats={'read':len(rows),'likes':likes,'replies':replies,'top1Share':top1,'top3Share':top3,'shape':shape,
           'discussion':sum(r['kind']=='讨论' for r in rows),'consensus':sum(r['kind']=='共识' for r in rows),
           'authorReplies':sum(bool(r.get('isAuthorReply')) for r in rows),'reliable':bool(rows) and total>=20}
    return rows,stats


def fetch(root, content_id, request, author_uid='', clock=time.time):
    if not re.fullmatch(r'[0-9]{5,40}',str(content_id or '')):return []
    try:
        root=Path(root);root.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(root/'comments.sqlite',timeout=1) as db:
            db.execute('CREATE TABLE IF NOT EXISTS comments(content TEXT PRIMARY KEY,at REAL,payload TEXT)')
            db.execute('DELETE FROM comments WHERE at < ?',(clock()-86400,))
            row=db.execute('SELECT payload FROM comments WHERE content=?',(content_id,)).fetchone()
            if row:return sanitize(json.loads(row[0]))
        result=request('/api/v1/douyin/video/comments?aweme_id='+content_id+'&count=20&include_raw=false&wait=8',timeout=9)
        data=result.get('data',{}) if isinstance(result,dict) else {}
        if not isinstance(data,dict) or not isinstance(data.get('items'),list):return []
        rows=sanitize(data['items'],author_uid)
        with sqlite3.connect(root/'comments.sqlite',timeout=1) as db:
            db.execute('INSERT OR REPLACE INTO comments VALUES(?,?,?)',(content_id,clock(),json.dumps(rows,ensure_ascii=False)))
        return rows
    except Exception:
        return []
