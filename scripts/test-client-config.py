import importlib.util,json,os,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('config',Path(__file__).with_name('client-config.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ConfigTests(unittest.TestCase):
 def test_allowlist_and_bad_config(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'config.json';old=os.environ.get('YOUAI_CLIENT_CONFIG');os.environ['YOUAI_CLIENT_CONFIG']=str(p)
   try:
    self.assertFalse(m.client_config()['tools']['audio']['maintenance'])
    p.write_text(json.dumps({'script':'evil','tools':{'audio':{'maintenance':True,'url':'evil'},'new':{}}}))
    value=m.client_config();self.assertTrue(value['tools']['audio']['maintenance']);self.assertNotIn('script',value);self.assertNotIn('new',value['tools'])
    video_spec=importlib.util.spec_from_file_location('video_config_test',Path(__file__).with_name('video-server.py'))
    video=importlib.util.module_from_spec(video_spec);video_spec.loader.exec_module(video)
    with self.assertRaisesRegex(ValueError,'维护'):video.run_creation_tool('audio','invalid-url')
    for text in ('[]','broken','x'*17000):
     p.write_text(text);self.assertFalse(m.client_config()['tools']['audio']['maintenance'])
   finally:
    if old is None:os.environ.pop('YOUAI_CLIENT_CONFIG',None)
    else:os.environ['YOUAI_CLIENT_CONFIG']=old
if __name__=='__main__':unittest.main()
