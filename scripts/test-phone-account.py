import importlib.util,io,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('auth',Path(__file__).with_name('wechat-auth.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.config=self.root/'config';self.config.write_text(json.dumps({'appId':'wx-test','appSecret':'private-secret'}));self.calls=[];self.reply={'errcode':0,'phone_info':{'purePhoneNumber':'13812345678','countryCode':'86','watermark':{'appid':'wx-test'}}}
  def opener(req,**kw):
   url=req if isinstance(req,str) else req.full_url;self.calls.append(url)
   value={'openid':'stable-openid'} if 'jscode2session' in url else {'access_token':'secret-token','expires_in':7200} if 'stable_token' in url else self.reply
   return io.BytesIO(json.dumps(value).encode())
  self.auth=m.WechatAuth(self.config,self.root/'auth.sqlite',opener=opener);self.login=self.auth.login('login-code');self.user=self.login['userId']
 def tearDown(self):self.temp.cleanup()
 def test_profile_persists_and_binding_preserves_identity_assets_and_hides_phone(self):
  self.auth.claim(self.user,'run:'+'a'*32);before=self.auth.profile(self.user);self.assertFalse(before['phoneBound'])
  self.assertEqual(before,self.auth.profile(self.user));self.assertIn(before['avatar'],range(8));self.assertTrue(before['nickname'])
  result=self.auth.bind_phone(self.user,'phone-code');self.assertTrue(result['phoneBound']);self.assertEqual(result['userId'],self.user);self.assertEqual(result['nickname'],before['nickname']);self.assertNotIn('13812345678',json.dumps(result));self.assertTrue(self.auth.owns(self.user,'run:'+'a'*32))
  count=len(self.calls);self.assertEqual(self.auth.bind_phone(self.user,'another-code'),result);self.assertEqual(len(self.calls),count)
  restored=m.WechatAuth(self.config,self.root/'auth.sqlite');self.assertEqual(restored.profile(self.user),result)
  self.assertEqual(self.auth.phone(self.user),'+86 13812345678','完整手机号只供运营溯源（按所有者决定保存，已写入采集声明）')
 def test_wrong_app_replay_and_failed_provider_never_unlock_account(self):
  self.reply['phone_info']['watermark']['appid']='wrong'
  with self.assertRaises(m.LoginError):self.auth.bind_phone(self.user,'phone-code')
  self.assertFalse(self.auth.bound(self.user))
  with self.assertRaisesRegex(m.LoginError,'已使用'):self.auth.bind_phone('other-user','phone-code')
  self.reply={'errcode':48001,'errmsg':'secret detail'}
  with self.assertRaises(m.LoginError) as e:self.auth.bind_phone(self.user,'new-phone-code')
  self.assertNotIn('secret',str(e.exception));self.assertFalse(self.auth.bound(self.user))
 def test_attempt_limit_and_client_supplied_number_rejected(self):
  with self.assertRaises(m.LoginError):self.auth.bind_phone(self.user,{'phoneNumber':'13812345678'})
  self.reply={'errcode':40029}
  for i in range(5):
   with self.assertRaises(m.LoginError):self.auth.bind_phone(self.user,'phone-code-'+str(i))
  with self.assertRaisesRegex(m.LoginError,'尝试过多'):self.auth.bind_phone(self.user,'phone-code-6')
if __name__=='__main__':unittest.main()
