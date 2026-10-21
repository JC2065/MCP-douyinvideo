import importlib.util,json,sqlite3,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('comments',Path(__file__).with_name('top-comments.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def test_safe_schema_sort_redaction_and_author(self):
        rows=m.sanitize([{'text':'联系微信:secret123 '+('长'*100),'digg_count':2,'reply_count':4,
                          'author':{'uid':'owner','nickname':'隐私名','avatar':'secret-url'},'comment_id':'secret-id'},
                         {'text':'接龙','digg_count':99,'reply_count':-2}],author_uid='owner')
        self.assertEqual(rows[0]['text'],'接龙');self.assertEqual(rows[0]['replies'],0)
        self.assertTrue(rows[1]['isAuthorReply']);self.assertLessEqual(len(rows[1]['text']),80)
        self.assertEqual(set(rows[1]),{'text','likes','replies','isAuthorReply'})
        self.assertNotIn('secret',json.dumps(rows));self.assertNotIn('隐私名',json.dumps(rows,ensure_ascii=False))
    def test_cache_expiry_failure_and_no_raw_storage(self):
        with tempfile.TemporaryDirectory() as root:
            calls=[];now=[100000]
            def request(path,timeout):
                calls.append(path);self.assertLessEqual(timeout,10)
                return {'data':{'items':[{'text':'真实评论','author':{'uid':'private-uid'},'digg_count':7}]}}
            self.assertEqual(len(m.fetch(root,'12345',request,clock=lambda:now[0])),1)
            m.fetch(root,'12345',request,clock=lambda:now[0]);self.assertEqual(len(calls),1)
            self.assertNotIn(b'private-uid',(Path(root)/'comments.sqlite').read_bytes())
            now[0]+=86401;m.fetch(root,'12345',request,clock=lambda:now[0]);self.assertEqual(len(calls),2)
            self.assertEqual(m.fetch(root,'99999',lambda *a,**k:(_ for _ in ()).throw(TimeoutError())),[])
            self.assertEqual(m.fetch(root,'../../x',request),[])

if __name__=='__main__':unittest.main()
