import importlib.util,io,json,sqlite3,tempfile,threading,unittest
from contextlib import closing
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
spec=importlib.util.spec_from_file_location('preferences',Path(__file__).with_name('analysis-preferences.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def prefs():return {'customTemplates':[],'typeDefaults':{},'typeGoals':{'voice':['structure','visual']},'goals':[],'goalOverrides':{},'materialOverrides':{},'materialType':'auto','mode':'auto','preset':'structure','overrides':{}}
class Tests(unittest.TestCase):
 def test_user_isolation_revision_conflict_delete_and_restart(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'prefs.sqlite';store=m.Store(path);a=store.write('alice','none',prefs());self.assertEqual(store.read('bob')['revision'],'none')
   with self.assertRaises(m.Conflict):store.write('alice','none',prefs())
   changed=prefs();changed['typeGoals']={};store.write('alice',a['revision'],changed)
   self.assertEqual(m.Store(path).read('alice')['preferences'],changed)
   with closing(sqlite3.connect(path)) as source,closing(sqlite3.connect(Path(folder)/'backup.sqlite')) as target:source.backup(target)
   self.assertEqual(m.Store(Path(folder)/'backup.sqlite').read('alice')['preferences'],changed)
 def test_simultaneous_writes_only_one_wins(self):
  with tempfile.TemporaryDirectory() as folder:
   store=m.Store(Path(folder)/'prefs.sqlite');barrier=threading.Barrier(2);results=[]
   def run():
    barrier.wait()
    try:store.write('alice','none',prefs());results.append('ok')
    except m.Conflict:results.append('conflict')
   threads=[threading.Thread(target=run) for _ in range(2)]
   for thread in threads:thread.start()
   for thread in threads:thread.join()
   self.assertEqual(sorted(results),['conflict','ok'])
 def test_reject_untrusted_fields_bad_types_and_unknown_template(self):
  for patch in ({'userId':'bob'},{'script':'execute'},{'materialType':{}},{'typeGoals':{'voice':['unknown']}},{'preset':'missing'},{'overrides':{'__proto__':'structure'}},{'customTemplates':[{}]}):
   value=prefs();value.update(patch)
   with self.assertRaises(ValueError):m.validate(value)
 def test_custom_template_roundtrip_and_bounds(self):
  value=prefs();row={'id':'custom-validabc1','name':'我的模板','description':'说明','materialType':'voice','sections':[{'key':'question-own','title':'证据','question':'仅保存为问题，不执行任何代码'}],'dimensions':['question-own'],'steps':['用自己的素材练习'],'version':1,'goalIds':['structure'],'custom':True};value['customTemplates']=[row];value['typeDefaults']={'voice':row['id']}
  self.assertEqual(m.validate(value),value)
  row['version']=True
  with self.assertRaises(ValueError):m.validate(value)
 def test_http_identity_cannot_be_spoofed_and_no_auth_is_denied(self):
  spec=importlib.util.spec_from_file_location('video_prefs_test',Path(__file__).with_name('video-server.py'));video=importlib.util.module_from_spec(spec);spec.loader.exec_module(video)
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);config=root/'config';config.write_text(json.dumps({'appId':'test','appSecret':'not-real'}));video.AUTH=video._auth_module.WechatAuth(config,root/'sessions',opener=lambda url,**kwargs:io.BytesIO(json.dumps({'openid':'alice' if 'alice-code' in url else 'bob'}).encode()));video.ANALYSIS_PREFERENCES=video._prefs_module.Store(root/'prefs')
   server=video.ThreadingHTTPServer(('127.0.0.1',0),video.Handler);threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
   def req(path,data=None,token=None):
    try:
     with urlopen(Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+token} if token else {})})) as res:return res.status,json.load(res)
    except HTTPError as error:return error.code,{}
   try:
    self.assertEqual(req('/analysis-preferences')[0],401)
    a=req('/auth/login',{'code':'alice-code'})[1];b=req('/auth/login',{'code':'bob-code-0'})[1]
    self.assertEqual(req('/analysis-preferences',token=a['token'])[0],403)
    with video.AUTH.db() as db:db.execute('UPDATE accounts SET bound_at=1 WHERE user_id IN (?,?)',(a['userId'],b['userId']))
    status,saved=req('/analysis-preferences',{'expectedRevision':'none','preferences':prefs()},a['token']);self.assertEqual(status,200)
    self.assertEqual(req('/analysis-preferences',token=b['token'])[1]['revision'],'none')
    self.assertEqual(req('/analysis-preferences?userId=bob',token=a['token'])[1]['revision'],saved['revision'])
    self.assertEqual(req('/analysis-preferences',{'expectedRevision':saved['revision'],'preferences':prefs(),'userId':b['userId']},a['token'])[0],400)
    self.assertEqual(req('/analysis-preferences',{'expectedRevision':'none','preferences':prefs()},a['token'])[0],409)
    video.AUTH=None;self.assertEqual(req('/analysis-preferences')[0],503)
   finally:server.shutdown();server.server_close()
if __name__=='__main__':unittest.main()
