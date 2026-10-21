import copy,importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError,URLError
def load(name):
 spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
m=load('inspiration-ai');admin=load('admin-console')
class Response:
 def __init__(self,content='OK'):self.content=content
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return json.dumps({'choices':[{'message':{'content':self.content}}],'usage':{'total_tokens':9}}).encode()
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.env=patch.dict(os.environ,{'YOUAI_HOTSPOT_AI_URL':'https://example.com/v1/chat/completions','YOUAI_HOTSPOT_AI_KEY':'private-test-key','YOUAI_HOTSPOT_AI_MODEL':'baseline'});self.env.start();self.g=m.Gateway(self.root/'ai')
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def save(self,scenes):return self.g.publish({'expectedRevision':self.g.config()['revision'],'scenes':scenes})
 def test_version_conflict_rollback_and_restart(self):
  old=self.g.config();scenes=copy.deepcopy(old['scenes']);scenes['ta_chat']['model']='qwen-test';new=self.save(scenes)
  with self.assertRaises(m.Conflict):self.g.publish({'expectedRevision':old['revision'],'scenes':scenes})
  self.assertEqual(m.Gateway(self.root/'ai').scene('ta_chat')['model'],'qwen-test')
  restored=self.g.publish({'expectedRevision':new['revision'],'rollback':old['revision']});self.assertEqual(restored['scenes'],old['scenes']);self.assertNotEqual(restored['revision'],old['revision'])
 def test_validation_no_partial_write(self):
  old=self.g.config()
  for field,value in [('timeoutSeconds',41),('maxTokens',True),('enabled','true'),('model','https://evil'),('connection','unknown'),('instruction','x'*1001)]:
   scenes=copy.deepcopy(old['scenes']);scenes['ta_chat'][field]=value
   with self.assertRaises(ValueError):self.save(scenes)
  self.assertEqual(self.g.config(),old)
 def test_scene_routing_and_redacted_observations(self):
  scenes=self.g.config()['scenes'];scenes['ta_chat'].update(model='custom-model',maxTokens=123,timeoutSeconds=7,instruction='private-style');self.save(scenes);calls=[]
  def opener(req,timeout):calls.append((json.loads(req.data),timeout));return Response()
  self.g.complete('ta_chat',[{'role':'user','content':'private-conversation'}],opener)
  self.assertEqual((calls[0][0]['model'],calls[0][0]['max_tokens'],calls[0][1]),('custom-model',123,7));self.assertIn('private-style',calls[0][0]['messages'][-1]['content'])
  dashboard=self.g.dashboard();self.assertEqual(dashboard['rows'][1]['calls'],1);self.assertEqual(dashboard['recentCalls'][0]['tokens'],9)
  events=json.dumps(dashboard['recentCalls']);self.assertNotIn('private-conversation',events);self.assertNotIn('private-test-key',json.dumps(dashboard));self.assertNotIn('private-style',events)
 def test_errors_classified_without_upstream_body(self):
  cases=[(HTTPError('https://example.com',code,'secret upstream',{},None),expected,code) for code,expected in [(401,'auth'),(403,'auth'),(404,'model'),(429,'quota'),(400,'request'),(503,'upstream')]]+[(TimeoutError('secret'),'timeout',None),(URLError('secret'),'network',None)]
  for error,expected,status in cases:
   def fail(*a,**k):raise error
   with self.assertRaises(m.AIError) as caught:self.g.complete('ta_opening',[],fail)
   self.assertEqual(caught.exception.code,expected);event=self.g.dashboard()['recentCalls'][0];self.assertEqual(event['httpStatus'],status);self.assertNotIn('secret',json.dumps(event))
 def test_probe_separate_and_disabled_does_not_connect(self):
  calls=[]
  def opener(req,timeout):calls.append(json.loads(req.data));return Response()
  dashboard=self.g.probe('ta_opening',opener);self.assertEqual(calls[0]['max_tokens'],32);self.assertEqual(dashboard['rows'][0]['calls'],0);self.assertIsNone(dashboard['rows'][0]['lastBusiness']);self.assertTrue(dashboard['rows'][0]['lastProbe']['ok'])
  scenes=self.g.config()['scenes'];scenes['ta_opening']['enabled']=False;self.save(scenes)
  with self.assertRaisesRegex(m.AIError,'暂停'):self.g.complete('ta_opening',[],opener)
  self.assertEqual(len(calls),1)
 def test_content_filter_is_distinct_and_provider_detail_stays_private(self):
  import io
  def fail(*a,**k):raise HTTPError('https://example.com',400,'private',{},io.BytesIO(b'{"error":{"code":"data_inspection_failed","message":"private input text"}}'))
  with self.assertRaises(m.AIError) as caught:self.g.complete('ta_chat',[],fail)
  self.assertEqual(caught.exception.code,'content_filter');self.assertIn('审核',str(caught.exception))
  self.assertNotIn('private',json.dumps(self.g.dashboard()));self.assertEqual(self.g.dashboard()['recentCalls'][0]['code'],'content_filter')
 def test_invalid_json_and_empty_response_recorded(self):
  for content in ('','not-json','{"reply":"x","topics":[]}'):
   with self.assertRaises(m.AIError) as caught:self.g.complete('ta_chat',[],lambda *a,**k:Response(content),json_mode=True)
   self.assertEqual(caught.exception.code,'invalid_response');self.assertEqual(self.g.dashboard()['recentCalls'][0]['httpStatus'],200)
 def test_admin_auth_cas_and_probe_schema(self):
  auth=self.root/'auth.json';auth.write_text(json.dumps(admin.credential('test-password-123456')));c=admin.Console(self.root/'admin',auth,self.root/'config.json',lambda:{},lambda:None,lambda:[],self.g)
  with self.assertRaises(admin.AdminError) as error:c.dispatch('GET','/admin-api/inspiration-ai',{},'Bearer ordinary-wx-user','test')
  self.assertEqual(error.exception.status,401);token=c.login({'username':'admin','password':'test-password-123456'},'test')['token'];header='Bearer '+token;old=self.g.config()
  c.dispatch('POST','/admin-api/inspiration-ai',{'expectedRevision':old['revision'],'scenes':old['scenes']},header,'test')
  with self.assertRaises(admin.AdminError) as error:c.dispatch('POST','/admin-api/inspiration-ai',{'expectedRevision':old['revision'],'scenes':old['scenes']},header,'test')
  self.assertEqual(error.exception.status,409)
  with self.assertRaises(admin.AdminError) as error:c.dispatch('POST','/admin-api/inspiration-ai/probe',{'scene':'ta_chat','url':'https://evil'},header,'test')
  self.assertEqual(error.exception.status,400)
 def test_qwen_nonthinking_request(self):
  with patch.dict(os.environ,{'YOUAI_HOTSPOT_AI_MODEL':'qwen3.8-max'}):
   def opener(req,timeout):
    self.assertIs(json.loads(req.data)['enable_thinking'],False);return Response()
   self.g.complete('ta_chat',[{'role':'user','content':'hello'}],opener=opener)
 def test_reference_understanding_scene_is_independent_and_legacy_config_is_compatible(self):
  old=self.g.config();self.assertEqual(old['scenes']['reference_understanding']['model'],'qwen3-vl-plus');self.assertEqual(old['scenes']['reference_understanding']['maxTokens'],3500)
  saved={'revision':'b'*32,'scenes':{k:v for k,v in old['scenes'].items() if k!='reference_understanding'},'publishedAt':1}
  self.g.write(self.g.root/'config.json',saved)
  current=self.g.config();self.assertEqual(current['scenes']['ta_chat']['model'],'baseline');self.assertEqual(current['scenes']['reference_understanding']['model'],'qwen3-vl-plus')
 def test_older_three_scene_config_gains_text_works_default(self):
  old=self.g.config();saved={'revision':'a'*32,'scenes':{k:v for k,v in old['scenes'].items() if k!='text_works'},'publishedAt':1}
  (self.root/'ai').mkdir(exist_ok=True);(self.root/'ai'/'config.json').write_text(json.dumps(saved))
  value=self.g.config();self.assertEqual(value['revision'],'a'*32);self.assertEqual(set(value['scenes']),set(m.SCENES));self.assertEqual(value['scenes']['text_works']['maxTokens'],1800)
  self.save(value['scenes']);self.assertEqual(self.g.scene('text_works')['timeoutSeconds'],40)
if __name__=='__main__':unittest.main()
