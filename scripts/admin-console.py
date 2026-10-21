import sqlite3
from contextlib import closing
"""Independent operator authentication and bounded, data-only configuration management."""
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

TOOLS = ('download', 'transcript', 'audio', 'eraser', 'cover')

class AdminError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message

def credential(password):
    salt = secrets.token_hex(16)
    return {'username': 'admin', 'salt': salt, 'iterations': 260000,
            'hash': hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000).hex()}

class Console:
    def __init__(self, root, auth_file, config_file, snapshot, content, jobs, ai=None, platform=None):
        self.root, self.auth_file, self.config_file = Path(root), Path(auth_file), Path(config_file)
        self.snapshot, self.content, self.jobs = snapshot, content, jobs
        self.ai = ai
        self.platform = platform
        self.board = None  # creation board, attached by the video server
        self.lock = threading.RLock()
        self.sessions, self.attempts = {}, {}
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + '.' + secrets.token_hex(8) + '.tmp')
        try:
            with temp.open('x', encoding='utf-8') as stream:
                os.chmod(temp, 0o600)
                stream.write(json.dumps(value, ensure_ascii=False))
                stream.flush()
                os.fsync(stream.fileno())
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)

    def audit(self, event, revision=''):
        # Never record passwords, session tokens, user prompts or provider responses.
        with (self.root / 'audit.jsonl').open('a', encoding='utf-8') as stream:
            os.chmod(stream.name, 0o600)
            stream.write(json.dumps({'at': int(time.time()), 'actor': 'admin',
                                     'event': event, 'revision': revision}) + '\n')

    def login(self, payload, peer):
        now = time.time()
        with self.lock:
            self.attempts = {key: value for key, value in self.attempts.items() if value[-1] > now - 300}
            history = [at for at in self.attempts.get(peer, []) if at > now - 300]
            if len(history) >= 5 or len(self.attempts) >= 1000:
                raise AdminError(429, '登录尝试过多，请5分钟后重试')
            self.attempts[peer] = history + [now]
            try:
                auth = json.loads(self.auth_file.read_text(encoding='utf-8-sig'))
                rounds = auth['iterations']
                if not isinstance(rounds, int) or not 200000 <= rounds <= 1000000: raise ValueError()
                password = payload.get('password', '')
                if not isinstance(password, str) or not 8 <= len(password) <= 256: raise AdminError(401, '管理员账号或密码不正确')
                actual = hashlib.pbkdf2_hmac('sha256', password.encode(), auth['salt'].encode(), rounds).hex()
                if payload.get('username') != auth['username'] or not hmac.compare_digest(actual, auth['hash']):
                    raise AdminError(401, '管理员账号或密码不正确')
            except (OSError, ValueError, KeyError, TypeError):
                raise AdminError(503, '管理员登录尚未配置')
            self.attempts.pop(peer, None)
            self.sessions = {key: value for key, value in self.sessions.items() if value > now}
            if len(self.sessions) >= 100: raise AdminError(429, '管理会话过多，请退出旧会话')
            token = secrets.token_urlsafe(32)
            self.sessions[hashlib.sha256(token.encode()).hexdigest()] = now + 3600
            self.audit('login')
            return {'token': token, 'expiresAt': int(now + 3600)}

    def authorize(self, header):
        token = header[7:] if header.startswith('Bearer ') else ''
        key = hashlib.sha256(token.encode()).hexdigest()
        with self.lock:
            if not token or self.sessions.get(key, 0) <= time.time():
                self.sessions.pop(key, None)
                raise AdminError(401, '请登录管理中台')
        return key

    def task_interest(self, user=None):
        with closing(sqlite3.connect(self.root / 'task-interest.sqlite', timeout=10)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS interest(user TEXT PRIMARY KEY,created INTEGER)')
            if user: db.execute('INSERT OR IGNORE INTO interest VALUES(?,?)',(user,int(time.time())))
            total=db.execute('SELECT COUNT(*) FROM interest').fetchone()[0]
            return {'total':total,'supported':bool(user and db.execute('SELECT 1 FROM interest WHERE user=?',(user,)).fetchone())}

    def config(self):
        try:
            value = json.loads(self.config_file.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError): value = {}
        if not isinstance(value, dict): value = {}
        tools = value.get('tools', {})
        if not isinstance(tools, dict): tools = {}
        return {'schemaVersion': 1, 'revision': str(value.get('revision', 'default'))[:64],
                'tools': {key: {'maintenance': isinstance(tools.get(key), dict) and tools[key].get('maintenance') is True} for key in TOOLS}}

    def versions(self):
        return sorted([json.loads(path.read_text(encoding='utf-8')) for path in (self.root / 'versions').glob('*.json')], key=lambda row: row['publishedAt'], reverse=True)

    def publish(self, payload):
        with self.lock:
            current = self.config()
            if payload.get('expectedRevision') != current['revision']: raise AdminError(409, '配置已被其他操作更新，请刷新后再发布')
            if 'rollback' in payload:
                if set(payload) != {'expectedRevision', 'rollback'}: raise AdminError(400, '回滚请求字段无效')
                revision = payload['rollback']
                if not isinstance(revision, str) or not re.fullmatch(r'[a-f0-9]{32}', revision): raise AdminError(400, '配置版本无效')
                try: tools = json.loads((self.root / 'versions' / (revision + '.json')).read_text())['tools']
                except (OSError, ValueError, KeyError): raise AdminError(404, '配置版本不存在')
                event = 'rollback'
            else:
                if set(payload) != {'expectedRevision', 'tools'}: raise AdminError(400, '只允许发布已有工具维护状态')
                tools, event = payload.get('tools'), 'publish'
            if not isinstance(tools, dict) or set(tools) != set(TOOLS): raise AdminError(400, '工具配置不完整')
            for key in TOOLS:
                if not isinstance(tools[key], dict) or set(tools[key]) != {'maintenance'} or type(tools[key]['maintenance']) is not bool:
                    raise AdminError(400, '维护状态必须为布尔值')
            # Preserve the previous state, including a baseline imported from the credential mount.
            if not re.fullmatch(r'[a-f0-9]{32}', current['revision']) or not (self.root / 'versions' / (current['revision'] + '.json')).exists():
                saved = dict(current, revision=secrets.token_hex(16), publishedAt=time.time(), event='baseline')
                self.write(self.root / 'versions' / (saved['revision'] + '.json'), saved)
            value = {'schemaVersion': 1, 'revision': secrets.token_hex(16), 'tools': tools,
                     'publishedAt': time.time(), 'event': event}
            self.write(self.root / 'versions' / (value['revision'] + '.json'), value)
            self.write(self.config_file, value)
            self.audit(event, value['revision'])
            for old in self.versions()[50:]:
                (self.root / 'versions' / (old['revision'] + '.json')).unlink(missing_ok=True)
            return self.config()

    def dispatch(self, method, path, payload, header, peer):
        if method == 'POST' and path == '/admin-api/login': return self.login(payload, peer)
        key = self.authorize(header)
        if path in ('/admin-api/inspiration-ai','/admin-api/inspiration-ai/probe'):
            if not self.ai:raise AdminError(503,'灵感AI配置尚未接入')
            try:
                if method=='GET' and path=='/admin-api/inspiration-ai':return self.ai.dashboard()
                if method=='POST' and path.endswith('/probe'):
                    if set(payload)!={'scene'} or payload['scene'] not in ('ta_opening','ta_chat','hotspot_summary'):raise ValueError('检测场景无效')
                    value=self.ai.probe(payload['scene'])
                    with self.lock:self.audit('inspiration_ai_probe',payload['scene'])
                    return value
                if method=='POST':
                    value=self.ai.publish(payload)
                    with self.lock:self.audit('inspiration_ai_rollback' if 'rollback' in payload else 'inspiration_ai_publish',value['revision'])
                    return value
                raise AdminError(405,'不支持的操作')
            except ValueError as e:raise AdminError(400,str(e)) from None
            except self.ai.Error as e:raise AdminError(503,str(e)) from None
            except Exception as e:
                if type(e).__name__=='Conflict':raise AdminError(409,'AI配置已有新版本，请刷新后重试') from None
                raise
        if path.startswith('/admin-api/creation/'):
            return self.creation_dispatch(method, path, payload)
        if path == '/admin-api/trial-accounts':
            auth = getattr(self, 'auth', None)
            if not auth: raise AdminError(503, '微信账号服务尚未接入')
            if method == 'POST':
                if set(payload) != {'enabled'} or not isinstance(payload['enabled'], bool): raise AdminError(400, '参数无效')
                enabled = auth.set_trial_enabled(payload['enabled'])
                with self.lock: self.audit('trial_accounts_' + ('on' if enabled else 'off'))
            return {'enabled': auth.trial_enabled(), 'rows': auth.trial_accounts()}
        if path == '/admin-api/platform' or path.startswith('/admin-api/platform/') or path == '/admin-api/workflows' or path.startswith('/admin-api/workflows/'):
            return self.platform_dispatch(method, path, payload)
        with self.lock:
            if method == 'POST' and path == '/admin-api/logout':
                self.sessions.pop(key, None); self.audit('logout'); return {'status': 'signed_out'}
            if method == 'GET' and path == '/admin-api/config': return self.config()
            if method == 'GET' and path == '/admin-api/versions': return {'rows': self.versions()[:50]}
            if method == 'POST' and path == '/admin-api/config': return self.publish(payload)
            if method == 'GET' and path == '/admin-api/audit':
                path = self.root / 'audit.jsonl'
                if not path.exists(): return {'rows': []}
                with path.open('rb') as stream:
                    stream.seek(max(0, path.stat().st_size - 32768))
                    lines = stream.read().splitlines()
                rows = []
                for line in lines[-100:]:
                    try: rows.append(json.loads(line))
                    except ValueError: pass
                return {'rows': rows[::-1]}
        if method == 'GET' and path == '/admin-api/overview':
            snap = self.snapshot()
            return {'at': int(time.time()), 'config': self.config(), 'sources': snap['sources'],
                    'taskInterest':self.task_interest(), 'tasks': self.jobs(), 'taskScope': '当前进程中的生成与内容分析任务；工具提取和历史任务不在此列表'}
        if method == 'GET' and path == '/admin-api/hotspots':
            snap = self.snapshot()
            return {'rows': [{'id': row['id'], 'title': row['title'], 'platform': row['platform'], 'rank': row['rank']} for row in snap['rows']]}
        match = re.fullmatch(r'/admin-api/topics/((?:douyin|weibo|toutiao|kuaishou)-[a-f0-9]{20})', path)
        if method in ('GET', 'POST') and match:
            value = self.content(match[1], self.snapshot()['rows'], retry=method == 'POST')
            if method == 'POST':
                with self.lock: self.audit('topic_retry', match[1])
            return value
        raise AdminError(404, '管理接口不存在')

    def creation_dispatch(self, method, path, payload):
        if not self.board: raise AdminError(503, '创作板块尚未接入')
        try:
            scoped = re.fullmatch(r'/admin-api/creation/(dashboard|stats)(?:/(all|formal|trial))?', path)
            if method == 'GET' and scoped and scoped[1] == 'dashboard': return self.board.admin_dashboard(scoped[2] or 'all')
            if method == 'GET' and path == '/admin-api/creation/clusters': return {'rows': self.board.admin_clusters()}
            if method == 'GET' and scoped: return {'rows': self.board.admin_stats(scoped[2] or 'all')}
            match = re.fullmatch(r'/admin-api/creation/reports/(all|new_type|confirm|interview|breakdown|output_text|output_package|metrics|work|rewatch|compose|induce)(?:/(all|formal|trial))?', path)
            if method == 'GET' and match: return {'rows': self.board.admin_reports(None if match[1] == 'all' else match[1], scope=match[2] or 'all')}
            if method == 'POST' and path == '/admin-api/creation/promote':
                if set(payload) != {'planId'} or not isinstance(payload['planId'], str): raise AdminError(400, '方案参数无效')
                value = self.board.admin_promote(payload['planId'])
                with self.lock: self.audit('creation_promote', value['id'])
                return value
        except ValueError as error: raise AdminError(400, str(error)) from None
        raise AdminError(404, '管理接口不存在')

    def platform_dispatch(self, method, path, payload):
        if not self.platform: raise AdminError(503, '配置中心尚未接入')
        try:
            if path == '/admin-api/platform':
                if method == 'GET':
                    value = self.platform.overview()
                    value['usage'] = self.ai.usage_ledger.overview() if self.ai and getattr(self.ai,'usage_ledger',None) else {}
                    value['scenesUsing'] = self.ai.scenes_using() if self.ai else []
                    return value
                if method == 'POST':
                    value, event, ref = self.platform.publish(payload, self.ai.scenes_using() if self.ai else ())
                    with self.lock: self.audit(event, ref)
                    return value
            if method == 'POST' and path == '/admin-api/platform/secret':
                value, event, ref = self.platform.set_secret(payload)
                with self.lock: self.audit(event, ref)
                return value
            if method == 'POST' and path == '/admin-api/platform/probe':
                if not self.ai: raise AdminError(503, '模型网关尚未接入')
                if set(payload) != {'connection'} or not isinstance(payload['connection'], str): raise AdminError(400, '检测请求字段无效')
                try: value = self.ai.probe_connection(payload['connection'])
                except ValueError as e: raise AdminError(400, str(e)) from None
                with self.lock: self.audit('connection_probe', payload['connection'])
                return value
            if method == 'GET' and path == '/admin-api/workflows':
                return self.platform.workflows()
            match = re.fullmatch(r'/admin-api/workflows/([a-z]+)/(draft|validate|publish|rollback)', path)
            if method == 'POST' and match:
                value, event, ref = self.platform.workflow_action(match[1], match[2], payload)
                if event:
                    with self.lock: self.audit(event, ref)
                return value
        except AdminError:
            raise
        except Exception as e:
            if type(e).__name__ == 'PlatformError': raise AdminError(e.status, e.message) from None
            raise
        raise AdminError(404, '管理接口不存在')

    def handle(self, handler):
        path = urlparse(handler.path).path
        if not (path in ('/admin', '/admin/') or path.startswith('/admin-api/')): return False
        status, body, mime = 200, b'', 'application/json; charset=utf-8'
        try:
            origin = handler.headers.get('Origin')
            # No cookie authentication and no CORS. Browser uses an in-memory bearer token.
            expected = os.environ.get('YOUAI_ADMIN_ORIGIN', 'https://youai888.top')
            if origin and origin != expected: raise AdminError(403, '管理请求来源不允许')
            if path in ('/admin', '/admin/'):
                if handler.command != 'GET': raise AdminError(405, '不支持的操作')
                body = Path(__file__).with_name('admin-console.html').read_bytes()
                mime = 'text/html; charset=utf-8'
            else:
                payload = {}
                if handler.command == 'POST':
                    try:
                        length = int(handler.headers.get('Content-Length', '0'))
                        if not 2 <= length <= (16384 if path=='/admin-api/inspiration-ai' or path.startswith(('/admin-api/platform','/admin-api/workflows')) else 8192) or not handler.headers.get('Content-Type', '').startswith('application/json'): raise ValueError()
                        payload = json.loads(handler.rfile.read(length))
                        if not isinstance(payload, dict): raise ValueError()
                    except (ValueError, TypeError): raise AdminError(400, '管理请求格式无效')
                body = json.dumps(self.dispatch(handler.command, path, payload, handler.headers.get('Authorization', ''), handler.client_address[0]), ensure_ascii=False).encode()
        except AdminError as error:
            status, body = error.status, json.dumps({'error': error.message}, ensure_ascii=False).encode()
        except Exception:
            status, body = 503, json.dumps({'error': '管理服务暂时不可用'}, ensure_ascii=False).encode()
        handler.send_response(status)
        handler.send_header('Content-Type', mime)
        handler.send_header('Content-Length', str(len(body)))
        handler.send_header('Cache-Control', 'no-store')
        handler.send_header('X-Content-Type-Options', 'nosniff')
        handler.send_header('Referrer-Policy', 'no-referrer')
        handler.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        handler.end_headers(); handler.wfile.write(body)
        return True
