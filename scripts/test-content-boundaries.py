import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('content-boundaries.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Tests(unittest.TestCase):
 def test_merge_and_reject(self):
  value={'version':b.CATALOG['version'],'platforms':['douyin','xiaohongshu','douyin']};self.assertEqual(b.validate(value)['platforms'],['douyin','xiaohongshu']);text=b.instruction(value);self.assertIn('显著标识',text);self.assertIn('不编造个人经历',text)
  for patch in ({'version':'old','platforms':['douyin']},{'version':b.CATALOG['version'],'platforms':[]},{'version':b.CATALOG['version'],'platforms':['unknown']}):
   with self.assertRaises(ValueError):b.validate(patch)
 def test_old_client(self):self.assertEqual(b.instruction(None),'');self.assertIsNone(b.validate(None))
if __name__=='__main__':unittest.main()
