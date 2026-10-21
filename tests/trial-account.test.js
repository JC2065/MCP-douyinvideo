const test=require('node:test');const assert=require('node:assert');const fs=require('fs');
function fresh(){for(const m of ['../utils/account','../utils/video-session','../utils/service-endpoints'])delete require.cache[require.resolve(m)];}
function fakeWx(env,routes){const store={},calls=[];return {store,calls,api:{
 getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;},removeStorageSync:k=>{delete store[k];},
 getSystemInfoSync:()=>({platform:'ios'}),getAccountInfoSync:()=>({miniProgram:{envVersion:env}}),
 login:o=>o.success({code:'wx-code-123'}),
 request:o=>{calls.push(o);const path=o.url.replace(/^https:\/\/youai888\.top\/youai/,'');setTimeout(()=>o.success(routes[path](o)),0);}}};}

test('体验版和开发版才显示体验账号入口，正式版不显示',()=>{fresh();const account=require('../utils/account');
 assert.equal(account.canTrial(fakeWx('trial').api),true);assert.equal(account.canTrial(fakeWx('develop').api),true);assert.equal(account.canTrial(fakeWx('release').api),false);});

test('生成体验账号后保存会话与账号ID，之后的登录携带该ID；服务端不认时自动回到本人账号',async()=>{fresh();const account=require('../utils/account'),session=require('../utils/video-session');
 let next='trial-1111-2222-3333-444444444444';
 const w=fakeWx('trial',{'/auth/login':o=>({statusCode:200,data:{token:'t-'+(o.data.trial||'real'),expiresAt:Date.now()/1000+7200,userId:o.data.trial?next:'real-user'}}),
  '/auth/trial':()=>({statusCode:200,data:{token:'t-trial',expiresAt:Date.now()/1000+7200,userId:'trial-1111-2222-3333-444444444444',trial:true,trialPhone:'10012345678',phoneBound:true,nickname:'体验晴天5678',avatar:1}})});
 const profile=await account.createTrial(w.api);assert.equal(profile.trial,true);assert.equal(profile.trialPhone,'10012345678');
 assert.deepEqual(w.store[session.TRIAL_KEY],{userId:'trial-1111-2222-3333-444444444444',phone:'10012345678'});assert.equal(w.store[session.KEY].token,'t-trial');
 delete w.store[session.KEY];const again=await session.session(w.api,'https://youai888.top/youai');
 assert.equal(again.userId,'trial-1111-2222-3333-444444444444');assert.equal(w.calls.at(-1).data.trial,'trial-1111-2222-3333-444444444444');
 next='real-user';delete w.store[session.KEY];await session.session(w.api,'https://youai888.top/youai');assert.equal(w.store[session.TRIAL_KEY],undefined);
 account.exitTrial(w.api);assert.equal(w.store[session.KEY],undefined);});

test('登录页提供体验账号入口，账号页标出体验版并可退出',()=>{const wxml=fs.readFileSync('pages/main/index.wxml','utf8');
 assert.match(wxml,/wx:if="\{\{canTrial\}\}"[^>]*bindtap="trialLogin"/);assert.match(wxml,/accountProfile\.trial/);assert.match(wxml,/bindtap="exitTrial"/);});
