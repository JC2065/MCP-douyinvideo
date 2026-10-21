const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');

function nativePage(responses,requests){
 let page;const api={clear(){requests.push('clear');},async request(wx,path,data){requests.push({path,data});const value=responses[path];if(value instanceof Error)throw value;return typeof value==='function'?value(data):value;}};
 const wx={showModal(o){o.success&&o.success({confirm:true});},showToast(){}};
 vm.runInNewContext(fs.readFileSync('pages/admin/index.js','utf8'),{require:()=>api,Page:p=>page=p,wx,Date});
 page.data=JSON.parse(JSON.stringify(page.data));page.setData=value=>Object.assign(page.data,value);return page;
}
const tools=Object.fromEntries(['download','transcript','audio','eraser','cover'].map(key=>[key,{maintenance:false}]));
const overview={config:{revision:'tools',tools},sources:{},tasks:[]};
const tick=()=>new Promise(resolve=>setImmediate(resolve));

test('native model board writes secrets once and never keeps them in page data',async()=>{
 const requests=[];const platform={notice:'只写不读',connections:[{id:'qwen-domestic',name:'国内千问',kind:'chat',endpoint:'https://q.example.com/v1',credential:{configured:true,source:'凭据文件',last4:'1234'}},{id:'wan-video',name:'Wan',kind:'video',endpoint:'https://w.example.com',credential:{configured:false,source:'',last4:''}}]};
 const page=nativePage({overview,platform,'platform/secret':{},'platform/probe':{ok:true,message:'连接检测成功'}},requests);
 page.data.section='模型与密钥';await page.load();
 assert.deepEqual(page.data.platformConnections.map(c=>c.credText),['密钥已配置 · 凭据文件 · 末4位 1234','密钥未配置']);
 page.secretInput({currentTarget:{dataset:{id:'wan-video'}},detail:{value:'wan-secret-value-9'}});
 assert.ok(!JSON.stringify(page.data).includes('wan-secret-value-9'));
 page.saveSecret({currentTarget:{dataset:{id:'wan-video',name:'Wan'}}});await tick();await tick();
 const write=requests.find(r=>r.path==='platform/secret');assert.deepEqual(JSON.parse(JSON.stringify(write.data)),{ref:'wan-video',value:'wan-secret-value-9'});
 assert.ok(!JSON.stringify(page.secrets).includes('wan-secret-value-9'));
 page.connectionProbe({currentTarget:{dataset:{id:'qwen-domestic'}}});await tick();await tick();
 assert.equal(requests.find(r=>r.path==='platform/probe').data.connection,'qwen-domestic');
 page.onUnload();assert.equal(requests.at(-1),'clear');
});

test('native flow board publishes drafts with revision and can return to defaults',async()=>{
 const requests=[];const flow={stage:'production',name:'作品产出',revision:'rev-1',published:{version:'production-abcdefabcdef',steps:[{id:'brief',title:'读取',required:true}]},draft:{steps:[]},diff:['调整顺序'],errors:[]};
 const page=nativePage({overview,workflows:{notice:'n',workflows:[flow]},'workflows/production/publish':{},'workflows/production/rollback':{},'workflows/production/draft':{}},requests);
 page.data.section='流程';await page.load();assert.equal(page.data.flows[0].name,'作品产出');
 page.flowPublish({currentTarget:{dataset:{stage:'production'}}});await tick();await tick();
 assert.deepEqual(JSON.parse(JSON.stringify(requests.find(r=>r.path==='workflows/production/publish').data)),{expectedRevision:'rev-1'});
 page.flowReset({currentTarget:{dataset:{stage:'production'}}});await tick();await tick();
 assert.deepEqual(JSON.parse(JSON.stringify(requests.find(r=>r.path==='workflows/production/rollback').data)),{expectedRevision:'rev-1',version:'default-v1'});
 const wxml=fs.readFileSync('pages/admin/index.wxml','utf8');for(const name of ['saveSecret','secretInput','connectionProbe','flowPublish','flowDiscard','flowReset','aiConnection'])assert.ok(wxml.includes(name),name);
 assert.match(wxml,/<input password value=""/);
});

test('native AI scene can switch to a registered connection',async()=>{
 const requests=[];const scenes={text_works:{enabled:true,connection:'qwen-domestic',model:'m',timeoutSeconds:40,maxTokens:1800,instruction:''}};
 const ai={revision:'ai-1',scenes,rows:[{id:'text_works',name:'文字作品生成',config:scenes.text_works}],connections:[{id:'qwen-domestic',name:'千问'},{id:'deepseek',name:'DeepSeek'}],versions:[],notice:''};
 const page=nativePage({overview,'inspiration-ai':ai,hotspots:{rows:[]}},requests);page.data.section='热点推荐';await page.load();
 page.aiConnection({currentTarget:{dataset:{id:'text_works'}},detail:{value:'1'}});page.aiPublish();await tick();await tick();
 assert.equal(requests.find(r=>r.path==='inspiration-ai'&&r.data).data.scenes.text_works.connection,'deepseek');
});

test('web console exposes six boards, write-only secrets and safe rendering',()=>{
 const html=fs.readFileSync('scripts/admin-console.html','utf8');new vm.Script(html.match(/<script>([\s\S]*?)<\/script>/)[1]);
 for(const label of ['热点推荐','创作工具','数据积累','确认需求','作品拆解','作品产出','模型与密钥'])assert.ok(html.includes("'"+label+"'"),label);
 assert.ok(html.includes("type='password'")||html.includes("key.type='password'"));assert.ok(!html.includes('innerHTML'));assert.ok(!html.includes('localStorage'));
 assert.match(html,/platform\/secret/);assert.match(html,/image:image\|\|platform\.image/);assert.match(html,/图片生成（图文作品）/);assert.match(html,/workflows\/'\+stage\+'\/publish/);
});

test('video image ships every module the server loads and probes get a long timeout',async()=>{
 const server=fs.readFileSync('scripts/video-server.py','utf8'),docker=fs.readFileSync('scripts/Dockerfile.video','utf8');
 const modules=[...new Set([...server.matchAll(/with_name\('([a-z-]+\.py)'\)/g)].map(m=>m[1]))];assert.ok(modules.includes('platform-config.py'));
 for(const name of modules)assert.ok(docker.includes('scripts/'+name),name+' missing from Dockerfile.video');
 // content-boundaries.py reads ../utils/platform-boundaries.json at import time; without it the server crashes on start.
 assert.ok(docker.includes('utils/platform-boundaries.json'));assert.match(fs.readFileSync('scripts/check-image-modules.py','utf8'),/exec_module/);
 const api=require('../utils/admin-client');let timeout;await api.request({request(o){timeout=o.timeout;o.success({statusCode:200,data:{}});}},'platform/probe',{});assert.equal(timeout,50000);
});
