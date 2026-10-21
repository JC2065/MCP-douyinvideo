import tempfile,unittest,json
from pathlib import Path
from PIL import Image
import numpy as np
import importlib.util
s=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('watch-flow.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
cfg={'maxAnalyzeSeconds':90,'maxFrames':32,'frameShortSide':360,'promptVersion':'v1','prices':{'cheap':{'in':1,'out':2}},'dailyBudgetYuan':20,'perUserDailyVideos':10,'autoDeepWatch':False,'deepWatchThreshold':.4,'chatMaxTurns':4}
class Tests(unittest.TestCase):
 def test_asr_model_invalidates_cache(self):
  with tempfile.TemporaryDirectory() as root:
   settings=dict(cfg,asrModel='tiny')
   gateway=type('Gateway',(),{'scene':lambda _,scene:{'model':'cheap'}})()
   flow=m.WatchFlow(root,gateway,lambda:settings,None)
   first=flow.key('sha','video_watch');settings['asrModel']='small'
   self.assertNotEqual(first,flow.key('sha','video_watch'))
 def test_deep_once_chat_four_calls_and_confirmed_output(self):
  with tempfile.TemporaryDirectory() as root:
   class Gateway:
    calls=0
    def scene(self,s):return {'model':'cheap'}
    def complete(self,scene,*args,**kwargs):
     self.calls+=1
     data={'overview':'真实音画','confidence':.9} if scene=='video_watch_deep' else {'reply':'保留固定机位','directions':['复刻动作'],'brief':{'output':'image','goal':'舞蹈海报','keep':['姿态'],'change':[],'notes':''}}
     return {'choices':[{'message':{'content':json.dumps(data)}}]}
   gateway=Gateway();ledger=m.usage.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg);flow=m.WatchFlow(root,gateway,lambda:cfg,ledger)
   card=flow.deep_watch('a','sha',lambda:'data:video/mp4;base64,Zg==',2);self.assertEqual(card['depth'],'deep')
   self.assertEqual(flow.deep_watch('a','sha',lambda:self.fail('must reuse'),2),card)
   for i in range(4):flow.chat('a','sha',card,'换成海报' if i else '',f'request-{i}')
   self.assertEqual(flow.chat('a','sha',card,'换成海报','request-3')['turn'],4)
   with self.assertRaises(ValueError):flow.chat('a','sha',card,'第五轮','request-5')
   confirmed=flow.confirm('a','sha',{'output':'image','goal':'海报'})
   self.assertEqual(flow.confirmed('a','sha',confirmed['briefId'],'image')['goal'],'海报')
   with self.assertRaises(ValueError):flow.confirmed('b','sha',confirmed['briefId'],'image')
   with self.assertRaises(ValueError):flow.confirmed('a','sha',confirmed['briefId'],'video')
 def test_cpu_preprocessing_caps_duration_frames_and_short_side(self):
  import subprocess
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/'test.mp4'
   subprocess.run([m.imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-f','lavfi','-i','color=blue:size=320x480:rate=5','-f','lavfi','-i','sine=frequency=440:sample_rate=16000','-t','2','-c:v','libx264',str(path)],check=True,capture_output=True)
   order=[]
   def ocr(*_):
    self.assertIs(m.threading.current_thread(),m.threading.main_thread());order.append('ocr')
    return {'status':'ready','items':[{'text':'似水汽年47','layer':'caption'}]}
   def transcriber(_):
    self.assertEqual(order,['ocr']);order.append('asr')
    return {'status':'ready','text':'似水汽年47','segments':[{'start':0,'end':1,'text':'似水汽年47'}]}
   value=m.preprocess(path,{'width':320,'height':480,'durationSeconds':2},dict(cfg,maxAnalyzeSeconds=1,maxFrames=8,frameShortSide=240),transcriber,
                      post={'description':'似水流年'},ocr=ocr)
   self.assertEqual(value['transcript']['text'],'似水流年47');self.assertEqual(value['transcript']['segments'][0]['text'],'似水流年47')
   self.assertEqual(value['screenText']['items'][0]['text'],'似水流年47')
   self.assertEqual(value['duration'],1);self.assertTrue(value['truncated']);self.assertLessEqual(len(value['frames']),8)
   self.assertTrue(all(min(image.size)==240 for _,image in value['frames']))
 def test_relaxed_json_fields_and_synthetic_audio(self):
  value=m.content.normalize_watch({'overview':'舞蹈','timeline':[{'start':0,'end':3,'what':'抬手'},{'start':-1,'end':3,'what':'坏字段'}],'style':7,'confidence':'bad'},4)
  self.assertEqual(len(value['timeline']),1);self.assertEqual(value['overview'],'舞蹈')
  for raw,kind in [(np.zeros(16000),'silence'),(np.sin(np.arange(16000)/10).astype(float)*.2,'music_or_non_speech')]:
   result=m.content.pcm_features(raw,8000,{},2);self.assertEqual(result['kindHint'],kind);self.assertTrue(result['estimated'])
  self.assertEqual(m.content.pcm_features(np.ones(16000)*.1,8000,{'segments':[{'start':0,'end':1}]},2)['speechRatio'],.5)
 def test_shared_cache_scoped_to_watch_model_not_global_revision(self):
  with tempfile.TemporaryDirectory() as root:
   class Gateway:
    revision='one';calls=0
    def scene(self,s):return {'model':'cheap','connection':'main','instruction':'','revision':self.revision}
    def complete(self,*args,**kwargs):self.calls+=1;return {'choices':[{'message':{'content':'{"overview":"舞蹈","confidence":0.8}'}}]}
   gateway=Gateway();ledger=m.usage.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg);flow=m.WatchFlow(root,gateway,lambda:cfg,ledger)
   def processor(*args):return {'duration':2,'frames':[(0,Image.new('RGB',(20,30)))],'transcript':{},'audioFeatures':{},'times':[0],'truncated':False}
   old_key=flow.key('sha','video_watch');first,cached=flow.watch('a','sha','path',{},None,processor=processor);self.assertFalse(cached)
   gateway.revision='unrelated-change';second,cached=flow.watch('b','sha','path',{},None,processor=lambda *_:self.fail('cache must avoid preprocessing'))
   self.assertTrue(cached);self.assertEqual(gateway.calls,1);self.assertEqual(first,second)
   gateway.scene=lambda _:dict(model='other',connection='main',instruction='');self.assertNotEqual(flow.key('sha','video_watch'),old_key)
 def test_quota_returns_local_analysis_without_fake_success(self):
  with tempfile.TemporaryDirectory() as root:
   class Gateway:
    def scene(self,s):return {'model':'cheap'}
    def complete(self,*a,**k):raise m.usage.UsageLimit('今日 AI 观看额度已用完')
   ledger=m.usage.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg);flow=m.WatchFlow(root,Gateway(),lambda:cfg,ledger)
   result,_=flow.watch('u','sha','path',{},None,processor=lambda *_:{'duration':2,'frames':[(0,Image.new('RGB',(2,2)))],'transcript':{'text':'歌词'},'audioFeatures':{},'times':[0],'truncated':False})
   self.assertEqual(result['understanding']['status'],'local_only');self.assertEqual(result['audio']['transcript']['text'],'歌词')
 def test_chat_tolerates_fenced_or_plain_replies_and_asks_json_each_turn(self):
  with tempfile.TemporaryDirectory() as root:
   replies=['```json\n{"reply":"看到手势舞","brief":{"output":"video","goal":"同款手势舞","keep":["手势"],"change":[],"notes":""}}\n```','好的，换成办公室场景，保留手势和直视镜头。','好的：{"reply":"已改成办公室","brief":{"output":"video","goal":"办公室手势舞","keep":[],"change":["场景"],"notes":""}} 请确认']
   class Gateway:
    modes=[]
    def scene(self,s):return {'model':'cheap'}
    def complete(self,scene,messages,**kwargs):self.modes.append(messages[0]['content']);return {'choices':[{'message':{'content':replies[len(self.modes)-1]}}]}
   gateway=Gateway();flow=m.WatchFlow(root,gateway,lambda:cfg,m.usage.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg))
   first=flow.chat('a','sha',{'overview':'手势舞'},'','request-1');self.assertEqual(first['brief']['goal'],'同款手势舞')
   second=flow.chat('a','sha',{'overview':'手势舞'},'换成办公室','request-2');self.assertIn('办公室',second['reply']);self.assertEqual(second['brief'],first['brief']);self.assertEqual(second['turn'],2)
   third=flow.chat('a','sha',{'overview':'手势舞'},'可以','request-3');self.assertEqual(third['brief']['goal'],'办公室手势舞')
   self.assertTrue(all('每一轮都只输出这个JSON对象' in x for x in gateway.modes))
   self.assertIn('简体中文',m.content.WATCH_SYSTEM)
 def test_peek_uses_cover_and_caption_and_is_cached_per_post(self):
  with tempfile.TemporaryDirectory() as root:
   seen=[]
   class Gateway:
    def scene(self,s):return {'model':'cheap','connection':'main','instruction':''}
    def complete(self,scene,messages,**kwargs):
     seen.append((scene,messages));return {'choices':[{'message':{'content':json.dumps({'overview':'女生在KTV唱歌','type':'翻唱','tags':['KTV'],'confidence':0.8},ensure_ascii=False)}}]}
   flow=m.WatchFlow(root,Gateway(),lambda:cfg,m.usage.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg))
   first=flow.peek('u1','123456',Image.new('RGB',(20,30)),'#KTV 翻唱')
   self.assertEqual(first['status'],'ready');self.assertEqual(first['overview'],'女生在KTV唱歌');self.assertEqual(first['source'],'cover')
   self.assertEqual(seen[0][0],'video_glance');self.assertIn('#KTV 翻唱',json.dumps(seen[0][1],ensure_ascii=False))
   again=flow.peek('u2','123456',Image.new('RGB',(20,30)),'')
   self.assertTrue(again['cached']);self.assertEqual(len(seen),1,'同一条作品只看一次')
 def test_watch_keeps_screen_text_and_glance_is_cached_for_everyone(self):
  with tempfile.TemporaryDirectory() as root:
   seen=[]
   class Gateway:
    calls=0
    def scene(self,s):return {'model':'cheap','connection':'main','instruction':''}
    def complete(self,scene,messages,**kwargs):
     self.calls+=1;seen.append((scene,messages))
     data={'overview':'对口型','type':'对口型','tags':['老歌'],'confidence':0.8} if scene=='video_glance' else {'overview':'对口型唱歌','confidence':0.9,'type':'深情对口型','valueSources':{'text':1}}
     return {'choices':[{'message':{'content':json.dumps(data,ensure_ascii=False)}}]}
   gateway=Gateway();flow=m.WatchFlow(root,gateway,lambda:cfg,m.usage.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg))
   screen={'status':'ready','items':[{'start':0,'end':2,'text':'有人问我','box':[0,0.8,1,0.05],'confidence':0.9,'persistent':False},{'start':0,'end':17,'text':'抖音号:1','box':[0,0,0.2,0.03],'confidence':0.9,'persistent':True}],'interval':1}
   def processor(*args):return {'duration':17,'frames':[(0,Image.new('RGB',(20,30)))],'transcript':{},'audioFeatures':{},'screenText':screen,'times':[0],'truncated':False}
   value,_=flow.watch('a','sha','path',{},None,processor=processor)
   self.assertEqual(value['analyzerVersion'],'content-watch-5');self.assertEqual(value['screenText'],screen);self.assertEqual(value['understanding']['type'],'深情对口型')
   payload=json.loads(seen[0][1][1]['content'][0]['text']);self.assertEqual([x['text'] for x in payload['screenText']],['有人问我'])
   video=Path(root)/'v.mp4';video.write_bytes(b'x')
   def run(cmd,**k):
    Image.new('RGB',(36,64)).save(cmd[-1]);return type('R',(),{'returncode':0})()
   first=flow.glance('a','sha',video,{'durationSeconds':17,'width':1080,'height':1920},runner=run)
   second=flow.glance('b','sha',video,{'durationSeconds':17,'width':1080,'height':1920},runner=lambda *a,**k:self.fail('cached'))
   self.assertEqual(first['overview'],'对口型');self.assertFalse(first['cached']);self.assertTrue(second['cached'])
   glance_images=sum(1 for c in seen[-1][1][1]['content'] if c['type']=='image_url');self.assertEqual(glance_images,3)
 def test_review_hook_rewatches_once_then_serves_cache(self):
  with tempfile.TemporaryDirectory() as root:
   class Gateway:
    calls=0
    def scene(self,s):return {'model':'cheap','connection':'main','instruction':''}
    def complete(self,*a,**k):self.calls+=1;return {'choices':[{'message':{'content':'{"overview":"第'+str(self.calls)+'次","confidence":0.8}'}}]}
   gateway=Gateway();flow=m.WatchFlow(root,gateway,lambda:cfg,m.usage.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg));flags={'sha'}
   flow.review_hook=(lambda a:a in flags,lambda a:flags.discard(a))
   processor=lambda *a:{'duration':2,'frames':[(0,Image.new('RGB',(20,30)))],'transcript':{},'audioFeatures':{},'times':[0],'truncated':False}
   flags.discard('sha');first,_=flow.watch('a','sha','p',{},None,processor=processor);flags.add('sha')
   second,cached=flow.watch('b','sha','p',{},None,processor=processor);self.assertFalse(cached);self.assertEqual(second['understanding']['overview'],'第2次');self.assertEqual(flags,set())
   third,cached=flow.watch('c','sha','p',{},None,processor=processor);self.assertTrue(cached);self.assertEqual(third['understanding']['overview'],'第2次')
if __name__=='__main__':unittest.main()
