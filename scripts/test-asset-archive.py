import importlib.util,unittest,tempfile,json,uuid,shutil
from pathlib import Path
spec=importlib.util.spec_from_file_location('archive',Path(__file__).with_name('asset-archive.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Fake:
    def __init__(self):self.records={};self.uploads={};self.fail=False;self.corrupt=False
    def upsert(self,table,key,fields):
        if self.fail:raise RuntimeError('temporary unavailable')
        identity=(table,fields[key]);self.records[identity]=fields;return 'rec'+str(list(self.records).index(identity))
    def upload(self,path,name):self.uploads.setdefault(name,(uuid.uuid4().hex,Path(path).read_bytes()));return self.uploads[name][0]
    def download(self,token,path):
        data=next(data for t,data in self.uploads.values() if t==token);Path(path).write_bytes(b'corrupted' if self.corrupt else data)
class Tests(unittest.TestCase):
    def setup_asset(self,root):
        id=uuid.uuid4().hex;folder=root/'runs'/id;folder.mkdir(parents=True);(folder/'final.mp4').write_bytes(b'video-data');(folder/'prompt.txt').write_text('test prompt');(folder/'analysis.json').write_text('{}');(folder/'storyboard.v1.json').write_text('{}');(folder/'request.json').write_text('{"secret":"must-not-archive"}')
        source=root/'sources'/'source.mp4';source.parent.mkdir(exist_ok=True);source.write_bytes(b'source-video');frame=root/'keyframes'/'frame.jpg';frame.parent.mkdir(exist_ok=True);frame.write_bytes(b'image')
        manifest={'runId':id,'source':{'type':'idea','storageUri':str(source)},'analysis':{'keyframes':[str(frame)]},'communication':{'goal':'test'},'storyboard':{'version':1,'shots':[]},'generation':{'model':'local'},'final':{'sha256':m.digest(folder/'final.mp4')},'lineage':{}}
        m.write_json(folder/'manifest.json',manifest);return id
    def test_complete_archive_restart_restore_and_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);id=self.setup_asset(root);fake=Fake();manager=m.ArchiveManager(root,root/'config',root/'state');manager.client=lambda:fake;manager.enqueue(id);manager.tick();self.assertEqual(manager.status(id)['status'],'archived');self.assertEqual(len({t for t,k in fake.records}),6);uploads=len(fake.uploads);manager.process(id);self.assertEqual(len(fake.uploads),uploads)
            receipt=json.loads((manager.work/id/'receipt.json').read_text());self.assertNotIn('run/request.json',receipt['files']);self.assertNotIn('must-not-archive',(manager.work/id/'bundle.zip').read_bytes().decode('latin1'));manager.feedback(id,{'rating':'满意'});manager.tick();self.assertEqual(fake.records[('feedback',id+'-cost')]['用户评价'],'满意');self.assertEqual(len(fake.uploads),uploads)
            (root/'runs'/id/'final.mp4').unlink();(root/'sources'/'source.mp4').unlink();(root/'keyframes'/'frame.jpg').unlink();result=manager.restore(id,fake);self.assertEqual(result['status'],'restored');self.assertEqual((root/'runs'/id/'final.mp4').read_bytes(),b'video-data');self.assertEqual((root/'sources'/'source.mp4').read_bytes(),b'source-video');self.assertEqual((root/'keyframes'/'frame.jpg').read_bytes(),b'image');reopened=m.ArchiveManager(root,root/'config',root/'state');self.assertEqual(reopened.status(id)['status'],'archived')
    def test_failure_retry_and_corruption_do_not_mark_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);id=self.setup_asset(root);fake=Fake();fake.fail=True;manager=m.ArchiveManager(root,root/'config',root/'state');manager.client=lambda:fake;manager.enqueue(id);manager.tick();self.assertEqual(manager.status(id)['status'],'failed');fake.fail=False;manager.enqueue(id);manager.tick();self.assertEqual(manager.status(id)['status'],'archived');fake.corrupt=True
            with self.assertRaisesRegex(ValueError,'哈希'):manager.restore(id,fake)
            self.assertEqual((root/'runs'/id/'final.mp4').read_bytes(),b'video-data')
    def test_paths_and_missing_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);id=self.setup_asset(root);manager=m.ArchiveManager(root,root/'missing',root/'state')
            with self.assertRaises(ValueError):manager.enqueue('../outside')
            manager.enqueue(id);manager.tick();self.assertEqual(manager.status(id)['status'],'failed');self.assertIn('配置',manager.status(id)['error'])
            manifest=manager.valid(id);manifest['source']['storageUri']=str(root.parent/'outside');
            with self.assertRaisesRegex(ValueError,'越界'):manager.bundle(id,manifest)
    def test_large_bundle_is_split_and_restored_without_duplicate_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);id=self.setup_asset(root);(root/'runs'/id/'final.mp4').write_bytes(b'0'*(19*1024*1024));fake=Fake();manager=m.ArchiveManager(root,root/'config',root/'state');manager.client=lambda:fake;manager.enqueue(id);manager.tick();self.assertEqual(manager.status(id)['status'],'archived');self.assertEqual(len(fake.uploads),2);self.assertTrue(all(len(data)<=18*1024*1024 for _,data in fake.uploads.values()));manager.restore(id,fake);manager.process(id);self.assertEqual(len(fake.uploads),2)
class IdempotencyTests(unittest.TestCase):
    def test_concurrent_search_misses_use_same_create_token(self):
        client=m.Feishu({'baseToken':'base'},{'roles':{'management':{'tables':{'works':{'id':'table'}}}}})
        tokens=[]
        def call(method,path,body=None):
            if path.endswith('/search'):return {'items':[]}
            tokens.append(body['client_token']);return {'record':{'record_id':'record'}}
        client.call=call
        client.upsert('works','作品ID',{'作品ID':'same-id'})
        client.upsert('works','作品ID',{'作品ID':'same-id'})
        client.upsert('works','作品ID',{'作品ID':'different-id'})
        self.assertEqual(tokens[0],tokens[1]);self.assertNotEqual(tokens[0],tokens[2])
if __name__=='__main__':unittest.main()
