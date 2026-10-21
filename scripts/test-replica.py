import base64,io,json,tempfile,unittest,importlib.util
from pathlib import Path
from urllib.error import HTTPError
from PIL import Image
spec=importlib.util.spec_from_file_location('replica',Path(__file__).with_name('replica.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
KEY='sk-test-user-key-123456'

class Resp(io.BytesIO):
    def __enter__(self):return self
    def __exit__(self,*a):pass

def photo(w=600,h=900):
    b=io.BytesIO();Image.new('RGB',(w,h),'white').save(b,'JPEG');return base64.b64encode(b.getvalue()).decode()

class Provider:
    def __init__(self,task_states=('RUNNING','SUCCEEDED'),fail=None):
        self.calls=[];self.states=list(task_states);self.fail=fail
    def __call__(self,request,timeout=0):
        url=request.full_url;self.calls.append((url,dict(request.header_items()),request.data))
        if self.fail:raise HTTPError(url,self.fail[0],'x',{},io.BytesIO(json.dumps(self.fail[1]).encode()))
        if 'getPolicy' in url:return Resp(json.dumps({'data':{'upload_dir':'dir','oss_access_key_id':'a','signature':'s','policy':'p','x_oss_object_acl':'private','x_oss_forbid_overwrite':'true','upload_host':'https://up.oss-cn-beijing.aliyuncs.com'}}).encode())
        if url.startswith('https://up.'):return Resp(b'')
        if url.endswith('/video-synthesis'):return Resp(json.dumps({'output':{'task_id':'task-1','task_status':'PENDING'}}).encode())
        if '/tasks/' in url:
            state=self.states.pop(0)
            return Resp(json.dumps({'output':{'task_status':state,'results':{'video_url':'http://result.oss-cn-shanghai.aliyuncs.com/v.mp4'}}}).encode())
        if 'result.oss' in url:return Resp(b'MP4DATA')
        raise AssertionError(url)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.video=self.root/'src.mp4';self.video.write_bytes(b'video')
        self.ref={'asset':{'sha256':'a'*64,'storagePath':str(self.video),'media':{'durationSeconds':12.4}}}
    def tearDown(self):self.tmp.cleanup()
    def payload(self,**k):return {'provider':'bailian','key':KEY,'photo':photo(),'consent':True,'mode':'wan-std',**k}
    def test_full_flow_never_persists_key_and_downloads_result(self):
        p=Provider();r=m.Replica(self.root/'rep',opener=p)
        job=r.create('u1',self.ref,self.payload())
        self.assertEqual(job['status'],'running');self.assertEqual(job['estimateYuan'],4.96)
        submit=[c for c in p.calls if c[0].endswith('/video-synthesis')][0];body=json.loads(submit[2])
        self.assertEqual(body['model'],'wan2.2-animate-move');self.assertTrue(body['input']['image_url'].startswith('oss://'));self.assertTrue(body['input']['watermark'])
        self.assertEqual(submit[1]['Authorization'],'Bearer '+KEY)
        self.assertTrue(submit[0].startswith('https://dashscope.aliyuncs.com/api/v1'))
        self.assertEqual(r.status('u1',job['id'],self.payload())['status'],'running')
        done=r.status('u1',job['id'],self.payload());self.assertEqual(done['status'],'done');self.assertEqual(done['video'],'/replica-media/%s.mp4'%job['id'])
        self.assertEqual(r.media(job['id']).read_bytes(),b'MP4DATA')
        for f in (self.root/'rep').rglob('*'):
            if f.is_file() and f.suffix in ('.json','.tmp'):self.assertNotIn(KEY,f.read_text())
        self.assertNotIn(KEY,json.dumps(done))
        # finished jobs answer without contacting the provider or needing the key
        n=len(p.calls);self.assertEqual(r.status('u1',job['id'],{})['status'],'done');self.assertEqual(len(p.calls),n)
    def test_other_user_cannot_see_job_and_consent_required(self):
        r=m.Replica(self.root/'rep',opener=Provider());job=r.create('u1',self.ref,self.payload())
        with self.assertRaises(m.ReplicaError):r.status('u2',job['id'],self.payload())
        with self.assertRaises(m.ReplicaError):r.create('u1',self.ref,self.payload(consent=False))
        self.assertEqual([j['id'] for j in r.jobs('u2')],[])
    def test_input_validation(self):
        r=m.Replica(self.root/'rep',opener=Provider())
        for bad in ({'provider':'evil'},{'key':'has space key'},{'key':'short'},{'mode':'ultra'},{'photo':photo(100,100)},{'photo':photo(200,900)},{'photo':'notbase64!!'}):
            with self.assertRaises(m.ReplicaError):r.create('u1',self.ref,self.payload(**bad))
        with self.assertRaises(m.ReplicaError):r.create('u1',{'asset':{'storagePath':str(self.root/'missing.mp4'),'media':{'durationSeconds':5}}},self.payload())
    def test_provider_errors_are_friendly_and_redact_key(self):
        for status,body,text in ((401,{'code':'InvalidApiKey','message':'bad '+KEY}, 'Key 无效'),(400,{'code':'Arrearage','message':'x'},'余额不足'),(403,{'code':'AccessDenied','message':'x'},'尚未开通')):
            r=m.Replica(self.root/('rep'+str(status)),opener=Provider(fail=(status,body)))
            with self.assertRaises(m.ReplicaError) as ctx:r.check({'provider':'qianwen','key':KEY})
            self.assertIn(text,str(ctx.exception));self.assertNotIn(KEY,str(ctx.exception))
    def test_active_and_daily_limits(self):
        r=m.Replica(self.root/'rep',opener=Provider())
        r.create('u1',self.ref,self.payload());r.create('u1',self.ref,self.payload())
        with self.assertRaises(m.ReplicaError) as ctx:r.create('u1',self.ref,self.payload())
        self.assertEqual(ctx.exception.code,'limit')
    def test_long_source_is_trimmed_to_30_seconds(self):
        calls=[]
        class FakeRun:pass
        r=m.Replica(self.root/'rep',opener=Provider(),ffmpeg='ffmpeg')
        import subprocess
        orig=subprocess.run
        def fake(cmd,**k):calls.append(cmd);Path(cmd[-1]).write_bytes(b'cut')
        subprocess.run=fake
        try:job=r.create('u1',{**self.ref,'asset':{**self.ref['asset'],'media':{'durationSeconds':48}}},self.payload())
        finally:subprocess.run=orig
        self.assertEqual(job['seconds'],30.0);self.assertIn('-t',calls[0]);self.assertEqual(calls[0][calls[0].index('-t')+1],'30')
if __name__=='__main__':unittest.main()
