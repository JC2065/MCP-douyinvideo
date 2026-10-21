"""Server-only WeChat login and revocable persistent opaque sessions."""
import hashlib,hmac,json,re,secrets,sqlite3,time,uuid,threading
from pathlib import Path
from urllib.parse import urlencode,urlparse,parse_qs
from urllib.request import urlopen,Request
from contextlib import contextmanager

class LoginError(ValueError):pass
class WechatAuth:
    def __init__(self,config_path,database,clock=time.time,opener=urlopen):
        self.config_path=Path(config_path);self.database=Path(database);self.clock=clock;self.opener=opener
        self.phone_lock=threading.RLock();self.access_token=None;self.access_expiry=0
        self.database.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS sessions (digest TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS resources (resource TEXT,user_id TEXT,payload TEXT,PRIMARY KEY(resource,user_id))')
            db.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY,value TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS accounts (user_id TEXT PRIMARY KEY,nickname TEXT NOT NULL,avatar INTEGER NOT NULL,phone_mask TEXT,phone_digest TEXT,bound_at INTEGER)')
            db.execute('CREATE TABLE IF NOT EXISTS account_details(user_id TEXT PRIMARY KEY,email TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS phone_codes (digest TEXT PRIMARY KEY,user_id TEXT NOT NULL,created INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS phones (user_id TEXT PRIMARY KEY,country TEXT NOT NULL,number TEXT NOT NULL,saved INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS openids (user_id TEXT PRIMARY KEY,openid TEXT NOT NULL)')  # only for subscribe messages the user agreed to
            # 体验版测试账号：由真实微信用户在体验版/开发版中生成，手机号为虚构号段100开头，数据照常写入但统一标注为体验版。
            db.execute('CREATE TABLE IF NOT EXISTS trial_accounts (user_id TEXT PRIMARY KEY,owner TEXT NOT NULL,phone TEXT NOT NULL,created INTEGER NOT NULL)')
            db.execute('INSERT OR IGNORE INTO settings VALUES (?,?)',('trial_enabled','1'))
            db.execute('INSERT OR IGNORE INTO settings VALUES (?,?)',('media_secret',secrets.token_hex(32)))
            self.media_secret=bytes.fromhex(db.execute('SELECT value FROM settings WHERE name=?',('media_secret',)).fetchone()[0])
        self.database.chmod(0o600)
    @contextmanager
    def db(self):
        connection=sqlite3.connect(self.database,timeout=10)
        try:
            with connection:yield connection
        finally:connection.close()
    TRIAL_LIMIT=20
    def _issue(self,db,user_id):
        token=secrets.token_urlsafe(32);expires=int(self.clock())+7200
        db.execute('DELETE FROM sessions WHERE expires<=?',(int(self.clock()),))
        db.execute('INSERT INTO sessions VALUES (?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user_id,expires))
        return token,expires
    def trial_enabled(self):
        with self.db() as db:row=db.execute('SELECT value FROM settings WHERE name=?',('trial_enabled',)).fetchone()
        return bool(row and row[0]=='1')
    def set_trial_enabled(self,enabled):
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('trial_enabled','1' if enabled else '0'))
            if not enabled:db.execute('DELETE FROM sessions WHERE user_id IN (SELECT user_id FROM trial_accounts)')
        return self.trial_enabled()
    def trial_owner(self,user):
        with self.db() as db:row=db.execute('SELECT owner FROM trial_accounts WHERE user_id=?',(user,)).fetchone()
        return row[0] if row else None
    def is_trial(self,user):return bool(user) and self.trial_owner(user) is not None
    def trial_users(self):
        with self.db() as db:return {r[0] for r in db.execute('SELECT user_id FROM trial_accounts').fetchall()}
    def trial_accounts(self):
        with self.db() as db:
            rows=db.execute('SELECT t.user_id,t.owner,t.phone,t.created,a.nickname FROM trial_accounts t LEFT JOIN accounts a ON a.user_id=t.user_id ORDER BY t.created DESC LIMIT 500').fetchall()
        return [{'userId':r[0],'owner':r[1],'phone':r[2],'created':r[3],'nickname':r[4] or ''} for r in rows]
    def create_trial(self,user):
        """Generate a fresh test account with a fictitious 100-prefixed number (never a real allocation)."""
        if not self.trial_enabled():raise LoginError('体验版测试账号已被管理员关闭')
        owner=self.trial_owner(user) or user
        with self.db() as db:
            if db.execute('SELECT count(*) FROM trial_accounts WHERE owner=?',(owner,)).fetchone()[0]>=self.TRIAL_LIMIT:raise LoginError(f'每个微信最多生成{self.TRIAL_LIMIT}个测试账号')
            while True:
                phone='100'+''.join(str(secrets.randbelow(10)) for _ in range(8))
                if not db.execute('SELECT 1 FROM trial_accounts WHERE phone=?',(phone,)).fetchone():break
            trial=str(uuid.uuid4());now=int(self.clock())
            nickname='体验'+secrets.choice(('晴天','微光','山野','听风','星河','拾光'))+phone[-4:]
            db.execute('INSERT INTO accounts(user_id,nickname,avatar,phone_mask,phone_digest,bound_at) VALUES(?,?,?,?,?,?)',
                       (trial,nickname,secrets.randbelow(8),'+86 '+phone,hmac.new(self.media_secret,('86:'+phone).encode(),hashlib.sha256).hexdigest(),now))
            db.execute('INSERT INTO trial_accounts VALUES(?,?,?,?)',(trial,owner,phone,now))
            token,expires=self._issue(db,trial)
        return {'token':token,'expiresAt':expires,**self.profile(trial)}
    def login(self,code,trial=None):
        if not isinstance(code,str) or not re.fullmatch('[A-Za-z0-9_-]{8,256}',code):raise LoginError('微信登录凭证无效，请重新登录')
        try:
            config=json.loads(self.config_path.read_text(encoding='utf-8-sig'))
            if not config.get('appId') or not config.get('appSecret'):raise ValueError()
        except Exception:raise LoginError('服务端微信登录尚未配置') from None
        try:
            params=urlencode({'appid':config['appId'],'secret':config['appSecret'],'js_code':code,'grant_type':'authorization_code'})
            with self.opener('https://api.weixin.qq.com/sns/jscode2session?'+params,timeout=15) as response:
                raw=response.read(8193)
                if len(raw)>8192:raise ValueError()
                identity=json.loads(raw)
        except Exception:raise LoginError('微信登录服务暂时不可用，请重试') from None
        if identity.get('errcode') or not isinstance(identity.get('openid'),str) or not identity['openid']:
            raise LoginError('微信登录凭证已失效，请重新登录')
        user_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'youai-wechat:'+config['appId']+':'+identity['openid']))
        target=user_id
        if trial is not None and isinstance(trial,str) and re.fullmatch('[0-9a-f-]{36}',trial) and self.trial_enabled() and self.trial_owner(trial)==user_id:target=trial
        with self.db() as db:
            token,expires=self._issue(db,target)
            db.execute('INSERT OR REPLACE INTO openids VALUES (?,?)',(user_id,identity['openid']))
        return {'token':token,'expiresAt':expires,**self.profile(target)}
    def profile(self,user):
        with self.db() as db:
            nickname=secrets.choice(('晴天','微光','山野','听风','星河','拾光'))+secrets.choice(('旅人','记录员','创作者','观察家'))+str(secrets.randbelow(9000)+1000)
            db.execute('INSERT OR IGNORE INTO accounts(user_id,nickname,avatar) VALUES(?,?,?)',(user,nickname,secrets.randbelow(8)))
            row=db.execute('SELECT nickname,avatar,phone_mask,bound_at FROM accounts WHERE user_id=?',(user,)).fetchone()
            details=db.execute('SELECT email FROM account_details WHERE user_id=?',(user,)).fetchone()
            trial=db.execute('SELECT phone FROM trial_accounts WHERE user_id=?',(user,)).fetchone()
        return {'email':details[0] if details else '', 'emailVerified':False,'userId':user,'nickname':row[0],'avatar':row[1],'phoneMasked':row[2] or '', 'phoneBound':row[3] is not None,
                'trial':bool(trial),'trialPhone':trial[0] if trial else ''}
    def update_profile(self,user,payload):
        if not isinstance(payload,dict) or set(payload)!={'nickname','email','avatar'}:raise LoginError('资料字段无效')
        name=payload['nickname'];email=payload['email'];avatar=payload['avatar']
        if not isinstance(name,str) or not 1<=len(name.strip())<=30 or any(ord(c)<32 for c in name):raise LoginError('昵称需为1–30字')
        if not isinstance(email,str) or len(email)>254 or (email and not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}",email)):raise LoginError('请输入有效邮箱')
        if type(avatar) is not int or not 0<=avatar<8:raise LoginError('头像选项无效')
        self.profile(user)
        with self.db() as db:
            db.execute('UPDATE accounts SET nickname=?,avatar=? WHERE user_id=?',(name.strip(),avatar,user))
            db.execute('INSERT OR REPLACE INTO account_details VALUES(?,?)',(user,email))
        return self.profile(user)

    def bound(self,user):
        with self.db() as db:return bool(db.execute('SELECT 1 FROM accounts WHERE user_id=? AND bound_at IS NOT NULL',(user,)).fetchone())
    def wechat_json(self,url,body):
        try:
            with self.opener(Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=15) as response:
                raw=response.read(16385)
                if len(raw)>16384:raise ValueError()
                value=json.loads(raw)
            if not isinstance(value,dict):raise ValueError()
            return value
        except Exception:raise LoginError('手机号授权服务暂时不可用，请稍后重试') from None
    def token(self):
        """Shared stable access token (also used by phone binding)."""
        cfg=json.loads(self.config_path.read_text(encoding='utf-8-sig'));now=int(self.clock())
        if not self.access_token or self.access_expiry<=now:
            result=self.wechat_json('https://api.weixin.qq.com/cgi-bin/stable_token',{'grant_type':'client_credential','appid':cfg['appId'],'secret':cfg['appSecret'],'force_refresh':False})
            if not result.get('access_token'):raise LoginError('微信接口未就绪')
            self.access_token=result['access_token'];self.access_expiry=now+max(0,int(result.get('expires_in',0))-120)
        return self.access_token
    def notify(self,user,template,page,data):
        """Send one subscribe message (the user must have accepted the template in the mini program)."""
        with self.db() as db:row=db.execute('SELECT openid FROM openids WHERE user_id=?',(user,)).fetchone()
        if not row or not template:return False
        result=self.wechat_json('https://api.weixin.qq.com/cgi-bin/message/subscribe/send?'+urlencode({'access_token':self.token()}),
                                {'touser':row[0],'template_id':template,'page':page,'data':{k:{'value':str(v)[:20]} for k,v in data.items()},'miniprogram_state':'formal','lang':'zh_CN'})
        if result.get('errcode') in (40001,40014,42001):self.access_token=None
        return result.get('errcode') in (None,0)
    def bind_phone(self,user,code):
        if not isinstance(code,str) or not re.fullmatch('[A-Za-z0-9_-]{8,256}',code):raise LoginError('请点击按钮重新授权手机号')
        with self.phone_lock:
            if self.bound(user):return self.profile(user)
            self.profile(user)
            now=int(self.clock());digest=hashlib.sha256(code.encode()).hexdigest()
            with self.db() as db:
                db.execute('DELETE FROM phone_codes WHERE created<?',(now-600,))
                if db.execute('SELECT count(*) FROM phone_codes WHERE user_id=?',(user,)).fetchone()[0]>=5:raise LoginError('授权尝试过多，请10分钟后重试')
                try:db.execute('INSERT INTO phone_codes VALUES(?,?,?)',(digest,user,now))
                except sqlite3.IntegrityError:raise LoginError('授权凭证已使用，请重新点击授权') from None
            try:
                cfg=json.loads(self.config_path.read_text(encoding='utf-8-sig'))
                appid,secret=cfg['appId'],cfg['appSecret']
            except Exception:raise LoginError('手机号授权服务尚未配置') from None
            if not self.access_token or self.access_expiry<=now:
                result=self.wechat_json('https://api.weixin.qq.com/cgi-bin/stable_token',{'grant_type':'client_credential','appid':appid,'secret':secret,'force_refresh':False})
                if not result.get('access_token'):raise LoginError('手机号接口未就绪，请管理员检查微信权限和IP白名单')
                self.access_token=result['access_token'];self.access_expiry=now+max(0,int(result.get('expires_in',0))-120)
            result=self.wechat_json('https://api.weixin.qq.com/wxa/business/getuserphonenumber?'+urlencode({'access_token':self.access_token}),{'code':code})
            if result.get('errcode') not in (None,0):
                if result.get('errcode') in (40001,40014,42001):self.access_token=None
                raise LoginError('手机号授权未完成，请重新授权；仍失败请管理员检查接口权限及额度')
            info=result.get('phone_info') or {};watermark=info.get('watermark') or {}
            number=info.get('purePhoneNumber');country=info.get('countryCode')
            if watermark.get('appid')!=appid or not isinstance(number,str) or not re.fullmatch(r'\d{5,15}',number) or not isinstance(country,str) or not re.fullmatch(r'\d{1,4}',country):
                raise LoginError('微信手机号校验失败，请重新授权')
            mask='+'+country+' '+(number[:3]+'****'+number[-4:] if len(number)>=8 else number[:1]+'****'+number[-1:])
            phone_digest=hmac.new(self.media_secret,(country+':'+number).encode(),hashlib.sha256).hexdigest()
            with self.db() as db:
                db.execute('UPDATE accounts SET phone_mask=?,phone_digest=?,bound_at=? WHERE user_id=?',(mask,phone_digest,now,user))
                db.execute('INSERT OR REPLACE INTO phones VALUES(?,?,?,?)',(user,country,number,now))  # 完整手机号：运营溯源与沟通（已在采集声明中告知）
            return self.profile(user)
    def phone(self,user):
        """Full phone number for operations (empty for accounts bound before numbers were kept)."""
        with self.db() as db:
            row=db.execute('SELECT country,number FROM phones WHERE user_id=?',(user,)).fetchone()
            trial=db.execute('SELECT phone FROM trial_accounts WHERE user_id=?',(user,)).fetchone()
        if row:return '+'+row[0]+' '+row[1]
        return trial[0] if trial else ''
    def user(self,token):
        if not isinstance(token,str) or not re.fullmatch('[A-Za-z0-9_-]{43}',token):return None
        with self.db() as db:
            row=db.execute('SELECT user_id FROM sessions WHERE digest=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),int(self.clock()))).fetchone()
        return row[0] if row else None
    def revoke(self,token):
        if not isinstance(token,str):return
        with self.db() as db:db.execute('DELETE FROM sessions WHERE digest=?',(hashlib.sha256(token.encode()).hexdigest(),))
    @staticmethod
    def resource(path):
        path=urlparse(path).path
        for pattern,kind in [(r'/(?:works/image|image-assets)/([a-f0-9]{32})(?:\.png)?','image'),(r'/(?:jobs|asset-runs|assets)/([a-f0-9]{32})(?:/.*)?','run'),(r'/media/([a-f0-9]{32})\.mp4','run'),(r'/reference-analyses/([a-f0-9]{32})','analysis'),(r'/tool-assets/([a-f0-9]{64})/.*','tool'),(r'/reference-assets/([a-f0-9]{64})\.mp4','reference'),(r'/replica-media/([a-f0-9]{32})\.mp4','replica'),(r'/board-media/([a-f0-9]{32})\.mp4','board'),(r'/idea-media/([a-f0-9]{32})\.jpg','idea')]:
            match=re.fullmatch(pattern,path)
            if match:return kind+':'+match[1]
        return None
    def claim(self,user,resource,payload=None):
        with self.db() as db:
            db.execute('INSERT INTO resources VALUES (?,?,?) ON CONFLICT(resource,user_id) DO UPDATE SET payload=coalesce(excluded.payload,resources.payload)',(resource,user,json.dumps(payload) if payload is not None else None))
    def owns(self,user,resource):
        if not user or not resource:return False
        with self.db() as db:return bool(db.execute('SELECT 1 FROM resources WHERE resource=? AND user_id=?',(resource,user)).fetchone())
    def reference(self,user,sha):
        with self.db() as db:row=db.execute('SELECT payload FROM resources WHERE resource=? AND user_id=?',('reference:'+str(sha),user)).fetchone()
        if not row or not row[0]:raise LoginError('参考素材不属于当前账号，请重新获取')
        return json.loads(row[0])
    def remember(self,user,value):
        if isinstance(value,dict):
            asset=value.get('asset')
            if isinstance(asset,dict) and re.fullmatch('[a-f0-9]{64}',str(asset.get('sha256',''))) and asset.get('storagePath'):
                self.claim(user,'reference:'+asset['sha256'],value)
            for item in value.values():self.remember(user,item)
        elif isinstance(value,list):
            for item in value:self.remember(user,item)
    def signed_url(self,user,url,ttl=3600):
        resource=self.resource(url)
        if not self.owns(user,resource):raise LoginError('素材不属于当前账号')
        parsed=urlparse(url);expires=int(self.clock())+max(1,min(3600,int(ttl)))
        signature=hmac.new(self.media_secret,f'{user}|{parsed.path}|{expires}'.encode(),hashlib.sha256).hexdigest()
        return url+('&' if parsed.query else '?')+urlencode({'__u':user,'__e':expires,'__s':signature})
    def media_user(self,url):
        parsed=urlparse(url);query=parse_qs(parsed.query)
        try:
            user=query['__u'][0];expires=int(query['__e'][0]);signature=query['__s'][0]
            if not self.clock()<expires<=self.clock()+3600:return None
            expected=hmac.new(self.media_secret,f'{user}|{parsed.path}|{expires}'.encode(),hashlib.sha256).hexdigest()
            return user if hmac.compare_digest(expected,signature) and self.owns(user,self.resource(url)) else None
        except (KeyError,ValueError,TypeError):return None
