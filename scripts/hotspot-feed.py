"""Scheduled, bounded DailyHotApi snapshots. Requests never trigger scraping."""
import copy
import hashlib
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

INTERVAL = 600
SOURCES = {'douyin': '抖音', 'weibo': '微博', 'toutiao': '今日头条', 'kuaishou': '快手'}
ROOT = Path(os.environ.get('YOUAI_HOTSPOT_STATE', '/data/hotspots/snapshot.json'))
BASE = os.environ.get('YOUAI_HOTSPOT_API', '')
LOCK = threading.Lock()
STATE = {'sources': {}}

def normalize(key, payload, now):
    if payload.get('code') != 200 or not isinstance(payload.get('data'), list):
        raise ValueError('invalid feed')
    rows = []
    for rank, item in enumerate(payload['data'][:50], 1):
        title = str(item.get('title', '')).strip()[:200]
        if not title:
            continue
        url = str(item.get('url', ''))[:1000]
        if not url.startswith('https://'):
            url = ''
        rows.append({'id': key + '-' + hashlib.sha256(title.encode()).hexdigest()[:20],
                     'title': title, 'platform': SOURCES[key], 'rank': rank,
                     'url': url, 'kind': '平台热榜', 'tags': [],
                     'summary': title, 'angle': '结合自己的观察创作，发布前核实话题事实。',
                     'sourceLabel': SOURCES[key] + '热榜 · DailyHotApi',
                     'fetchedAt': now})
    if not rows:
        raise ValueError('empty feed')
    return {'rows': rows, 'fetchedAt': now, 'sourceUpdatedAt': str(payload.get('updateTime', ''))[:60], 'error': ''}

def refresh(fetch=None, now=None):
    now = time.time() if now is None else now
    if fetch is None:
        def fetch(key):
            with urllib.request.urlopen(BASE.rstrip('/') + '/' + key + '?cache=false', timeout=20) as r:
                return json.loads(r.read(2_000_000))
    with LOCK:
        result = copy.deepcopy(STATE)
    for key in SOURCES:
        try:
            latest = normalize(key, fetch(key), now)
            previous = result['sources'].get(key, {})
            before = {r['id']: r for r in previous.get('rows', [])}
            interval = now - previous.get('fetchedAt', 0)
            comparable = bool(before) and 0 < interval <= 1800
            history = previous.get('history', [])
            if not history and before:
                history = [{'at': previous['fetchedAt'], 'ranks': {k:r['rank'] for k,r in before.items()}}]
            history = [h for h in history if 0 <= now-h['at'] <= 3600]
            history = (history + [{'at': now, 'ranks': {r['id']:r['rank'] for r in latest['rows']}}])[-6:]
            for row in latest['rows']:
                old = before.get(row['id'])
                change = old['rank'] - row['rank'] if comparable and old else 0
                row.update(trend='baseline' if not comparable else 'new' if not old else 'rising' if change > 0 else 'falling' if change < 0 else 'steady',
                           rankChange=change, previousRank=old['rank'] if comparable and old else None,
                           comparedAt=previous.get('fetchedAt') if comparable else None,
                           comparisonSeconds=interval if comparable else None,
                           rankTrail=[{'at':h['at'], 'rank':h['ranks'].get(row['id'])} for h in history])
            latest['history'] = history
            result['sources'][key] = latest
        except Exception:
            old = result['sources'].setdefault(key, {'rows': [], 'fetchedAt': 0})
            old['error'] = '来源暂不可用'
        result['sources'][key]['attemptedAt'] = now
    result['lastAttemptAt'] = now
    ROOT.parent.mkdir(parents=True, exist_ok=True)
    temp = ROOT.with_suffix('.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    temp.replace(ROOT)
    with LOCK:
        STATE.clear()
        STATE.update(result)

def snapshot(now=None):
    now = time.time() if now is None else now
    with LOCK:
        result = copy.deepcopy(STATE)
    result.update(schemaVersion=1, refreshSeconds=INTERVAL)
    rows = []
    for key, name in SOURCES.items():
        source = result['sources'].setdefault(key, {'rows': [], 'fetchedAt': 0})
        source['platform'] = name
        age = now - source['fetchedAt']
        source['status'] = 'unavailable' if not source['rows'] or age > 86400 else 'stale' if source.get('error') or age > INTERVAL + 60 else 'fresh'
        current = source.pop('rows')
        source.pop('history', None)
        if source['status'] != 'unavailable':
            rows.extend(dict(row, stale=source['status'] != 'fresh') for row in current)
    # 综合交错展示各平台同名次；不比较跨平台热度。
    result['rows'] = sorted(rows, key=lambda row: row['rank'])
    return result

def start():
    if not BASE:
        return
    try:
        saved = json.loads(ROOT.read_text(encoding='utf-8'))
        if isinstance(saved.get('sources'), dict):
            STATE.update(saved)
    except (OSError, ValueError):
        pass
    def run():
        while True:
            began = time.monotonic()
            try:
                refresh()
            except Exception as error:
                print('hotspot refresh failed: ' + type(error).__name__, flush=True)
            time.sleep(max(1, INTERVAL - (time.monotonic() - began)))
    threading.Thread(target=run, daemon=True, name='hotspot-refresh').start()
