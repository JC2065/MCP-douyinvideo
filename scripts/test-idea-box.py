import importlib.util, io, json, tempfile, unittest
from pathlib import Path
here = Path(__file__).parent
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, here / file); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
m = load('idea_box', 'idea-box.py'); link = load('link_platform_ideas', 'link-platform.py'); topic = load('topic_chat_ideas', 'topic-chat.py')

class Gateway:
    class Error(Exception): pass
    def __init__(self): self.calls = []
    def scene(self, scene): return {'revision': 'r1'}
    def complete(self, scene, messages, **kw):
        self.calls.append((scene, messages))
        if scene == 'idea_note': return {'choices': [{'message': {'content': '{"note":"适合做成反差剧情","tags":["租房","吐槽","剧情","多余"]}'}}]}
        ctx = json.loads(messages[1]['content'])
        frag = ctx['ideaFragments'][0]['id'] if ctx['ideaFragments'] else 'f' * 32
        return {'choices': [{'message': {'content': json.dumps({'reply': '你之前记的房东那条可以拍', 'topics': [{'title': '奇葩房东', 'angle': '第一视角', 'fragmentId': frag}, {'title': '别的', 'angle': '口播', 'fragmentId': 'nope'}]}, ensure_ascii=False)}}]}

def png():
    from PIL import Image
    data = io.BytesIO(); Image.new('RGB', (40, 30), 'white').save(data, 'PNG'); return data.getvalue()

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.now = [1_800_000_000.0]; self.g = Gateway()
        self.box = m.IdeaBox(self.tmp.name, self.g, ocr=lambda p: [{'text': '房东不退押金'}], asr=lambda p: {'status': 'available', 'text': '下班路上想到一个梗'},
                             detect=link.detect, clock=lambda: self.now[0], background=False)
    def tearDown(self): self.tmp.cleanup()

    def test_text_link_note_and_client_dedupe(self):
        a = self.box.add_text('u1', {'text': '租房遇到奇葩房东', 'clientId': 'local-1'})
        self.assertEqual(a['kind'], 'text'); self.assertEqual(self.box.get('u1', a['id'])['note'], '适合做成反差剧情'); self.assertEqual(self.box.get('u1', a['id'])['tags'], ['租房', '吐槽', '剧情'])
        self.assertEqual(self.box.add_text('u1', {'text': '租房遇到奇葩房东', 'clientId': 'local-1'})['id'], a['id'])
        b = self.box.add_text('u1', {'text': '看这个 https://v.douyin.com/TeEyQHWbxf4/ 好玩'})
        self.assertEqual((b['kind'], b['platform']), ('link', 'douyin')); self.assertTrue(b['url'].startswith('https://v.douyin.com/'))
        self.assertIsNone(self.box.get('u2', a['id'])); self.assertEqual(self.box.list('u2')['total'], 0)
        for bad in ({'text': '  '}, {'text': 'x', 'userId': 'u2'}, 'x'):
            with self.assertRaises(m.IdeaError): self.box.add_text('u1', bad)

    def test_image_ocr_kept_voice_transcribed_and_discarded(self):
        image = self.box.add_media('u1', 'image', png(), 'img-1')
        self.assertEqual(image['text'], '房东不退押金'); self.assertEqual(image['image'], '/idea-media/%s.jpg' % image['id']); self.assertTrue(self.box.media_path(image['id']))
        voice = self.box.add_media('u1', 'voice', b'\x00' * 2000)
        self.assertEqual((voice['kind'], voice['text']), ('voice', '下班路上想到一个梗'))
        self.assertEqual(sorted(p.name for p in Path(self.tmp.name, 'media').iterdir()), [image['id'] + '.jpg'])
        silent = m.IdeaBox(self.tmp.name + '/s', None, asr=lambda p: {'status': 'silent', 'text': ''}, clock=lambda: self.now[0])
        with self.assertRaises(m.IdeaError): silent.add_media('u1', 'voice', b'\x00' * 2000)
        with self.assertRaises(m.IdeaError): self.box.add_media('u1', 'video', b'\x00' * 2000)
        with self.assertRaises(m.IdeaError): self.box.add_media('u1', 'image', b'\x00' * (m.MAX_IMAGE_BYTES + 1))
        self.box.delete('u1', image['id']); self.assertIsNone(self.box.media_path(image['id']))

    def test_status_quota_and_ta_selection(self):
        old = self.box.add_text('u1', {'text': '旧碎片'}); self.now[0] += 5 * 86400; new = self.box.add_text('u1', {'text': '新碎片'})
        picks = self.box.for_ta('u1'); self.assertEqual(picks[0]['id'], new['id']); self.assertEqual(picks[1]['ageDays'], 5)
        self.box.surfaced('u1', [new['id']]); self.assertEqual(self.box.for_ta('u1')[0]['id'], old['id'])
        self.assertEqual(self.box.for_ta('u1', focus=new['id'])[0]['id'], new['id'])
        self.box.set_status('u1', old['id'], 'used'); self.assertNotIn(old['id'], [p['id'] for p in self.box.for_ta('u1')])
        self.assertEqual(self.box.list('u1')['counts'], {'new': 1, 'used': 1, 'archived': 0})
        with self.assertRaises(m.IdeaError): self.box.set_status('u2', new['id'], 'used')
        m.MAX_PER_DAY, saved = 2, m.MAX_PER_DAY
        try:
            self.box.add_text('u1', {'text': 'a'})
            with self.assertRaises(m.IdeaError) as quota: self.box.add_text('u1', {'text': 'b'})
            self.assertEqual(quota.exception.code, 'quota')
        finally: m.MAX_PER_DAY = saved

    def test_ta_opening_builds_on_fragment_and_marks_it(self):
        frag = self.box.add_text('u1', {'text': '租房遇到奇葩房东'})
        chat = topic.TopicChat(Path(self.tmp.name) / 'chat.sqlite', self.g)
        result = chat.chat('u1', {'message': '', 'requestId': 'req-00001', 'opening': True}, {'rows': []}, [], {},
                           fragments=lambda focus: self.box.for_ta('u1', focus=focus), surfaced=lambda ids: self.box.surfaced('u1', ids))
        self.assertEqual(result['topics'][0]['fragmentId'], frag['id']); self.assertEqual(result['topics'][0]['fragmentText'], '租房遇到奇葩房东')
        self.assertNotIn('fragmentId', result['topics'][1])   # an id TA was not given is dropped
        self.assertEqual(self.box.get('u1', frag['id'])['surfaced'], 1)
        context = json.loads(self.g.calls[-1][1][1]['content']); self.assertEqual(context['ideaFragments'][0]['text'], '租房遇到奇葩房东')
        chat.attempts.clear()
        focused = chat.chat('u1', {'message': '聊聊这个', 'requestId': 'req-00002', 'opening': False, 'fragmentId': frag['id']}, {'rows': []}, [], {},
                            fragments=lambda focus: self.box.for_ta('u1', focus=focus))
        self.assertEqual(json.loads(self.g.calls[-1][1][1]['content'])['focusFragmentId'], frag['id']); self.assertTrue(focused['topics'])
        with self.assertRaises(ValueError):
            chat.chat('u1', {'message': 'x', 'requestId': 'req-00003', 'opening': False, 'fragmentId': '../x'}, {'rows': []}, [], {})

if __name__ == '__main__':
    unittest.main()
