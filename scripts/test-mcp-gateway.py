import hashlib, importlib.util, io, json, tempfile, unittest
from pathlib import Path
from urllib.error import HTTPError, URLError

spec = importlib.util.spec_from_file_location('mcp_gateway', Path(__file__).with_name('mcp-gateway.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class Response(io.BytesIO):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data); self.status = status; self.headers = headers or {}


def call(name, ident=1):
    return {'jsonrpc': '2.0', 'id': ident, 'method': 'tools/call', 'params': {'name': name, 'arguments': {}}}


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); self.now = [1_800_000_000.0]; self.sent = []
        def opener(request, timeout=0):
            self.sent.append(request)
            return Response(b'event: message\ndata: {"ok":1}\n\n', 200, {'Content-Type': 'text/event-stream', 'Mcp-Session-Id': 's1', 'Set-Cookie': 'x'})
        self.g = m.Gateway(self.root, 'http://dtk-api-1:8000/mcp/', opener, clock=lambda: self.now[0])
    def tearDown(self): self.tmp.cleanup()

    def configure(self, **extra):
        (self.root / 'config.json').write_text(json.dumps({'tokenSha256': hashlib.sha256(b'client-token').hexdigest(), 'dtkKey': 'dtk_abc_secret', **extra}))

    def test_token_is_checked_against_the_stored_hash(self):
        self.assertFalse(self.g.authorized('Bearer client-token'), '未配置时一律拒绝')
        self.configure()
        self.assertTrue(self.g.authorized('Bearer client-token'))
        for bad in ('Bearer other', 'client-token', '', None, 'Bearer '):
            self.assertFalse(self.g.authorized(bad))
        (self.root / 'config.json').write_text('{"tokenSha256": "short", "dtkKey": "k"}'); self.now[0] += 1
        import os; os.utime(self.root / 'config.json', (self.now[0], self.now[0]))
        self.assertFalse(self.g.authorized('Bearer client-token'), '配置不合法时拒绝')

    def test_daily_cap_counts_platform_calls_only_and_resets_at_beijing_midnight(self):
        self.configure(dailyLimit=3)
        body = json.dumps([call('parse_url', 1), call('pool_status', 2), {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/list'}, call('list_comments', 4)]).encode()
        self.assertEqual([x['id'] for x in self.g.billable(body)], [1, 4])
        self.assertEqual(self.g.billable(b'not json'), [])
        self.assertTrue(self.g.charge(2)); self.assertTrue(self.g.charge(1)); self.assertFalse(self.g.charge(1)); self.assertEqual(self.g.used(), 3)
        self.assertTrue(self.g.charge(0), '不计费的请求总能通过')
        self.now[0] += 86400; self.assertEqual(self.g.used(), 0); self.assertTrue(self.g.charge(1))
        self.assertEqual(m.Gateway(self.root, 'x').limit(), 3)
        (self.root / 'config.json').unlink(); self.assertEqual(m.Gateway(self.root, 'x').limit(), 50, '默认每天 50 次')

    def test_refusal_answers_each_request_as_a_readable_tool_error(self):
        self.configure(dailyLimit=50)
        one = json.loads(self.g.refusal(json.dumps(call('parse_url', 7)).encode()))
        self.assertEqual(one['id'], 7); self.assertTrue(one['result']['isError']); self.assertIn('每天 50 次', one['result']['content'][0]['text'])
        many = json.loads(self.g.refusal(json.dumps([call('parse_url', 1), call('get_video', 2)]).encode()))
        self.assertEqual([r['id'] for r in many], [1, 2])
        self.assertEqual(self.g.refusal(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}).encode()), b'')

    def test_relay_injects_the_dtk_key_and_streams_back_only_safe_headers(self):
        self.configure()
        status, headers, chunks = self.g.relay('POST', {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream', 'Mcp-Session-Id': 's1', 'Authorization': 'Bearer client-token', 'Cookie': 'c'}, b'{}')
        request = self.sent[0]
        self.assertEqual(request.full_url, 'http://dtk-api-1:8000/mcp/'); self.assertEqual(request.get_method(), 'POST')
        sent = {k.lower(): v for k, v in request.header_items()}
        self.assertEqual(sent['x-api-key'], 'dtk_abc_secret'); self.assertEqual(sent['mcp-session-id'], 's1')
        self.assertNotIn('authorization', sent, '客户端令牌不外传'); self.assertNotIn('cookie', sent)
        self.assertEqual(status, 200); self.assertEqual(dict(headers), {'Content-Type': 'text/event-stream', 'Mcp-Session-Id': 's1'})
        self.assertEqual(b''.join(chunks), b'event: message\ndata: {"ok":1}\n\n')
        self.g.relay('GET', {'Accept': 'text/event-stream'}); self.assertIsNone(self.sent[1].data); self.assertEqual(self.sent[1].get_method(), 'GET')

    def test_upstream_errors_pass_through_or_become_502(self):
        self.configure()
        def refused(request, timeout=0): raise HTTPError(request.full_url, 404, 'gone', {'Content-Type': 'application/json'}, io.BytesIO(b'{"error":"session"}'))
        self.g.opener = refused
        status, headers, chunks = self.g.relay('POST', {}, b'{}'); self.assertEqual(status, 404); self.assertEqual(b''.join(chunks), b'{"error":"session"}')
        def down(request, timeout=0): raise URLError('down')
        self.g.opener = down
        status, _, chunks = self.g.relay('POST', {}, b'{}'); self.assertEqual(status, 502); self.assertIn('上游', json.loads(b''.join(chunks))['error'])

    def test_local_tool_is_listed_and_answered_here(self):
        self.configure()
        seen = []
        def handler(args):
            seen.append(args)
            if args.get('url') == 'bad': raise m.ToolError('链接无法解析')
            if args.get('url') == 'boom': raise RuntimeError('secret detail')
            return {'downloadUrl': 'https://x/mcp/files/a.mp4'}
        self.g.register({'name': 'download_video', 'inputSchema': {'type': 'object'}}, handler)
        self.assertTrue(self.g.is_list(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}).encode()))
        self.assertFalse(self.g.is_list(json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}]).encode()))
        sse = b'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"parse_url"}]}}\n\n'
        out = self.g.augment_list(sse, 'text/event-stream').decode()
        self.assertTrue(out.startswith('event: message\ndata: ')); self.assertTrue(out.endswith('\n\n'))
        names = [t['name'] for t in json.loads(out.split('data: ')[1].split('\n')[0])['result']['tools']]
        self.assertEqual(names, ['parse_url', 'download_video'])
        plain = json.loads(self.g.augment_list(b'{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"download_video"}]}}', 'application/json'))
        self.assertEqual(len(plain['result']['tools']), 1, '同名不重复添加')
        self.assertEqual(self.g.augment_list(b'not json', 'application/json'), b'not json')
        self.assertIsNone(self.g.local_call(json.dumps(call('parse_url')).encode()), 'dtk 的工具照常转发')
        ok = json.loads(self.g.local_call(json.dumps({**call('download_video', 9), 'params': {'name': 'download_video', 'arguments': {'url': 'https://v.douyin.com/x/'}}}).encode()))
        self.assertEqual(ok['id'], 9); self.assertFalse(ok['result']['isError']); self.assertEqual(ok['result']['structuredContent']['downloadUrl'], 'https://x/mcp/files/a.mp4')
        self.assertEqual(seen[-1], {'url': 'https://v.douyin.com/x/'})
        bad = json.loads(self.g.local_call(json.dumps({**call('download_video'), 'params': {'name': 'download_video', 'arguments': {'url': 'bad'}}}).encode()))
        self.assertTrue(bad['result']['isError']); self.assertEqual(bad['result']['content'][0]['text'], '链接无法解析')
        boom = json.loads(self.g.local_call(json.dumps({**call('download_video'), 'params': {'name': 'download_video', 'arguments': {'url': 'boom'}}}).encode()))
        self.assertNotIn('secret', boom['result']['content'][0]['text'], '内部异常细节不外泄')

    def test_file_links_are_signed_and_expire(self):
        sha = 'a' * 64
        self.configure()
        link, expires = self.g.file_link('https://youai888.top/youai/', sha)
        self.assertTrue(link.startswith('https://youai888.top/youai/mcp/files/' + sha + '.mp4?e=%d&s=' % expires)); self.assertEqual(expires, int(self.now[0]) + 1800)
        signature = link.split('&s=')[1]
        self.assertTrue(self.g.file_allowed(sha, str(expires), signature))
        self.assertFalse(self.g.file_allowed('b' * 64, str(expires), signature)); self.assertFalse(self.g.file_allowed(sha, str(expires + 1), signature))
        self.assertFalse(self.g.file_allowed('../x', str(expires), signature)); self.assertFalse(self.g.file_allowed(sha, 'abc', signature))
        self.now[0] += 1801; self.assertFalse(self.g.file_allowed(sha, str(expires), signature), '30 分钟后过期')
        (self.root / 'config.json').unlink(); self.now[0] -= 1801
        self.assertFalse(self.g.file_allowed(sha, str(expires), signature), '配置删除后链接全部失效')



if __name__ == '__main__':
    unittest.main()
