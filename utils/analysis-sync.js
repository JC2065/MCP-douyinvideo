const engine=require('./analysis-presets');
const {BASE}=require('./service-endpoints');
const OWNER='youai-analysis-cloud-owner-v1',PREFIX='youai-analysis-cloud-user:',UNLINKED='youai-analysis-cloud-unlinked-v1';
const contexts=new WeakMap(),same=(a,b)=>JSON.stringify(engine.normalize(a))===JSON.stringify(engine.normalize(b));
function read(api,key){try{return api.getStorageSync(key);}catch{return null;}}
function cachedSlot(raw,legacy){const value=raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:null;const result={revision:value&&typeof value.revision==='string'?value.revision:'none',preferences:engine.normalize(value?value.preferences:legacy),dirty:value?value.dirty===true:!!legacy&&!same(legacy,{})};const backup=value&&(value.localBackup||value.legacyBackup||value.cloudBackup);if(backup&&typeof backup==='object')result.localBackup=engine.normalize(backup);return result;}
function request(api,path,data,token){return new Promise((resolve,reject)=>api.request({url:BASE+path,method:data?'POST':'GET',data,timeout:15000,header:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},success:res=>res.statusCode===200?resolve(res.data):reject(Object.assign(Error(res.data&&res.data.error||'模板云同步暂不可用'),{status:res.statusCode})),fail:()=>reject(Error('网络不可用，修改已保存在本机'))}));}
function identity(api){return new Promise((resolve,reject)=>api.login({timeout:10000,success:value=>value.code?resolve(value.code):reject(Error('请重新登录微信后重试')),fail:()=>reject(Error('无法识别微信账号，请联网重试'))})).then(code=>request(api,'/auth/login',{code}));}
function open(api,status=()=>{}){
 const prior=contexts.get(api);if(prior)prior.close();
 const previous=read(api,OWNER),legacy=previous?null:(read(api,UNLINKED)||engine.load(api));
 if(legacy)api.setStorageSync(UNLINKED,legacy);
 const ctx={user:null,token:null,slot:null,ready:false,closed:false,saving:false,again:false,timer:null,conflict:false};contexts.set(api,ctx);
 const active=()=>contexts.get(api)===ctx&&!ctx.closed;
 const notify=(message,conflict=ctx.conflict)=>{if(active())status({message,conflict,ready:ctx.ready,userId:ctx.user,hasBackup:!!(ctx.slot&&(ctx.slot.localBackup||ctx.slot.legacyBackup))});};
 const store=()=>{const current=contexts.get(api);if(current!==ctx&&current&&current.user===ctx.user)return;api.setStorageSync(PREFIX+ctx.user,ctx.slot);};
 const apply=()=>{if(active())engine.save(api,ctx.slot.preferences,false);};
 ctx.close=()=>{clearTimeout(ctx.timer);if(ctx.ready&&ctx.slot.dirty&&!ctx.saving&&!ctx.conflict)ctx.push();ctx.closed=true;if(ctx.detach)ctx.detach();};
 // Until a fresh WeChat identity is established, never expose the last account's cache.
 engine.save(api,{},false);notify('正在识别微信账号并同步模板…');
 ctx.detach=engine.observe(api,value=>{if(!ctx.ready||!ctx.user)return;ctx.slot.preferences=value;ctx.slot.dirty=true;store();notify('修改已保存在本机，等待同步');clearTimeout(ctx.timer);ctx.timer=setTimeout(()=>ctx.push(),400);});
 ctx.push=async()=>{
  if(!ctx.ready||!ctx.user||ctx.closed||!ctx.slot.dirty)return;
  clearTimeout(ctx.timer);ctx.timer=null;
  if(ctx.saving){ctx.again=true;return;}
  if(ctx.conflict){notify('云端已有新版本，请选择保留哪一份');return;}
  ctx.saving=true;const sent=engine.normalize(ctx.slot.preferences),revision=ctx.slot.revision;notify('正在同步到微信账号…');
  try{const remote=await request(api,'/analysis-preferences',{expectedRevision:revision,preferences:sent},ctx.token);ctx.slot.revision=remote.revision;ctx.slot.dirty=!same(sent,ctx.slot.preferences);store();notify(ctx.slot.dirty?'还有本机修改等待同步':'已同步到微信账号');}
  catch(error){ctx.slot.dirty=true;if(error.status===409){
    try{const remote=await request(api,'/analysis-preferences',null,ctx.token);if(remote.preferences&&same(remote.preferences,ctx.slot.preferences)){ctx.slot.revision=remote.revision;ctx.slot.dirty=false;ctx.conflict=false;notify('已同步到微信账号');}else{ctx.conflict=true;notify('云端已有新版本，本机修改已保留');}}catch{ctx.conflict=true;notify('云端版本冲突，请联网后选择保留哪一份');}
   }else notify(error.status===401?'登录已过期，修改已保留，请重新同步':error.message);store();}
  finally{ctx.saving=false;const again=ctx.again||(!ctx.conflict&&ctx.slot.dirty&&ctx.slot.revision!==revision);ctx.again=false;if(again&&active())ctx.timer=setTimeout(()=>ctx.push(),400);}
 };
 ctx.resolve=async choice=>{
  if(!ctx.ready||ctx.saving||ctx.closed)return;
  try{const remote=await request(api,'/analysis-preferences',null,ctx.token);const local=engine.normalize(ctx.slot.preferences);if(choice==='cloud'){ctx.slot.localBackup=local;ctx.slot.preferences=engine.normalize(remote.preferences);ctx.slot.revision=remote.revision;ctx.slot.dirty=false;ctx.conflict=false;store();apply();notify('已使用云端版本，本机修改仍保留在备份');}else{ctx.slot.localBackup=engine.normalize(remote.preferences);ctx.slot.revision=remote.revision;ctx.conflict=false;store();await ctx.push();}}catch(error){notify(error.message);}
 };
 ctx.restore=()=>{const backup=ctx.slot&&(ctx.slot.localBackup||ctx.slot.legacyBackup);if(!backup)return;ctx.slot.localBackup=ctx.slot.preferences;ctx.slot.legacyBackup=null;ctx.slot.preferences=engine.normalize(backup);ctx.slot.dirty=true;store();apply();notify('已恢复本机备份，正在同步');return ctx.push();};
 ctx.promise=(async()=>{
  try{const login=await identity(api);if(!login.userId||!login.token)throw Error('微信登录信息无效');if(!active())return;ctx.user=login.userId;ctx.token=login.token;ctx.slot=cachedSlot(read(api,PREFIX+ctx.user),legacy);store();api.setStorageSync(OWNER,{userId:ctx.user});if(typeof api.removeStorageSync==='function')api.removeStorageSync(UNLINKED);
   try{const remote=await request(api,'/analysis-preferences',null,ctx.token);if(!active())return;
    if(ctx.slot.dirty){if(remote.revision!==ctx.slot.revision&&!same(remote.preferences,ctx.slot.preferences))ctx.conflict=true;else if(remote.preferences&&same(remote.preferences,ctx.slot.preferences)){ctx.slot.revision=remote.revision;ctx.slot.dirty=false;}}
    else if(remote.preferences){if(legacy&&!same(legacy,{})&&!same(legacy,remote.preferences))ctx.slot.legacyBackup=legacy;ctx.slot.preferences=engine.normalize(remote.preferences);ctx.slot.revision=remote.revision;}
    else{ctx.slot.preferences=engine.normalize(legacy||ctx.slot.preferences);ctx.slot.revision=remote.revision;ctx.slot.dirty=true;}
    ctx.ready=true;store();apply();notify(ctx.conflict?'云端已有新版本，本机修改已保留':ctx.slot.dirty?'本机模板等待上传':'已同步到微信账号');if(ctx.slot.dirty&&!ctx.conflict)await ctx.push();
   }catch(error){if(!active())return;ctx.ready=true;ctx.slot.preferences=engine.normalize(ctx.slot.preferences);store();apply();notify(error.message);}
  }catch(error){notify(error.message);}
 })();return ctx;
}
module.exports={BASE,OWNER,PREFIX,open};
