import importlib.util, io, json, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
spec=importlib.util.spec_from_file_location('image_works',Path(__file__).with_name('image-works.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.settings=lambda:{'base':'https://images.example.com/api/v1','model':'wan2.6-t2i','key':'private-test-secret'}
        self.store=m.ImageWorks(self.root,self.settings);self.payload={'idea':'窗边看雨的猫','creativeIntent':'做一张有留白的插画','requestId':'request-image-1'};self.calls=[]
        def opener(req,timeout):
            self.calls.append(req)
            output={'task_id':'task-00001','task_status':'PENDING'} if req.method=='POST' else {'task_status':'SUCCEEDED','choices':[{'message':{'content':[{'image':'https://cdn.example.com/image.png'}]}}]}
            return io.BytesIO(json.dumps({'output':output}).encode())
        self.opener=opener
    def tearDown(self):self.tmp.cleanup()
    def aged(self,ident):
        with self.store.db() as db:db.execute('UPDATE works SET updated=? WHERE id=?',(time.time()-3,ident))
    def test_submit_poll_local_persistence_idempotence_and_cross_account(self):
        row=self.store.create('one',self.payload,opener=self.opener);ident=row['id']
        self.assertEqual(row['status'],'generating');self.assertEqual(row['url'],'')
        self.assertEqual(self.store.create('one',self.payload,opener=self.opener)['id'],ident);self.assertEqual(len(self.calls),1)
        self.assertIsNone(self.store.poll('other',ident,opener=self.opener));self.assertEqual(self.store.list('other'),[])
        self.aged(ident)
        png=io.BytesIO();Image.new('RGB',(10,10)).save(png,'PNG')
        row=self.store.poll('one',ident,opener=self.opener,downloader=lambda url:png.getvalue())
        self.assertEqual(row['status'],'done');self.assertTrue((self.root/(ident+'.png')).exists())
        self.assertEqual(m.ImageWorks(self.root,self.settings).get('one',ident)['url'],row['url'])
        self.assertNotIn('private-test-secret',(self.root/'images.sqlite').read_bytes().decode(errors='ignore'))
        self.assertEqual(self.calls[0].full_url,'https://images.example.com/api/v1/services/aigc/image-generation/generation')
        payload=json.loads(self.calls[0].data);self.assertEqual(payload['parameters']['n'],1);self.assertIn('留白',payload['input']['messages'][0]['content'][0]['text'])
    def test_uncertain_submission_never_repeats_billable_post(self):
        calls=[]
        def fail(*a,**k):calls.append(1);raise TimeoutError('private provider error')
        first=self.store.create('one',self.payload,opener=fail);second=self.store.create('one',self.payload,opener=fail)
        self.assertEqual(first['status'],'failed');self.assertEqual(first,second);self.assertEqual(len(calls),1)
        self.assertNotIn('private',first['error'])
    def test_download_failure_keeps_task_for_retry_not_resubmission(self):
        row=self.store.create('one',self.payload,opener=self.opener);self.aged(row['id'])
        def fail(url):raise RuntimeError('private url')
        row=self.store.poll('one',row['id'],opener=self.opener,downloader=fail)
        self.assertEqual(row['status'],'generating');self.assertIn('不会重复提交',row['error'])
        self.assertEqual(sum(r.method=='POST' for r in self.calls),1)
    def test_missing_config_and_wrong_model_do_not_create_billable_request(self):
        def fail():raise RuntimeError('secret')
        self.store.settings=fail
        with self.assertRaises(m.Unavailable):self.store.create('one',self.payload,opener=self.opener)
        self.store.settings=lambda:{**self.settings(),'model':'unsupported'}
        with self.assertRaises(m.Unavailable):self.store.create('one',self.payload,opener=self.opener)
        self.assertEqual(self.calls,[])
    def test_same_request_with_changed_content_rejected(self):
        self.store.create('one',self.payload,opener=self.opener)
        with self.assertRaises(ValueError):self.store.create('one',{**self.payload,'creativeIntent':'改了'},opener=self.opener)
    def test_provider_failure_and_timeout_remain_visible(self):
        row=self.store.create('one',self.payload,opener=self.opener);self.aged(row['id'])
        row=self.store.poll('one',row['id'],opener=lambda *a,**k:io.BytesIO(b'{"output":{"task_status":"FAILED"}}'))
        self.assertEqual(row['status'],'failed');self.assertTrue(row['error'])
    def test_private_media_url_and_private_redirect_are_blocked(self):
        for url in ['http://cdn.example.com/a','https://user:pass@cdn.example.com/a','https://cdn.example.com:8443/a']:
            with self.assertRaises(ValueError):m.public_url(url)
        with patch.object(m.socket,'getaddrinfo',return_value=[(None,None,None,None,('127.0.0.1',443))]):
            with self.assertRaises(ValueError):m.public_url('https://cdn.example.com/a')
    def test_technical_sizes_and_free_requirements(self):
        p={**self.payload,'imageRatio':'9:16','audience':'刚搬进新家的养猫人'}
        c=m.context(p,'不要虚构功效');self.assertEqual(c['size'],'960*1712');self.assertIn('刚搬进新家',m.prompt(c));self.assertIn('不要虚构功效',m.prompt(c))
        with self.assertRaises(ValueError):m.context({**p,'imageRatio':'arbitrary'},'')
    def test_poll_uses_the_original_provider_when_admin_changes_endpoint(self):
        row=self.store.create('one',self.payload,opener=self.opener);self.aged(row['id'])
        self.store.settings=lambda:{**self.settings(),'base':'https://different.example.com/api/v1'}
        self.store.poll('one',row['id'],opener=self.opener,downloader=lambda _:b'png')
        self.assertTrue(self.calls[-1].full_url.startswith('https://images.example.com/api/v1/tasks/'))
    def test_explicit_requirements_are_not_silently_cut_off(self):
        c=m.context({**self.payload,'creativeIntent':'甲'*1000,'referenceNotes':'乙'*1000},'平台边界'*60)
        with self.assertRaisesRegex(ValueError,'2100'):m.prompt(c)
    def test_expired_and_interrupted_tasks_do_not_block_user_forever(self):
        row=self.store.create('one',self.payload,opener=self.opener)
        with self.store.db() as db:db.execute('UPDATE works SET created=?,updated=? WHERE id=?',(time.time()-90000,time.time()-3,row['id']))
        self.assertEqual(self.store.poll('one',row['id'],opener=self.opener)['status'],'failed')
if __name__=='__main__':unittest.main()
