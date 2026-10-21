"""Run Douyin links through the live creation-board pipeline as the test account `claude-test` (server-side tool, not shipped in the image).

Usage on the server:  docker cp scripts/sample-breakdown-run.py youai-video-video-1:/tmp/run.py
  docker exec -d youai-video-video-1 sh -c "cd /app && python3 /tmp/run.py /data/assets/claude-runs/runN.json <link> [<link> ...] > /data/assets/claude-runs/runN.log 2>&1"
Write results under /data/assets (a volume): /tmp is lost on every redeploy. Each link: acquire → analyze → glance → board session → confirm → breakdown → text → package.
Costs real model calls (about the same as a user doing it in the mini program)."""
import json, sqlite3, sys, time, importlib.util
from urllib.request import Request, urlopen
from urllib.error import HTTPError
spec = importlib.util.spec_from_file_location('auth', '/app/scripts/wechat-auth.py'); auth = importlib.util.module_from_spec(spec); spec.loader.exec_module(auth)
A = auth.WechatAuth('/nonexistent', '/data/assets/auth/sessions.sqlite')
USER = 'claude-test'
A.profile(USER)
with A.db() as db:
    db.execute("UPDATE accounts SET bound_at=COALESCE(bound_at,?), phone_mask=COALESCE(phone_mask,'+86 claude-test') WHERE user_id=?", (int(time.time()), USER))
    TOKEN, _ = A._issue(db, USER)
BASE = 'http://127.0.0.1:8765'
def call(path, data=None, timeout=200):
    req = Request(BASE + path, data=json.dumps(data).encode() if data is not None else None,
                  headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=timeout) as r: return json.load(r)
    except HTTPError as e:
        body = e.read().decode('utf-8', 'replace')[:400]
        return {'__error': e.code, 'body': body}
LINKS = sys.argv[2:]
out = []
for url in LINKS:
    row = {'url': url, 'steps': {}}; t0 = time.time()
    try:
        ref = call('/references/acquire', {'url': url}, 200); row['steps']['acquire'] = {k: ref.get(k) for k in ('status', 'error', '__error', 'body')} | {'asset': {k: (ref.get('asset') or {}).get(k) for k in ('sha256', 'kind', 'media', 'mediaType')}, 'source': ref.get('source'), 'comments':ref.get('comments',[])}
        if ref.get('__error') or not (ref.get('asset') or {}).get('sha256'):
            row['failed'] = 'acquire'; out.append(row); continue
        job = call('/references/analyze', {'reference': ref, 'sampling': 'smart'}, 60)
        if job.get('__error'): row['failed'] = 'analyze'; row['steps']['analyze'] = job; out.append(row); continue
        jid = job.get('id') or job.get('jobId')
        for _ in range(90):
            st = call('/reference-analyses/' + jid, None, 30)
            if st.get('status') in ('done', 'failed'): break
            time.sleep(4)
        row['steps']['analyze'] = {'status': st.get('status'), 'error': st.get('error'), 'seconds': round(time.time() - t0)}
        if st.get('status') != 'done': row['failed'] = 'analyze'; out.append(row); continue
        reference = st['reference']; an = reference.get('analysis') or {}
        row['analysis'] = {'version': an.get('analyzerVersion'), 'summary': an.get('summary'), 'understanding': an.get('understanding'), 'screenText': an.get('screenText'), 'audio':an.get('audio'), 'truncated': an.get('truncated')}
        glance = call('/references/glance', {'reference': reference}, 40); row['glance'] = glance
        sess = call('/board/session', {'reference': {'asset': {'sha256': reference['asset']['sha256']}}, 'glance': glance if glance.get('status') == 'ready' else None}, 40)
        if sess.get('__error'): row['failed'] = 'session'; row['steps']['session'] = sess; out.append(row); continue
        sess = call('/board/refresh', {'id': sess['id']}, 40)
        row['card'] = sess.get('card'); row['plan'] = sess.get('plan'); row['suggestion'] = sess.get('suggestion'); row['questions'] = sess.get('questions'); row['countdown'] = sess.get('countdownSeconds')
        conf = call('/board/confirm', {'id': sess['id'], 'verdict': 'ok', 'corrections': [], 'auto': False}, 60)
        bd = call('/board/breakdown', {'id': sess['id']}, 120); row['breakdown'] = bd.get('breakdown') if not bd.get('__error') else bd
        text = call('/board/output/text', {'id': sess['id']}, 120); row['text'] = (text.get('outputs') or {}).get('text') if not text.get('__error') else text
        pack = call('/board/output/package', {'id': sess['id'], 'conditions': ''}, 120); row['package'] = (pack.get('outputs') or {}).get('package') if not pack.get('__error') else pack
        row['seconds'] = round(time.time() - t0)
    except Exception as e:
        row['exception'] = repr(e)
    out.append(row)
    json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
print('done', len(out))
