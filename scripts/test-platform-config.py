import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load('platform-config')
ai = load('inspiration-ai')
admin = load('admin-console')


class Response:
    def __init__(self, content='OK'):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def read(self, n):
        return json.dumps({'choices': [{'message': {'content': self.content}}], 'usage': {'total_tokens': 5}}).encode()


CUSTOM = {'id': 'deepseek', 'name': 'DeepSeek', 'endpoint': 'https://api.deepseek.example.com/v1/chat/completions', 'defaultModel': 'deepseek-chat'}


class Tests(unittest.TestCase):
    def test_watch_asr_selection(self):
        self.assertEqual(m.WATCH_DEFAULT['asrModel'],'small')
        for model in ('tiny','base','small'):
            m.validate_watch(dict(m.WATCH_DEFAULT,asrModel=model))
        with self.assertRaises(ValueError):m.validate_watch(dict(m.WATCH_DEFAULT,asrModel='large'))
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.legacy = {'qwen-domestic': lambda: {'url': 'https://qwen.example.com/v1/chat', 'key': 'server-file-key-1234', 'model': 'qwen-base', 'keySource': '凭据文件'},
                       'wan-video': lambda: {'url': 'https://wan.example.com/api/v1', 'key': '', 'model': 'wan3.0-video', 'timeoutSeconds': 1800},
                       'reference-parser': lambda: {'url': 'http://dtk-api-1:8000', 'key': ''}}
        self.p = m.Platform(self.root / 'platform', legacy=self.legacy, environment=lambda: [{'name': '微信登录', 'ok': True, 'detail': '已配置'}])
        self.g = ai.Gateway(self.root / 'ai', resolver=self.p)

    def tearDown(self):
        self.tmp.cleanup()

    def publish(self, connections=None, video=None):
        cfg = self.p.config()
        return self.p.publish({'expectedRevision': cfg['revision'], 'connections': connections if connections is not None else cfg['connections'],
                               'video': video or cfg['video']}, self.g.scenes_using())

    def test_secrets_are_write_only_and_override_server_credentials(self):
        before = self.p.overview()
        qwen = next(c for c in before['connections'] if c['id'] == 'qwen-domestic')
        self.assertEqual((qwen['credential']['source'], qwen['credential']['last4']), ('凭据文件', '1234'))
        value, event, ref = self.p.set_secret({'ref': 'qwen-domestic', 'value': 'console-secret-abcd'})
        self.assertEqual((event, ref), ('secret_set', 'qwen-domestic'))
        dumped = json.dumps(value, ensure_ascii=False)
        self.assertNotIn('console-secret', dumped)
        self.assertNotIn('server-file-key', dumped)
        self.assertIn('abcd', dumped)
        self.assertEqual(self.p.resolve('qwen-domestic')['key'], 'console-secret-abcd')
        self.assertEqual(oct(os.stat(self.root / 'platform' / 'secrets.json').st_mode & 0o777), '0o600')
        self.p.set_secret({'ref': 'qwen-domestic', 'clear': True})
        self.assertEqual(self.p.resolve('qwen-domestic')['key'], 'server-file-key-1234')
        for bad in ({'ref': 'qwen-domestic', 'value': 'short'}, {'ref': 'qwen-domestic', 'value': 'has space inside'},
                    {'ref': 'unknown', 'value': 'long-enough-value'}, {'ref': 'qwen-domestic', 'value': 'x' * 20, 'extra': 1},
                    {'ref': 'qwen-domestic', 'clear': 'yes'}):
            with self.assertRaises(m.PlatformError):
                self.p.set_secret(bad)

    def test_custom_connection_routes_ai_scene_and_cannot_be_removed_while_used(self):
        self.publish([CUSTOM])
        self.p.set_secret({'ref': 'deepseek', 'value': 'deepseek-secret-9999'})
        scenes = self.g.config()['scenes']
        scenes['text_works'].update(connection='deepseek', model='deepseek-chat')
        self.g.publish({'expectedRevision': self.g.config()['revision'], 'scenes': scenes})
        calls = []

        def opener(request, timeout):
            calls.append((request.full_url, request.headers['Authorization'], json.loads(request.data)['model']))
            return Response()

        self.g.complete('text_works', [{'role': 'user', 'content': 'hi'}], opener=opener)
        self.assertEqual(calls[0], (CUSTOM['endpoint'], 'Bearer deepseek-secret-9999', 'deepseek-chat'))
        with self.assertRaises(m.PlatformError) as error:
            self.publish([])
        self.assertIn('仍被AI场景使用', error.exception.message)
        scenes['text_works']['connection'] = 'qwen-domestic'
        self.g.publish({'expectedRevision': self.g.config()['revision'], 'scenes': scenes})
        self.publish([])
        self.assertEqual(self.p.secret('deepseek'), '')  # removed connections drop their secret

    def test_connection_validation_and_conflict(self):
        for row in ({**CUSTOM, 'endpoint': 'http://api.example.com/v1'}, {**CUSTOM, 'endpoint': 'https://127.0.0.1/v1'},
                    {**CUSTOM, 'endpoint': 'https://localhost/v1'}, {**CUSTOM, 'endpoint': 'https://user:pw@api.example.com/'},
                    {**CUSTOM, 'id': 'qwen-domestic'}, {**CUSTOM, 'defaultModel': 'bad model'}, {**CUSTOM, 'script': 'x'}):
            with self.assertRaises(m.PlatformError):
                self.publish([row])
        with self.assertRaises(m.PlatformError):
            self.publish([CUSTOM, dict(CUSTOM)])
        old = self.p.config()['revision']
        self.publish([CUSTOM])
        with self.assertRaises(m.PlatformError) as error:
            self.p.publish({'expectedRevision': old, 'connections': [], 'video': self.p.config()['video']})
        self.assertEqual(error.exception.status, 409)

    def test_video_settings_versioned_with_rollback(self):
        with self.assertRaisesRegex(RuntimeError, 'API Key'):
            self.p.video_settings()
        self.p.set_secret({'ref': 'wan-video', 'value': 'wan-secret-0000'})
        first = self.p.config()
        video = dict(first['video'], model='wan3.1-video', resolution='1080P', timeoutSeconds=900)
        self.publish(video=video)
        settings = self.p.video_settings()
        self.assertEqual((settings['model'], settings['resolution'], settings['timeout'], settings['key']), ('wan3.1-video', '1080P', 900, 'wan-secret-0000'))
        for bad in ({**video, 'resolution': '4K'}, {**video, 'timeoutSeconds': 10}, {**video, 'watermark': 'no'}):
            with self.assertRaises(m.PlatformError):
                self.publish(video=bad)
        current = self.p.config()
        self.p.publish({'expectedRevision': current['revision'], 'rollback': first['revision']})
        self.assertEqual(self.p.config()['video'], first['video'])
        self.assertNotEqual(self.p.config()['revision'], first['revision'])

    def test_image_connection_write_only_and_versioned(self):
        overview = self.p.overview()
        row = next(c for c in overview['connections'] if c['id'] == 'image-gen')
        self.assertEqual((row['kind'], row['credential']['configured'], row['defaultModel']), ('image', False, 'wan2.6-t2i'))
        with self.assertRaisesRegex(RuntimeError, '图片生成'):
            self.p.image_settings()
        self.p.set_secret({'ref': 'image-gen', 'value': 'sk-image-secret-2468'})
        self.assertNotIn('sk-image-secret', json.dumps(self.p.overview(), ensure_ascii=False))
        cfg = self.p.config()
        image = {'baseUrl': 'https://dashscope.aliyuncs.com/api/v1', 'model': 'wan2.6-t2i-pro'}
        self.p.publish({'expectedRevision': cfg['revision'], 'connections': [], 'video': cfg['video'], 'image': image})
        self.assertEqual(self.p.image_settings(), {'key': 'sk-image-secret-2468', 'base': 'https://dashscope.aliyuncs.com/api/v1', 'model': 'wan2.6-t2i-pro'})
        # publishing without "image" (older clients) keeps the current image settings
        cfg = self.p.config()
        self.p.publish({'expectedRevision': cfg['revision'], 'connections': [], 'video': cfg['video']})
        self.assertEqual(self.p.config()['image']['model'], 'wan2.6-t2i-pro')
        for bad in ({**image, 'baseUrl': 'http://dashscope.aliyuncs.com/api/v1'}, {**image, 'model': 'bad model'}, {**image, 'extra': 1}):
            cfg = self.p.config()
            with self.assertRaises(m.PlatformError):
                self.p.publish({'expectedRevision': cfg['revision'], 'connections': [], 'video': cfg['video'], 'image': bad})

    def test_config_published_before_image_support_still_loads(self):
        old = {'connections': [], 'video': self.p.config()['video'], 'revision': 'b' * 32, 'publishedAt': 1}
        (self.root / 'platform' / 'config.json').write_text(json.dumps(old))
        self.assertEqual(self.p.config()['image']['model'], 'wan2.6-t2i')
        self.p.publish({'expectedRevision': 'b' * 32, 'connections': [], 'video': old['video']})

    def test_workflow_draft_validate_publish_rollback(self):
        rows = {w['stage']: w for w in self.p.workflows()['workflows']}
        self.assertEqual(set(rows), {'requirements', 'analysis', 'production'})
        production = rows['production']
        steps = copy.deepcopy(production['published']['steps'])
        steps[1]['title'] = '生成口播脚本与拍摄分镜'
        value, event, _ = self.p.workflow_action('production', 'draft', {'expectedRevision': production['revision'], 'steps': steps})
        draft_row = next(w for w in value['workflows'] if w['stage'] == 'production')
        self.assertEqual(draft_row['diff'], ['改名：生成脚本、分镜与素材清单 → 生成口播脚本与拍摄分镜'])
        self.assertEqual(self.p.effective('production')['version'], 'default-v1')  # drafts do not take effect
        value, event, version = self.p.workflow_action('production', 'publish', {'expectedRevision': draft_row['revision']})
        self.assertEqual(event, 'workflow_publish')
        self.assertEqual(self.p.effective('production')['steps'][1]['title'], '生成口播脚本与拍摄分镜')
        with self.assertRaises(m.PlatformError) as error:
            self.p.workflow_action('production', 'publish', {'expectedRevision': draft_row['revision']})
        self.assertEqual(error.exception.status, 409)
        current = next(w for w in value['workflows'] if w['stage'] == 'production')
        self.p.workflow_action('production', 'rollback', {'expectedRevision': current['revision'], 'version': 'default-v1'})
        self.assertEqual(self.p.effective('production')['steps'], m.DEFAULT_FLOWS['production'])
        self.assertNotEqual(self.p.effective('production')['version'], 'default-v1')

    def test_workflow_rules_block_unsafe_or_reordered_publish(self):
        base = copy.deepcopy(m.DEFAULT_FLOWS['production'])
        swapped = copy.deepcopy(base)
        swapped[2], swapped[3] = swapped[3], swapped[2]  # generate before confirm
        self.assertIn('必须先确认分镜与费用，再生成，再验收归档', m.validate_steps('production', swapped))
        missing = [s for s in base if s['id'] != 'archive']
        self.assertTrue(any('必须保留' in e for e in m.validate_steps('production', missing)))
        self.assertTrue(m.validate_steps('requirements', [dict(s) for s in m.DEFAULT_FLOWS['requirements'][:-1]]))
        revision = self.p.workflows()['workflows'][2]['revision']
        # a reordered draft can be saved (shown with errors) but never published
        value, _, _ = self.p.workflow_action('production', 'draft', {'expectedRevision': revision, 'steps': swapped})
        row = value['workflows'][2]
        self.assertTrue(row['errors'])
        with self.assertRaises(m.PlatformError) as error:
            self.p.workflow_action('production', 'publish', {'expectedRevision': row['revision']})
        self.assertIn('未通过校验', error.exception.message)
        for unsafe in ([{**base[0], 'url': 'https://evil'}] + base[1:], [{**base[0], 'capability': 'shell'}] + base[1:], base * 2):
            with self.assertRaises(m.PlatformError):
                self.p.workflow_action('production', 'draft', {'expectedRevision': row['revision'], 'steps': unsafe})

    def test_admin_routes_require_login_and_audit_without_secret(self):
        auth = self.root / 'auth.json'
        auth.write_text(json.dumps(admin.credential('test-password-123456')))
        console = admin.Console(self.root / 'admin', auth, self.root / 'config.json', lambda: {}, lambda: None, lambda: [], self.g, self.p)
        with self.assertRaises(admin.AdminError) as error:
            console.dispatch('GET', '/admin-api/platform', {}, 'Bearer ordinary-wx-user', 'test')
        self.assertEqual(error.exception.status, 401)
        header = 'Bearer ' + console.login({'username': 'admin', 'password': 'test-password-123456'}, 'test')['token']
        overview = console.dispatch('GET', '/admin-api/platform', {}, header, 'test')
        self.assertEqual(overview['scenesUsing'], ['qwen-domestic'])
        console.dispatch('POST', '/admin-api/platform/secret', {'ref': 'wan-video', 'value': 'wan-private-77777'}, header, 'test')
        flows = console.dispatch('GET', '/admin-api/workflows', {}, header, 'test')
        self.assertEqual([b['id'] for b in flows['boards']], ['hotspots', 'tools', 'data', 'requirements', 'analysis', 'production'])
        result = console.dispatch('POST', '/admin-api/workflows/requirements/validate', {'steps': []}, header, 'test')
        self.assertTrue(result['errors'])
        with self.assertRaises(admin.AdminError) as error:
            console.dispatch('POST', '/admin-api/workflows/unknown/publish', {'expectedRevision': 'x'}, header, 'test')
        self.assertEqual(error.exception.status, 404)
        with self.assertRaises(admin.AdminError) as error:
            console.dispatch('POST', '/admin-api/platform/probe', {'connection': 'qwen-domestic', 'url': 'https://evil'}, header, 'test')
        self.assertEqual(error.exception.status, 400)
        audit = (self.root / 'admin' / 'audit.jsonl').read_text(encoding='utf-8')
        self.assertIn('secret_set', audit)
        self.assertNotIn('wan-private', audit)

    def test_connection_probe_reports_without_leaking(self):
        self.publish([CUSTOM])
        result = self.g.probe_connection('deepseek', opener=lambda *a, **k: Response())
        self.assertFalse(result['ok'])  # no key written yet
        self.assertEqual(result['code'], 'not_configured')
        self.p.set_secret({'ref': 'deepseek', 'value': 'deepseek-secret-9999'})
        self.assertTrue(self.g.probe_connection('deepseek', opener=lambda *a, **k: Response())['ok'])
        self.assertNotIn('deepseek-secret', json.dumps(self.g.dashboard()))
        with self.assertRaises(ValueError):
            self.g.probe_connection('not-registered')


if __name__ == '__main__':
    unittest.main()
