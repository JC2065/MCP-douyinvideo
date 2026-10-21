import importlib.util,tempfile,unittest,threading
from pathlib import Path
def module(name):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('usage-ledger');p=module('platform-config')
class Tests(unittest.TestCase):
 def test_atomic_quota_budget_usage_and_cache(self):
  with tempfile.TemporaryDirectory() as root:
   cfg=dict(p.WATCH_DEFAULT,perUserDailyVideos=1);ledger=m.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg)
   ident=ledger.reserve('u','sha','video_watch','qwen3.8-flash',100,100)
   ledger.settle(ident,{'prompt_tokens':90,'completion_tokens':10,'prompt_tokens_details':{'cached_tokens':20}})
   with self.assertRaises(m.UsageLimit):ledger.reserve('u','sha2','video_watch','qwen3.8-flash',100,100)
   ledger.cache_hit('u','sha2','video_watch','qwen3.8-flash')
   self.assertEqual(ledger.overview()['today']['cacheHits'],1);self.assertEqual(ledger.overview()['today']['tokens'],100)
   cfg['dailyBudgetYuan']=0
   with self.assertRaises(m.UsageLimit):ledger.reserve('v','sha','video_chat','qwen3.8-flash',1,1)
 def test_credits_extend_personal_quota_only_when_available(self):
  with tempfile.TemporaryDirectory() as root:
   cfg=dict(p.WATCH_DEFAULT,perUserDailyVideos=1);ledger=m.UsageLedger(Path(root)/'usage.sqlite',lambda:cfg);credits=[1]
   def spend(user):
    if credits[0]<=0:return False
    credits[0]-=1;return True
   ledger.extra=spend;ledger.reserve('u','a','video_watch','qwen3.8-flash',10,10);ledger.reserve('u','b','video_watch','qwen3.8-flash',10,10)
   self.assertEqual(credits[0],0)
   with self.assertRaises(m.UsageLimit):ledger.reserve('u','c','video_watch','qwen3.8-flash',10,10)
 def test_config_validation_and_old_config_publish(self):
  with tempfile.TemporaryDirectory() as root:
   platform=p.Platform(root);cfg=platform.config();self.assertEqual(cfg['videoUnderstanding']['maxFrames'],32)
   with self.assertRaises(ValueError):p.validate_watch(dict(p.WATCH_DEFAULT,chatMaxTurns=5))
   payload={'expectedRevision':cfg['revision'],'connections':[],'video':cfg['video'],'videoUnderstanding':dict(p.WATCH_DEFAULT,maxFrames=16)}
   platform.publish(payload);self.assertEqual(platform.config()['videoUnderstanding']['maxFrames'],16)
if __name__=='__main__':unittest.main()
