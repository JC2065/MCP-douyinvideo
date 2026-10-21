import importlib.util
import json
import tempfile
import subprocess
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
spec=importlib.util.spec_from_file_location('admin',Path(__file__).with_name('admin-console.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.auth=self.root/'auth.json';self.auth.write_text(json.dumps(m.credential('test-password-123456')))
        self.console=m.Console(self.root/'admin',self.auth,self.root/'config.json',lambda:{'sources':{},'rows':[]},lambda *a,**k:{'status':'expired'},lambda:[])
        self.token=self.console.login({'username':'admin','password':'test-password-123456'},'test')['token']
        self.header='Bearer '+self.token
    def tearDown(self): self.tmp.cleanup()
    def call(self,path,method='GET',payload=None,header=None):
        return self.console.dispatch(method,'/admin-api/'+path,payload or {},self.header if header is None else header,'test')
    def test_task_interest_deduplicated_persistent_and_admin_only(self):
        self.assertEqual(self.call('overview')['taskInterest']['total'],0)
        self.assertTrue(self.console.task_interest('user-a')['supported'])
        self.assertEqual(self.console.task_interest('user-a')['total'],1)
        self.assertEqual(self.console.task_interest('user-b')['total'],2)
        other=m.Console(self.root/'admin',self.auth,self.root/'config.json',lambda:{'sources':{},'rows':[]},lambda *a,**k:{'status':'expired'},lambda:[])
        self.assertEqual(other.task_interest()['total'],2)
        self.assertNotIn('user-a',json.dumps(self.call('overview')['taskInterest']))

    def test_independent_auth_and_expiry(self):
        for header in ('','Bearer wx-user-token','Basic admin'):
            with self.assertRaises(m.AdminError) as e:self.call('overview',header=header)
            self.assertEqual(e.exception.status,401)
        self.console.sessions={key:0 for key in self.console.sessions}
        with self.assertRaises(m.AdminError):self.call('config')
    def test_logout_and_restart_revoke(self):
        self.call('logout','POST')
        with self.assertRaises(m.AdminError):self.call('config')
        self.assertEqual(len(self.console.sessions),0)
    def test_eight_character_password_and_old_password_rejection(self):
        self.auth.write_text(json.dumps(m.credential('pass1234')))
        value=self.console.login({'username':'admin','password':'pass1234'},'changed')
        self.assertTrue(value['token'])
        for password in ('short','test-password-123456'):
            with self.assertRaises(m.AdminError) as error:self.console.login({'username':'admin','password':password},'changed')
            self.assertEqual(error.exception.status,401)
    def test_publish_conflict_rollback_and_persistence(self):
        tools=self.call('config')['tools'];tools['audio']['maintenance']=True
        value=self.call('config','POST',{'expectedRevision':'default','tools':tools})
        self.assertTrue(value['tools']['audio']['maintenance'])
        with self.assertRaises(m.AdminError) as e:self.call('config','POST',{'expectedRevision':'default','tools':tools})
        self.assertEqual(e.exception.status,409)
        baseline=next(v for v in self.call('versions')['rows'] if v['event']=='baseline')
        reverted=self.call('config','POST',{'expectedRevision':value['revision'],'rollback':baseline['revision']})
        self.assertFalse(reverted['tools']['audio']['maintenance']);self.assertNotEqual(reverted['revision'],value['revision'])
        other=m.Console(self.root/'admin',self.auth,self.root/'config.json',None,None,None)
        self.assertEqual(other.config(),reverted);self.assertFalse(other.sessions)
        self.assertEqual(self.call('audit')['rows'][0]['event'],'rollback')
    def test_reject_code_extra_fields_invalid_types_and_traversal(self):
        tools=self.call('config')['tools']
        for data in ({'expectedRevision':'default','tools':tools,'script':'evil'}, {'expectedRevision':'default','tools':{}},{'expectedRevision':'default','rollback':'../auth'}):
            with self.assertRaises(m.AdminError):self.call('config','POST',data)
        tools['audio']['maintenance']='true'
        with self.assertRaises(m.AdminError):self.call('config','POST',{'expectedRevision':'default','tools':tools})
        self.assertEqual(self.call('config')['revision'],'default')
    def test_login_rate_limit_and_audit_no_secrets(self):
        for i in range(5):
            with self.assertRaises(m.AdminError) as e:self.console.login({'username':'admin','password':'wrong-password'},'bad')
            self.assertEqual(e.exception.status,401)
        with self.assertRaises(m.AdminError) as e:self.console.login({'username':'admin','password':'test-password-123456'},'bad')
        self.assertEqual(e.exception.status,429)
        audit=(self.root/'admin/audit.jsonl').read_text()
        self.assertNotIn(self.token,audit);self.assertNotIn('test-password',audit)
    def test_bootstrap_keeps_credentials_outside_checkout_and_preserves_existing(self):
        script=Path(__file__).with_name('admin-bootstrap.py')
        target=self.root/'initial'
        result=subprocess.run([sys.executable,str(script),'--directory',str(target)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        auth=json.loads((target/'admin-auth.json').read_text());self.assertNotIn('password',auth)
        initial=(target/'admin-login.txt').read_bytes()
        result=subprocess.run([sys.executable,str(script),'--directory',str(target)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertEqual((target/'admin-login.txt').read_bytes(),initial)
        result=subprocess.run([sys.executable,str(script),'--directory',str(script.resolve().parent/'unsafe-auth')],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertFalse((script.parent/'unsafe-auth').exists())
    def test_simultaneous_publish_one_wins(self):
        barrier=threading.Barrier(2);results=[];tools=self.call('config')['tools']
        def save():
            barrier.wait()
            try:self.call('config','POST',{'expectedRevision':'default','tools':tools});results.append(200)
            except m.AdminError as error:results.append(error.status)
        threads=[threading.Thread(target=save) for _ in range(2)]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        self.assertEqual(sorted(results),[200,409])
    def test_http_origin_size_and_web_headers(self):
        self.assertEqual(len(self.console.sessions),1)
        console=self.console
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):console.handle(self)
            def do_POST(self):console.handle(self)
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            with urlopen(base+'/admin/') as res:
                self.assertIn('YOUAI'.encode(),res.read());self.assertIn("frame-ancestors 'none'",res.headers['Content-Security-Policy']);self.assertNotIn('Access-Control-Allow-Origin',res.headers)
            for headers,status in [({'Authorization':self.header,'Origin':'https://evil.test'},403),({},401)]:
                with self.assertRaises(HTTPError) as e:urlopen(Request(base+'/admin-api/overview',headers=headers))
                self.assertEqual(e.exception.code,status)
            with self.assertRaises(HTTPError) as e:urlopen(Request(base+'/admin-api/config',data=b'x'*9000,headers={'Authorization':self.header,'Content-Type':'application/json'}))
            self.assertEqual(e.exception.code,400)
            with urlopen(Request(base+'/admin-api/overview',headers={'Authorization':self.header})) as res:self.assertEqual(json.load(res)['tasks'],[])
            with urlopen(Request(base+'/admin-api/overview',headers={'Authorization':self.header,'Origin':'https://youai888.top'})) as res:self.assertEqual(res.status,200)
        finally:server.shutdown();server.server_close()

    def test_history_cap_keeps_latest_and_current_version(self):
        for index in range(55):
            current=self.call('config')
            self.call('config','POST',{'expectedRevision':current['revision'],'tools':current['tools']})
        rows=self.call('versions')['rows']
        self.assertEqual(len(rows),50)
        self.assertEqual(rows[0]['revision'],self.call('config')['revision'])
        self.assertEqual(len(list((self.root/'admin/versions').glob('*.json'))),50)

    def test_task_export_omits_provider_error_user_and_signed_url(self):
        spec=importlib.util.spec_from_file_location('video_admin_test',Path(__file__).with_name('video-server.py'))
        video=importlib.util.module_from_spec(spec);spec.loader.exec_module(video)
        video.JOBS['a'*32]={'status':'failed','error':'provider-secret https://signed.test?token=private','userId':'private-user','idea':'private-prompt','startedAt':1}
        exported=json.dumps(video.admin_tasks())
        for secret in ('provider-secret','signed.test','private-user','private-prompt'):self.assertNotIn(secret,exported)
        self.assertIn('failed',exported)

if __name__=='__main__':unittest.main()
