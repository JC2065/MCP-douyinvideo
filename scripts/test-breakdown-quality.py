"""Breakdown quality fixes (2026-10-18 five-video review): author-text layers, post data and account context, keyText, titles, package reference, 图文."""
import importlib.util, io, json, tempfile, unittest
from pathlib import Path
here = Path(__file__).parent
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, here / file); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
screen = load('screen_text_q', 'screen-text.py'); board = load('board_q', 'creation-board.py'); content = load('content_q', 'content-understanding.py')

def span(text, h, start=0, end=1, conf=0.9, persistent=False, y=0.5):
    return {'start': start, 'end': end, 'text': text, 'box': [0.1, y, 0.5, h], 'confidence': conf, 'persistent': persistent}

class ScreenText(unittest.TestCase):
    def test_layers_are_relative_to_the_biggest_text_and_misreads_are_voted_out(self):
        rows = [span('codex剪2分钟视频', 0.039, 0, 6, y=0.3), span('跑了47分钟', 0.033, 0, 5, 0.95, y=0.36), span('跑了4分钟', 0.033, 0, 1, 0.6, y=0.36),
                span('校对似水流年繁体字幕', 0.024), span('已处理47m55s', 0.015), span('抖音号:123', 0.03, 0, 10, persistent=True, y=0.9)]
        merged = screen.merge([(0.5, [{k: r[k] for k in ('text', 'box', 'confidence')} for r in rows])], 1.0, 10)
        layers = {s['text']: s['layer'] for s in merged}
        self.assertEqual(layers['codex剪2分钟视频'], 'caption'); self.assertEqual(layers['跑了47分钟'], 'caption')
        self.assertNotIn('跑了4分钟', layers)                    # the low-confidence misread merged into 47
        self.assertEqual(layers['校对似水流年繁体字幕'], 'ui'); self.assertEqual(layers['已处理47m55s'], 'ui'); self.assertEqual(layers['抖音号:123'], 'watermark')
        titles = [dict(span('35岁女生被一扫而光', 0.05, 0, 10, persistent=True)), dict(span('郑州相亲角现状', 0.069, 0, 10, persistent=True, y=0.1))]
        self.assertEqual({r['layer'] for r in screen.author_text({'items': titles})}, {'title'})   # persistent big titles are kept: they are the hook

class Board(unittest.TestCase):
    def test_real_comment_context_and_display_are_bounded_and_sanitized(self):
        ctx=board.post_context({},[{'text':'行业爆料'+str(i),'likes':i,'author':{'nickname':'不可保存'}} for i in range(20)])
        self.assertEqual(len(ctx['topComments']),20)
        insight=board.Board.insight({'commentPlay':'大家在爆料'},ctx)
        self.assertEqual(len(insight['topComments']),20); self.assertEqual(insight['commentStats']['read'],20)
        self.assertNotIn('不可保存',json.dumps(insight,ensure_ascii=False))
    def test_comments_are_weighed_by_likes_and_replies(self):
        rows=[{'text':'随口一说','likes':40,'replies':0},{'text':'吵起来了','likes':12,'replies':30},{'text':'没人理','likes':0,'replies':0}]
        ctx=board.post_context({},rows+[{'text':'凑数'+str(i),'likes':1} for i in range(17)])
        top=ctx['topComments']; st=ctx['commentStats']
        self.assertEqual(top[0]['text'],'吵起来了'); self.assertEqual(top[0]['heat'],102); self.assertEqual(top[0]['kind'],'讨论')
        self.assertEqual(top[1]['kind'],'共识'); self.assertEqual(next(r for r in top if r['text']=='没人理')['kind'],'长尾')
        self.assertTrue(st['reliable']); self.assertEqual(st['likes'],69); self.assertEqual(st['replies'],30); self.assertEqual(st['shape'],'单条主导')
        weak=board.post_context({},[{'text':'嗯','likes':2}])['commentStats']
        self.assertFalse(weak['reliable']); self.assertEqual(weak['shape'],'互动太少')
        self.assertEqual(board.post_context({},[])['commentStats']['shape'],'没有评论')
    def test_post_context_reads_how_it_spread_and_who_posted_it(self):
        ctx = board.post_context({'kind': 'video', 'description': '说说你们行业的内幕', 'stats': {'digg_count': 126603, 'comment_count': 44546, 'collect_count': 41628, 'share_count': 14065},
                                  'author': {'nickname': '我叫李醒醒', 'followerCount': 1994, 'signature': '', 'hasContact': False}})
        self.assertIn('评论驱动', ctx['drivers']); self.assertTrue(ctx['account']['lowFollowerHit']); self.assertFalse(ctx['account']['business'])
        self.assertEqual(ctx['account']['tier'], '素人/小号（<1万粉）'); self.assertEqual(ctx['ratios']['commentPerLike'], 0.35)
        shop = board.post_context({'stats': {'digg_count': 1358, 'comment_count': 358}, 'author': {'nickname': '❤爱情连线❤（招红娘）', 'followerCount': 13113, 'hasContact': True}})
        self.assertTrue(shop['account']['business']); self.assertFalse(shop['account']['lowFollowerHit']); self.assertEqual(board.post_context({})['drivers'], ['数据不足'])
        insight = board.Board.insight({'why': '评论区就是内容', 'difficulty': {'score': 9, 'reason': 'x'}, 'driver': '评论'}, ctx)
        self.assertIsNone(insight['difficulty']['score']); self.assertEqual(insight['numbers']['tier'], '素人/小号（<1万粉）')
        self.assertEqual(board.Board.insight({'difficulty': {'score': 2}}, ctx)['difficulty']['score'], 2)
        night = board.post_context({'stats': {'digg_count': 684, 'comment_count': 5546}, 'author': {'followerCount': 16}})
        self.assertTrue(night['account']['lowFollowerHit']); self.assertEqual(night['drivers'], ['评论驱动'])   # comments count too

    def test_a_cut_off_reply_gets_one_repair_pass(self):
        replies = ['{"fields":{"a":"x"},"insight":{"why":"评论', '{"fields":{"a":"x"}}']
        class G:
            def __init__(self): self.calls = 0
            def complete(self, scene, messages, **k):
                self.calls += 1; return {'choices': [{'message': {'content': replies.pop(0)}}]}
        with tempfile.TemporaryDirectory() as root:
            g = G(); b = board.Board(root, g, lambda: {})
            self.assertEqual(b.call('board_breakdown', 's', 'u', 'u1'), {'fields': {'a': 'x'}}); self.assertEqual(g.calls, 2)

    def test_author_text_prefers_the_watch_models_corrected_key_text(self):
        analysis = {'understanding': {'keyText': [{'start': 0, 'end': 6, 'text': '跑了47分钟', 'layer': 'caption'}]},
                    'screenText': {'items': [span('跑了4分钟', 0.033)]}}
        self.assertEqual([r['text'] for r in board.author_text(analysis)], ['跑了47分钟'])
        self.assertEqual([r['text'] for r in board.author_text({'screenText': {'items': [span('跑了4分钟', 0.033), span('界面小字', 0.012)]}})], ['跑了4分钟'])

class Understanding(unittest.TestCase):
    def test_key_text_and_post_context(self):
        card = content.normalize_watch({'overview': 'x', 'keyText': [{'start': 0, 'end': 3, 'text': '跑了47分钟', 'layer': 'caption'}, {'start': 0, 'end': 99, 'text': '越界'}, {'start': 1, 'end': 2}], 'confidence': 0.8}, 10)
        self.assertEqual(card['keyText'], [{'start': 0, 'end': 3, 'text': '跑了47分钟', 'layer': 'caption'}])
        self.assertIn('keyText', content.WATCH_SYSTEM); self.assertIn('product 才大于0', content.WATCH_SYSTEM); self.assertIn('以字幕为准', content.WATCH_SYSTEM)
        seen = []
        class G:
            def complete(self, scene, messages, **k):
                seen.append(messages); return {'choices': [{'message': {'content': '{"overview":"ok","confidence":0.9}'}}]}
        from PIL import Image
        content.watch(G(), [(0.0, Image.new('RGB', (8, 8)))], {'text': ''}, 3, {}, [], post={'kind': 'gallery', 'description': '避雷帖', 'author': {'nickname': '慢节奏', 'signature': '私密'}})
        payload = json.loads(seen[0][1]['content'][0]['text'])
        self.assertEqual(payload['post'], {'kind': 'gallery', 'caption': '避雷帖', 'hashtags': [], 'account': '慢节奏'})   # the bio is not sent to the watch model

class Outputs(unittest.TestCase):
    def test_titles_are_rewritten_apart_from_captions_and_the_package_keeps_originals_for_reference(self):
        calls = []
        class G:
            def complete(self, scene, messages, **k):
                calls.append((scene, messages)); system = messages[0]['content']
                if 'shots' in system:
                    out = {'shots': [{'start': 0, 'end': 3, 'shot': '近景', 'action': '提问', 'line': '那就是以你们现在的职业', 'orig': '那就是以你们现在的职业'},
                                     {'start': 3, 'end': 6, 'shot': '近景', 'action': '追问', 'line': '你那行有啥外人不懂的门道', 'orig': '能给我们透露一点点什么行情内幕'}]}
                else:
                    out = {'screenTitles': [{'orig': '35岁女生被一扫而光', 'text': '30岁男生排队相亲'}], 'lines': [{'start': 0, 'end': 10, 'orig': '35岁女生被一扫而光', 'text': '重复的标题'}, {'start': 1, 'end': 3, 'orig': '', 'text': '新字幕'}]}
                return {'choices': [{'message': {'content': json.dumps(out, ensure_ascii=False)}}]}
        cfg = {'countdownSeconds': 8, 'autoConfidence': 0.7, 'rewatchLimit': 2, 'interviewTurns': 3, 'attemptWindowDays': 7, 'similarityThreshold': 0.6, 'maxPlanFields': 12,
               'reviewVotes': 3, 'rewardPerMetrics': 2, 'streakUnlock': 2, 'predictMinWorks': 3, 'subscribeTemplateId': '', 'composeMaxSeconds': 90}
        ref = {'asset': {'sha256': 'b' * 64, 'storagePath': '/missing', 'media': {'durationSeconds': 10}}, 'source': {'kind': 'video', 'stats': {'digg_count': 100}},
               'analysis': {'understanding': {'overview': '相亲角', 'type': '街头观察'}, 'screenText': {'items': [span('35岁女生被一扫而光', 0.05, 0, 10, persistent=True)]}}}
        with tempfile.TemporaryDirectory() as root:
            b = board.Board(root, G(), lambda: cfg, resolve_reference=lambda u, sha: ref)
            session = b.start('u1', ref)
            work = b.text_work('u1', session['id'])['outputs']['text']
            self.assertEqual(work['screenTitles'][0]['text'], '30岁男生排队相亲'); self.assertEqual([l['text'] for l in work['lines']], ['新字幕'])
            sent = json.loads(calls[-1][1][1]['content']); self.assertEqual(sent['original']['screen'][0]['layer'], 'title'); self.assertIn('post', sent)
            pack = b.package('u1', session['id'])['outputs']['package']
            self.assertTrue(pack['shots'][0]['tooClose']); self.assertFalse(pack['shots'][1]['tooClose']); self.assertEqual(pack['shots'][1]['orig'], '能给我们透露一点点什么行情内幕')
            sent = json.loads(calls[-1][1][1]['content']); self.assertEqual(sent['rewritten']['screenTitles'][0]['text'], '30岁男生排队相亲'); self.assertIn('reference', sent)

class Gallery(unittest.TestCase):
    def test_photo_posts_become_a_slideshow_with_every_image(self):
        server = load('video_server_gallery', 'video-server.py')
        doc = {'data': {'media': {'video': None, 'images': [{'url': 'https://p.example/1.jpg'}, {'urls': ['https://p.example/2.jpg']}, {'url': 'http://insecure/3.jpg'}]}}}
        self.assertEqual(server._gallery_image_urls(doc), [['https://p.example/1.jpg'], ['https://p.example/2.jpg']])
        self.assertEqual(server._gallery_image_urls({'data': {'media': {'video': {'url': 'https://v.example/a.mp4'}, 'images': [{'url': 'https://p/1.jpg'}]}}}), [])
        from PIL import Image
        def image(color):
            data = io.BytesIO(); Image.new('RGB', (300, 400), color).save(data, 'JPEG'); return data.getvalue()
        files = {'https://p.example/1.jpg': image('red'), 'https://p.example/2.jpg': image('blue')}
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False
        opener = lambda request, timeout=0: Response(files[request.full_url])
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / '.g.download'   # the real temp file has no .mp4 suffix
            self.assertEqual(server._build_gallery(server._gallery_image_urls(doc), target, opener), 2)
            media = server._probe_video(target)
            self.assertAlmostEqual(media['durationSeconds'], 2 * server.GALLERY_SECONDS, delta=0.3); self.assertEqual((media['width'], media['height']), (1080, 1440))

if __name__ == '__main__':
    unittest.main()
