import base64, importlib.util, io, json, tempfile, time, unittest
from pathlib import Path
from PIL import Image
spec = importlib.util.spec_from_file_location('board', Path(__file__).with_name('creation-board.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CFG = {'countdownSeconds': 8, 'autoConfidence': 0.7, 'rewatchLimit': 2, 'interviewTurns': 3, 'attemptWindowDays': 7, 'similarityThreshold': 0.6, 'maxPlanFields': 12,
       'reviewVotes': 3, 'rewardPerMetrics': 2, 'streakUnlock': 2, 'predictMinWorks': 3, 'subscribeTemplateId': 'tpl', 'composeMaxSeconds': 90}
SHA = 'a' * 64
PLAN = {'name': '情侣反转剧情', 'fitFor': '剧情', 'fields': [{'key': 'twist', 'label': '反转点', 'ask': '几秒反转', 'format': 'timeline', 'needTime': True, 'useIn': 'shotlist'},
                                                     {'key': 'persona', 'label': '人设', 'ask': '人设', 'format': 'list', 'useIn': 'brief'}, {'label': '', 'ask': 'x'}]}


class Gateway:
    def __init__(self): self.calls = []
    def complete(self, scene, messages, user_id='', asset='', **k):
        self.calls.append((scene, messages, user_id))
        system = messages[0]['content']
        if scene == 'board_plan' and 'understanding' in system:
            out = {'understanding': {'overview': '其实是反差萌剧情', 'type': '反差萌剧情'}, 'plan': {**PLAN, 'name': '反差萌剧情'}}
        elif scene == 'board_plan':
            out = PLAN
        elif scene == 'board_breakdown':
            out = {'fields': {'positioning': '情侣日常反转', 'timeline': [{'start': 0, 'end': 3, 'text': '开场'}, {'start': 5, 'end': 999, 'text': '越界'}],
                              'learnable': getattr(self, 'learnable', None) or [{'item': '反转', 'level': '高', 'how': '前 3 秒埋梗'}, 'x'], 'twist': [{'start': 4, 'end': 6, 'text': '女生反将一军'}]}}
        elif scene == 'board_output' and 'shots' in system:
            out = {'shots': [{'start': 0, 'end': 3, 'shot': '近景', 'phone': '固定', 'action': '比心', 'difficulty': '易'}], 'script': '口播', 'rhythm': {'bpm': 500}, 'checklist': ['手机支架']}
        elif scene == 'board_output' and '"variants"' in system:
            out = getattr(self, 'variants', None) or {'variants': [
                {'angle': '直接邀请', 'title': '版本一', 'caption': '正文一', 'lines': [{'start': 0, 'end': 2, 'text': '一句'}, {'start': 2, 'end': 4, 'text': '二句'}]},
                {'angle': '讲经过', 'title': '版本二', 'caption': '正文二', 'lines': [{'start': 0, 'end': 2, 'text': '甲'}, {'start': 2, 'end': 999, 'text': '超时被丢'}]},
                {'angle': '没有可用句', 'lines': [{'start': 'x', 'end': 2, 'text': '坏'}]},
                {'angle': '第四个', 'lines': [{'start': 0, 'end': 1, 'text': '丁'}]},
                {'angle': '第五个不要', 'lines': [{'start': 0, 'end': 1, 'text': '戊'}]}]}
        elif scene == 'board_output':
            out = {'lines': [{'start': 0, 'end': 2, 'orig': '有人问我你究竟是哪里好', 'text': '有人问我你究竟是哪里好呀'}, {'start': 2, 'end': 4, 'orig': '这么多年我还忘不了', 'text': '时间走了好远心还在原地'}],
                   'titles': ['标题一', '标题二', '标题三', '多'], 'cover': '封面', 'hashtags': ['#老歌', '情歌'], 'caption': getattr(self, 'caption', '')}
        elif scene == 'board_interview' and '追问' in system:
            out = {'items': [{'question': '你想保留开头吗？', 'options': ['是', '否']}]}
        elif scene == 'board_interview':
            out = {'reply': '你想给谁看？', 'done': True, 'summary': '给上班族看，保留反转'}
        elif scene == 'data_screenshot':
            out = {'play': 12000, 'completion': 35, 'bounce2s': 0.2, 'likes': 100, 'collects': 200, 'secret': 'x'}
        elif scene == 'video_watch':
            out = {'overview': '重看', 'timeline': [{'start': 1, 'end': 2, 'what': '女生转身'}], 'confidence': 0.9}
        else:
            out = {}
        if scene=='board_output':out.update(pinnedComment='你还知道什么内幕？',replySuggestions=['谢谢补充'])
        if scene=='board_output':out['usedMethods']=getattr(self,'used',[])
        return {'choices': [{'message': {'content': json.dumps(out, ensure_ascii=False)}}]}


def reference(path=None, confidence=0.9):
    return {'asset': {'sha256': SHA, 'storagePath': str(path or '/missing'), 'media': {'durationSeconds': 10}},
            'source': {'author': {'uid': 'author-1', 'nickname': '博主', 'followerCount': 1000}, 'hashtags': ['情侣', '反转'], 'stats': {'digg_count': 100, 'comment_count': 10, 'share_count': 5, 'collect_count': 5}},
            'analysis': {'understanding': {'overview': '情侣对话', 'type': '情侣剧情', 'tags': ['情侣', '反转'], 'confidence': confidence, 'timeline': [{'start': 0, 'end': 3, 'what': '男生说话'}, {'start': 3, 'end': 6, 'what': '女生回应'}]},
                         'screenText': {'items': [{'start': 0, 'end': 2, 'text': '有人问我你究竟是哪里好', 'persistent': False}, {'start': 0, 'end': 10, 'text': '抖音号1', 'persistent': True}]},
                         'audio': {'transcript': {'text': '歌词'}, 'features': {'bpmEstimate': 118, 'onsetTimes': [0.5, 1.0]}}}}


class Tests(unittest.TestCase):
    def test_quota_debug_phase_grants_immediately(self):
        with self.assertRaises(m.BoardError):self.b.request_quota('u1',30)
        r=self.b.request_quota('u1',5,'调试');self.assertTrue(r['auto']);self.assertEqual(r['status'],'approved');self.assertEqual(r['balance'],5)
        self.assertEqual(self.b.request_quota('u1',1)['balance'],6,'调试阶段可以多次申请');self.assertEqual(self.b.quota_requests(),[])
    def test_quota_request_one_per_day_and_approval_grants_credits(self):
        m.Board.QUOTA_AUTO_APPROVE=False;m.Board.QUOTA_AMOUNTS=(10,30,100)
        self.addCleanup(lambda:(setattr(m.Board,'QUOTA_AUTO_APPROVE',True),setattr(m.Board,'QUOTA_AMOUNTS',(1,5,10))))
        with self.assertRaises(m.BoardError):self.b.request_quota('u1',7)
        first=self.b.request_quota('u1',30,'做账号要批量拆对标')
        self.assertEqual(first['status'],'pending');self.assertEqual(first['amount'],30)
        again=self.b.request_quota('u1',10);self.assertTrue(again['existing']);self.assertEqual(again['id'],first['id'])
        self.assertEqual([r['id'] for r in self.b.quota_requests()],[first['id']])
        self.assertEqual(self.b.quota_status('u1')['balance'],0)
        done=self.b.decide_quota(first['id'],True)
        self.assertEqual(done['status'],'approved');self.assertEqual(done['granted'],30)
        self.assertEqual(self.b.quota_status('u1')['balance'],30);self.assertTrue(self.b.spend_credit('u1'));self.assertEqual(self.b.credits('u1')['balance'],29)
        self.assertEqual(self.b.decide_quota(first['id'],True)['granted'],30,'重复批准不重复发放');self.assertEqual(self.b.credits('u1')['balance'],29)
        self.assertEqual(self.b.quota_requests(),[])
        no=self.b.decide_quota(self.b.request_quota('u2',10)['id'],False,note='先回传数据');self.assertEqual(no['status'],'rejected');self.assertEqual(self.b.credits('u2')['balance'],0)
    def test_history_lists_each_pasted_video_once_with_progress(self):
        self.ref['source']={**self.ref['source'],'description':'说说你们行业的内幕','contentId':'7697544984564710315'}
        first=self.b.start('u1',self.ref);second=self.b.start('u1',self.ref)
        rows=self.b.history('u1')
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['id'],second['id']);self.assertEqual(rows[0]['stage'],'已识别内容')
        self.assertEqual(rows[0]['title'],'说说你们行业的内幕');self.assertEqual(rows[0]['url'],'https://www.douyin.com/video/7697544984564710315')
        self.b.breakdown('u1',second['id'])
        self.assertEqual(self.b.history('u1')[0]['stage'],'已完成拆解')
        self.assertEqual(self.b.history('u2'),[],'只看自己的')
        self.assertNotIn('博主',json.dumps(self.b.history('u1'),ensure_ascii=False))
    def test_comments_reach_breakdown_and_both_outputs(self):
        self.ref['comments']=[{'text':'同行都来爆料了','likes':88,'replies':3,'isAuthorReply':False}]
        s=self.b.start('u1',self.ref)
        result=self.b.breakdown('u1',s['id'])
        self.assertEqual(result['breakdown']['insight']['topComments'][0]['text'],'同行都来爆料了')
        for method,kind in [(self.b.text_work,'text'),(self.b.package,'package')]:
            out=method('u1',s['id'])['outputs'][kind]
            self.assertEqual(out['pinnedComment'],'你还知道什么内幕？')
            self.assertEqual(out['replySuggestions'],['谢谢补充'])
        calls=[messages for scene,messages,_ in self.g.calls if scene in ('board_breakdown','board_output')]
        self.assertEqual(len(calls),3)
        for messages in calls:self.assertIn('同行都来爆料了',messages[1]['content'])
        for scene,messages,_ in self.g.calls:
            if scene=='board_breakdown':self.assertIn('真实评论的具体话题',messages[0]['content'])
            if scene=='board_output':
                self.assertIn('不得把评论者的经历改写为创作者亲历或亲测',messages[0]['content'])
                self.assertIn('完整成句',messages[0]['content'])
                self.assertIn('"pinnedComment":',messages[0]['content'])
                self.assertIn('"replySuggestions":',messages[0]['content'])
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); self.g = Gateway(); self.now = [1000.0]; self.signals = []; self.notes = []
        self.ref = reference()
        self.b = m.Board(self.root, self.g, lambda: CFG, resolve_reference=lambda u, sha: self.ref, clock=lambda: self.now[0],
                         profile_signal=lambda u, p: self.signals.append(p), notify=lambda *a: self.notes.append(a),
                         parse_stats=lambda url: {'contentId': '9', 'stats': {'digg_count': 50, 'comment_count': 5, 'share_count': 1, 'collect_count': 2}})
    def tearDown(self): self.tmp.cleanup()

    def test_method_library_reused_by_category_and_scored_by_metrics(self):
        def run(sha, kind, learn):
            self.ref = reference(); self.ref['asset']['sha256'] = sha; self.ref['analysis']['understanding']['type'] = kind
            self.g.learnable = learn; s = self.b.start('u1', self.ref); self.b.breakdown('u1', s['id']); return s
        hook = {'item': '评论区接龙', 'level': '高', 'how': '结尾抛一个二选一问题'}
        run('b' * 64, '情侣·剧情', [hook, {'item': '颜值', 'level': '低'}]); run('c' * 64, '情侣剧情', [hook, {'item': '道具反差', 'level': '中', 'how': '同一件衣服'}])
        run('d' * 64, '美食探店', [{'item': '先上价格', 'level': '高', 'how': '开头报人均'}])
        lib = {(r['cat'], r['name']): r for r in self.b.method_library()}
        self.assertEqual(lib[('情侣剧情', '评论区接龙')]['count'], 2, '分隔符不同的类型归为同一类目，按素材去重')
        self.assertNotIn(('情侣剧情', '颜值'), lib, '可学程度低的不进方法库')
        s = run(SHA, '情侣剧情', None)
        self.g.used = ['评论区接龙', '模型编造的方法']; self.g.calls.clear(); out = self.b.text_work('u1', s['id'])
        prompt = [c for c in self.g.calls if c[0] == 'board_output'][-1][1]
        self.assertIn('usedMethods', prompt[0]['content']); payload = json.loads(prompt[1]['content'])
        names = [x['name'] for x in payload['methods']]
        self.assertEqual(names[0], '评论区接龙'); self.assertIn('道具反差', names); self.assertNotIn('先上价格', names, '同类目足够时不跨类目')
        self.assertNotIn('反转', names, '本片自己拆出来的方法不重复推荐')
        self.assertEqual(payload['methods'][0]['seen'], 2)
        self.assertEqual(out['outputs']['text']['usedMethods'], ['评论区接龙'], '只记录确实提供过的方法')
        self.assertEqual({(r['name'], r['used']) for r in self.b.method_library() if r['name'] == '评论区接龙'}, {('评论区接龙', 1)})
        for play in (1000, 1000):
            o = self.b.start('u1', self.ref); w = self.b.create_work('u1', o['id'], {}); self.now[0] += 10
            self.b.save_metrics('u1', w['id'], 3, {'play': play})
        work = self.b.create_work('u1', s['id'], {}); self.assertEqual(work['methods'] if 'methods' in work else self.b._work('u1', work['id'])['methods'], [{'name': '评论区接龙', 'cat': '情侣剧情'}])
        self.now[0] += 10; self.b.save_metrics('u1', work['id'], 3, {'play': 3000})
        lib = {(r['cat'], r['name']): r for r in self.b.method_library()}
        self.assertEqual((lib[('情侣剧情', '评论区接龙')]['works'], lib[('情侣剧情', '评论区接龙')]['lift']), (1, 3.0))
        self.assertIn('methods', self.b.admin_dashboard())
        # 数据差（≥2 条作品中位数 <0.8 倍）的方法不再推荐；同类目不足时跨类目补位需出现在 ≥3 条其它爆款
        with self.b.db() as db:
            db.execute("INSERT OR REPLACE INTO method_results VALUES('w1','情侣剧情','道具反差',0.5,0)"); db.execute("INSERT OR REPLACE INTO method_results VALUES('w2','情侣剧情','道具反差',0.6,0)")
        session = self.b.session('u1', s['id']); card = {'type': '情侣剧情'}
        self.assertNotIn('道具反差', [x['name'] for x in self.b.methods_for(card, session)])
        for sha in ('e' * 64, 'f' * 64): run(sha, '美食探店', [{'item': '先上价格', 'level': '高'}])
        offered = self.b.methods_for({'type': '萌宠'}, {'asset': '0' * 64})
        self.assertEqual([(x['name'], x['scope']) for x in offered], [('先上价格', '跨类目')], '评论区接龙只出现 2 次，不够跨类目')

    def test_method_backfill_runs_once_from_existing_breakdowns(self):
        s = self.b.start('u1', self.ref); self.b.breakdown('u1', s['id'])
        with self.b.db() as db: db.execute('DELETE FROM methods')
        self.assertEqual(self.b.backfill_methods(), 1); self.assertEqual([r['name'] for r in self.b.method_library()], ['反转'])
        with self.b.db() as db: db.execute('DELETE FROM methods')
        self.assertEqual(self.b.backfill_methods(), 0, '只跑一次'); self.assertEqual(self.b.method_library(), [])

    def test_attempts_tier_questions_and_default_suggestion(self):
        first = self.b.start('u1', self.ref)
        self.assertEqual(first['attempt'], 1); self.assertEqual(first['questions']['mode'], 'probe')
        self.assertEqual(first['suggestion']['strength'], 'weak'); self.assertEqual(first['countdownSeconds'], 0)
        second = self.b.start('u1', self.ref); self.assertEqual(second['questions']['mode'], 'followup')
        self.assertEqual(second['suggestion']['basis'], ['上次提交这条视频时你用的方案'])
        third = self.b.start('u1', self.ref); self.assertEqual(third['questions']['mode'], 'interview')
        self.assertEqual(self.b.start('u2', self.ref)['attempt'], 1)
        self.now[0] += 8 * 86400; self.assertEqual(self.b.start('u1', self.ref)['attempt'], 1)

    def test_learning_makes_same_author_strong_with_countdown(self):
        plan = self.b.save_plan('u1', PLAN)
        s = self.b.start('u1', self.ref)
        self.b.confirm('u1', s['id'], {'verdict': 'ok', 'planId': plan['id']})
        self.b.breakdown('u1', s['id']); self.b.text_work('u1', s['id'])
        other = dict(self.ref, asset={**self.ref['asset'], 'sha256': 'b' * 64})
        self.ref = other
        nxt = self.b.start('u1', other)
        self.assertEqual(nxt['suggestion']['planId'], plan['id']); self.assertEqual(nxt['suggestion']['strength'], 'strong')
        self.assertTrue(any('同一博主' in b for b in nxt['suggestion']['basis'])); self.assertEqual(nxt['countdownSeconds'], 8)
        self.ref = reference(confidence=0.3); self.ref['asset']['sha256'] = 'c' * 64
        self.assertEqual(self.b.start('u1', self.ref)['countdownSeconds'], 0)

    def test_corrections_are_personal_and_statement_creates_draft_type_and_report(self):
        s = self.b.start('u1', self.ref)
        out = self.b.confirm('u1', s['id'], {'verdict': 'partial', 'corrections': [{'index': 1, 'text': '女生反问'}, {'index': 9, 'text': 'x'}], 'statement': '这其实是反差萌剧情'})
        self.assertEqual(out['card']['timeline'][1]['what'], '女生反问'); self.assertEqual(out['card']['type'], '反差萌剧情')
        self.assertEqual(self.ref['analysis']['understanding']['timeline'][1]['what'], '女生回应')
        self.assertEqual(out['plan']['name'], '反差萌剧情'); self.assertEqual(out['plan']['status'], 'draft')
        reports = self.b.admin_reports('new_type'); self.assertEqual(reports[0]['user'], 'u1'); self.assertEqual(reports[0]['payload']['statement'], '这其实是反差萌剧情')
        self.assertEqual(len(out['plan']['fields']), 3 + 2)

    def test_shared_cache_review_after_enough_votes(self):
        for user in ('u1', 'u2'):
            s = self.b.start(user, self.ref); self.b.confirm(user, s['id'], {'verdict': 'wrong', 'describe': '主角是猫'})
        self.assertFalse(self.b.needs_review(SHA))
        s = self.b.start('u3', self.ref); self.b.confirm('u3', s['id'], {'verdict': 'partial', 'corrections': [{'index': 0, 'text': '猫'}]})
        self.assertTrue(self.b.needs_review(SHA)); self.b.reviewed(SHA); self.assertFalse(self.b.needs_review(SHA))

    def test_breakdown_normalizes_caches_and_never_invents(self):
        s = self.b.start('u1', self.ref); self.b.confirm('u1', s['id'], {'verdict': 'ok'})
        out = self.b.breakdown('u1', s['id'])
        fields = {f['key']: f['value'] for f in out['breakdown']['fields']}
        self.assertEqual(fields['timeline'], [{'start': 0, 'end': 3, 'text': '开场'}])
        self.assertEqual(fields['learnable'][1], {'item': 'x'}); self.assertEqual(fields['hook'], '本视频没有')
        n = len(self.g.calls); self.b.breakdown('u1', s['id']); self.assertEqual(len(self.g.calls), n)
        from unittest.mock import patch
        with patch.object(m,'BREAKDOWN_SCHEMA','next-prompt'):
            self.b.breakdown('u1',s['id']);self.assertEqual(len(self.g.calls),n+1)
            self.b.breakdown('u1',s['id']);self.assertEqual(len(self.g.calls),n+1)
        context = json.loads(self.g.calls[-1][1][1]['content'])
        self.assertEqual([x['text'] for x in context['screenText']], ['有人问我你究竟是哪里好'])

    def test_adjust_only_once_or_save_new_version(self):
        own = self.b.save_plan('u1', PLAN); s = self.b.start('u1', self.ref)
        self.b.confirm('u1', s['id'], {'verdict': 'ok', 'planId': own['id']})
        once = self.b.adjust('u1', s['id'], '多看台词节奏', False); self.assertIn('仅本次', once['plan']['name'])
        self.assertEqual(self.b.plan('u1', own['id'])['version'], 1)
        saved = self.b.adjust('u1', s['id'], '多看台词节奏', True); self.assertEqual(self.b.plan('u1', own['id'])['version'], 2)
        self.assertEqual(self.b.rollback_plan('u1', own['id'], 1)['version'], 3)
        s2 = self.b.start('u1', self.ref); self.b.confirm('u1', s2['id'], {'verdict': 'ok', 'planId': 'builtin-general'})
        forked = self.b.adjust('u1', s2['id'], '加一个字段', True); self.assertEqual(forked['plan']['owner'], 'mine')
        with self.assertRaises(m.BoardError): self.b.save_plan('u1', PLAN, ident='builtin-general')
        with self.assertRaises(m.BoardError): self.b.plan('u2', own['id'])

    def test_followups_and_interview(self):
        self.b.start('u1', self.ref); s = self.b.start('u1', self.ref)
        items = self.b.followups('u1', s['id'], '拆解')['items']; self.assertEqual(items[0]['key'], 'followup1')
        self.b.start('u1', self.ref); s3 = self.b.start('u1', self.ref)
        out = self.b.interview('u1', s3['id'], '我想拍给同事看'); self.assertEqual(out['requirements'], '给上班族看，保留反转')
        self.assertEqual([t['role'] for t in out['interview']], ['user', 'ai'])
        self.b.interview('u1', s3['id'], ''); self.b.interview('u1', s3['id'], '')
        with self.assertRaises(m.BoardError): self.b.interview('u1', s3['id'], '再来')

    def test_text_work_compares_with_original_and_flags_close_copies(self):
        s = self.b.start('u1', self.ref)
        out = self.b.text_work('u1', s['id'])
        work = out['outputs']['text']
        self.assertEqual(work['original']['screen'][0]['text'], '有人问我你究竟是哪里好'); self.assertEqual(len(work['original']['screen']), 1)
        self.assertTrue(work['lines'][0]['tooClose']); self.assertFalse(work['lines'][1]['tooClose']); self.assertEqual(work['tooClose'], 1)
        self.assertEqual(len(work['titles']), 3); self.assertEqual(work['hashtags'], ['老歌', '情歌'])
        package = self.b.package('u1', s['id'], '不出镜')['outputs']['package']
        self.assertEqual(package['rhythm']['bpm'], 118); self.assertEqual(package['rhythm']['beats'], [0.5, 1.0]); self.assertEqual(package['shots'][0]['difficulty'], '中')

    def test_gallery_text_work_rewrites_caption_without_timeline(self):
        self.ref['source'] = {**self.ref['source'], 'kind': 'gallery', 'imageCount': 1, 'description': '各位，自建一个抖店动销群，有兴趣的可以加入 #店铺动销 #抖店运营'}
        self.g.caption = '大家好，我拉了个抖店互助群，想一起动销的可以来'
        s = self.b.start('u1', self.ref)
        work = self.b.text_work('u1', s['id'])['outputs']['text']
        system = next(c[1][0]['content'] for c in self.g.calls if c[0] == 'board_output')
        self.assertIn('发布正文 caption', system); self.assertIn('直接邀请', system)
        self.assertEqual(work['kind'], 'gallery'); self.assertEqual(work['caption'], '大家好，我拉了个抖店互助群，想一起动销的可以来')
        self.assertEqual(work['captionOrig'], '各位，自建一个抖店动销群，有兴趣的可以加入'); self.assertFalse(work['captionTooClose'])
        self.assertTrue(all(l['start'] is None and l['end'] is None for l in work['lines']))
        own = self.b.create_work('u1', s['id'], {}); self.assertEqual(own['caption'], work['caption'])

    def test_plans_chat_fork_and_induce(self):
        draft = self.b.chat_plan('u1', '按情侣反转剧情拆，看台词')['draft']; self.assertEqual(draft['name'], '情侣反转剧情')
        fork = self.b.fork_plan('u1', 'builtin-emotion'); self.assertEqual(fork['source'], 'fork')
        self.b.acquire = lambda u, url: {**reference(), 'source': {'author': {'uid': 'author-9'}}}
        self.b.analyze = lambda u, r: r['analysis']
        job = self.b.induce('u1', ['https://v.douyin.com/a/', 'https://v.douyin.com/b/', 'https://v.douyin.com/c/'])
        for _ in range(50):
            if self.b.job('u1', job['id'])['status'] != 'running': break
            time.sleep(0.02)
        done = self.b.job('u1', job['id']); self.assertEqual(done['status'], 'done'); self.assertEqual(done['plan']['source'], 'samples')
        self.assertIn('author-9', self.b.match_of('u1', done['plan']['id'])['authors'])
        with self.assertRaises(m.BoardError): self.b.induce('u1', ['a'])
        with self.assertRaises(m.BoardError): self.b.job('u2', job['id'])

    def test_works_metrics_rewards_review_and_reminders(self):
        reviews = []
        for index, play in enumerate((1000, 2000, 3000, 9000)):
            s = self.b.start('u1', self.ref); self.b.text_work('u1', s['id'])
            work = self.b.create_work('u1', s['id'], {})
            self.assertEqual(work['title'], '标题一')
            self.now[0] += 10
            view = self.b.save_metrics('u1', work['id'], 3, {'play': play, 'completion': 40, 'bounce2s': 0.2, 'likes': 10, 'collects': 200})
            reviews.append(view['review'])
        self.assertEqual(reviews[-1]['ratio'], 4.5); self.assertEqual(reviews[-1]['samples'], 3)
        self.assertIn('开头钩子', [f['element'] for f in reviews[-1]['findings']]); self.assertIn('信息价值', [f['element'] for f in reviews[-1]['findings']])
        self.assertTrue(self.signals); credits = self.b.credits('u1'); self.assertEqual(credits['balance'], 8); self.assertTrue(credits['predictUnlocked'])
        self.assertTrue(self.b.spend_credit('u1')); self.assertEqual(self.b.credits('u1')['balance'], 7)
        self.b.save_metrics('u1', work['id'], 3, {'play': 9100}); self.assertEqual(self.b.credits('u1')['balance'], 7)
        with self.assertRaises(m.BoardError): self.b.save_metrics('u2', work['id'], 1, {'play': 1})
        with self.assertRaises(m.BoardError): self.b.link_work('u1', work['id'], 'https://v.kuaishou.com/x')
        linked = self.b.link_work('u1', work['id'], '复制 https://v.douyin.com/abc/ 打开')
        self.assertEqual(linked['link'], 'https://v.douyin.com/abc/'); self.b.subscribe('u1', work['id'], True)
        self.now[0] += 86400 + 1; self.b.tick()
        self.assertEqual(self.notes[0][1], 'tpl'); self.assertIn(work['id'], self.notes[0][2])
        self.assertEqual(self.b._work('u1', work['id'])['fetchedDays'], [1]); self.b.tick(); self.assertEqual(len(self.notes), 1)

    def test_monitor_any_douyin_post_daily_snapshots_refresh_and_isolation(self):
        counts = {'n': 0}
        def stats(url):
            counts['n'] += 1
            return {'contentId': '77', 'description': '下班后一个人做饭 #日常 #vlog', 'author': {'nickname': '阿禾'},
                    'stats': {'digg_count': 100 * counts['n'], 'comment_count': 10, 'share_count': 1, 'collect_count': 3, 'play_count': 5000 * counts['n']}}
        self.b.parse_stats = stats
        with self.assertRaises(m.BoardError): self.b.add_monitor('u1', 'https://v.kuaishou.com/x')
        view = self.b.add_monitor('u1', '7.12 复制打开抖音 https://v.douyin.com/mon1/ 看看')
        self.assertEqual(view['kind'], 'monitor'); self.assertEqual(view['role'], 'benchmark'); self.assertEqual(view['title'], '下班后一个人做饭'); self.assertEqual(view['author'], '阿禾')
        self.assertIsNone(view['review']); self.assertEqual(view['summary']['values']['likes'], 100); self.assertEqual(view['summary']['delta'], {})
        self.assertEqual(self.b.add_monitor('u1', 'https://v.douyin.com/mon1/')['id'], view['id'], '同一链接不重复添加')
        self.assertEqual(self.b.add_monitor('u1', 'https://v.douyin.com/other-share/')['id'], view['id'], '同一作品不同分享链接按作品去重')
        self.now[0] += 3600; fresh = self.b.refresh_work('u1', view['id'])
        self.assertEqual(fresh['summary']['values']['likes'], 300)
        with self.assertRaises(m.BoardError): self.b.refresh_work('u1', view['id'])
        self.now[0] += 86400; self.b.tick(); listed = self.b.works('u1')[0]
        self.assertEqual(listed['summary']['day'], 1); self.assertEqual(listed['summary']['delta']['likes'], 100); self.assertEqual(listed['summary']['snapshots'], 2)
        self.assertEqual(self.notes, [], '监控作品不发回传提醒')
        with self.assertRaises(m.BoardError): self.b.save_metrics('u1', view['id'], 1, {'play': 9999})
        with self.assertRaises(m.BoardError): self.b.add_monitor('u1', 'https://v.douyin.com/mon1/', 'friend')
        mine = self.b.add_monitor('u1', 'https://v.douyin.com/mon1/', 'own'); self.assertEqual(mine['id'], view['id']); self.assertEqual(mine['role'], 'own')
        self.b.save_metrics('u1', view['id'], 1, {'play': 9999, 'completion': 0.4})
        self.assertIsNotNone(self.b.work_view('u1', view['id'])['review'], '我的作品有后台数据时出复盘')
        self.assertEqual(self.b.set_role('u1', view['id'], 'benchmark')['review'], None)
        self.assertEqual(self.b.credits('u1')['balance'], 0); self.assertEqual(self.b.credits('u1')['reportedWorks'], 0)
        with self.assertRaises(m.BoardError): self.b.refresh_work('u2', view['id'])
        with self.assertRaises(m.BoardError): self.b.remove_work('u2', view['id'])
        s = self.b.start('u1', self.ref); self.b.text_work('u1', s['id']); own = self.b.create_work('u1', s['id'], {})
        with self.assertRaises(m.BoardError): self.b.remove_work('u1', own['id'])
        with self.assertRaises(m.BoardError): self.b.set_role('u1', own['id'], 'benchmark')
        with self.assertRaises(m.BoardError): self.b.set_role('u2', view['id'], 'own')
        self.assertEqual(self.b.remove_work('u1', view['id']), {'removed': True}); self.assertEqual([w['id'] for w in self.b.works('u1')], [own['id']])

    def test_extra_answer_is_accepted_and_reaches_breakdown_prompt(self):
        s = self.b.start('u1', self.ref)
        self.assertEqual(self.b.answer('u1', s['id'], 'extra', '  我是做母婴的，能不能借这个形式  ')['answers']['extra'], '我是做母婴的，能不能借这个形式')
        with self.assertRaises(m.BoardError): self.b.answer('u1', s['id'], 'other', 'x')
        with self.assertRaises(m.BoardError): self.b.answer('u1', s['id'], 'extra', 'x' * 301)
        self.b.confirm('u1', s['id'], {'verdict': 'ok'}); self.b.breakdown('u1', s['id'])
        system, user = [msgs for scene, msgs, _ in self.g.calls if scene == 'board_breakdown'][-1][:2]
        self.assertIn('user.answers.extra', system['content']); self.assertIn('我是做母婴的', user['content'])

    def test_screenshot_read_is_memory_only(self):
        s = self.b.start('u1', self.ref); work = self.b.create_work('u1', s['id'], {'title': 't'})
        buf = io.BytesIO(); Image.new('RGB', (300, 600), 'white').save(buf, 'PNG')
        before = sorted(p.name for p in self.root.rglob('*') if p.is_file())
        out = self.b.read_screenshot('u1', work['id'], base64.b64encode(buf.getvalue()).decode())
        self.assertEqual(out['values'], {'play': 12000, 'completion': 0.35, 'bounce2s': 0.2, 'likes': 100, 'collects': 200})
        self.assertEqual(sorted(p.name for p in self.root.rglob('*') if p.is_file()), before)
        with self.assertRaises(m.BoardError): self.b.read_screenshot('u1', work['id'], 'not-an-image')

    def test_compose_builds_ffmpeg_command_and_registers_media(self):
        commands = []
        def runner(cmd, **k):
            commands.append(cmd)
            if cmd[-1].endswith('.mp4'): Path(cmd[-1]).write_bytes(b'mp4')
            return type('R', (), {'returncode': 0})()
        self.b.runner = runner; self.b.font = None
        s = self.b.start('u1', self.ref)
        job = self.b.compose('u1', s['id'], {'lines': [{'start': 0, 'end': 2, 'text': "新的一句: 'x'"}, {'start': 2, 'end': 4, 'text': '第二句'}]}, ['/a.mp4', '/b.mp4'])
        for _ in range(50):
            if self.b.job('u1', job['id'])['status'] != 'running': break
            time.sleep(0.02)
        done = self.b.job('u1', job['id']); self.assertEqual(done['status'], 'done')
        graph = commands[-1][commands[-1].index('-filter_complex') + 1]; self.assertIn('concat=n=2', graph); self.assertIn("overlay=0:940:enable='between(t,0.00,2.00)'", graph)
        self.assertEqual(sum(1 for x in commands[-1] if str(x).endswith('.png')), 2)
        self.assertEqual(self.b.media(done['video'].split('/')[-1][:-4]).read_bytes(), b'mp4')
        self.assertEqual(self.b.session('u1', s['id'])['outputs']['composed']['seconds'], 4.0)
        with self.assertRaises(m.BoardError): self.b.compose('u1', s['id'], {'lines': []}, ['/a.mp4'])

    def test_variants_write_three_scripts_and_render_them_one_by_one(self):
        commands = []
        def runner(cmd, **k):
            commands.append(cmd)
            if cmd[-1].endswith('.mp4'):
                if len(commands) == 2: return type('R', (), {'returncode': 1})()
                Path(cmd[-1]).write_bytes(b'mp4')
            return type('R', (), {'returncode': 0})()
        self.b.runner = runner; self.b.font = None
        s = self.b.start('u1', self.ref)
        with self.assertRaisesRegex(m.BoardError, '文字作品'): self.b.variants('u1', s['id'], {}, ['/a.mp4'])
        self.b.text_work('u1', s['id'])
        with self.assertRaisesRegex(m.BoardError, '画面'): self.b.variants('u1', s['id'], {}, [])
        job = self.b.variants('u1', s['id'], {'position': 'top'}, ['/a.mp4'])
        system = [c for c in self.g.calls if c[0] == 'board_output'][-1][1][0]['content']
        self.assertIn('沿用 work 的人称和口吻', system); self.assertIn('base 的时间轴', system)
        self.assertEqual([i['angle'] for i in job['items']], ['直接邀请', '讲经过', '第四个'], '无可用句的版本跳过，最多 3 条')
        self.assertEqual(job['items'][1]['lines'], [{'start': 0.0, 'end': 2.0, 'text': '甲'}], '超出时长的句子被丢弃')
        for _ in range(100):
            if self.b.job('u1', job['id'])['status'] != 'running': break
            time.sleep(0.02)
        done = self.b.job('u1', job['id'])
        self.assertEqual(done['status'], 'done'); self.assertEqual(done['message'], '已生成 2/3 条')
        self.assertEqual([i['status'] for i in done['items']], ['done', 'failed', 'done'])
        self.assertEqual(len([c for c in commands if c[-1].endswith('.mp4')]), 3, '依次合成，每条一次')
        self.assertIn("overlay=0:140:", commands[0][commands[0].index('-filter_complex') + 1])
        saved = self.b.session('u1', s['id'])['outputs']['variants']['items']
        self.assertEqual([v['title'] for v in saved], ['版本一', ''])
        self.assertEqual(self.b.media(done['items'][0]['video'].split('/')[-1][:-4]).read_bytes(), b'mp4')

    def test_rewatch_window_limit(self):
        video = self.root / 'v.mp4'; video.write_bytes(b'x'); self.ref = reference(video)
        def runner(cmd, **k):
            Image.new('RGB', (36, 64)).save(cmd[-1]); return type('R', (), {'returncode': 0})()
        self.b.runner = runner
        s = self.b.start('u1', self.ref)
        out = self.b.rewatch('u1', s['id'], 1, 2.5)
        self.assertEqual(out['card']['timeline'][0]['what'], '女生转身'); self.assertEqual(out['rewatchLeft'], 1)
        self.b.rewatch('u1', s['id'], 0, 9)
        with self.assertRaises(m.BoardError): self.b.rewatch('u1', s['id'])

    def test_admin_views(self):
        s = self.b.start('u1', self.ref); self.b.confirm('u1', s['id'], {'verdict': 'partial', 'statement': '反差萌剧情', 'auto': True})
        self.b.save_plan('u2', {**PLAN, 'name': '反差萌剧情二'})
        clusters = self.b.admin_clusters(); self.assertEqual(len(clusters[0]['plans']), 2)
        promoted = self.b.admin_promote(clusters[0]['plans'][0]['id']); self.assertIn(promoted['id'], [p['id'] for p in self.b.plans('u9')['builtin']])
        dash = self.b.admin_dashboard(); self.assertEqual(dash['funnel']['confirmed'], 1); self.assertEqual(dash['autoStart']['count'], 1)
        self.assertEqual(dash['correctionRateByType'][0]['rate'], 1.0)
        self.assertEqual(self.b.admin_stats(), [])

    def test_trial_accounts_are_reported_with_label_and_scoped(self):
        self.b.is_trial = lambda u: u == 'tester'
        for user in ('u1', 'tester'):
            s = self.b.start(user, self.ref); self.b.confirm(user, s['id'], {'verdict': 'partial', 'statement': '反差萌剧情'})
        rows = self.b.admin_reports()
        self.assertEqual({r['user']: r['account'] for r in rows}, {'u1': '正式', 'tester': '体验版'})
        self.assertTrue(all(r['payload']['account'] == r['account'] for r in rows))
        self.assertEqual({r['user'] for r in self.b.admin_reports(scope='trial')}, {'tester'})
        self.assertEqual({r['user'] for r in self.b.admin_reports(scope='formal')}, {'u1'})
        dash = self.b.admin_dashboard('formal'); self.assertEqual((dash['sessions'], dash['trialSessions'], dash['allSessions']), (1, 1, 2))
        self.assertEqual(self.b.admin_dashboard()['sessions'], 2); self.assertEqual(self.b.admin_dashboard('trial')['funnel']['confirmed'], 1)


if __name__ == '__main__':
    unittest.main()
