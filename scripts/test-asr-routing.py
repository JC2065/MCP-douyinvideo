import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('server',Path(__file__).with_name('video-server.py'))
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)

class Tests(unittest.TestCase):
    def test_models_are_separate_cached_and_voice_defaults_tiny(self):
        constructed=[]
        class Model:
            def __init__(self,path,**kwargs):
                constructed.append(path)
                self.path=path
                self.assert_local=kwargs['local_files_only']
            def transcribe(self,*args,**kwargs):
                return iter([]),SimpleNamespace(language='zh')
        with patch.dict(server.ASR_MODELS,{},clear=True),patch('faster_whisper.WhisperModel',Model):
            self.assertEqual(server._transcribe_reference('a')['status'],'silent')
            self.assertEqual(server._transcribe_reference('a','small')['status'],'silent')
            server._transcribe_reference('a')
            self.assertEqual(len(constructed),2)
            self.assertEqual(set(server.ASR_MODELS),{'tiny','small'})
            self.assertTrue(all(m.assert_local for m in server.ASR_MODELS.values()))
    def test_video_routes_to_configured_small(self):
        # Injecting the default transcriber keeps the production routing condition exercised.
        original=server._transcribe_reference
        calls=[]
        def transcribe(path,model='tiny'):calls.append(model);return {}
        def watch(user,sha,path,media,callback,*args,**kwargs):
            callback('audio');return {'understanding':{'status':'ready'}},False
        with patch.object(server,'_transcribe_reference',transcribe),patch.object(server,'_reference_asset',return_value=('sha','path',{})),patch.object(server.WATCH_FLOW,'watch',side_effect=watch),patch.object(server.PLATFORM,'config',return_value={'videoUnderstanding':{'asrModel':'small','autoDeepWatch':False}}):
            server.analyze_reference({},transcriber=transcribe)
        self.assertEqual(calls,['small'])

if __name__=='__main__':unittest.main()
