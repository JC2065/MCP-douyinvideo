import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


up = load('user-profile')
plat = load('platform-config')
ai = load('inspiration-ai')
chat = load('topic-chat')
DAY = 86400


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def read(self, n):
        content = json.dumps({'reply': '好的', 'topics': [{'title': '早餐挑战', 'angle': '一周不重样'}]}, ensure_ascii=False)
        return json.dumps({'choices': [{'message': {'content': content}}]}).encode()


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.settings = json.loads(json.dumps(up.DEFAULTS))
        self.runs = []
        self.p = up.Profiles(self.root / 'profile.sqlite', settings=lambda: self.settings, owned_runs=lambda user: self.runs)

    def tearDown(self):
        self.tmp.cleanup()

    def feedback(self, kind, title, angle='', user='u1', at=None):
        return self.p.signal(user, {'kind': kind, 'title': title, 'angle': angle}, now=at)

    def values(self, facet, user='u1', now=None):
        return [r['value'] for r in self.p.facets(user, now) if r['facet'] == facet]

    def test_needs_repeated_evidence_before_learning(self):
        self.feedback('up', '减脂早餐', '')
        self.feedback('adopt', '减脂早餐 做法', '')
        self.assertNotIn('减脂早餐', self.values('interest'))
        self.feedback('up', '减脂早餐 合集', '')
        self.assertIn('减脂早餐', self.values('interest'))
        self.assertIn('感兴趣的方向：减脂早餐', self.p.text('u1'))

    def test_repeated_tap_on_same_topic_counts_once(self):
        for _ in range(5):
            self.feedback('up', '露营装备', '')
        self.assertEqual(self.values('interest'), [])

    def test_recent_signals_outweigh_old_ones(self):
        now = time.time()
        for i in range(3):
            self.feedback('up', '城市骑行%d' % i, '', at=now - 120 * DAY)
            self.feedback('up', '咖啡拉花%d' % i, '', at=now - DAY)
        ranked = self.values('interest', now=now)
        self.assertLess(ranked.index('咖啡拉花'), ranked.index('城市骑行'))

    def test_dislike_and_conflict_keep_net_side(self):
        for i in range(3):
            self.feedback('down', '恐怖故事%d' % i, '')
        self.assertIn('恐怖故事', self.values('avoid'))
        for i in range(4):
            self.feedback('up', '恐怖故事 新%d' % i, '')
        self.assertNotIn('恐怖故事', self.values('avoid'))

    def test_user_controls_remove_disable_clear(self):
        for i in range(3):
            self.feedback('up', '旅行攻略%d' % i, '')
        self.p.remove('u1', {'facet': 'interest', 'value': '旅行攻略'})
        self.assertNotIn('旅行攻略', self.values('interest'))
        for i in range(3):
            self.feedback('up', '手冲咖啡%d' % i, '')
        self.p.set_enabled('u1', {'enabled': False})
        self.assertEqual(self.p.text('u1'), '')
        self.assertFalse(self.p.view('u1')['enabled'])
        self.p.set_enabled('u1', {'enabled': True})
        self.assertTrue(self.p.text('u1'))
        self.p.clear('u1')
        self.assertEqual(self.p.facets('u1'), [])
        self.assertEqual(self.values('interest', user='u2'), [])  # other accounts unaffected and isolated

    def test_sensitive_terms_never_become_profile_items(self):
        for i in range(4):
            self.feedback('up', '抑郁症日记%d 银行贷款 13800138000' % i, '')
        joined = json.dumps(self.p.facets('u1'), ensure_ascii=False)
        for word in ('抑郁', '贷款', '13800138000'):
            self.assertNotIn(word, joined)

    def test_saved_works_teach_audience_and_tone(self):
        now = time.time()
        self.runs = [{'audience': '上班族', 'tone': '轻松幽默', 'goal': '吸引看完', 'at': now - i * DAY} for i in range(3)]
        self.assertEqual(self.values('audience'), ['上班族'])
        self.assertIn('常用语气：轻松幽默', self.p.text('u1'))

    def test_length_cap_and_global_switch(self):
        self.settings['maxProfileChars'] = 60
        for i in range(30):
            self.feedback('up', '主题词%02d一号 主题词%02d二号' % (i, i), '')
        for i in range(3):
            for j in range(10):
                self.feedback('adopt', '长期方向%d' % j, '变体%d' % i)
        self.assertLessEqual(len(self.p.text('u1')), 60)
        self.settings['enabled'] = False
        self.assertEqual(self.p.text('u1'), '')

    def test_settings_validation(self):
        up.validate_settings(up.DEFAULTS)
        for key, bad in (('minEvidence', 0), ('halfLifeDays', 0), ('maxProfileChars', 5000), ('historyTurns', 20), ('exploreCount', 3), ('enabled', 'yes')):
            value = json.loads(json.dumps(up.DEFAULTS))
            value[key] = bad
            with self.assertRaises(ValueError):
                up.validate_settings(value)
        with self.assertRaises(ValueError):
            self.p.signal('u1', {'kind': 'like', 'title': 'x', 'angle': ''})

    def test_profile_survives_switching_model_connection(self):
        # Learn something, then switch the chat scene to another provider: the same profile is sent.
        for i in range(3):
            self.feedback('up', '家常快手菜%d' % i, '')
        platform = plat.Platform(self.root / 'platform', legacy={'qwen-domestic': lambda: {'url': 'https://qwen.example.com/v1/chat', 'key': 'qwen-key-1234', 'model': 'qwen-x'}})
        gateway = ai.Gateway(self.root / 'ai', resolver=platform)
        cfg = platform.config()
        platform.publish({'expectedRevision': cfg['revision'], 'connections': [{'id': 'deepseek', 'name': 'DeepSeek', 'endpoint': 'https://api.deepseek.example.com/v1/chat', 'defaultModel': 'deepseek-chat'}], 'video': cfg['video']})
        platform.set_secret({'ref': 'deepseek', 'value': 'deepseek-key-9999'})
        topics = chat.TopicChat(self.root / 'chat.sqlite', gateway)
        sent = []

        def opener(request, timeout):
            sent.append((request.full_url, json.loads(json.loads(request.data)['messages'][1]['content'])))
            return Response()

        payload = lambda rid: {'message': '今天拍什么', 'requestId': rid, 'opening': False}
        profile = self.p.text('u1')
        topics.chat('u1', payload('request-0001'), {'rows': []}, [], {}, opener=opener, profile=profile, settings=platform.personalization())
        scenes = gateway.config()['scenes']
        scenes['ta_chat'].update(connection='deepseek', model='deepseek-chat')
        gateway.publish({'expectedRevision': gateway.config()['revision'], 'scenes': scenes})
        time.sleep(3.1)  # topic chat rate limit between turns
        topics.chat('u1', payload('request-0002'), {'rows': []}, [], {}, opener=opener, profile=self.p.text('u1'), settings=platform.personalization())
        self.assertEqual([url for url, _ in sent], ['https://qwen.example.com/v1/chat', 'https://api.deepseek.example.com/v1/chat'])
        self.assertTrue(profile)
        self.assertEqual(sent[0][1]['learnedProfile'], sent[1][1]['learnedProfile'])
        self.assertIn('家常快手菜', sent[1][1]['learnedProfile'])
        self.assertTrue(sent[1][1]['exploreRequirement'])

    def test_platform_personalization_versioned(self):
        platform = plat.Platform(self.root / 'platform2')
        cfg = platform.config()
        self.assertEqual(platform.personalization(), up.DEFAULTS)
        changed = dict(cfg['personalization'], minEvidence=5, exploreCount=0)
        platform.publish({'expectedRevision': cfg['revision'], 'connections': [], 'video': cfg['video'], 'personalization': changed})
        self.assertEqual(platform.personalization()['minEvidence'], 5)
        bad = dict(changed, halfLifeDays=0)
        with self.assertRaises(plat.PlatformError):
            platform.publish({'expectedRevision': platform.config()['revision'], 'connections': [], 'video': cfg['video'], 'personalization': bad})
        platform.publish({'expectedRevision': platform.config()['revision'], 'rollback': cfg['revision']})
        self.assertEqual(platform.personalization()['minEvidence'], 3)


if __name__ == '__main__':
    unittest.main()
