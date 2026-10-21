import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('plan',Path(__file__).with_name('analysis-plan.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):self.plan={'templateId':'custom-templateabc','templateName':'我的模板','version':1,'materialType':'product','goalIds':['selling','trust'],'questions':[{'key':'proof','title':'证据','question':'哪些画面支持真实卖点？'}],'steps':['只写可验证信息']}
 def test_valid_multigoal_and_instruction_boundaries(self):
  value=m.validate(self.plan);self.assertEqual(value['goalIds'],['selling','trust']);text=m.instruction(value);self.assertIn('不',text);self.assertIn('不是原片事实',text);self.assertIn('真实卖点',text);self.assertIsNone(m.validate(None))
 def test_reject_unknown_fields_types_oversize_and_duplicate_questions(self):
  for update in ({'code':'evil'},{'version':True},{'materialType':'unknown'},{'goalIds':['unknown']},{'templateName':'x'*33},{'questions':self.plan['questions']*2}):
   value=copy.deepcopy(self.plan);value.update(update)
   with self.assertRaises(ValueError):m.validate(value)
 def test_generation_requires_same_approved_plan_and_preserves_it(self):
  spec=importlib.util.spec_from_file_location('video_plan_test',Path(__file__).with_name('video-server.py'));video=importlib.util.module_from_spec(spec);spec.loader.exec_module(video)
  shots=[{'narration':'真实文字','visual':'文字画面'} for _ in range(3)]
  data={'idea':'原创新主题','duration':2,'mood':'温柔治愈','visualStyle':'纯文字画面','analysisPlan':self.plan,'storyboard':{'status':'approved','shots':shots,'analysisPlan':self.plan}}
  value=video.validate(data);self.assertEqual(value['analysisPlan'],self.plan);self.assertIn('用户拆解模板',video.ai_prompt(value))
  data['storyboard']['analysisPlan']={**self.plan,'templateName':'已改变'}
  with self.assertRaisesRegex(ValueError,'重新确认'):video.validate(data)
if __name__=='__main__':unittest.main()
