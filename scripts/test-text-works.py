import importlib.util,json,tempfile,unittest
from pathlib import Path
from urllib.error import HTTPError
spec=importlib.util.spec_from_file_location('text_works',Path(__file__).with_name('text-works.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Response:
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return json.dumps({'choices':[{'message':{'content':'咖啡的早晨\n磨豆香唤醒了街角。'}}]},ensure_ascii=False).encode()
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.profile=lambda:{'url':'https://example.com/chat','key':'private-key','model':'text-model'};self.store=m.TextWorks(Path(self.tmp.name)/'works.sqlite',self.profile);self.payload={'idea':'咖啡的早晨','requestId':'request-0001'}
 def tearDown(self):self.tmp.cleanup()
 def test_content_understanding_and_free_intent_reach_text_generation(self):
  sent=[]
  def opener(req,timeout):sent.append(json.loads(req.data));return Response()
  payload={**self.payload,'creativeIntent':'写成一封给猫的信','referenceNotes':'主角是我的猫','tone':'安静而细腻','source':{'type':'douyin','reference':{'analysis':{'understanding':{'status':'ready','overview':'猫看雨','facts':[{'text':'猫在窗前'}]}}}}}
  self.store.create('owner',payload,opener=opener)
  context=json.loads(sent[0]['messages'][1]['content']);self.assertEqual(context['creativeIntent'],'写成一封给猫的信');self.assertEqual(context['source']['referenceAnalysis']['understanding']['overview'],'猫看雨');self.assertEqual(context['tone'],'安静而细腻')
 def test_real_text_contract_persistence_ownership_and_retry(self):
  calls=[]
  def opener(req,timeout):calls.append(json.loads(req.data));return Response()
  self.payload['aiPreference']='少用口号，先写具体场景';value=self.store.create('a',self.payload,'平台边界',opener);self.assertEqual(self.store.create('a',self.payload,'平台边界',opener),value);self.assertEqual(len(calls),1);self.assertIn('平台边界',calls[0]['messages'][1]['content']);self.assertIn('少用口号，先写具体场景',calls[0]['messages'][1]['content']);self.assertNotIn('private-key',json.dumps(value));self.assertIsNone(self.store.get('b',value['id']));self.assertEqual(self.store.list('b'),[]);self.assertEqual(m.TextWorks(self.store.path,self.profile).get('a',value['id']),value)
 def test_bad_inputs_and_sanitized_provider_failure(self):
  with self.assertRaises(ValueError):self.store.create('a',{},opener=lambda *a,**k:Response())
  def fail(*a,**k):raise RuntimeError('private-key')
  with self.assertRaisesRegex(m.Unavailable,'文字生成失败'):self.store.create('a',self.payload,opener=fail)
  self.assertEqual(self.store.list('a'),[])
  with self.assertRaises(m.Busy):self.store.create('a',{'idea':'x','requestId':'request-0002'},opener=fail)
 def test_preference_validation(self):
  payload={**self.payload,'aiPreference':'x'*501}
  with self.assertRaisesRegex(ValueError,'AI个人偏好'):self.store.create('a',payload,opener=lambda *a,**k:Response())
 def test_qwen_nonthinking_and_safe_failures(self):
  self.profile=lambda:{'url':'https://example.com/chat','key':'private-key','model':'qwen3.8-max'};self.store.profile=self.profile
  def opener(req,timeout):
   self.assertIs(json.loads(req.data)['enable_thinking'],False);return Response()
  self.store.create('qwen',self.payload,opener=opener)
  for user,error,expected in [('timeout',TimeoutError('private-key'),'超时'),('auth',HTTPError('private-key',401,'private-key',{},None),'凭据'),('quota',HTTPError('private-key',429,'private-key',{},None),'额度')]:
   def fail(*a,**k):raise error
   with self.assertRaises(m.Unavailable) as caught:self.store.create(user,self.payload,opener=fail)
   self.assertIn(expected,str(caught.exception));self.assertNotIn('private-key',str(caught.exception));self.assertEqual(self.store.list(user),[])
 def test_gateway_scene_controls_text_model(self):
  class Error(Exception):
   def __init__(self,code):self.code=code;super().__init__('模型限流或额度不足')
  calls=[]
  class Gateway:
   pass
  g=Gateway();g.Error=Error
  def complete(scene,messages,opener=None):
   calls.append((scene,messages));return {'choices':[{'message':{'content':'标题\n正文'}}]}
  g.complete=complete;store=m.TextWorks(Path(self.tmp.name)/'g.sqlite',self.profile,g)
  value=store.create('g',self.payload);self.assertEqual(value['text'],'标题\n正文');self.assertEqual(calls[0][0],'text_works');self.assertEqual(calls[0][1][0]['role'],'system')
  def fail(scene,messages,opener=None):raise Error('quota')
  g.complete=fail
  with self.assertRaisesRegex(m.Unavailable,'额度'):store.create('h',{**self.payload,'requestId':'request-0009'})
  self.assertEqual(store.list('h'),[])
if __name__=='__main__':unittest.main()
