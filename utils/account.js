const {BASE}=require('./service-endpoints');
const sessions=require('./video-session');
const AVATARS=['🌱','🌙','🪁','🐳','🦊','🐼','🪴','🐧'];
const KEY='youai.account.profile.v1';
function cached(api){try{return api.getStorageSync(KEY)||null;}catch(_){return null;}}
function decorate(value){return {...value,avatarText:AVATARS[value.avatar]||AVATARS[0]};}
function request(api,path,data){return new Promise((resolve,reject)=>sessions.send(api,BASE,{url:BASE+path,method:data?'POST':'GET',data,timeout:25000,header:{'Content-Type':'application/json'},success:r=>{
 if(r.statusCode!==200)return reject(Error(r.data&&r.data.error||'账号服务暂不可用'));
 const value=decorate(r.data);api.setStorageSync(KEY,value);resolve(value);
},fail:e=>reject(Error(e.errMsg||'无法连接账号服务'))}));}
function clear(api){api.removeStorageSync(KEY);api.removeStorageSync(sessions.KEY);}
let simulatorPreview=false;
function canPreview(api){try{return api.getSystemInfoSync().platform==='devtools'&&api.getAccountInfoSync().miniProgram.envVersion==='develop';}catch(_){return false;}}
function previewActive(api){return canPreview(api)&&simulatorPreview;}
function enablePreview(api){if(!canPreview(api))return false;simulatorPreview=true;return true;}
// 体验版（trial）与开发版（develop）可生成测试账号；正式版不显示入口，服务端也会按请求来源拒绝。
function canTrial(api){try{return ['trial','develop'].includes(api.getAccountInfoSync().miniProgram.envVersion);}catch(_){return false;}}
function createTrial(api){return new Promise((resolve,reject)=>sessions.send(api,BASE,{url:BASE+'/auth/trial',method:'POST',data:{},timeout:25000,header:{'Content-Type':'application/json'},success:r=>{
 if(r.statusCode!==200||!r.data||!r.data.token)return reject(Error(r.data&&r.data.error||'测试账号生成失败'));
 const {token,expiresAt,...profile}=r.data;
 try{api.setStorageSync(sessions.KEY,{...r.data,base:BASE});api.setStorageSync(sessions.TRIAL_KEY,{userId:profile.userId,phone:profile.trialPhone});}catch(_){}
 const value=decorate(profile);api.setStorageSync(KEY,value);resolve(value);
},fail:e=>reject(Error(e.errMsg||'无法连接账号服务'))}));}
function exitTrial(api){try{api.removeStorageSync(sessions.TRIAL_KEY);}catch(_){}clear(api);}
module.exports={canTrial,createTrial,exitTrial,save:(api,data)=>request(api,'/auth/profile',data),canPreview,previewActive,enablePreview,KEY,AVATARS,cached,decorate,clear,load:api=>request(api,'/auth/me'),bind:(api,code)=>request(api,'/auth/phone',{code})};
