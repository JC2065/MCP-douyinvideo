const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('native AI configuration publishes exact scene fields with revision and confirms probes',async()=>{
 let page;const calls=[],ids=['ta_opening','ta_chat','hotspot_summary'];const scenes=Object.fromEntries(ids.map(id=>[id,{enabled:true,connection:'qwen-domestic',model:'baseline',timeoutSeconds:35,maxTokens:900,instruction:''}]));
 const api={async request(wx,path,data){calls.push({path,data});if(path==='overview')return {config:{revision:'tools',tools:Object.fromEntries(['download','transcript','audio','eraser','cover'].map(k=>[k,{maintenance:false}]))},sources:{},tasks:[]};if(path==='inspiration-ai')return {revision:'ai-revision',scenes,rows:ids.map(id=>({id,name:id,config:scenes[id]})),connections:[],versions:[],notice:'safe'};return {rows:[]};}};
 const wx={showModal(o){o.success({confirm:true});},showToast(){}};vm.runInNewContext(fs.readFileSync('pages/admin/index.js','utf8'),{require:()=>api,Page:p=>page=p,wx,Date});page.data=JSON.parse(JSON.stringify(page.data));page.setData=v=>Object.assign(page.data,v);page.data.section='热点推荐';await page.load();assert.equal(page.data.aiRows.length,3);
 page.aiField({currentTarget:{dataset:{id:'ta_chat',key:'maxTokens'}},detail:{value:'120'}});page.aiPublish();await new Promise(r=>setImmediate(r));const publish=calls.find(c=>c.path==='inspiration-ai'&&c.data);assert.equal(publish.data.expectedRevision,'ai-revision');assert.equal(publish.data.scenes.ta_chat.maxTokens,120);assert.deepEqual(Object.keys(publish.data.scenes.ta_chat).sort(),['connection','enabled','instruction','maxTokens','model','timeoutSeconds']);
 page.aiProbe({currentTarget:{dataset:{id:'ta_opening'}}});await new Promise(r=>setImmediate(r));assert.equal(calls.find(c=>c.path==='inspiration-ai/probe').data.scene,'ta_opening');
});
test('probe timeout allows configured model deadline and web script parses safely',async()=>{
 const api=require('../utils/admin-client');let timeout;await api.request({request(o){timeout=o.timeout;o.success({statusCode:200,data:{}});}},'inspiration-ai/probe',{});assert.equal(timeout,50000);
 const html=fs.readFileSync('scripts/admin-console.html','utf8');new vm.Script(html.match(/<script>([\s\S]*?)<\/script>/)[1]);assert.match(html,/recentCalls/);assert.match(html,/ai-status-grid/);assert.ok(!html.includes('localStorage'));
 const wxml=fs.readFileSync('pages/admin/index.wxml','utf8');for(const name of ['aiField','aiPublish','aiProbe','aiRollback'])assert.ok(wxml.includes(name));
});
