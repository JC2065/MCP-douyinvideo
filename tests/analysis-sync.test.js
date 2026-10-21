const test=require('node:test'),assert=require('node:assert/strict');
const engine=require('../utils/analysis-presets'),sync=require('../utils/analysis-sync');
const clone=value=>JSON.parse(JSON.stringify(value));
function fixture(){const server={users:{},counter:0,failWrite:false,failLogin:false,hold:false,held:[]};
 function device(user,cache={}){const api={user,cache,getStorageSync:key=>cache[key],setStorageSync:(key,value)=>cache[key]=clone(value),removeStorageSync:key=>delete cache[key],login(o){const user=api.user;queueMicrotask(()=>server.failLogin?o.fail():o.success({code:user}));},request(o){queueMicrotask(()=>{const path=new URL(o.url).pathname.replace('/youai','');if(path==='/auth/login')return o.success({statusCode:200,data:{userId:o.data.code,token:'token-'+o.data.code}});const user=o.header.Authorization?.slice(13);if(!user)return o.success({statusCode:401,data:{error:'登录过期'}});const current=server.users[user]||{revision:'none',preferences:null};if(o.method==='POST'){if(server.failWrite)return o.fail();if(o.data.expectedRevision!==current.revision)return o.success({statusCode:409,data:{error:'版本冲突'}});const value={revision:'r'+(++server.counter),preferences:clone(o.data.preferences)};server.users[user]=value;return o.success({statusCode:200,data:clone(value)});}const deliver=()=>o.success({statusCode:200,data:clone(current)});if(server.hold)server.held.push(deliver);else deliver();});},showModal(o){o.success({confirm:true});},showToast(){}};return api;}
 return{server,device};}
function prefs(name){const row=engine.templates.clone(engine.presets[0],'voice',engine.labels);row.name=name;return engine.normalize({customTemplates:[row],typeDefaults:{voice:row.id},typeGoals:{voice:['structure','visual']}});}
test('local templates migrate to account and a second device restores saved defaults/goals',async()=>{
 const {server,device}=fixture(),a=device('alice');engine.save(a,prefs('我的模板'));const first=sync.open(a);await first.promise;assert.equal(first.slot.dirty,false);assert.equal(server.users.alice.preferences.customTemplates[0].name,'我的模板');first.close();
 const b=device('alice'),second=sync.open(b);await second.promise;assert.equal(engine.load(b).customTemplates[0].name,'我的模板');assert.deepEqual(engine.load(b).typeGoals.voice,['structure','visual']);second.close();
});
test('switching account clears old visible data and keeps the old account private cache',async()=>{
 const {server,device}=fixture(),api=device('alice');engine.save(api,prefs('Alice私有'));let ctx=sync.open(api);await ctx.promise;ctx.close();server.users.bob={revision:'b1',preferences:prefs('Bob私有')};api.user='bob';ctx=sync.open(api);assert.equal(engine.load(api).customTemplates.length,0);await ctx.promise;assert.equal(engine.load(api).customTemplates[0].name,'Bob私有');assert.equal(api.cache[sync.PREFIX+'alice'].preferences.customTemplates[0].name,'Alice私有');ctx.close();
});
test('failed upload remains dirty locally and is recovered after reopen',async()=>{
 const {server,device}=fixture(),api=device('alice');let ctx=sync.open(api);await ctx.promise;server.failWrite=true;engine.save(api,prefs('离线修改'));await ctx.push();assert.equal(ctx.slot.dirty,true);assert.equal(api.cache[sync.PREFIX+'alice'].preferences.customTemplates[0].name,'离线修改');ctx.close();server.failWrite=false;ctx=sync.open(api);await ctx.promise;assert.equal(server.users.alice.preferences.customTemplates[0].name,'离线修改');ctx.close();
});
test('concurrent device writes conflict instead of overwriting, and cloud choice keeps local backup',async()=>{
 const {server,device}=fixture(),a=device('alice'),b=device('alice');const ca=sync.open(a);await ca.promise;const cb=sync.open(b);await cb.promise;engine.save(a,prefs('设备A'));await ca.push();engine.save(b,prefs('设备B'));await cb.push();assert.equal(cb.conflict,true);assert.equal(server.users.alice.preferences.customTemplates[0].name,'设备A');assert.equal(engine.load(b).customTemplates[0].name,'设备B');await cb.resolve('cloud');assert.equal(engine.load(b).customTemplates[0].name,'设备A');assert.equal(cb.slot.localBackup.customTemplates[0].name,'设备B');ca.close();cb.close();
});
test('explicit local choice uses latest revision, preserving cloud backup',async()=>{
 const {server,device}=fixture(),api=device('alice'),ctx=sync.open(api);await ctx.promise;server.users.alice={revision:'external',preferences:prefs('云端旧版')};engine.save(api,prefs('本机保留'));await ctx.push();assert.equal(ctx.conflict,true);await ctx.resolve('local');assert.equal(server.users.alice.preferences.customTemplates[0].name,'本机保留');assert.equal(ctx.slot.localBackup.customTemplates[0].name,'云端旧版');ctx.close();
});
test('late response from previous account cannot replace the current account',async()=>{
 const {server,device}=fixture(),api=device('alice');server.users.alice={revision:'a1',preferences:prefs('Alice')};server.users.bob={revision:'b1',preferences:prefs('Bob')};server.hold=true;const old=sync.open(api);await new Promise(resolve=>setImmediate(resolve));assert.equal(server.held.length,1);api.user='bob';server.hold=false;const current=sync.open(api);await current.promise;server.held[0]();await old.promise;assert.equal(engine.load(api).customTemplates[0].name,'Bob');current.close();
});
test('identity failure preserves unlinked legacy templates for later migration',async()=>{
 const {server,device}=fixture(),api=device('alice');engine.save(api,prefs('未联网旧模板'));server.failLogin=true;let ctx=sync.open(api);await ctx.promise;assert.equal(ctx.ready,false);assert.equal(engine.load(api).customTemplates.length,0);ctx.close();server.failLogin=false;ctx=sync.open(api);await ctx.promise;assert.equal(server.users.alice.preferences.customTemplates[0].name,'未联网旧模板');ctx.close();
});
test('leaving the page flushes the last edit without losing its local copy',async()=>{
 const {server,device}=fixture(),api=device('alice'),ctx=sync.open(api);await ctx.promise;engine.save(api,prefs('离开前保存'));ctx.close();await new Promise(resolve=>setImmediate(resolve));assert.equal(server.users.alice.preferences.customTemplates[0].name,'离开前保存');assert.equal(api.cache[sync.PREFIX+'alice'].dirty,false);
});
test('damaged local cache reloads cloud data instead of pretending to sync empty preferences',async()=>{
 const {server,device}=fixture(),api=device('alice',{[sync.PREFIX+'alice']:'bad-cache'});server.users.alice={revision:'a1',preferences:prefs('云端恢复')};const ctx=sync.open(api);await ctx.promise;assert.equal(engine.load(api).customTemplates[0].name,'云端恢复');ctx.close();
});
test('a backup can be restored as a new cloud version',async()=>{
 const {server,device}=fixture(),api=device('alice'),ctx=sync.open(api);await ctx.promise;server.users.alice={revision:'external',preferences:prefs('云端备份')};engine.save(api,prefs('本机版本'));await ctx.push();await ctx.resolve('local');await ctx.restore();assert.equal(server.users.alice.preferences.customTemplates[0].name,'云端备份');assert.equal(ctx.slot.localBackup.customTemplates[0].name,'本机版本');ctx.close();
});
