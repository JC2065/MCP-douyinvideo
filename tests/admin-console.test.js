const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('native management entry and independent in-memory sessions',async()=>{
 const api=require('../utils/admin-client');const calls=[];const wx={request(options){calls.push(options);options.success({statusCode:200,data:options.url.endsWith('/login')?{token:'admin-token'}:{tasks:[]}});}};
 api.clear();await api.request(wx,'overview');assert.equal(calls[0].header.Authorization,undefined);
 await api.login(wx,'admin','not-real-secret');await api.request(wx,'overview');assert.equal(calls[2].header.Authorization,'Bearer admin-token');assert.ok(calls[2].url.startsWith('https://youai888.top/youai/admin-api/'));
 api.clear();await api.request(wx,'overview');assert.equal(calls[3].header.Authorization,undefined);
 assert.ok(JSON.parse(fs.readFileSync('app.json')).pages.includes('pages/admin/index'));
 assert.match(fs.readFileSync('pages/main/index.wxml','utf8'),/bindtap="adminConsole"/);
 assert.match(fs.readFileSync('pages/main/index.js','utf8'),/navigateTo\(\{url:'\/pages\/admin\/index'/);
});
test('expired operator session and transport failures give actionable errors',async()=>{
 const api=require('../utils/admin-client');await assert.rejects(api.request({request(o){o.success({statusCode:401,data:{error:'请登录管理中台'}});}},'config'),/请登录/);
 await assert.rejects(api.request({request(o){o.fail();}},'config'),/无法连接/);
});
test('native publishes previewed changes, confirms rollback, clears sessions on unload',async()=>{
 let page;const requests=[];const tools=Object.fromEntries(['download','transcript','audio','eraser','cover'].map(key=>[key,{maintenance:false}]));
 const api={clear(){requests.push('clear');},async request(wx,path,data){requests.push({path,data});return path==='overview'?{config:{revision:'v1',tools},sources:{},tasks:[],taskScope:'scope'}:{status:'pending',topicId:'douyin-abc'};}};
 const wx={showModal(o){o.success({confirm:true});},showToast(){}};
 vm.runInNewContext(fs.readFileSync('pages/admin/index.js','utf8'),{require:()=>api,Page:p=>page=p,wx,Date});page.data=JSON.parse(JSON.stringify(page.data));page.setData=value=>Object.assign(page.data,value);
 await page.load();page.toggle({currentTarget:{dataset:{key:'audio'}},detail:{value:true}});assert.deepEqual(Array.from(page.data.diff),['音频提取：暂停']);
 page.publish();await new Promise(resolve=>setImmediate(resolve));assert.equal(requests.find(r=>r.path==='config').data.expectedRevision,'v1');assert.equal(requests.find(r=>r.path==='config').data.tools.audio.maintenance,true);
 page.setData({selected:{topicId:'douyin-abc'}});await page.retry();assert.equal(requests.at(-1).path,'topics/douyin-abc');page.onUnload();assert.equal(requests.at(-1),'clear');
});
test('admin web renders untrusted source content as text and never persists bearer tokens',()=>{
 const html=fs.readFileSync('scripts/admin-console.html','utf8');assert.ok(html.includes('textContent'));assert.ok(!html.includes('innerHTML'));assert.ok(!html.includes('localStorage'));assert.ok(html.includes("credentials:'omit'"));
 const py=fs.readFileSync('scripts/video-server.py','utf8');assert.ok(py.indexOf('if ADMIN.handle(self):return',py.indexOf('def do_POST'))<py.indexOf('if not self.guard():return',py.indexOf('def do_POST')));
});
