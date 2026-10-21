import importlib.util,unittest,tempfile,json,io,os
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('chat',Path(__file__).with_name('topic-chat.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec_ai=importlib.util.spec_from_file_location('ai',Path(__file__).with_name('inspiration-ai.py'));ai=importlib.util.module_from_spec(spec_ai);spec_ai.loader.exec_module(ai)
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.chat=m.TopicChat(Path(self.tmp.name)/'chat.sqlite',ai.Gateway(Path(self.tmp.name)/'ai'));self.calls=[]
 def tearDown(self):self.tmp.cleanup()
 def opener(self,req,**kw):
  self.calls.append(json.loads(req.data));return io.BytesIO(json.dumps({'choices':[{'message':{'content':json.dumps({'reply':'先从生活细节开始，不是实时热点','topics':[{'title':'咖啡店的早晨','angle':'拍三个开店细节'}]})}}]}).encode())
 def ask(self,user='a',rid='request-0001',opening=True,message='',preference=''):
  with patch.dict(os.environ,{'YOUAI_HOTSPOT_AI_URL':'https://example.com/chat','YOUAI_HOTSPOT_AI_KEY':'secret','YOUAI_HOTSPOT_AI_MODEL':'test'}):return self.chat.chat(user,{'message':message,'requestId':rid,'opening':opening,'preference':preference},{'rows':[]},[{'title':'已有作品'}],{},self.opener)
 def test_identity_history_cache_and_idempotency(self):
  a=self.ask();self.assertEqual(a['userId'],'a');self.assertFalse(a['hasHotspots']);self.assertEqual(self.ask(rid='request-0002'),a);self.assertEqual(len(self.calls),1);self.assertEqual(self.chat.history('b'),[]);self.ask('b');self.assertEqual(len(self.calls),2);self.assertNotIn('咖啡店',json.dumps(self.calls[1]));restored=m.TopicChat(self.chat.path,self.chat.gateway);self.assertEqual(len(restored.history('a')),1);self.assertEqual(self.ask(),a)
 def test_validation_and_clear_isolation(self):
  self.ask();self.ask('b');self.chat.clear('a');self.assertEqual(self.chat.history('a'),[]);self.assertEqual(len(self.chat.history('b')),1)
  with self.assertRaises(ValueError):self.chat.chat('a',{'userId':'b'}, {},[],{})
  with self.assertRaises(ValueError):self.ask(message='bad')
 def test_followup_uses_only_own_history_and_no_raw_keys(self):
  self.ask();self.chat.attempts.clear();r=self.ask(rid='followup-001',opening=False,message='我想拍15秒口播');context=json.loads(self.calls[-1]['messages'][1]['content']);self.assertEqual(context['userMessage'],'我想拍15秒口播');self.assertTrue(context['conversation']);self.assertNotIn('secret',json.dumps(r));self.assertEqual(len(self.chat.history('a')),3)
 def test_profile_preference_is_contextual_and_changes_opening_cache(self):
  self.ask(preference='先从真实日常切入');context=json.loads(self.calls[-1]['messages'][1]['content']);self.assertEqual(context['userPreference'],'先从真实日常切入');self.chat.attempts.clear();self.ask(rid='next-open-001',preference='优先讨论美食');self.assertEqual(len(self.calls),2);context=json.loads(self.calls[-1]['messages'][1]['content']);self.assertEqual(context['userPreference'],'优先讨论美食')
  with self.assertRaises(ValueError):self.ask(rid='bad-pref-001',preference='x'*501)
 def test_reopening_after_followup_requests_new_conversational_recommendation(self):
  self.ask();self.chat.attempts.clear();self.ask(rid='followup-001',opening=False,message='换成咖啡店选题');self.chat.attempts.clear();self.ask(rid='next-open-001');self.assertEqual(len(self.calls),3);context=json.loads(self.calls[-1]['messages'][1]['content']);self.assertIn('主动先开场',context['userMessage']);self.assertTrue(context['conversation'])
 def test_concurrent_opening_waits_and_reuses_result_instead_of_busy_error(self):
  import threading;gate=threading.Event();started=threading.Event()
  def slow(req,**kw):started.set();gate.wait(5);return self.opener(req,**kw)
  out={}
  def first():
   with patch.dict(os.environ,{'YOUAI_HOTSPOT_AI_URL':'https://example.com/chat','YOUAI_HOTSPOT_AI_KEY':'secret','YOUAI_HOTSPOT_AI_MODEL':'test'}):out['a']=self.chat.chat('a',{'message':'','requestId':'open-first-01','opening':True},{},[],{},slow)
  th=threading.Thread(target=first);th.start();self.assertTrue(started.wait(5))
  with self.assertRaisesRegex(m.ChatError,'AI正在回复'):self.ask(rid='followup-busy1',opening=False,message='追问')
  threading.Timer(0.8,gate.set).start()
  second=self.ask(rid='open-second-1');th.join(5)
  self.assertEqual(second,out['a']);self.assertEqual(len(self.calls),1,'第二个开场请求复用第一个的结果，不再调用模型');self.assertNotIn('a',self.chat.active)
 def test_failure_not_persisted_or_fabricated(self):
  def bad(*args,**kwargs):raise RuntimeError('private-token')
  with patch.dict(os.environ,{'YOUAI_HOTSPOT_AI_URL':'https://example.com/chat','YOUAI_HOTSPOT_AI_KEY':'secret','YOUAI_HOTSPOT_AI_MODEL':'test'}):
   with self.assertRaisesRegex(m.ChatError,'连接失败'):self.chat.chat('a',{'message':'','requestId':'request-0001','opening':True},{},[],{},bad)
  self.assertEqual(self.chat.history('a'),[]);self.assertNotIn('a',self.chat.active)
 def test_filtered_optional_news_retries_once_without_changing_user_content(self):
  from urllib.error import HTTPError
  for repeated,code,with_news in [(False,'data_inspection_failed',True),(True,'data_inspection_failed',True),(False,'unsupported_parameter',True),(False,'data_inspection_failed',False)]:
   with self.subTest(repeated=repeated,code=code,with_news=with_news):
    self.chat.clear('a');self.chat.attempts.clear();calls=[];timeouts=[]
    def opener(req,timeout):
     calls.append(json.loads(req.data));timeouts.append(timeout)
     if len(calls)==1 or repeated:raise HTTPError(req.full_url,400,'blocked',{},io.BytesIO(json.dumps({'error':{'code':code,'message':'private upstream detail'}}).encode()))
     return self.opener(req,timeout=timeout)
    args=('a',{'message':'拍咖啡','opening':False,'requestId':'filtered-request-001','preference':'自然一点'},{'rows':[{'id':'news','title':'自动热榜'}] if with_news else []},[],{})
    with patch.dict(os.environ,{'YOUAI_HOTSPOT_AI_URL':'https://example.com/chat','YOUAI_HOTSPOT_AI_KEY':'secret','YOUAI_HOTSPOT_AI_MODEL':'test'}):
     if not repeated and code=='data_inspection_failed' and with_news:
      result=self.chat.chat(*args,opener=opener);self.assertFalse(result['hasHotspots']);self.assertTrue(result['hotspotsUnavailable']);self.assertIn('创作建议',result['reply'])
     else:
      with self.assertRaises(m.ChatError):self.chat.chat(*args,opener=opener)
      self.assertEqual(self.chat.history('a'),[])
    retry=code=='data_inspection_failed' and with_news
    self.assertEqual(len(calls),2 if retry else 1)
    if retry:
     before=json.loads(calls[0]['messages'][1]['content']);after=json.loads(calls[1]['messages'][1]['content']);self.assertTrue(before.pop('currentHotspots'));self.assertEqual(after.pop('currentHotspots'),[]);self.assertEqual(before,after);self.assertLessEqual(timeouts[1],timeouts[0])
if __name__=='__main__':unittest.main()
