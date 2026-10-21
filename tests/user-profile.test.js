const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const plain=v=>JSON.parse(JSON.stringify(v));const tick=()=>new Promise(r=>setImmediate(r));
function mainPage(profileApi,toasts){let page;const wx={showToast:o=>toasts.push(o.title),navigateTo(){}};vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:n=>n.endsWith('user-profile')?profileApi:n.endsWith('creator-preferences')?{profile:()=>({})}:n.endsWith('store')?{initial:()=>({role:'个人'})}:n.endsWith('learning')?{cases:[],hotspots:[],hotspotDiscovery:{platforms:[]}}:{},Page:p=>page=p,wx,setTimeout:()=>0});page.data=plain(page.data);page.setData=v=>{for(const [k,val] of Object.entries(v)){const path=k.replace(/\[(\d+)\]/g,'.$1').split('.');let o=page.data;for(const part of path.slice(0,-1))o=o[part];o[path.at(-1)]=val;}};page.videoStudio=()=>{};return page;}
const topics=[{title:'减脂早餐',angle:'十分钟搞定'},{title:'城市夜骑',angle:'周末路线'}];
test('选题“喜欢/不想要”：游客引导登录；登录后记录一次并即时标记，失败回退',async()=>{
 const calls=[],toasts=[];const api={signal:async(wx,kind,topic)=>{calls.push([kind,plain(topic)]);return {recorded:true};}};
 const page=mainPage(api,toasts);let login=null;page.openLogin=e=>login=e.currentTarget.dataset.message;page.data.topicMessages=[{role:'assistant',text:'hi',topics:plain(topics)}];
 const tap=kind=>page.topicFeedback({currentTarget:{dataset:{kind,title:'减脂早餐',angle:'十分钟搞定',msg:'0'}}});
 tap('up');assert.match(login,/登录/);assert.equal(calls.length,0);
 page.data.accountProfile={phoneBound:true};tap('up');await tick();
 assert.deepEqual(calls,[['up',{title:'减脂早餐',angle:'十分钟搞定'}]]);assert.equal(page.data.topicMessages[0].topics[0].feedback,'up');assert.match(toasts.at(-1),/多推荐/);
 tap('down');await tick();assert.equal(calls.length,1,'one feedback per topic');
 api.signal=async()=>{throw Error('暂时无法连接，请稍后重试');};page.topicFeedback({currentTarget:{dataset:{kind:'down',title:'城市夜骑',angle:'周末路线',msg:'0'}}});await tick();await tick();
 assert.equal(page.data.topicMessages[0].topics[1].feedback,'');assert.match(toasts.at(-1),/无法连接/);
});
test('采纳选题会记录为采纳信号（仅登录用户）',async()=>{
 const calls=[];const page=mainPage({signal:async(wx,kind,t)=>{calls.push([kind,t.title]);return {};}},[]);
 page.topicCreate({currentTarget:{dataset:{title:'城市夜骑',angle:'周末路线'}}});assert.equal(calls.length,0);
 page.data.accountProfile={phoneBound:true};page.topicCreate({currentTarget:{dataset:{title:'城市夜骑',angle:'周末路线'}}});await tick();
 assert.deepEqual(calls,[['adopt','城市夜骑']]);assert.equal(page.data.input,'城市夜骑。周末路线');
});
test('偏好页“TA 的了解”：查看、关闭、删除、清空都走服务端，游客只看到登录提示',async()=>{
 const calls=[];let cached=null;let page;const view={enabled:true,serviceEnabled:true,minEvidence:3,items:[{facet:'interest',facetName:'感兴趣的方向',value:'早餐',evidence:3}],notice:'n'};
 const api={view:async()=>{calls.push('view');return view;},setEnabled:async(wx,v)=>{calls.push(['enabled',v]);return {...view,enabled:v};},remove:async(wx,f,v)=>{calls.push(['remove',f,v]);return {...view,items:[]};},clear:async()=>{calls.push('clear');return {...view,items:[]};}};
 const wx={showModal:o=>o.success({confirm:true})};
 vm.runInNewContext(fs.readFileSync('pages/preferences/index.js','utf8'),{require:n=>n.endsWith('user-profile')?api:n.endsWith('account')?{cached:()=>cached}:{options:{},boundaries:{platforms:[]},load:()=>({profiles:[{id:'a',keywords:[]}],active:'a'})},Page:p=>page=p,wx});
 page.data=plain(page.data);page.setData=v=>Object.assign(page.data,v);
 assert.ok(page.data.sections.some(s=>s.id==='memory'));
 page.section({currentTarget:{dataset:{id:'memory'}}});await tick();assert.equal(page.data.memoryLogged,false);assert.equal(calls.length,0);
 cached={phoneBound:true};page.section({currentTarget:{dataset:{id:'memory'}}});await tick();assert.equal(page.data.memory.items.length,1);
 await page.memoryToggle({detail:{value:false}});assert.equal(page.data.memory.enabled,false);
 page.memoryRemove({currentTarget:{dataset:{facet:'interest',value:'早餐'}}});await tick();await tick();
 page.memoryClear();await tick();await tick();
 assert.deepEqual(plain(calls),['view',['enabled',false],['remove','interest','早餐'],'clear']);
 const wxml=fs.readFileSync('pages/preferences/index.wxml','utf8');for(const name of ['memoryToggle','memoryRemove','memoryClear'])assert.ok(wxml.includes(name));
 assert.ok(fs.readFileSync('pages/main/index.wxml','utf8').includes('bindtap="topicFeedback"'));
});
test('个性化参数在中台可配置；画像与模型连接无关',()=>{
 const html=fs.readFileSync('scripts/admin-console.html','utf8');assert.match(html,/renderPersonalization/);for(const k of ['minEvidence','halfLifeDays','maxProfileChars','historyTurns','creationRecords','exploreCount'])assert.ok(html.includes("'"+k+"'"),k);
 const server=fs.readFileSync('scripts/video-server.py','utf8');assert.match(server,/profile=PROFILES\.text\(self\.user_id\)/);
 const docker=fs.readFileSync('scripts/Dockerfile.video','utf8');assert.ok(docker.includes('scripts/user-profile.py'));
});
