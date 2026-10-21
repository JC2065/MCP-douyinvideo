const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function pageWith(account){let p;const routes=[],toasts=[];const module={exports:{}};const wx={reLaunch:o=>routes.push(o.url),showToast:o=>toasts.push(o)};vm.runInNewContext(fs.readFileSync('utils/account-sheet.js','utf8'),{module,require:()=>account,wx});p=module.exports;p.data={...p.data};p.setData=d=>Object.assign(p.data,d);return{p,routes,toasts};}
test('authorization is required and denied or failed phone binding never enters the app',async()=>{
 let binds=0;const {p,routes}=pageWith({load:async()=>({phoneBound:false}),bind:async()=>{binds++;throw Error('未开通手机号接口');}});
 await p.prepare();assert.equal(p.data.ready,true);assert.equal(p.data.authVisible,false);assert.equal(routes.length,0);
 await p.authorize({detail:{errMsg:'deny'}});assert.equal(binds,0);assert.match(p.data.error,/已取消手机号授权/);
 await p.authorize({detail:{code:'phone-code'}});assert.equal(binds,1);assert.match(p.data.error,/未开通/);assert.equal(routes.length,0);assert.equal(p.data.busy,false);
});
test('微信授权返回具体错误信息，方便定位额度以外的配置故障',async()=>{
 const {p}=pageWith({load:async()=>({phoneBound:false}),bind:async()=>{throw Error('should not bind');}});
 await p.prepare();await p.authorize({detail:{errno:1400001,errMsg:'getPhoneNumber:fail'}});assert.match(p.data.error,/额度已达上限/);assert.match(p.data.error,/付费管理/);
 await p.authorize({detail:{errno:112,errMsg:'getPhoneNumber:fail api scope is not declared in the privacy agreement'}});assert.match(p.data.error,/用户隐私保护指引/);assert.match(p.data.error,/账号注册登录与账号安全/);
 await p.authorize({detail:{errno:40013,errMsg:'getPhoneNumber:fail system error\ninvalid appid'}});assert.match(p.data.error,/微信错误码 40013/);assert.match(p.data.error,/system error invalid appid/);assert.doesNotMatch(p.data.error,/\n/);
 await p.authorize({detail:{errMsg:'getPhoneNumber:fail user deny'}});assert.match(p.data.error,/已取消手机号授权/);
});
test('游客先浏览，只有主动选择登录后才显示手机号授权',async()=>{
 const {p}=pageWith({load:async()=>({phoneBound:false})});assert.equal(p.data.authVisible,false);await p.prepare();assert.equal(p.data.authVisible,false);
 await p.openLogin({currentTarget:{dataset:{message:'登录后同步创作资产'}}});assert.equal(p.data.authVisible,true);assert.equal(p.data.authPrompt,'登录后同步创作资产');p.closeLogin();assert.equal(p.data.authVisible,false);
 const xml=fs.readFileSync('pages/main/index.wxml','utf8');assert.match(xml,/先体验，再决定登录/);assert.match(xml,/手机号快速验证登录/);assert.match(xml,/稍后再说，先逛逛/);
 const app=fs.readFileSync('app.js','utf8');assert.doesNotMatch(app,/account\.load|reLaunch/);
});
test('successful and returning bound accounts enter without asking for avatar or nickname',async()=>{
 const profile={phoneBound:true,nickname:'晴天旅人1234',avatar:2};let code;
 const {p,routes}=pageWith({load:async()=>profile,bind:async(_,c)=>{code=c;return profile;}});
 await p.prepare();assert.equal(p.data.authVisible,false);await p.authorize({detail:{code:'verified-code'}});assert.equal(code,'verified-code');assert.equal(routes.length,0);assert.equal(p.data.authVisible,false);
 const xml=fs.readFileSync('pages/main/index.wxml','utf8');assert.match(xml,/open-type="getPhoneNumber"[^>]*bindgetphonenumber="authorize"/);assert.match(xml,/phone-number-no-quota-toast="\{\{true\}\}"/);assert.match(xml,/手机号快速验证并进入/);assert.doesNotMatch(xml,/phoneAuthorizationTap|chooseAvatar|type="nickname"/);assert.match(xml,/auth-overlay/);
 assert.equal(JSON.parse(fs.readFileSync('app.json')).pages[0],'pages/main/index');
});
test('app startup does not silently create an account session or force phone authorization',()=>{
 let app;vm.runInNewContext(fs.readFileSync('app.js','utf8'),{App:x=>app=x,require:n=>n.endsWith('client-config')?{refresh(){}}:{baseUrl:'https://example.invalid'}});
 assert.equal(typeof app.onShow,'undefined');assert.equal(typeof app.onLaunch,'function');
});

test('preview requires both develop and simulator and never marks an account bound',()=>{
 const account=require('../utils/account');
 const api=(platform,envVersion)=>({getSystemInfoSync:()=>({platform}),getAccountInfoSync:()=>({miniProgram:{envVersion}})});
 for(const platform of ['ios','android','devtools'])for(const env of ['develop','trial','release']){
  const allowed=platform==='devtools'&&env==='develop';assert.equal(account.canPreview(api(platform,env)),allowed);
  if(!allowed)assert.equal(account.enablePreview(api(platform,env)),false);
 }
 assert.equal(account.canPreview({}),false);
 assert.equal(account.enablePreview(api('devtools','develop')),true);
 assert.equal(account.previewActive(api('devtools','develop')),true);
 assert.equal(account.previewActive(api('ios','develop')),false);
 assert.equal(account.cached({getStorageSync:()=>null}),null);
});
test('preview closes sheet and persists during navigation without phone binding',async()=>{
 let active=false;const {p}=pageWith({canPreview:()=>true,previewActive:()=>active,enablePreview:()=>active=true,load:async()=>({phoneBound:false})});
 await p.prepare();assert.equal(p.data.canPreview,true);p.previewLocally();assert.equal(p.data.authVisible,false);
 await p.prepare();assert.equal(p.data.authVisible,false);assert.equal(p.data.profile.phoneBound,false);
});
