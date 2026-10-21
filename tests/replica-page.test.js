const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function load(storage={},responses={}){let page;const calls=[];const store={...storage};
 const wx={getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;},removeStorageSync:k=>{delete store[k];},showModal:o=>o.success({confirm:true}),showToast(){},setClipboardData(o){o.success&&o.success();},
  getFileSystemManager:()=>({readFile:o=>o.success({data:'QUJD'}),unlink(){}}),chooseMedia(o){o.success({tempFiles:[{tempFilePath:'tmp/photo.jpg'}]});},navigateTo(){}};
 const config={baseUrl:'https://api.example.com',send:(api,o)=>{calls.push({url:o.url,method:o.method,data:o.data});const path=o.url.replace('https://api.example.com','');const v=responses[path];o.success({statusCode:200,data:typeof v==='function'?v(o.data):v||{}});}};
 const req=n=>n.includes('video-service')?config:{response:r=>Error(r.data&&r.data.error||'x'),network:()=>Error('net')};
 vm.runInNewContext(fs.readFileSync('pages/replica/index.js','utf8'),{require:req,Page:p=>page=p,wx,setTimeout:()=>0,clearTimeout(){},Number,Math});
 page.data=JSON.parse(JSON.stringify(page.data));page.setData=v=>Object.assign(page.data,v);return {page,calls,store};}
const tick=()=>new Promise(r=>setImmediate(r));
test('replica page sends the user key per request and only remembers it locally when allowed',async()=>{
 const sha='a'.repeat(64);const {page,calls,store}=load({},{'/replica/jobs':d=>d?{id:'b'.repeat(32),status:'running',message:'生成中',estimateYuan:4.96}:{jobs:[]}});
 page.onLoad({sha,seconds:'12'});await tick();
 page.keyInput({detail:{value:'sk-user-key-123456'}});page.choosePhoto();page.consentChange({detail:{value:['1']}});page.submit();await tick();await tick();await tick();
 const create=calls.find(c=>c.url.endsWith('/replica/jobs')&&c.method==='POST');
 assert.equal(create.data.key,'sk-user-key-123456');assert.equal(create.data.provider,'bailian');assert.equal(create.data.reference.asset.sha256,sha);assert.equal(create.data.consent,true);assert.equal(create.data.photo,'QUJD');
 assert.equal(store['youai-replica-key-v1'].key,'sk-user-key-123456');
 page.rememberChange({detail:{value:[]}});assert.equal(store['youai-replica-key-v1'],undefined);
});
test('replica page requires reference, key, photo and consent before any paid call',async()=>{
 const {page,calls}=load();page.onLoad({sha:'bad'});await tick();page.submit();assert.match(page.data.error,/参考视频/);
 page.setData({sha:'c'.repeat(64)});page.submit();assert.match(page.data.error,/Key/);
 page.keyInput({detail:{value:'sk-user-key-123456'}});page.submit();assert.match(page.data.error,/照片/);
 page.choosePhoto();page.submit();assert.match(page.data.error,/授权/);
 assert.ok(!calls.some(c=>c.url.endsWith('/replica/jobs')&&c.method==='POST'));
});
test('replica entry and server wiring stay registered',()=>{
 assert.ok(JSON.parse(fs.readFileSync('app.json','utf8')).pages.includes('pages/replica/index'));
 assert.match(fs.readFileSync('pages/video/index.wxml','utf8'),/bindtap="replicaHint"/);assert.match(fs.readFileSync('utils/board-page.js','utf8'),/this\.openReplica\(\)/);
 assert.match(fs.readFileSync('utils/watch-page.js','utf8'),/pages\/replica\/index\?sha=/);
 const server=fs.readFileSync('scripts/video-server.py','utf8');assert.match(server,/'\/replica\/jobs'/);assert.match(server,/replica-media/);
 assert.match(fs.readFileSync('scripts/wechat-auth.py','utf8'),/replica-media/);
});
