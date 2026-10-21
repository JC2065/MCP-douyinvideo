const KEY='youai.video.session.v1';
// 体验版测试账号：保存生成的测试账号ID，登录时随微信凭证一起提交；服务端只在体验版/开发版且归属当前微信时切换到该账号。
const TRIAL_KEY='youai.trial.account.v1';
function trialAccount(wx){try{const v=wx.getStorageSync(TRIAL_KEY);return v&&v.userId?v:null;}catch(_){return null;}}
let pending=null;
function session(wx,base){
 let cached;try{cached=wx.getStorageSync(KEY);}catch(_){}
 if(cached&&cached.base===base&&cached.token&&cached.expiresAt*1000>Date.now()+60000)return Promise.resolve(cached);
 if(pending)return pending;
 pending=new Promise((resolve,reject)=>wx.login({timeout:10000,success:login=>{
  if(!login.code)return reject(Error('微信登录失败，请重试'));
  const trial=trialAccount(wx);
  wx.request({url:base+'/auth/login',method:'POST',data:trial?{code:login.code,trial:trial.userId}:{code:login.code},timeout:20000,success:r=>{
   if(r.statusCode!==200||!r.data||!r.data.token)return reject(Error(r.data&&r.data.error||'微信登录失败，请重试'));
   if(trial&&r.data.userId!==trial.userId){try{wx.removeStorageSync(TRIAL_KEY);}catch(_){}}
   const value={...r.data,base};try{wx.setStorageSync(KEY,value);}catch(_){}resolve(value);
  },fail:()=>reject(Error('无法连接登录服务，请重试'))});
 },fail:()=>reject(Error('微信登录失败，请重试'))})).finally(()=>{pending=null;});
 return pending;
}
function send(wx,base,options,retry=true){
 if(/^http:\/\/(127\.0\.0\.1|localhost)(:|\/)/.test(base))return wx.request(options);
 session(wx,base).then(login=>wx.request({...options,header:{...options.header,Authorization:'Bearer '+login.token},success:r=>{
  if(r.statusCode===401&&retry){try{wx.removeStorageSync(KEY);}catch(_){}return send(wx,base,options,false);}
  if(options.success)options.success(r);
 }})).catch(error=>options.fail&&options.fail({errMsg:error.message}));
}
module.exports={KEY,TRIAL_KEY,trialAccount,session,send};
