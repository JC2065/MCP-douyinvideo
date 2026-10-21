const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function mainPage(wx){let page;vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:n=>n.endsWith('creator-preferences')?{profile:()=>({})}:n.endsWith('store')?{initial:()=>({role:'个人'})}:n.endsWith('learning')?{cases:[],hotspots:[],hotspotDiscovery:{platforms:[]}}:{},Page:p=>page=p,wx,setTimeout:()=>0});page.data=JSON.parse(JSON.stringify(page.data));page.setData=v=>Object.assign(page.data,v);page.refreshCreativeAssets=()=>{};return page;}
test('切换底部标签回到页面顶部，重复点击当前标签不打断阅读位置',()=>{
 const scrolls=[];const page=mainPage({pageScrollTo:o=>scrolls.push(o)});page.data.tab='灵感';page._pageScrollTop=900;
 page.tab({currentTarget:{dataset:{tab:'创作'}}});assert.equal(page.data.tab,'创作');assert.deepEqual(JSON.parse(JSON.stringify(scrolls)),[{scrollTop:0,duration:0}]);assert.equal(page._pageScrollTop,0);
 page.tab({currentTarget:{dataset:{tab:'创作'}}});assert.equal(scrolls.length,1);
});
test('选题对话请求字段与服务端白名单一致，避免客户端新增字段后服务端整体拒绝',()=>{
 const js=fs.readFileSync('pages/main/index.js','utf8'),py=fs.readFileSync('scripts/topic-chat.py','utf8');
 const call=js.match(/topicChat\.chat\(wx,\{([^}]*)\}\)/);assert.ok(call,'client topic chat call not found');
 const sent=call[1].split(',').map(s=>s.split(':')[0].trim()).sort();
 const allowed=[...py.matchAll(/\{('message'[^}]*)\}/g)].map(m=>m[1].replace(/'/g,'').split(',').map(s=>s.trim()).sort().join(','));
 assert.ok(allowed.includes(sent.join(',')),'client sends '+sent+' but server accepts '+allowed.join(' | '));
});
