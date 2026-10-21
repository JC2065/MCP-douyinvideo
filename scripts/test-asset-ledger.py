import importlib.util, json, tempfile, unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location('ledger', Path(__file__).with_name('asset-ledger.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class Fake:
    def __init__(self, cfg): self.rows = {}; self.uploads = []; self.tables = {}
    def ensure(self, state):
        for key, name, _ in m.TABLES: state[key] = {'id': 'tbl_' + key, 'name': name}
        return state
    def upsert(self, table_id, key, fields): self.rows.setdefault(table_id, {})[fields[key]] = {**self.rows.get(table_id, {}).get(fields[key], {}), **fields}
    def attach(self, path, name, kind): self.uploads.append((Path(path).name, kind)); return 'tok_' + Path(path).name
    def ensure_plan(self, state, plan_id, name, labels):
        state.setdefault('plans', {})[plan_id] = {'id': 'tbl_plan_' + plan_id, 'name': '拆解库·' + name, 'fields': labels}; self.plan_labels = labels; return 'tbl_plan_' + plan_id

def ledger(root, fake):
    cfg = Path(root) / 'cfg.json'; cfg.write_text(json.dumps({'management': {'appId': 'cli_x', 'appSecret': 'x' * 10, 'baseToken': 'b'}}))
    return m.Ledger(Path(root) / 'l', cfg, Path(root) / 'state.json', ffmpeg=None, client_factory=lambda c: fake)

class Tests(unittest.TestCase):
    def test_chain_reaches_every_table_and_merges(self):
        with tempfile.TemporaryDirectory() as root:
            fake = Fake({}); led = ledger(root, fake); sha = 'a' * 64
            led.user('u1', {'nickname': '小明', 'phoneMasked': '+86 138****0000'}, phone='+86 13800000000')
            ref = {'title': '女生唱歌', 'description': '女生唱歌 #翻唱', 'resolvedUrl': 'https://v.douyin.com/x/', 'asset': {'sha256': sha, 'storagePath': '/none', 'media': {'durationSeconds': 12}},
                   'source': {'contentId': '123', 'hashtags': ['翻唱'], 'author': {'nickname': '歌手', 'followerCount': 900}, 'stats': {'digg_count': 50, 'comment_count': 3}, 'createdAt': '2026-10-01T00:00:00Z'}}
            led.source('u1', ref, {'overview': '女生在KTV唱歌'}); led.source('u2', ref)
            led.card(sha, {'understanding': {'status': 'ready', 'overview': '概述', 'type': '翻唱', 'tags': ['KTV'], 'timeline': [{'start': 0, 'end': 3, 'what': '开唱'}]}, 'audio': {'transcript': {'text': '歌词'}}}, '女生唱歌')
            session = {'id': 's1', 'asset': sha, 'breakdown': {'planName': '通用拆解', 'insight': {'why': '评论驱动', 'difficulty': {'score': 2, 'reason': '单人'}},
                       'fields': [{'key': 'learnable', 'label': '能学的', 'value': [{'item': '反差 开场', 'level': '高', 'how': '前3秒'}]}, {'key': 'hook', 'label': '钩子', 'value': '提问'}]}}
            led.breakdown('u1', session, '女生唱歌'); led.breakdown('u2', {**session, 'id': 's2', 'asset': 'b' * 64}, '另一条')
            led.work('u1', 'w1', '文字作品', session, '标题', '正文'); led.metric('u1', 'w1', 20380, 'public', {'likes': 9})
            while led.tick(): pass
            rows = fake.rows
            self.assertEqual(rows['tbl_users']['u1']['手机号'], '+86 13800000000')
            src = rows['tbl_sources'][sha]; self.assertEqual(src['提交次数'], 2); self.assertEqual(src['提交用户'], 'u1, u2'); self.assertEqual(src['大致内容'], '女生在KTV唱歌')
            self.assertEqual(src['链接']['link'], 'https://v.douyin.com/x/'); self.assertTrue(src['发布时间'] > 0)
            self.assertIn('0–3秒 开唱', rows['tbl_cards'][sha]['逐段画面'])
            self.assertEqual(rows['tbl_breakdowns']['s1']['最该学'], '反差 开场'); self.assertIn('【钩子】', rows['tbl_breakdowns']['s1']['全部字段'])
            method = list(rows['tbl_methods'].values())[0]; self.assertEqual(method['方法'], '反差开场'); self.assertEqual(method['出现次数'], 2, '同一方法跨视频合并计数')
            self.assertEqual(rows['tbl_works']['w1']['来源拆解ID'], 's1'); self.assertEqual(rows['tbl_metrics']['w1|20380|public']['点赞'], 9)
            self.assertNotIn('运营备注', src, '人工列不被系统写入')
    def test_failure_backs_off_and_retries(self):
        with tempfile.TemporaryDirectory() as root:
            class Broken(Fake):
                def upsert(self, *a): raise RuntimeError('飞书接口失败 code=1254')
            fake = Broken({}); led = ledger(root, fake); led.user('u1', {})
            self.assertEqual(led.tick(), 0); st = led.status(); self.assertEqual(st['failing'][0]['attempts'], 1); self.assertIn('1254', st['failing'][0]['error'])
            self.assertEqual(led.tick(), 0, '退避期内不重试')
    def test_media_four_shots_and_low_res(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            def runner(cmd, **k):
                calls.append(cmd); Path(cmd[-1]).write_bytes(b'x'); return type('R', (), {'returncode': 0})()
            video = Path(root) / 'v.mp4'; video.write_bytes(b'v')
            fake = Fake({}); led = ledger(root, fake); led.ffmpeg = 'ffmpeg'; led.runner = runner
            shots, low = led.prepare_media('c' * 64, {'path': str(video), 'cover': '', 'duration': 30})
            self.assertEqual(len(shots), 4, '无封面时取开头 + 中段两张 + 结尾'); self.assertTrue(low and low.name == 'low.mp4')
            self.assertTrue(any('-crf' in c for c in calls))

class PlanTables(unittest.TestCase):
    def test_custom_plan_gets_its_own_table_builtin_does_not(self):
        with tempfile.TemporaryDirectory() as root:
            fake = Fake({}); led = ledger(root, fake)
            fields = [{'key': 'twist', 'label': '反转点', 'value': [{'start': 4, 'end': 6, 'text': '女生反将一军'}]}, {'key': 'persona', 'label': '人设', 'value': '傲娇'}]
            led.breakdown('u1', {'id': 's1', 'asset': 'a' * 64, 'breakdown': {'planId': 'p123', 'planName': '情侣反转', 'version': 2, 'insight': {'why': '反转'}, 'fields': fields}}, '情侣')
            led.breakdown('u1', {'id': 's2', 'asset': 'b' * 64, 'breakdown': {'planId': 'builtin-general', 'planName': '通用拆解', 'insight': {}, 'fields': fields}}, '通用')
            while led.tick(): pass
            self.assertIn('tbl_plan_p123', fake.rows); self.assertNotIn('tbl_plan_builtin-general', fake.rows, '内置方案不单独建表')
            row = fake.rows['tbl_plan_p123']['s1']; self.assertEqual(row['反转点'], '4–6秒 女生反将一军'); self.assertEqual(row['人设'], '傲娇'); self.assertEqual(row['方案版本'], 2)
            self.assertEqual(fake.plan_labels, ['反转点', '人设']); self.assertIn('s1', fake.rows['tbl_breakdowns'], '总拆解库照常写')
            led.breakdown('u1', {'id': 's3', 'asset': 'c' * 64, 'adjustments': [{'message': '多看台词节奏'}], 'breakdown': {'planId': 'once-1', 'planName': '通用拆解（仅本次）', 'insight': {}, 'fields': fields}}, 'x')
            led.breakdown('u1', {'id': 's4', 'asset': 'd' * 64, 'breakdown': {'planId': 'once-2', 'planName': '通用拆解（仅本次）', 'insight': {}, 'fields': fields}}, 'y')
            while led.tick(): pass
            once = fake.rows['tbl_plan_once']; self.assertEqual(set(once), {'s3', 's4'}, '仅本次调整统一进一张表'); self.assertEqual(once['s3']['调整说明'], '多看台词节奏')

class Token(unittest.TestCase):
    def test_client_token_is_stable_uuid4(self):
        import uuid
        sent = []
        class C(m.FeishuBase):
            def call(self, method, path, body=None, **k):
                sent.append(path)
                return {'items': []} if path.endswith('/search') else {'record': {'record_id': 'r'}}
        c = C({'baseToken': 'b'}); c.upsert('t', 'ID', {'ID': 'x'}); c.upsert('t', 'ID', {'ID': 'x'})
        token = sent[1].split('client_token=')[1]; self.assertEqual(uuid.UUID(token).version, 4); self.assertEqual(sent[1], sent[3], '同一条记录重试用同一个 token')

if __name__ == '__main__':
    unittest.main()
