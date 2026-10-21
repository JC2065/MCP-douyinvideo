import importlib.util,io,json,tempfile,unittest,threading
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
spec=importlib.util.spec_from_file_location('auth',Path(__file__).with_name('wechat-auth.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
    def test_trial_accounts_are_owned_marked_and_switchable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'config';config.write_text(json.dumps({'appId':'wx','appSecret':'secret'}))
            openid=['owner-openid'];auth=m.WechatAuth(config,root/'auth.sqlite',opener=lambda *a,**k:io.BytesIO(json.dumps({'openid':openid[0]}).encode()))
            real=auth.login('valid-code');self.assertFalse(real['trial'])
            trial=auth.create_trial(real['userId']);self.assertTrue(trial['trial']);self.assertTrue(trial['phoneBound']);self.assertNotEqual(trial['userId'],real['userId'])
            self.assertRegex(trial['trialPhone'],r'^100\d{8}$');self.assertEqual(auth.user(trial['token']),trial['userId']);self.assertTrue(auth.is_trial(trial['userId']));self.assertFalse(auth.is_trial(real['userId']))
            self.assertEqual(auth.trial_owner(auth.create_trial(trial['userId'])['userId']),real['userId'])   # generated from a trial account still belongs to the real owner
            self.assertEqual(auth.login('valid-code',trial['userId'])['userId'],trial['userId'])
            self.assertEqual(auth.login('valid-code','not-a-uuid')['userId'],real['userId'])
            openid[0]='someone-else';self.assertNotEqual(auth.login('valid-code',trial['userId'])['userId'],trial['userId'])
            openid[0]='owner-openid';self.assertEqual(len(auth.trial_accounts()),2);self.assertEqual(auth.trial_users(),{r['userId'] for r in auth.trial_accounts()})
            self.assertFalse(auth.set_trial_enabled(False));self.assertIsNone(auth.user(trial['token']))
            self.assertEqual(auth.login('valid-code',trial['userId'])['userId'],real['userId'])
            with self.assertRaises(m.LoginError):auth.create_trial(real['userId'])
            auth.set_trial_enabled(True);auth.TRIAL_LIMIT=2
            with self.assertRaises(m.LoginError):auth.create_trial(real['userId'])
    def test_edit_profile_and_unverified_email_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);auth=m.WechatAuth(root/'config',root/'auth.sqlite')
            auth.profile('owner');value=auth.update_profile('owner',{'nickname':'新昵称','avatar':3,'email':'creator@example.com'})
            self.assertEqual(value['nickname'],'新昵称');self.assertEqual(value['avatar'],3);self.assertEqual(value['email'],'creator@example.com');self.assertFalse(value['emailVerified'])
            self.assertEqual(m.WechatAuth(root/'config',root/'auth.sqlite').profile('owner')['email'],value['email']);self.assertEqual(auth.profile('other')['email'],'')
            for invalid in [{'nickname':'','avatar':3,'email':''},{'nickname':'a','avatar':True,'email':''},{'nickname':'a','avatar':0,'email':'bad@email'},{'nickname':'a','avatar':0,'email':'a@b.com','userId':'other'}]:
                with self.assertRaises(m.LoginError):auth.update_profile('owner',invalid)

    def test_ownership_and_signed_media_are_persistent_and_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);now=[100];auth=m.WechatAuth(root/'config',root/'sessions',clock=lambda:now[0])
            run='a'*32;path='/assets/'+run+'/final.mp4';auth.claim('user-a','run:'+run)
            self.assertTrue(auth.owns('user-a','run:'+run));self.assertFalse(auth.owns('user-b','run:'+run))
            url=auth.signed_url('user-a',path);self.assertEqual(auth.media_user(url),'user-a')
            self.assertIsNone(auth.media_user(url.replace('user-a','user-b')));self.assertIsNone(auth.media_user(url.replace('/final.mp4','/secret.mp4')))
            restored=m.WechatAuth(root/'config',root/'sessions',clock=lambda:now[0]);self.assertEqual(restored.media_user(url),'user-a')
            now[0]=3700;self.assertIsNone(restored.media_user(url))
            sha='f'*64;reference={'asset':{'sha256':sha,'storagePath':'trusted-path'},'status':'acquired'};auth.remember('user-a',reference)
            self.assertEqual(auth.reference('user-a',sha)['asset']['storagePath'],'trusted-path')
            with self.assertRaises(m.LoginError):auth.reference('user-b',sha)
            auth.remember('user-b',{'visual':'/assets/'+run+'/final.mp4'});self.assertFalse(auth.owns('user-b','run:'+run))
    def test_http_login_identity_and_logout(self):
        server_spec=importlib.util.spec_from_file_location('video_auth_test',Path(__file__).with_name('video-server.py'));server=importlib.util.module_from_spec(server_spec);server_spec.loader.exec_module(server)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'config';config.write_text(json.dumps({'appId':'wx','appSecret':'secret'}))
            server.AUTH=server._auth_module.WechatAuth(config,root/'sessions',opener=lambda *a,**k:io.BytesIO(b'{"openid":"verified-user"}'))
            http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(http.server_port)
            try:
                with urlopen(base+'/client-config') as response:self.assertEqual(json.load(response)['schemaVersion'],1)
                with urlopen(Request(base+'/auth/login',data=b'{"code":"valid-code"}',headers={'Content-Type':'application/json'})) as response:login=json.load(response)
                headers={'Authorization':'Bearer '+login['token']}
                with urlopen(Request(base+'/auth/me',headers=headers)) as response:self.assertEqual(json.load(response)['userId'],login['userId'])
                with self.assertRaises(HTTPError) as unbound:urlopen(Request(base+'/analysis-preferences',headers=headers))
                self.assertEqual(unbound.exception.code,403)
                self.assertEqual(json.load(unbound.exception)['code'],'PHONE_REQUIRED')
                with self.assertRaises(HTTPError) as summary_denied:urlopen(Request(base+'/hotspots/summary',data=b'{"platform":"x"}',headers=headers))
                self.assertEqual(summary_denied.exception.code,403)
                with self.assertRaises(HTTPError) as chat_denied:urlopen(Request(base+'/topics/chat',data=b'{}',headers=headers))
                self.assertEqual(chat_denied.exception.code,403)
                with self.assertRaises(HTTPError) as watch_denied:urlopen(Request(base+'/hotspot-watch',data=b'{"keyword":"test"}',headers=headers))
                self.assertEqual(watch_denied.exception.code,403)
                with self.assertRaises(HTTPError) as text_denied:urlopen(Request(base+'/works/text',data=b'{}',headers=headers))
                self.assertEqual(text_denied.exception.code,403)
                def phone_provider(request,**kwargs):
                    url=request.full_url
                    return io.BytesIO(json.dumps({'access_token':'test-token','expires_in':7200} if 'stable_token' in url else {'errcode':0,'phone_info':{'purePhoneNumber':'13812345678','countryCode':'86','watermark':{'appid':'wx'}}}).encode())
                server.AUTH.opener=phone_provider
                with self.assertRaises(HTTPError) as invalid:urlopen(Request(base+'/auth/phone',data=b'{"code":"valid-phone-code","phoneNumber":"forged"}',headers=headers))
                self.assertEqual(invalid.exception.code,400)
                with urlopen(Request(base+'/auth/phone',data=b'{"code":"valid-phone-code"}',headers=headers)) as response:
                    profile=json.load(response);self.assertTrue(profile['phoneBound']);self.assertEqual(profile['userId'],login['userId'])
                server.TEXT_WORKS=server._text_module.TextWorks(root/'text.sqlite',lambda:{'url':'https://example.com/chat','key':'fake-key','model':'fake-model'})
                create=server.TEXT_WORKS.create
                server.TEXT_WORKS.create=lambda user,payload,boundary:create(user,payload,boundary,opener=lambda *a,**k:io.BytesIO(json.dumps({'choices':[{'message':{'content':'测试文字正文'}}]}).encode()))
                with urlopen(Request(base+'/works/text',data=json.dumps({'idea':'文字测试','requestId':'http-test-0001'}).encode(),headers=headers)) as response:
                    text=json.load(response);self.assertEqual(text['text'],'测试文字正文')
                for _ in range(2):
                    with urlopen(Request(base+'/task-interest',data=b'{}',headers=headers)) as response:interest=json.load(response)
                    self.assertTrue(interest['supported']);self.assertEqual(interest['total'],1)
                with self.assertRaises(HTTPError) as anonymous:urlopen(Request(base+'/task-interest',data=b'{}'))
                self.assertEqual(anonymous.exception.code,401)
                with urlopen(Request(base+'/auth/profile',data=json.dumps({'nickname':'修改后的昵称','avatar':2,'email':'creator@example.com'}).encode(),headers=headers)) as response:profile=json.load(response)
                self.assertEqual(profile['nickname'],'修改后的昵称');self.assertFalse(profile['emailVerified'])
                server.IDEAS=server._idea_module.IdeaBox(root/'ideas',None,ocr=lambda p:[{'text':'截图里的文字'}],detect=server._link_module.detect,background=False)
                with urlopen(Request(base+'/ideas',data=json.dumps({'text':'租房遇到奇葩房东','clientId':'local-1'}).encode(),headers=headers)) as response:idea=json.load(response)
                self.assertEqual(idea['kind'],'text')
                import io as _io;from PIL import Image as _Image;buffer=_io.BytesIO();_Image.new('RGB',(40,30),'white').save(buffer,'PNG')
                body=b'--b0\r\nContent-Disposition: form-data; name="file"; filename="a.png"\r\nContent-Type: image/png\r\n\r\n'+buffer.getvalue()+b'\r\n--b0--\r\n'
                with urlopen(Request(base+'/ideas/media?kind=image&clientId=img-1',data=body,headers={**headers,'Content-Type':'multipart/form-data; boundary=b0'})) as response:shot=json.load(response)
                self.assertEqual(shot['text'],'截图里的文字');self.assertIn('__s=',shot['image'])
                with urlopen(base+shot['image']) as response:self.assertEqual(response.headers['Content-Type'],'image/jpeg')
                with self.assertRaises(HTTPError) as foreign:urlopen(base+shot['image'].split('?')[0])
                self.assertEqual(foreign.exception.code,401)
                with urlopen(Request(base+'/ideas',headers=headers)) as response:listing=json.load(response)
                self.assertEqual(listing['total'],2)
                with urlopen(Request(base+'/ideas/'+idea['id']+'/delete',data=b'{}',headers=headers)) as response:self.assertEqual(json.load(response)['deleted'],idea['id'])
                server._transcribe_reference=lambda path:{'status':'available','text':' 你好  TA '}
                voice=b'--b0\r\nContent-Disposition: form-data; name="file"; filename="v.mp3"\r\n\r\n'+b'\x01'*500+b'\r\n--b0--\r\n'
                with urlopen(Request(base+'/voice/transcribe',data=voice,headers={**headers,'Content-Type':'multipart/form-data; boundary=b0'})) as response:self.assertEqual(json.load(response),{'text':'你好 TA'})
                self.assertFalse(list((server.ASSET_ROOT/'ideas').glob('.*.voice')))
                with self.assertRaises(HTTPError) as anonymous_voice:urlopen(Request(base+'/voice/transcribe',data=voice,headers={'Content-Type':'multipart/form-data; boundary=b0'}))
                self.assertEqual(anonymous_voice.exception.code,401)
                release={**headers,'Referer':'https://servicewechat.com/wx8ae5d4f3ea8d0d8b/12/page-frame.html'}
                trial_headers={**headers,'Referer':'https://servicewechat.com/wx8ae5d4f3ea8d0d8b/0/page-frame.html'}
                for denied in (headers,release):
                    with self.assertRaises(HTTPError) as blocked:urlopen(Request(base+'/auth/trial',data=b'{}',headers=denied))
                    self.assertEqual(blocked.exception.code,403)
                with urlopen(Request(base+'/auth/trial',data=b'{}',headers=trial_headers)) as response:trial=json.load(response)
                self.assertTrue(trial['trial']);self.assertTrue(trial['phoneBound']);self.assertNotEqual(trial['userId'],login['userId'])
                with urlopen(Request(base+'/task-interest',data=b'{}',headers={'Authorization':'Bearer '+trial['token']})) as response:self.assertTrue(json.load(response)['supported'])
                server.AUTH.opener=lambda *a,**k:io.BytesIO(b'{"openid":"verified-user"}')
                body=json.dumps({'code':'valid-code','trial':trial['userId']}).encode()
                with urlopen(Request(base+'/auth/login',data=body,headers={'Referer':trial_headers['Referer']})) as response:self.assertEqual(json.load(response)['userId'],trial['userId'])
                with urlopen(Request(base+'/auth/login',data=body,headers={'Referer':release['Referer']})) as response:self.assertEqual(json.load(response)['userId'],login['userId'])
                with server.TOPIC_CHAT.db() as db:
                    db.execute('INSERT INTO turns VALUES(?,?,?,?,?)',(login['userId'],'asset-test-111','我的提问',json.dumps({'reply':'AI回答','topics':[{'title':'推荐主题','angle':'推荐角度'}]}),1))
                    db.execute('INSERT INTO turns VALUES(?,?,?,?,?)',('other-private','asset-test-other','不可见提问',json.dumps({'reply':'不可见回答'}),1))
                with urlopen(Request(base+'/creative-assets',headers=headers)) as response:assets=json.load(response)
                self.assertEqual(len(assets['texts']),1);self.assertEqual(len(assets['chats']),1);self.assertIn('推荐角度',assets['chats'][0]['text']);self.assertNotIn('不可见',json.dumps(assets,ensure_ascii=False))
                with self.assertRaises(HTTPError) as anon_assets:urlopen(base+'/creative-assets')
                self.assertEqual(anon_assets.exception.code,401)
                with urlopen(Request(base+'/works/text',headers=headers)) as response:self.assertEqual(len(json.load(response)['rows']),1)
                with self.assertRaises(HTTPError) as anon:urlopen(base+'/works/text/'+text['id'])
                self.assertEqual(anon.exception.code,401)
                with self.assertRaises(HTTPError) as denied:urlopen(Request(base+'/auth/me',headers={'Authorization':'Bearer forged'}))
                self.assertEqual(denied.exception.code,401)
                owned='a'*32;server.AUTH.claim(login['userId'],'run:'+owned)
                server.JOBS[owned]={'status':'done','url':'/assets/'+owned+'/final.mp4'}
                with urlopen(Request(base+'/jobs/'+owned,headers=headers)) as response:job=json.load(response)
                self.assertIn('__s=',job['url'])
                server.ASSET_ROOT=root/'assets';video=server.ASSET_ROOT/'runs'/owned/'final.mp4';video.parent.mkdir(parents=True);video.write_bytes(b'hello-media')
                with urlopen(Request(base+job['url'],headers={'Range':'bytes=0-3'})) as response:self.assertEqual(response.status,206);self.assertEqual(response.read(),b'hell')
                with self.assertRaises(HTTPError):urlopen(Request(base+job['url'].replace('__s=','__s=bad')))
                sha='f'*64;server.TOOL_ROOT=root/'tools';audio=server.TOOL_ROOT/sha/'audio.mp3';audio.parent.mkdir(parents=True);audio.write_bytes(b'ID3audio-test')
                server.AUTH.claim(login['userId'],'tool:'+sha)
                audio_url=server.AUTH.signed_url(login['userId'],'/tool-assets/'+sha+'/audio.mp3')
                with urlopen(Request(base+audio_url,headers={'Range':'bytes=0-2'})) as response:
                    self.assertEqual(response.status,206);self.assertEqual(response.read(),b'ID3');self.assertEqual(response.headers['Content-Type'],'audio/mpeg')
                with urlopen(base+audio_url) as response:self.assertEqual(response.read(),b'ID3audio-test')
                with self.assertRaises(HTTPError):urlopen(base+audio_url.replace('__s=','__s=bad'))
                server.AUTH.opener=lambda *a,**k:io.BytesIO(b'{"openid":"other-user"}')
                other=server.AUTH.login('other-code')
                with self.assertRaises(HTTPError) as denied:urlopen(Request(base+'/asset-runs/'+owned,headers={'Authorization':'Bearer '+other['token']}))
                self.assertEqual(denied.exception.code,403)
                with self.assertRaises(HTTPError) as denied:urlopen(Request(base+'/jobs/'+('b'*32),headers=headers))
                self.assertEqual(denied.exception.code,403)
                with self.assertRaises(HTTPError) as denied:urlopen(Request(base+'/jobs/'+owned))
                self.assertEqual(denied.exception.code,401)
                with self.assertRaises(HTTPError) as denied:urlopen(Request(base+'/references/analyze',data=json.dumps({'reference':{'asset':{'sha256':'f'*64,'storagePath':'forged'}}}).encode(),headers=headers))
                self.assertEqual(denied.exception.code,403)
                with urlopen(Request(base+'/auth/logout',data=b'{}',headers=headers)) as response:self.assertEqual(json.load(response)['status'],'signed_out')
                with self.assertRaises(HTTPError):urlopen(Request(base+'/auth/me',headers=headers))
            finally:http.shutdown();http.server_close();thread.join()
    def test_identity_persistence_expiry_and_revocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'config.json';config.write_text('\ufeff'+json.dumps({'appId':'wx-test','appSecret':'private-secret'}),encoding='utf-8')
            now=[100];identity=[{'openid':'first','session_key':'never-return'}]
            opener=lambda *a,**k:io.BytesIO(json.dumps(identity[0]).encode())
            auth=m.WechatAuth(config,root/'sessions.db',clock=lambda:now[0],opener=opener)
            first=auth.login('valid-code');second=auth.login('valid-code')
            self.assertEqual(first['userId'],second['userId']);self.assertNotEqual(first['token'],second['token']);self.assertNotIn('session_key',first)
            identity[0]['openid']='second';self.assertNotEqual(auth.login('valid-code')['userId'],first['userId'])
            restored=m.WechatAuth(config,root/'sessions.db',clock=lambda:now[0],opener=opener);self.assertEqual(restored.user(first['token']),first['userId'])
            self.assertIsNone(restored.user(first['token']+'x'));restored.revoke(first['token']);self.assertIsNone(restored.user(first['token']))
            now[0]=7300;self.assertIsNone(restored.user(second['token']))
            self.assertNotIn(second['token'],(root/'sessions.db').read_bytes().decode(errors='ignore'))
    def test_errors_do_not_leak_credentials_or_upstream_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'config';config.write_text(json.dumps({'appId':'wx','appSecret':'sensitive-secret'}))
            def fail(*a,**k):raise RuntimeError('https://secret=sensitive-secret')
            auth=m.WechatAuth(config,root/'sessions',opener=fail)
            with self.assertRaisesRegex(m.LoginError,'暂时不可用') as caught:auth.login('valid-code')
            self.assertNotIn('sensitive',str(caught.exception));self.assertIsNone(auth.user('forged-token'))
            auth.opener=lambda *a,**k:io.BytesIO(b'{"errcode":40029,"errmsg":"private"}')
            with self.assertRaisesRegex(m.LoginError,'已失效'):auth.login('valid-code')
            with self.assertRaises(m.LoginError):auth.login('../bad')
if __name__=='__main__':unittest.main()
