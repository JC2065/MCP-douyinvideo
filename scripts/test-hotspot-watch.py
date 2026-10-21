import importlib.util,tempfile,unittest,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('watch',Path(__file__).with_name('hotspot-watch.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.w=m.Watches(Path(self.tmp.name)/'watch.sqlite');self.now=time.time()
 def tearDown(self):self.tmp.cleanup()
 def feed(self,rank=9,delta=0,status='fresh',match=True,ident='one'):
  return {'sources':{'weibo':{'platform':'微博','status':status,'fetchedAt':self.now+delta,'attemptedAt':self.now+delta}},'rows':[{'id':ident,'title':'向日葵花田开放','platform':'微博','rank':rank}] if match else []}
 def test_pinned_order_isolation_restart_and_remove(self):
  self.w.add('a','向日葵');self.w.add('a','咖啡');self.w.add('a','向日葵');self.assertEqual(self.w.view('a')['keywords'],['向日葵','咖啡']);self.assertEqual(self.w.view('b')['keywords'],[]);self.assertEqual(m.Watches(self.w.path).view('a')['keywords'],['向日葵','咖啡']);self.w.remove('b','向日葵');self.assertEqual(len(self.w.view('a')['keywords']),2);self.w.remove('a','向日葵');self.assertEqual(self.w.view('a')['keywords'],['咖啡'])
 def test_measured_movement_no_duplicate_samples_and_source_failure_not_drop(self):
  self.w.add('a','向日葵');self.w.sample(self.feed(9));self.w.sample(self.feed(3,600));self.w.sample(self.feed(3,600));row=self.w.view('a')['observations'][0];self.assertEqual(row['rank'],3);self.assertEqual(row['rankChange'],6);self.assertEqual(len(row['trail']),2);self.w.sample(self.feed(3,1200,'stale'));row=self.w.view('a')['observations'][0];self.assertEqual(row['status'],'unknown');self.assertIsNone(row['rank']);self.assertIsNone(row['rankChange'])
 def test_not_ranked_and_changed_topic_never_invent_comparable_movement(self):
  self.w.add('a','向日葵');self.w.sample(self.feed(match=False));self.assertEqual(self.w.view('a')['observations'][0]['status'],'not_ranked');self.w.sample(self.feed(4,600));self.w.sample(self.feed(1,1200,ident='another'));self.assertIsNone(self.w.view('a')['observations'][0]['rankChange'])
 def test_limits(self):
  with self.assertRaises(ValueError):self.w.add('a','')
  with self.assertRaises(ValueError):self.w.add('a','x'*41)
  for i in range(20):self.w.add('a',str(i))
  with self.assertRaises(ValueError):self.w.add('a','overflow')
 def test_search_returns_actual_sources_separately_and_caches_only_web_results(self):
  search=m.Search();calls=[]
  def retrieve(term):calls.append(term);return [{'title':'向日葵植物百科','source':'example.org','url':'https://example.org'}]
  r=search.query('向日葵',self.feed(match=False),retrieve);self.assertEqual(r['ranked'],[]);self.assertEqual(len(r['items']),1);self.assertNotIn('rank',r['items'][0]);self.assertEqual(search.query('向日葵',self.feed(),retrieve)['ranked'][0]['rank'],9);self.assertEqual(len(calls),1)
if __name__=='__main__':unittest.main()
