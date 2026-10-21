const test=require('node:test'),assert=require('node:assert/strict');
const auth=require('../utils/video-session');
const fs=require('node:fs'),vm=require('node:vm');
test('手机与模拟器默认使用国内 HTTPS 前缀',()=>{
 for(const platform of ['ios','android','devtools']){
  const context={module:{exports:{}},wx:{getSystemInfoSync:()=>({platform})},require:name=>name==='./service-endpoints'?require('../utils/service-endpoints'):auth};vm.runInNewContext(fs.readFileSync('utils/video-service.js','utf8'),context);
  assert.equal(context.module.exports.baseUrl,'https://youai888.top/youai');
 }
});
function setup(){const calls=[],store={};let logins=0;const wx={getStorageSync:k=>store[k],setStorageSync:(k,v)=>store[k]=v,removeStorageSync:k=>delete store[k],login(o){logins++;o.success({code:'one-use-code'});},request(o){calls.push(o);}};return{wx,calls,store,get logins(){return logins;}};}
test('并行云请求共享登录，会话缓存且请求携带令牌',async()=>{
 const s=setup(),base='https://example.test/youai';let first,second;
 auth.send(s.wx,base,{url:base+'/jobs/a',success:r=>first=r});auth.send(s.wx,base,{url:base+'/jobs/b',success:r=>second=r});
 assert.equal(s.logins,1);assert.equal(s.calls.length,1);
 s.calls[0].success({statusCode:200,data:{token:'test-token',expiresAt:Math.floor(Date.now()/1000)+7200,userId:'user'}});
 await new Promise(r=>setImmediate(r));assert.equal(s.calls.length,3);
 assert.equal(s.calls[1].header.Authorization,'Bearer test-token');assert.equal(s.calls[2].header.Authorization,'Bearer test-token');
 s.calls[1].success({statusCode:200,data:{ok:true}});s.calls[2].success({statusCode:200,data:{ok:true}});assert.ok(first&&second);
});
test('失效会话只重登一次，本机请求不触发微信登录',async()=>{
 const s=setup(),base='https://example.test/youai';s.store[auth.KEY]={base,token:'old-token',expiresAt:Math.floor(Date.now()/1000)+7200};let result;
 auth.send(s.wx,base,{url:base+'/jobs/a',success:r=>result=r});await new Promise(r=>setImmediate(r));s.calls[0].success({statusCode:401});
 assert.equal(s.logins,1);s.calls[1].success({statusCode:200,data:{token:'new-token',expiresAt:Math.floor(Date.now()/1000)+7200}});await new Promise(r=>setImmediate(r));s.calls[2].success({statusCode:401});assert.equal(result.statusCode,401);assert.equal(s.logins,1);
 const local=setup();auth.send(local.wx,'http://127.0.0.1:8765',{url:'http://127.0.0.1:8765/health'});assert.equal(local.logins,0);assert.equal(local.calls.length,1);
});
