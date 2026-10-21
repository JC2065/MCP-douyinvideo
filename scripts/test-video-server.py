import json
import importlib.util
import unittest
import subprocess
import uuid
import os
import shutil
from io import BytesIO
from urllib.error import HTTPError
from urllib.parse import urlparse
spec=importlib.util.spec_from_file_location('video_server',__file__.replace('test-video-server.py','video-server.py'))
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

class RendererTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        server._PARSE_CACHE.clear()
        mock=patch.object(server._understand_module,'understand',side_effect=lambda gateway,frames,transcript,duration:{'status':'ready','overview':'模拟素材内容','segments':[{'start':duration*i/3,'end':duration*(i+1)/3,'description':'模拟内容段'} for i in range(3)],'facts':[],'recommendations':{}});mock.start();self.addCleanup(mock.stop)

    def test_reference_upload_multipart_is_stored_like_an_acquired_video(self):
        import tempfile,hashlib
        from pathlib import Path
        from unittest.mock import patch
        video=b'\x00\x00\x00\x18ftypmp42'+b'v'*4096;boundary='----youaiBoundary'
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="a.mp4"\r\nContent-Type: video/mp4\r\n\r\n').encode()+video+f'\r\n--{boundary}--\r\n'.encode()
        class Probe:
            returncode=0;stderr=b'Duration: 00:00:12.40, start: 0 Stream #0:0: Video: h264 (High), yuv420p, 1080x1920'
        with tempfile.TemporaryDirectory() as directory,patch.object(server,'REFERENCE_ROOT',Path(directory)):
            result=server.receive_reference_upload(BytesIO(body),len(body),'multipart/form-data; boundary='+boundary,runner=lambda *a,**k:Probe())
            self.assertEqual(result['platform'],'upload');self.assertEqual(result['asset']['sha256'],hashlib.sha256(video).hexdigest())
            self.assertEqual(Path(result['asset']['storagePath']).read_bytes(),video)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()),[result['asset']['sha256']+'.mp4'])
            with self.assertRaises(ValueError):server.receive_reference_upload(BytesIO(body[:-40]),len(body)-40,'multipart/form-data; boundary='+boundary,runner=lambda *a,**k:Probe())
            with self.assertRaises(ValueError):server.receive_reference_upload(BytesIO(body),len(body),'application/json',runner=lambda *a,**k:Probe())
            self.assertEqual(len(list(Path(directory).iterdir())),1)
    def test_non_douyin_links_ask_for_upload_without_calling_the_parser(self):
        with self.assertRaises(server.ReferenceAcquireError) as context:server.acquire_reference('https://v.kuaishou.com/abc',opener=lambda *a,**k:self.fail('parser must not be called'))
        self.assertEqual(context.exception.code,'unsupported_platform');self.assertIn('上传原视频',str(context.exception))
    def test_platform_boundaries_reach_prompt_and_require_storyboard_reconfirmation(self):
        boundary={'version':server._boundary_module.CATALOG['version'],'platforms':['douyin','xiaohongshu']}
        board=self.approved_storyboard();board['contentBoundaries']=boundary
        raw={'idea':'咖啡短片','duration':5,'mood':'温柔治愈','storyboard':board,'contentBoundaries':boundary}
        result=server.validate(raw);prompt=server.ai_prompt(result)
        self.assertIn('抖音：',prompt);self.assertIn('小红书：',prompt)
        raw['contentBoundaries']={'version':boundary['version'],'platforms':['kuaishou']}
        with self.assertRaisesRegex(ValueError,'重新确认分镜'):server.validate(raw)
    def test_background_analysis_results_survive_restart_and_interruption_is_visible(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        ident=uuid.uuid4().hex
        with tempfile.TemporaryDirectory() as directory,patch.object(server,'REFERENCE_ROOT',Path(directory)):
            server.ANALYSIS_JOBS[ident]={'status':'running','startedAt':1}
            with patch.object(server,'analyze_reference',return_value=({'summary':{'pace':'中等'}},False)):
                server.analysis_worker(ident,{'asset':{'sha256':'test'}},'smart')
            del server.ANALYSIS_JOBS[ident]
            self.assertEqual(server.analysis_status(ident)['status'],'done')
            server.ANALYSIS_JOBS[ident]={'status':'running','startedAt':1};server.persist_analysis(ident);del server.ANALYSIS_JOBS[ident]
            self.assertEqual(server.analysis_status(ident)['status'],'failed');self.assertIn('重启',server.analysis_status(ident)['error'])
    def test_content_requirements_and_variable_scene_count_reach_video_prompt(self):
        board=self.approved_storyboard();board['shots']=board['shots'][:2]
        raw={'idea':'猫看雨','duration':12,'mood':'温柔治愈','storyboard':board,'creativeIntent':'保留等待的情绪，不做营销','referenceNotes':'这是我的猫','tone':'细腻安静'}
        value=server.validate(raw);prompt=server.ai_prompt(value)
        self.assertEqual(len(value['storyboard']['shots']),2);self.assertIn('保留等待的情绪',prompt);self.assertIn('这是我的猫',prompt);self.assertEqual(value['tone'],'细腻安静')
        raw['storyboard']['shots']=[]
        with self.assertRaises(ValueError):server.validate(raw)
    def approved_storyboard(self):
        return {'version':1,'status':'approved','referenceMode':'same-topic','shots':[{'role':'开场','narration':'先给结果','visual':'展示结果'},{'role':'展开','narration':'讲清过程','visual':'展示步骤'},{'role':'收束','narration':'评论互动','visual':'回到主题'}]}
    def test_post_limits_allow_analysis_generation_payload_but_bound_each_interface(self):
        self.assertEqual(server.POST_LIMITS['/jobs'],64*1024)
        self.assertGreater(server.POST_LIMITS['/jobs'],4237)
        self.assertLess(server.POST_LIMITS['/references/config/check'],server.POST_LIMITS['/jobs'])
    def test_run_assets_persist_manifest_prompt_storyboard_and_final(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def read(self):return b'{"status":"saved","generationJobId":"db-job"}'
        job=uuid.uuid4().hex;data=server.validate({'idea':'资产样片','duration':2,'mood':'温柔治愈','visualStyle':'纯文字画面','source':{'type':'idea'},'storyboard':self.approved_storyboard(),'mustInclude':'品牌名','avoid':'密钥'})
        server.render(job,data);old=server.ASSET_ROOT;server.ASSET_ROOT=__import__('pathlib').Path(__import__('tempfile').mkdtemp())
        try:
            manifest=server.persist_run_assets(job,data,'local-text',opener=lambda *_a,**_k:Response())
            folder=server.ASSET_ROOT/'runs'/job
            for name in ('final.mp4','manifest.json','analysis.json','storyboard.v1.json','request.json','prompt.txt'):self.assertTrue((folder/name).exists(),name)
            self.assertEqual(manifest['database']['status'],'saved');self.assertEqual(manifest['storyboard']['shots'][0]['role'],'开场');self.assertNotIn('Authorization',(folder/'request.json').read_text(encoding='utf-8'))
            public=server.public_asset_manifest(job,manifest);encoded=__import__('json').dumps(public,ensure_ascii=False)
            self.assertNotIn(str(server.ASSET_ROOT),encoded);self.assertNotIn('requestPath',encoded);self.assertEqual(public['generation']['prompt'],'纯文字画面按批准故事板逐段合成')
        finally:
            server.ASSET_ROOT=old;__import__('shutil').rmtree(folder.parent.parent,ignore_errors=True)
    def test_asset_preview_only_allows_manifest_files_inside_asset_roots(self):
        from pathlib import Path
        import tempfile,shutil,json
        old=server.ASSET_ROOT;root=Path(tempfile.mkdtemp());server.ASSET_ROOT=root;run='a'*32
        try:
            source=root/'sources'/'safe.mp4';source.parent.mkdir();source.write_bytes(b'video')
            frame=root/'keyframes'/'sha'/'0.jpg';frame.parent.mkdir(parents=True);frame.write_bytes(b'image')
            folder=root/'runs'/run;folder.mkdir(parents=True);(folder/'manifest.json').write_text(json.dumps({'source':{'storageUri':str(source)},'analysis':{'keyframes':[str(frame),str(root.parent/'outside.jpg')]}}),encoding='utf-8')
            self.assertEqual(server.asset_preview_file(run,'source'),source.resolve());self.assertEqual(server.asset_preview_file(run,'keyframe',0),frame.resolve())
            self.assertIsNone(server.asset_preview_file(run,'keyframe',1));self.assertIsNone(server.asset_preview_file('../escape','source'))
        finally:server.ASSET_ROOT=old;shutil.rmtree(root,ignore_errors=True)
    def test_validation(self):
        for data in [{}, {'idea':'x','duration':1,'mood':'温柔治愈'}, {'idea':'x','duration':31,'mood':'温柔治愈'}, {'idea':'x','duration':True,'mood':'温柔治愈'}, {'idea':'x'*161,'duration':15,'mood':'温柔治愈'}]:
            with self.assertRaises(ValueError):server.validate(data)
        for duration in (2, 17, 30):
            self.assertEqual(server.validate({'idea':'x','duration':duration,'mood':'温柔治愈'})['duration'],duration)
    def test_text_preserved(self):
        text='下班后，只想静一静。'+('长文案'*35)
        self.assertEqual(''.join(server.segments(text)),text)
        self.assertTrue(all(len(x)<=42 for x in server.segments(text)))
    def test_douyin_metadata_cannot_be_used_as_video_analysis(self):
        data=server.validate({'idea':'参考这个视频','duration':2,'mood':'温柔治愈','visualStyle':'AI 生成画面','storyboard':self.approved_storyboard(),'source':{'type':'douyin','reference':{'status':'acquired','title':'网页标题'}}})
        with self.assertRaisesRegex(ValueError,'尚未完成内容分析'):server.ai_prompt(data)
    def test_approved_storyboard_and_communication_constraints_reach_prompt(self):
        base={'idea':'山药早餐','duration':12,'mood':'温柔治愈','visualStyle':'AI 生成画面','source':{'type':'idea'},'audience':'目标客户','hookStyle':'提出问题','tone':'清晰专业','cta':'评论互动','mustInclude':'蒸熟后粉糯','avoid':'疗效承诺','aiPreference':'画面自然，避免夸张镜头'}
        with self.assertRaisesRegex(ValueError,'确认分镜'):server.validate(base)
        data=server.validate({**base,'storyboard':self.approved_storyboard()});prompt=server.ai_prompt(data)
        for value in ('目标客户','提出问题','清晰专业','评论互动','蒸熟后粉糯','疗效承诺','按已批准分镜执行','画面自然，避免夸张镜头','仅作风格参考'):self.assertIn(value,prompt)
    def test_ai_generation_submits_polls_without_async_header_and_downloads(self):
        class Response:
            def __init__(self,data):self.data=data
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def read(self):return self.data
        requests=[];polls=iter(['PENDING','RUNNING','SUCCEEDED']);phases=[]
        def opener(request,timeout=0):
            requests.append(request)
            if request.full_url.endswith('/video-synthesis'):
                body=__import__('json').loads(request.data)
                self.assertEqual(body['parameters']['duration'],-1)
                self.assertEqual(body['parameters']['ratio'],'1:1')
                self.assertEqual(body['parameters']['resolution'],'1080P')
                self.assertEqual(body['parameters']['audio'],False)
                self.assertEqual(body['parameters']['prompt_extend'],False)
                self.assertEqual(body['parameters']['watermark'],False)
                return Response(b'{"output":{"task_id":"remote-123"}}')
            if request.full_url.endswith('/tasks/remote-123'):
                self.assertIsNone(request.headers.get('X-dashscope-async'))
                status=next(polls)
                video=',"video_url":"https://cdn.example/video.mp4"' if status=='SUCCEEDED' else ''
                return Response(('{"output":{"task_status":"'+status+'"'+video+'}}').encode())
            return Response(b'\x00\x00\x00\x18ftypmock-video')
        old=os.environ.get('YOUAI_QIANWEN_API_KEY');os.environ['YOUAI_QIANWEN_API_KEY']='test-key'
        try:
            job_id=uuid.uuid4().hex
            task=server.generate_qianwen(job_id,server.validate({'idea':'雨天咖啡','duration':2,'mood':'温柔治愈','visualStyle':'AI 生成画面','generation':{'resolution':'1080P','ratio':'1:1','audio':False,'promptExtend':False,'watermark':False,'smartDuration':True}}),opener,lambda _:phases.append(server.JOBS[job_id]['phase']))
            self.assertEqual(task,'remote-123')
            self.assertIn(b'ftyp',(server.ROOT/job_id/'video.mp4').read_bytes())
            self.assertEqual(requests[0].headers['Authorization'],'Bearer test-key')
            self.assertEqual(phases,['queued','generating'])
            self.assertEqual(server.JOBS[job_id]['phase'],'downloading')
        finally:
            if old is None:os.environ.pop('YOUAI_QIANWEN_API_KEY',None)
            else:os.environ['YOUAI_QIANWEN_API_KEY']=old
    def test_reference_modes_send_real_video_or_frames_to_provider_input(self):
        sample=server.render(uuid.uuid4().hex,server.validate({'idea':'参考媒体','duration':2,'mood':'温柔治愈'}));data=sample.read_bytes();sha=__import__('hashlib').sha256(data).hexdigest();stored=server.REFERENCE_ROOT/f'{sha}.mp4';stored.write_bytes(data)
        base={'source':{'type':'douyin','reference':{'status':'analyzed','asset':{'sha256':sha},'analysis':{'summary':{'durationSeconds':2},'visual':{'evidenceTimes':[0,.8,1.6]}}}},'storyboard':self.approved_storyboard()}
        try:
            base['storyboard']['referenceMode']='reference-video'
            old_state,old_credentials=server.REFERENCE_RELAY_STATE,server.REFERENCE_RELAY_CREDENTIALS
            server.REFERENCE_RELAY_STATE=server.REFERENCE_ROOT/'missing-relay-state.json';server.REFERENCE_RELAY_CREDENTIALS=server.REFERENCE_ROOT/'missing-relay-credentials.env'
            try:
                with self.assertRaisesRegex(ValueError,'HTTPS 素材地址'):server.generation_reference_media(base)
            finally:server.REFERENCE_RELAY_STATE,server.REFERENCE_RELAY_CREDENTIALS=old_state,old_credentials
            old_base=os.environ.get('YOUAI_PUBLIC_ASSET_BASE_URL');old_secret=os.environ.get('YOUAI_REFERENCE_MEDIA_SECRET');os.environ['YOUAI_PUBLIC_ASSET_BASE_URL']='https://media.example.com';os.environ['YOUAI_REFERENCE_MEDIA_SECRET']='test-secret'
            try:
                video=server.generation_reference_media(base);self.assertEqual(len(video),1);self.assertEqual(video[0]['type'],'reference_video');self.assertTrue(video[0]['url'].startswith(f'https://media.example.com/reference-assets/{sha}.mp4?'))
                self.assertEqual(server.verified_reference_video(urlparse(video[0]['url']).path+'?'+urlparse(video[0]['url']).query),stored.resolve())
            finally:
                if old_base is None:os.environ.pop('YOUAI_PUBLIC_ASSET_BASE_URL',None)
                else:os.environ['YOUAI_PUBLIC_ASSET_BASE_URL']=old_base
                if old_secret is None:os.environ.pop('YOUAI_REFERENCE_MEDIA_SECRET',None)
                else:os.environ['YOUAI_REFERENCE_MEDIA_SECRET']=old_secret
            base['storyboard']['referenceMode']='visual-style';frames=server.generation_reference_media(base);self.assertEqual(len(frames),3);self.assertTrue(all(x['type']=='reference_image' and x['url'].startswith('data:image/jpeg;base64,') for x in frames))
            for mode in ('content-structure','same-topic'):
                base['storyboard']['referenceMode']=mode;self.assertEqual(server.generation_reference_media(base),[])
            stored.unlink();base['storyboard']['referenceMode']='reference-video'
            with self.assertRaisesRegex(ValueError,'已验证的参考原片'):server.generation_reference_media(base)
        finally:stored.unlink(missing_ok=True)
    def test_wan3_generation_options_and_first_last_frames_are_validated(self):
        with self.assertRaisesRegex(ValueError,'生成参数无效'):server.validate({'idea':'参数','duration':5,'mood':'温柔治愈','generation':{'resolution':'8K'}})
        with self.assertRaisesRegex(ValueError,'AI个人偏好'):server.validate({'idea':'参数','duration':5,'mood':'温柔治愈','aiPreference':'x'*501})
        with self.assertRaisesRegex(ValueError,'AI个人偏好'):server.validate({'idea':'参数','duration':5,'mood':'温柔治愈','aiPreference':3})
        with self.assertRaisesRegex(ValueError,'参考原片'):server.validate({'idea':'参数','duration':5,'mood':'温柔治愈','generation':{'mode':'first-last-frame'}})
        source={'type':'douyin','reference':{'status':'analyzed','analysis':{'summary':{'durationSeconds':14.6}}}}
        board=self.approved_storyboard();board['referenceMode']='reference-video'
        with self.assertRaisesRegex(ValueError,'总时长不能超过 30 秒'):server.validate({'idea':'参数','duration':16,'mood':'温柔治愈','source':source,'storyboard':board})
        smart=server.validate({'idea':'参数','duration':16,'mood':'温柔治愈','source':source,'storyboard':board,'generation':{'smartDuration':True}});self.assertTrue(smart['generation']['smartDuration'])
        sample=server.render(uuid.uuid4().hex,server.validate({'idea':'首尾帧','duration':2,'mood':'温柔治愈'}));data=sample.read_bytes();sha=__import__('hashlib').sha256(data).hexdigest();stored=server.REFERENCE_ROOT/f'{sha}.mp4';stored.write_bytes(data)
        try:
            media=server.generation_reference_media({'generation':{'mode':'first-last-frame'},'source':{'type':'douyin','reference':{'asset':{'sha256':sha},'analysis':{'summary':{'durationSeconds':2}}}},'storyboard':board})
            self.assertEqual([item['type'] for item in media],['first_frame','last_frame']);self.assertTrue(all(item['url'].startswith('data:image/jpeg;base64,') for item in media))
        finally:stored.unlink(missing_ok=True)
    def test_small_reference_duration_overrun_is_normalized_and_reused(self):
        sample=server.render(uuid.uuid4().hex,server.validate({'idea':'边界素材','duration':2,'mood':'温柔治愈'}));data=sample.read_bytes();sha=__import__('hashlib').sha256(data).hexdigest();stored=server.REFERENCE_ROOT/f'{sha}.mp4';stored.write_bytes(data);derived=None;lineage=server.REFERENCE_ROOT/f'{sha}.reference-video.json'
        try:
            derived_sha,derived,changed=server.normalized_reference_video(sha,stored,15.09);self.assertTrue(changed);self.assertNotEqual(derived_sha,sha);self.assertTrue(derived.is_file());self.assertLessEqual(server._probe_video(derived)['durationSeconds'],15);self.assertTrue(lineage.is_file())
            cached_sha,cached,cached_changed=server.normalized_reference_video(sha,stored,15.09);self.assertEqual(cached_sha,derived_sha);self.assertEqual(cached,derived);self.assertTrue(cached_changed)
            with self.assertRaisesRegex(ValueError,'当前素材为 15.60 秒'):server.normalized_reference_video(sha,stored,15.6)
        finally:
            stored.unlink(missing_ok=True);lineage.unlink(missing_ok=True)
            if derived:derived.unlink(missing_ok=True)
    def test_mcp_download_tool_uses_the_mcp_key_skips_comments_and_returns_a_signed_link(self):
        import json as _json
        cfg=server.MCP_GATEWAY.root/'config.json';server.MCP_GATEWAY.root.mkdir(parents=True,exist_ok=True)
        cfg.write_text(_json.dumps({'tokenSha256':'0'*64,'dtkKey':'dtk_mcp_key','dailyLimit':50}))
        seen={};sha='c'*64
        def fake(value,parser_config=None,comments=True,**k):
            seen.update(value=value,config=parser_config,comments=comments)
            return {'status':'acquired','kind':'video','asset':{'sha256':sha,'sizeBytes':1234,'media':{'durationSeconds':6.7,'width':576,'height':1024,'hasAudio':True}},
                    'source':{'contentId':'769','description':'各位 #抖店','hashtags':['抖店'],'author':{'nickname':'阿禾','followerCount':10,'uid':'secret-uid'},'stats':{'digg_count':285,'comment_count':803,'collect_count':119,'share_count':29}}}
        old=server.acquire_reference;server.acquire_reference=fake
        try:
            out=server.mcp_download({'url':' https://v.douyin.com/abc/ '})
            self.assertEqual(seen['value'],'https://v.douyin.com/abc/');self.assertFalse(seen['comments']);self.assertEqual(seen['config']['token'],'dtk_mcp_key')
            self.assertTrue(out['downloadUrl'].startswith('https://youai888.top/youai/mcp/files/'+sha+'.mp4?e='))
            e=out['downloadUrl'].split('e=')[1].split('&')[0];s=out['downloadUrl'].split('&s=')[1]
            self.assertTrue(server.MCP_GATEWAY.file_allowed(sha,e,s))
            self.assertEqual(out['stats'],{'likes':285,'comments':803,'collects':119,'shares':29});self.assertEqual(out['author'],{'nickname':'阿禾','followerCount':10})
            self.assertEqual(out['video']['durationSeconds'],6.7);self.assertIn('北京时间',out['expiresAt'])
            with self.assertRaises(server._mcp_module.ToolError):server.mcp_download({'url':''})
            def refuse(*a,**k):raise server.ReferenceAcquireError('平台已解析视频，但媒体下载受限','media_download_failed','retry_or_upload')
            server.acquire_reference=refuse
            with self.assertRaisesRegex(server._mcp_module.ToolError,'媒体下载受限'):server.mcp_download({'url':'https://v.douyin.com/x/'})
            self.assertIn('download_video',server.MCP_GATEWAY.local)
        finally:
            server.acquire_reference=old;cfg.unlink(missing_ok=True)
    def test_reference_preview_is_compressed_once_and_reused(self):
        data=server.render(uuid.uuid4().hex,server.validate({'idea':'预览','duration':2,'mood':'温柔治愈'})).read_bytes();sha=__import__('hashlib').sha256(data).hexdigest()
        stored=server.REFERENCE_ROOT/f'{sha}.mp4';stored.write_bytes(data);reference={'asset':{'sha256':sha,'storagePath':str(stored)}}
        try:
            first=server.reference_preview('u1',reference);self.assertRegex(first['url'],r'^/reference-assets/[a-f0-9]{64}\.mp4$');self.assertGreater(first['bytes'],0)
            def refuse(*a,**k):raise AssertionError('preview must be reused')
            self.assertEqual(server.reference_preview('u1',reference,runner=refuse)['url'],first['url'])
        finally:
            marker=server.REFERENCE_ROOT/(sha+'.preview');digest=marker.read_text().strip() if marker.exists() else ''
            marker.unlink(missing_ok=True);stored.unlink(missing_ok=True)
            if digest:(server.REFERENCE_ROOT/(digest+'.mp4')).unlink(missing_ok=True)
    def test_reference_relay_reads_external_state_and_rejects_expired_signature(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            old_state,old_credentials=server.REFERENCE_RELAY_STATE,server.REFERENCE_RELAY_CREDENTIALS
            server.REFERENCE_RELAY_STATE=__import__('pathlib').Path(folder)/'state.json';server.REFERENCE_RELAY_CREDENTIALS=__import__('pathlib').Path(folder)/'relay.env'
            server.REFERENCE_RELAY_STATE.write_text('{"publicBaseUrl":"https://relay.example.com"}',encoding='utf-8')
            server.REFERENCE_RELAY_CREDENTIALS.write_text('YOUAI_REFERENCE_MEDIA_SECRET=external-secret\n',encoding='utf-8')
            try:
                url=server.signed_reference_video_url('a'*64,now=100)
                self.assertTrue(url.startswith('https://relay.example.com/reference-assets/'))
                self.assertIsNone(server.verified_reference_video(url,now=1901))
            finally:server.REFERENCE_RELAY_STATE,server.REFERENCE_RELAY_CREDENTIALS=old_state,old_credentials
    def test_reference_relay_status_checks_public_health(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*_):pass
        old_base=os.environ.get('YOUAI_PUBLIC_ASSET_BASE_URL');old_secret=os.environ.get('YOUAI_REFERENCE_MEDIA_SECRET')
        os.environ['YOUAI_PUBLIC_ASSET_BASE_URL']='https://relay.example.com';os.environ['YOUAI_REFERENCE_MEDIA_SECRET']='secret'
        try:self.assertEqual(server.reference_relay_status(lambda *_a,**_k:Response())['ready'],True)
        finally:
            if old_base is None:os.environ.pop('YOUAI_PUBLIC_ASSET_BASE_URL',None)
            else:os.environ['YOUAI_PUBLIC_ASSET_BASE_URL']=old_base
            if old_secret is None:os.environ.pop('YOUAI_REFERENCE_MEDIA_SECRET',None)
            else:os.environ['YOUAI_REFERENCE_MEDIA_SECRET']=old_secret
    def test_douyin_reference_expands_and_requires_readable_video_page(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def geturl(self):return 'https://www.iesdouyin.com/share/video/7397005934863732019/'
            def read(self,_):return '<html><title>咖啡店的一天 - 抖音</title><meta name="description" content="记录一杯咖啡的制作过程"></html>'.encode()
        result=server.read_reference('复制打开抖音 https://v.douyin.com/abc/ 看视频',lambda *_args,**_kwargs:Response())
        self.assertEqual(result['status'],'identified')
        self.assertEqual(result['videoId'],'7397005934863732019')
        self.assertIn('咖啡店',result['title'])
        with self.assertRaises(ValueError):server.reference_url('https://example.com/video')
        self.assertEqual(server.reference_url('https://v.douyin.com/abc/，复制打开抖音'),'https://v.douyin.com/abc/')
    def test_reference_acquisition_requires_parser_or_valid_download(self):
        class Page:
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def geturl(self):return 'https://www.iesdouyin.com/share/video/7397005934863732019/'
            def read(self,_=None):return b'<html><title>coffee</title></html>'
        old=os.environ.pop('YOUAI_REFERENCE_PARSER_URL',None)
        try:
            with self.assertRaisesRegex(server.ReferenceAcquireError,'尚未配置'):server.acquire_reference('https://v.douyin.com/abc/',lambda *_a,**_k:Page())
        finally:
            if old is not None:os.environ['YOUAI_REFERENCE_PARSER_URL']=old
        for url in ('http://media.example/video.mp4','https://127.0.0.1/video.mp4','https://host.local/video.mp4'):
            with self.assertRaises(ValueError):server._safe_media_url(url)
    def test_reference_acquisition_hashes_deduplicates_and_probes_media(self):
        sample=server.render(uuid.uuid4().hex,server.validate({'idea':'样片','duration':2,'mood':'温柔治愈'})).read_bytes()
        class Response:
            def __init__(self,data,url=''):self.data=data;self.url=url
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def geturl(self):return self.url
            def read(self,size=-1):
                if size<0:data,self.data=self.data,b'';return data
                data,self.data=self.data[:size],self.data[size:];return data
        def opener(request,timeout=0):
            url=request.full_url
            if 'v.douyin.com' in url:return Response(b'<title>sample</title>','https://www.iesdouyin.com/share/video/7397005934863732019/')
            if '/api/v1/parse?wait=30' in url:return Response(b'{"success":true,"data":{"media":{"video":{"url":"https://media.example/sample.mp4"}}}}')
            return Response(sample)
        old=os.environ.get('YOUAI_REFERENCE_PARSER_URL');os.environ['YOUAI_REFERENCE_PARSER_URL']='https://parser.local'
        try:
            first=server.acquire_reference('https://v.douyin.com/abc/',opener)
            second=server.acquire_reference('https://v.douyin.com/abc/',opener)
            self.assertEqual(first['status'],'acquired');self.assertEqual(first['asset']['sha256'],second['asset']['sha256'])
            self.assertTrue(os.path.exists(first['asset']['storagePath']));self.assertGreater(first['asset']['sizeBytes'],1024)
        finally:
            if old is None:os.environ.pop('YOUAI_REFERENCE_PARSER_URL',None)
            else:os.environ['YOUAI_REFERENCE_PARSER_URL']=old
    def test_parser_settings_allows_explicit_container_http_host(self):
        old_url=os.environ.get('YOUAI_REFERENCE_PARSER_URL')
        old_hosts=os.environ.get('YOUAI_REFERENCE_PARSER_INTERNAL_HTTP_HOSTS')
        os.environ['YOUAI_REFERENCE_PARSER_URL']='http://api:8000'
        os.environ['YOUAI_REFERENCE_PARSER_INTERNAL_HTTP_HOSTS']='api, parser-internal'
        try:
            base,_=server._parser_settings()
            self.assertEqual(base,'http://api:8000')
            with self.assertRaises(ValueError):server._parser_settings({'baseUrl':'http://api.evil.example:8000'})
            with self.assertRaises(ValueError):server._parser_settings({'baseUrl':'http://10.0.0.1:8000'})
            with self.assertRaises(ValueError):server._parser_settings({'baseUrl':'http://user:password@api:8000'})
        finally:
            if old_url is None:os.environ.pop('YOUAI_REFERENCE_PARSER_URL',None)
            else:os.environ['YOUAI_REFERENCE_PARSER_URL']=old_url
            if old_hosts is None:os.environ.pop('YOUAI_REFERENCE_PARSER_INTERNAL_HTTP_HOSTS',None)
            else:os.environ['YOUAI_REFERENCE_PARSER_INTERNAL_HTTP_HOSTS']=old_hosts
    def test_reference_download_uses_video_candidates_referer_and_falls_back_after_403(self):
        sample=server.render(uuid.uuid4().hex,server.validate({'idea':'回退样片','duration':2,'mood':'温柔治愈'})).read_bytes();seen=[]
        class Response:
            def __init__(self,data):self.data=data
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def read(self,size=-1):
                if size<0:data,self.data=self.data,b'';return data
                data,self.data=self.data[:size],self.data[size:];return data
        def opener(request,timeout=0):
            seen.append(request)
            if '/api/v1/parse?wait=30' in request.full_url:
                return Response(b'{"success":true,"data":{"media":{"video":{"url":"https://cdn.example/blocked.mp4","urls":["https://cdn.example/blocked.mp4","https://cdn.example/working.mp4"]},"covers":[{"url":"https://images.example/cover.jpeg"}]}}}')
            if request.full_url.endswith('blocked.mp4'):raise HTTPError(request.full_url,403,'forbidden',{},BytesIO())
            return Response(sample)
        result=server.acquire_reference('https://v.douyin.com/abc/',opener,parser_config={'baseUrl':'https://parser.example.com'})
        downloads=[item for item in seen if 'cdn.example' in item.full_url]
        self.assertEqual(result['status'],'acquired');self.assertEqual(len(downloads),2)
        self.assertEqual(downloads[0].headers['Referer'],'https://www.douyin.com/')
        self.assertFalse(any('images.example' in item.full_url for item in seen))
    def test_reference_download_failure_is_actionable_and_hides_signed_url(self):
        def opener(request,timeout=0):
            if '/api/v1/parse?wait=30' in request.full_url:return type('R',(),{'__enter__':lambda s:s,'__exit__':lambda *_:None,'read':lambda s:b'{"data":{"media":{"video":{"url":"https://cdn.example/private-signature.mp4"}}}}'})()
            raise HTTPError(request.full_url,403,'forbidden',{},BytesIO())
        with self.assertRaises(server.ReferenceAcquireError) as caught:server.acquire_reference('https://v.douyin.com/abc/',opener,parser_config={'baseUrl':'https://parser.example.com'})
        self.assertEqual(caught.exception.code,'media_download_failed');self.assertEqual(caught.exception.action,'retry_or_upload')
        self.assertNotIn('private-signature',str(caught.exception))
    def test_expired_short_link_preserves_parser_reason_without_leaking_secret(self):
        seen=[]
        def opener(request,timeout=0):
            seen.append(request)
            body=b'{"success":false,"error":{"code":"INVALID_URL","details":{"reason":"short_link_dead_end","resolved_to":"https://www.douyin.com/"}}}'
            raise HTTPError(request.full_url,422,'invalid',{},BytesIO(body))
        with self.assertRaises(server.ReferenceAcquireError) as caught:
            server.acquire_reference('文案 https://v.douyin.com/dead/ 复制打开',opener,parser_config={'baseUrl':'https://parser.example.com','token':'private-token'})
        self.assertEqual(caught.exception.code,'short_link_expired');self.assertEqual(caught.exception.action,'replace_or_upload')
        self.assertIn('短链已失效',str(caught.exception));self.assertNotIn('private-token',str(caught.exception))
        self.assertEqual(__import__('json').loads(seen[0].data)['url'],'https://v.douyin.com/dead/')
        self.assertEqual(len(seen),1,'parser must receive the original short link before any brittle page expansion')
    def test_parser_configuration_contract_and_secret_safe_errors(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def read(self):return b'{"paths":{"/api/v1/parse":{"post":{}}}}'
        seen=[]
        def opener(request,timeout=0):seen.append(request);return Response()
        result=server.check_parser({'baseUrl':'https://parser.example.com','token':'private-token'},opener)
        self.assertEqual(result['status'],'ready');self.assertEqual(result['service'],'douyin-tiktok-download-api-v5');self.assertEqual(seen[0].headers['Authorization'],'Bearer private-token')
        server.check_parser({'baseUrl':'http://127.0.0.1:8000','token':'private-token'},opener)
        for value in ({'baseUrl':'http://parser.example.com'},{'baseUrl':'https://user:pass@parser.example.com'},{'baseUrl':'https://parser.example.com','token':'bad\nheader'}):
            with self.assertRaises(ValueError) as caught:server.check_parser(value,opener)
            self.assertNotIn('private-token',str(caught.exception))
    def test_reference_analysis_uses_video_evidence_and_reuses_sha_cache(self):
        path=server.render(uuid.uuid4().hex,server.validate({'idea':'分析样片','duration':2,'mood':'温柔治愈'}))
        data=path.read_bytes();sha=__import__('hashlib').sha256(data).hexdigest();stored=server.REFERENCE_ROOT/f'{sha}.mp4';stored.write_bytes(data)
        reference={'status':'acquired','asset':{'sha256':sha,'storagePath':str(stored),'sizeBytes':len(data),'media':server._probe_video(stored)}}
        try:
            phases=[];analysis,reused=server.analyze_reference_legacy(reference,transcriber=lambda _:{'status':'available','language':'zh','text':'这是自动转写文案','confidence':.7,'segments':[{'start':0,'end':1,'text':'这是自动转写文案'}]},progress=lambda phase,_:phases.append(phase))
            self.assertFalse(reused);self.assertEqual(analysis['version'],'reference-analysis-v1');self.assertEqual(analysis['analyzerVersion'],'content-evidence-3');self.assertEqual(analysis['assetSha256'],sha);self.assertEqual(len(analysis['structure']),3);self.assertGreaterEqual(analysis['shots']['representativeFrameCount'],4);self.assertEqual(analysis['sampling']['mode'],'smart');self.assertIn('这是自动转写文案',analysis['summary']['detectedSpeech']);self.assertEqual(analysis['confidence']['transcript'],.7);self.assertTrue(any('需要用户核对' in item for item in analysis['limitations']));self.assertEqual(phases,['extracting','transcribing','understanding','structuring'])
            cached,reused=server.analyze_reference_legacy(reference,transcriber=lambda _:self.fail('cache must avoid transcription'))
            self.assertIn('画面变化不等于',analysis['summary']['pace'])
            self.assertTrue(reused);self.assertEqual(cached['assetSha256'],sha)
            (server.REFERENCE_ROOT/f'{sha}.analysis.smart.json').unlink()
            def unavailable(*args):raise server._ai_module.AIError('model')
            failed,reused=server.analyze_reference_legacy(reference,transcriber=lambda _:{'status':'available','text':'歌曲歌词'},understander=unavailable)
            self.assertFalse(reused);self.assertEqual(failed['understanding']['errorCode'],'model')
            self.assertIn('模型不存在或未开通',failed['understanding']['error']);self.assertEqual(failed['structure'],[])
            with self.assertRaises(ValueError):server.analyze_reference_legacy({'status':'acquired','asset':{'sha256':sha,'storagePath':str(path)}})
        finally:
            stored.unlink(missing_ok=True);(server.REFERENCE_ROOT/f'{sha}.analysis.smart.json').unlink(missing_ok=True)
    def test_reference_frame_sampling_profiles_and_partial_failure_fallback(self):
        self.assertEqual([p['label'] for p in server.FRAME_SAMPLING.values()],['智能','精简','正常','精细','超细'])
        self.assertEqual(server.frame_sampling_plan(15,'ultra')['targetCount'],16)
        self.assertEqual(server.frame_sampling_plan(600,'ultra')['targetCount'],24)
        self.assertEqual(server.frame_sampling_plan(15)['mode'],'smart')
        for mode in server.FRAME_SAMPLING:
            times=server.frame_sampling_plan(.1,mode)['times'];self.assertTrue(all(0<t<.1 for t in times))
        self.assertEqual(server.frame_sampling_plan(15,'smart')['targetCount'],6);self.assertEqual(server.frame_sampling_plan(15,'sparse')['targetCount'],4);self.assertEqual(server.frame_sampling_plan(15,'standard')['targetCount'],6);self.assertEqual(server.frame_sampling_plan(15,'detailed')['targetCount'],9)
        self.assertGreater(server.frame_sampling_plan(15,'smart')['times'][0],0);self.assertLess(server.frame_sampling_plan(15,'smart')['times'][-1],15)
        with self.assertRaisesRegex(ValueError,'采样档位'):server.frame_sampling_plan(15,'unknown')
        path=server.render(uuid.uuid4().hex,server.validate({'idea':'容错抽帧','duration':15,'mood':'温柔治愈'}));data=path.read_bytes();sha=__import__('hashlib').sha256(data).hexdigest();stored=server.REFERENCE_ROOT/f'{sha}.mp4';stored.write_bytes(data)
        reference={'status':'acquired','asset':{'sha256':sha,'storagePath':str(stored),'sizeBytes':len(data),'media':server._probe_video(stored)}};real_runner=subprocess.run
        def runner(command,**kwargs):
            if str(command[-1]).endswith('00.jpg'):return type('Failed',(),{'returncode':1,'stderr':b'simulated frame failure'})()
            return real_runner(command,**kwargs)
        try:
            analysis,reused=server.analyze_reference_legacy(reference,runner=runner,transcriber=lambda _:{'status':'silent','confidence':0,'text':'','segments':[]},sampling='smart')
            self.assertFalse(reused);self.assertEqual(analysis['sampling']['targetCount'],6);self.assertEqual(analysis['sampling']['successCount'],5);self.assertEqual(analysis['sampling']['failureCount'],1);self.assertTrue(any('采样点解码失败' in item for item in analysis['limitations']))
        finally:
            stored.unlink(missing_ok=True);(server.REFERENCE_ROOT/f'{sha}.analysis.smart.json').unlink(missing_ok=True)
    def test_real_mp4(self):
        output=server.render(uuid.uuid4().hex,server.validate({'idea':'下班后，只想一个人静一静。','duration':15,'mood':'温柔治愈'}))
        data=output.read_bytes()
        self.assertIn(b'ftyp',data[:32])
        self.assertLess(data.index(b'moov'),data.index(b'mdat'))
        result=subprocess.run([server.imageio_ffmpeg.get_ffmpeg_exe(),'-v','info','-i',str(output),'-f','null','-'],capture_output=True)
        self.assertEqual(result.returncode,0)
        self.assertIn(b'360x640',result.stderr)
        self.assertIn(b'00:00:15.',result.stderr)
        print('Rendered and decoded:',output)

    def test_creation_tools_reuse_source_and_generate_audio_cover_transcript(self):
        sample=server.render(uuid.uuid4().hex,server.validate({'idea':'工具样片','duration':2,'mood':'温柔治愈'}));with_audio=sample.parent/'with-audio.mp4'
        subprocess.run([server.imageio_ffmpeg.get_ffmpeg_exe(),'-y','-v','error','-i',str(sample),'-f','lavfi','-i','sine=frequency=440:duration=2','-shortest','-c:v','copy','-c:a','aac',str(with_audio)],check=True,capture_output=True)
        data=with_audio.read_bytes();sha=__import__('hashlib').sha256(data).hexdigest();stored=server.REFERENCE_ROOT/f'{sha}.mp4';stored.write_bytes(data)
        reference={'status':'acquired','title':'测试标题','asset':{'sha256':sha,'storagePath':str(stored),'sizeBytes':len(data),'media':server._probe_video(stored)}}
        original=server.acquire_reference;acquisitions=[]
        def acquire(*_a,**_k):acquisitions.append(True);return reference
        server.acquire_reference=acquire
        try:
            download=server.run_creation_tool('download','https://v.douyin.com/test/');self.assertEqual(download['kind'],'video');self.assertIn(sha,download['assetUrl'])
            eraser=server.run_creation_tool('eraser','https://v.douyin.com/test/');self.assertIn('无水印原片',eraser['message']);self.assertTrue(eraser['sourceReused'])
            before=len(acquisitions);server.run_creation_tool('download','https://v.douyin.com/test/',cache_scope='user-a');self.assertEqual(len(acquisitions),before+1)
            server.run_creation_tool('download','https://v.douyin.com/test/',cache_scope='user-a');self.assertEqual(len(acquisitions),before+1)
            server.run_creation_tool('download','https://v.douyin.com/test/',cache_scope='user-b');self.assertEqual(len(acquisitions),before+2)
            transcript=server.run_creation_tool('transcript','https://v.douyin.com/test/',transcriber=lambda _:{'status':'available','text':'自动转写','segments':[]});self.assertEqual(transcript['transcript']['text'],'自动转写')
            cache=server.TOOL_ROOT/sha/'transcript.json'
            cache.write_text(json.dumps({'status':'unavailable'}))
            with self.assertRaisesRegex(ValueError,'稍后重试'):
                server.run_creation_tool('transcript','https://v.douyin.com/test/',transcriber=lambda _:{'status':'unavailable'})
            recovered=server.run_creation_tool('transcript','https://v.douyin.com/test/',transcriber=lambda _:{'status':'available','text':'恢复后的真实音轨','segments':[]})
            self.assertEqual(recovered['transcript']['text'],'恢复后的真实音轨')
            cached=server.run_creation_tool('transcript','https://v.douyin.com/test/',transcriber=lambda _:self.fail('successful transcript should be reused'))
            self.assertEqual(cached['transcript']['text'],'恢复后的真实音轨')
            audio=server.run_creation_tool('audio','https://v.douyin.com/test/');self.assertEqual(audio['kind'],'audio');self.assertTrue((server.TOOL_ROOT/sha/'audio.mp3').exists())
            cover=server.run_creation_tool('cover','https://v.douyin.com/test/');self.assertEqual(cover['kind'],'image');self.assertTrue((server.TOOL_ROOT/sha/'cover.jpg').exists())
            for name in ('source.mp4','audio.mp3','cover.jpg'):
                path,mime=server.creation_tool_asset(sha,name);self.assertTrue(path.is_file());self.assertTrue(mime)
            self.assertEqual(server.creation_tool_asset('../escape','source.mp4'),(None,None));self.assertEqual(server.creation_tool_asset(sha,'transcript.json'),(None,None))
            with self.assertRaisesRegex(ValueError,'不支持'):server.run_creation_tool('unknown','x')
        finally:
            server.acquire_reference=original;stored.unlink(missing_ok=True);shutil.rmtree(server.TOOL_ROOT/sha,ignore_errors=True);shutil.rmtree(server.TOOL_ROOT/'url-index',ignore_errors=True)

if __name__=='__main__':unittest.main()
