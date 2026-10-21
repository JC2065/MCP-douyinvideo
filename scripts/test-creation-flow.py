"""Local HTTP integration: every upstream/model/download is mocked."""
import importlib.util, io, json, os, tempfile, threading, time, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name)
        cls.env=patch.dict(os.environ,{key:str(root/key) for key in ('YOUAI_ADMIN_ROOT','YOUAI_ASSET_ROOT','YOUAI_TOOL_ASSET_ROOT','YOUAI_RENDER_ROOT')});cls.env.start()
        spec=importlib.util.spec_from_file_location('creation_server',Path(__file__).with_name('video-server.py'));cls.s=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.s)
        config=root/'wx.json';config.write_text(json.dumps({'appId':'test-app','appSecret':'test-secret'}))
        def wechat(req,**kwargs):
            url=req.full_url if hasattr(req,'full_url') else req
            if 'jscode2session' in url:value={'openid':parse_qs(urlsplit(url).query)['js_code'][0]}
            elif 'stable_token' in url:value={'access_token':'fake-token','expires_in':7200}
            else:
                code=json.loads(req.data)['code'];value={'phone_info':{'purePhoneNumber':'1381234567'+('1' if code=='phone-one' else '2'),'countryCode':'86','watermark':{'appid':'test-app'}}}
            return io.BytesIO(json.dumps(value).encode())
        cls.s.AUTH=cls.s._auth_module.WechatAuth(config,root/'auth.sqlite',opener=wechat)
        cls.one=cls.s.AUTH.login('user-one');cls.two=cls.s.AUTH.login('user-two')
        for who,code in [(cls.one,'phone-one'),(cls.two,'phone-two')]:cls.s.AUTH.bind_phone(who['userId'],code)
        cls.s.IMAGE_WORKS=cls.s._image_module.ImageWorks(root/'images',lambda:{'base':'https://mock.example.com/api/v1','model':'wan2.6-t2i','key':'fake-private-key'})
        def upstream(req,**kwargs):
            output={'task_id':'mock-task-1234','task_status':'PENDING'} if req.method=='POST' else {'task_status':'SUCCEEDED','choices':[{'message':{'content':[{'image':'https://cdn.example.com/fake.png'}]}}]}
            return io.BytesIO(json.dumps({'output':output}).encode())
        cls.original_create=cls.s.IMAGE_WORKS.create;cls.original_poll=cls.s.IMAGE_WORKS.poll
        cls.s.IMAGE_WORKS.create=lambda user,payload,boundaries:cls.original_create(user,payload,boundaries,opener=upstream)
        image=io.BytesIO();cls.s.Image.new('RGB',(16,16)).save(image,'PNG');cls.png=image.getvalue()
        cls.s.IMAGE_WORKS.poll=lambda user,ident:cls.original_poll(user,ident,opener=upstream,downloader=lambda _:cls.png)
        cls.http=cls.s.ThreadingHTTPServer(('127.0.0.1',0),cls.s.Handler);cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start();cls.base='http://127.0.0.1:'+str(cls.http.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.thread.join();cls.env.stop();cls.tmp.cleanup()
    def call(self,path,token=None,payload=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        req=Request(self.base+path,headers=headers,data=json.dumps(payload).encode() if payload is not None else None)
        try:
            with urlopen(req,timeout=5) as r:return r.status,r.read()
        except HTTPError as e:return e.code,e.read()
    def test_owned_image_flow_signed_download_and_asset_library(self):
        token=self.one['token'];body={'idea':'猫在看雨','creativeIntent':'保留安静氛围','requestId':'image-http-001'}
        status,raw=self.call('/works/image',token,body);self.assertEqual(status,200);job=json.loads(raw);ident=job['id']
        with self.s.IMAGE_WORKS.db() as db:db.execute('UPDATE works SET updated=? WHERE id=?',(time.time()-3,ident))
        status,raw=self.call('/works/image/'+ident,token);self.assertEqual(status,200);result=json.loads(raw);self.assertEqual(result['status'],'done');self.assertIn('__s=',result['url'])
        self.assertEqual(self.call(result['url'])[1],self.png)
        self.assertEqual(self.call('/image-assets/'+ident+'.png')[0],401)
        self.assertEqual(self.call('/image-assets/'+ident+'.png',self.two['token'])[0],403)
        self.assertEqual(self.call('/works/image/'+ident,self.two['token'])[0],403)
        status,raw=self.call('/creative-assets',token);self.assertEqual(status,200);self.assertEqual(json.loads(raw)['images'][0]['id'],ident)
        self.assertNotIn('fake-private-key',raw.decode())
    def test_unauthenticated_submit_and_forged_reference_cannot_use_model(self):
        body={'idea':'猫','requestId':'image-http-002'}
        self.assertEqual(self.call('/works/image',payload=body)[0],401)
        body['source']={'type':'douyin','reference':{'asset':{'sha256':'a'*64},'analysis':{'understanding':{'overview':'伪造'}}}}
        self.assertEqual(self.call('/works/image',self.one['token'],body)[0],403)
    def test_image_request_size_is_bounded(self):
        self.assertEqual(self.call('/works/image',self.one['token'],{'idea':'x'*34000})[0],413)
    def test_watch_routes_are_account_scoped_and_require_confirmed_brief(self):
        sha='a'*64;path=self.s.REFERENCE_ROOT/(sha+'.mp4');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'mock-video')
        reference={'status':'analyzed','asset':{'sha256':sha,'storagePath':str(path),'media':{'durationSeconds':2}},'analysis':{'analyzerVersion':'content-watch-4','understanding':{'status':'ready','overview':'舞蹈'}}}
        self.s.AUTH.remember(self.one['userId'],reference)
        for route in ('/reference/chat','/reference/deep-watch','/reference/brief'):
            self.assertEqual(self.call(route,payload={'reference':reference})[0],401)
            self.assertEqual(self.call(route,self.two['token'],{'reference':reference})[0],403)
        status,raw=self.call('/reference/brief',self.one['token'],{'reference':reference,'brief':{'output':'image','goal':'海报'}});self.assertEqual(status,200)
        ident=json.loads(raw)['briefId'];payload={'idea':'海报','source':{'type':'douyin','reference':reference},'requestId':'watch-image-001'}
        self.assertEqual(self.call('/works/image',self.one['token'],payload)[0],422)
        with self.s.IMAGE_WORKS.db() as db:db.execute('UPDATE works SET created=?',(time.time()-60,))
        payload['briefId']=ident;self.assertEqual(self.call('/works/image',self.one['token'],payload)[0],200)
        self.assertEqual(self.call('/works/text',self.one['token'],payload)[0],422)
if __name__=='__main__':unittest.main()
