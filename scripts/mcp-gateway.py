"""Remote MCP entry for outside AI clients (Claude, Codex, Cursor ...).

The clients talk to https://youai888.top/youai/mcp with an access token of their own. This gateway checks
that token, keeps a daily cap on the calls that spend the parser's identity pool, and relays the
Streamable-HTTP exchange to dtk's built-in MCP server using a dtk API key reserved for MCP. The dtk
address and that key never leave the server, and the mini program's own parser key and quota are
untouched.

Settings live in <root>/config.json (outside Git, mode 600):
  {"tokenSha256": "<sha256 hex of the client access token>", "dtkKey": "dtk_...", "dailyLimit": 50}
"""
import datetime
import hashlib
import re
import hmac
import json
import sqlite3
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Read-only status calls that do not touch the platform; everything else counts against the daily cap.
FREE_TOOLS = {'pool_status', 'get_task_result'}
FORWARD_HEADERS = ('Content-Type', 'Accept', 'Mcp-Session-Id', 'MCP-Protocol-Version', 'Last-Event-ID')
RETURN_HEADERS = ('Content-Type', 'Mcp-Session-Id', 'MCP-Protocol-Version', 'Cache-Control')
MAX_BODY = 64 * 1024
FILE_TTL = 1800


class ToolError(Exception):
    """A local tool failed in a way the agent should read (bad link, download refused ...)."""

CHINA = datetime.timezone(datetime.timedelta(hours=8))


class Gateway:
    def __init__(self, root, upstream, opener=urlopen, clock=time.time):
        self.root = Path(root)
        self.upstream = upstream  # dtk mounts MCP at /mcp/ and redirects /mcp, so keep the slash as given
        self.opener = opener
        self.clock = clock
        self.lock = threading.Lock()
        self._config = (None, None)
        self.local = {}

    def register(self, definition, handler):
        """A tool answered here instead of by dtk; it is appended to dtk's tools/list."""
        self.local[definition['name']] = (definition, handler)

    # ---------- settings ----------
    def config(self):
        path = self.root / 'config.json'
        try:
            stamp = path.stat().st_mtime
        except OSError:
            return None
        if self._config[0] != stamp:
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                data = None
            if not (isinstance(data, dict) and isinstance(data.get('tokenSha256'), str) and len(data['tokenSha256']) == 64 and isinstance(data.get('dtkKey'), str) and data['dtkKey']):
                data = None
            self._config = (stamp, data)
        return self._config[1]

    def limit(self):
        cfg = self.config() or {}
        value = cfg.get('dailyLimit')
        return value if isinstance(value, int) and value >= 0 else 50

    def authorized(self, header):
        cfg = self.config()
        if not cfg or not isinstance(header, str) or not header.startswith('Bearer '):
            return False
        presented = hashlib.sha256(header[7:].strip().encode()).hexdigest()
        return hmac.compare_digest(presented, cfg['tokenSha256'])

    # ---------- daily cap ----------
    def day(self):
        return datetime.datetime.fromtimestamp(self.clock(), CHINA).strftime('%Y-%m-%d')

    def _db(self):
        self.root.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.root / 'usage.sqlite', timeout=5)
        db.execute('CREATE TABLE IF NOT EXISTS usage(day TEXT PRIMARY KEY, calls INTEGER NOT NULL)')
        return db

    def used(self):
        with self.lock, self._db() as db:
            row = db.execute('SELECT calls FROM usage WHERE day=?', (self.day(),)).fetchone()
        return row[0] if row else 0

    def charge(self, count):
        """Reserve `count` calls for today; False (and nothing reserved) when that would pass the cap."""
        if count <= 0:
            return True
        with self.lock, self._db() as db:
            day = self.day()
            row = db.execute('SELECT calls FROM usage WHERE day=?', (day,)).fetchone()
            used = row[0] if row else 0
            if used + count > self.limit():
                return False
            db.execute('INSERT INTO usage VALUES (?,?) ON CONFLICT(day) DO UPDATE SET calls=excluded.calls', (day, used + count))
        return True

    @staticmethod
    def messages(body):
        try:
            data = json.loads(body.decode('utf-8')) if body else None
        except (UnicodeDecodeError, ValueError):
            return []
        items = data if isinstance(data, list) else [data]
        return [m for m in items if isinstance(m, dict)]

    @classmethod
    def billable(cls, body):
        return [m for m in cls.messages(body) if m.get('method') == 'tools/call'
                and str((m.get('params') or {}).get('name') if isinstance(m.get('params'), dict) else '') not in FREE_TOOLS]

    def refusal(self, body):
        """Answer every request in the body with a tool error the agent can read, instead of relaying it."""
        note = '今日 MCP 解析额度已用完（每天 %d 次，北京时间零点重置）。pool_status 仍可调用。' % self.limit()
        replies = [{'jsonrpc': '2.0', 'id': m.get('id'), 'result': {'content': [{'type': 'text', 'text': note}], 'isError': True}}
                   for m in self.messages(body) if 'id' in m]
        if not replies:
            return b''
        data = replies if isinstance(json.loads(body.decode('utf-8')), list) else replies[0]
        return json.dumps(data, ensure_ascii=False).encode()

    # ---------- local tools ----------
    @staticmethod
    def single(body):
        try:
            data = json.loads(body.decode('utf-8')) if body else None
        except (UnicodeDecodeError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def is_list(self, body):
        message = self.single(body)
        return bool(self.local) and bool(message) and message.get('method') == 'tools/list'

    def local_call(self, body):
        """Run a local tool when the body is one tools/call for it; None means relay to dtk as usual."""
        message = self.single(body)
        params = message.get('params') if message and isinstance(message.get('params'), dict) else {}
        if not message or message.get('method') != 'tools/call' or params.get('name') not in self.local:
            return None
        handler = self.local[params['name']][1]
        arguments = params.get('arguments') if isinstance(params.get('arguments'), dict) else {}
        try:
            data = handler(arguments)
            result = {'content': [{'type': 'text', 'text': json.dumps(data, ensure_ascii=False, indent=1)}], 'structuredContent': data, 'isError': False}
        except ToolError as error:
            result = {'content': [{'type': 'text', 'text': str(error)}], 'isError': True}
        except Exception:
            result = {'content': [{'type': 'text', 'text': '服务器处理失败，请稍后重试'}], 'isError': True}
        return json.dumps({'jsonrpc': '2.0', 'id': message.get('id'), 'result': result}, ensure_ascii=False).encode()

    def augment_list(self, data, content_type=''):
        """Append the local tools to dtk's tools/list answer, in whatever framing (JSON or SSE) it came."""
        def extend(text):
            try:
                reply = json.loads(text)
            except ValueError:
                return text
            tools = reply.get('result', {}).get('tools') if isinstance(reply, dict) and isinstance(reply.get('result'), dict) else None
            if not isinstance(tools, list):
                return text
            names = {t.get('name') for t in tools if isinstance(t, dict)}
            tools.extend(d for d, _ in self.local.values() if d['name'] not in names)
            return json.dumps(reply, ensure_ascii=False)
        body = data.decode('utf-8', 'replace')
        if 'text/event-stream' in (content_type or ''):
            lines = [('data: ' + extend(l[6:])) if l.startswith('data: ') else l for l in body.split('\n')]
            return '\n'.join(lines).encode()
        return extend(body).encode()

    # ---------- signed file links ----------
    def _file_key(self):
        cfg = self.config() or {}
        return hmac.new(cfg.get('dtkKey', '').encode(), b'youai-mcp-files', hashlib.sha256).digest() if cfg.get('dtkKey') else b''

    def file_link(self, base, sha, ttl=FILE_TTL):
        expires = int(self.clock()) + ttl
        signature = hmac.new(self._file_key(), ('%s:%d' % (sha, expires)).encode(), hashlib.sha256).hexdigest()
        return '%s/mcp/files/%s.mp4?e=%d&s=%s' % (base.rstrip('/'), sha, expires, signature), expires

    def file_allowed(self, sha, expires, signature):
        key = self._file_key()
        if not key or not re.fullmatch('[a-f0-9]{64}', str(sha)) or not re.fullmatch('[0-9]{1,12}', str(expires)) or int(expires) < self.clock():
            return False
        expected = hmac.new(key, ('%s:%s' % (sha, expires)).encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, str(signature))

    # ---------- relay ----------
    def relay(self, method, headers, body=b''):
        """Send the request on to dtk; returns (status, [(header, value)], chunk iterator)."""
        cfg = self.config() or {}
        sent = {name: headers[name] for name in FORWARD_HEADERS if headers.get(name)}
        sent['X-API-Key'] = cfg.get('dtkKey', '')
        request = Request(self.upstream, data=body if method == 'POST' else None, headers=sent, method=method)
        try:
            response = self.opener(request, timeout=300)
        except HTTPError as error:
            response = error
        except (URLError, OSError):
            data = json.dumps({'error': 'MCP 上游暂时不可用，请稍后重试'}, ensure_ascii=False).encode()
            return 502, [('Content-Type', 'application/json; charset=utf-8')], iter([data])
        status = getattr(response, 'status', None) or getattr(response, 'code', 502)
        back = [(name, response.headers.get(name)) for name in RETURN_HEADERS if response.headers.get(name)]

        def chunks():
            try:
                while True:
                    # read1 hands over what has arrived, so server-sent events reach the client as they come.
                    reader = getattr(response, 'read1', None) or response.read
                    chunk = reader(16384)
                    if not chunk:
                        break
                    yield chunk
            finally:
                try:
                    response.close()
                except Exception:
                    pass
        return status, back, chunks()
