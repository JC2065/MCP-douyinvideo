const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
function fresh(){for(const m of ['../utils/idea-box','../utils/video-session','../utils/video-service','../utils/service-endpoints','../utils/client-config'])delete require.cache[require.resolve(m)];}
function fakeWx(routes){const store={'youai.video.session.v1':{token:'tok',expiresAt:Date.now()/1000+3600,base:'https://youai888.top/youai'}},calls=[];return {calls,store,api:{
 getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;},removeStorageSync:k=>{delete store[k];},getSystemInfoSync:()=>({platform:'ios'}),
 request:o=>{calls.push(o);const path=o.url.replace('https://youai888.top/youai','');setTimeout(()=>o.success(routes[path]?routes[path](o):{statusCode:404,data:{error:'x'}}),0);},
 uploadFile:o=>{calls.push(o);setTimeout(()=>o.success({statusCode:200,data:JSON.stringify({id:'a'.repeat(32),kind:'voice',text:'语音文字'})}),0);}}};}
test('碎片箱客户端：文字、同步、列表、状态、删除与上传都带登录凭证',async()=>{fresh();const box=require('../utils/idea-box');
 const w=fakeWx({'/ideas':o=>({statusCode:200,data:o.method==='GET'?{rows:[],counts:{new:2}}:{id:'b'.repeat(32),kind:'link'}}),'/ideas?status=new':()=>({statusCode:200,data:{counts:{new:3}}}),'/ideas/sync':o=>({statusCode:200,data:{saved:o.data.items.length}}),['/ideas/'+'c'.repeat(32)+'/status']:o=>({statusCode:200,data:{status:o.data.status}}),['/ideas/'+'c'.repeat(32)+'/delete']:()=>({statusCode:200,data:{deleted:'c'.repeat(32)}})});
 assert.equal((await box.add(w.api,'看 https://v.douyin.com/x/','l1',1)).kind,'link');assert.equal(w.calls[0].header.Authorization,'Bearer tok');
 assert.equal((await box.list(w.api,'new')).counts.new,3);assert.equal((await box.sync(w.api,[{text:'a'},{text:'b'}])).saved,2);
 assert.equal((await box.setStatus(w.api,'c'.repeat(32),'used')).status,'used');assert.equal((await box.remove(w.api,'c'.repeat(32))).deleted,'c'.repeat(32));
 const voice=await box.upload(w.api,'voice','/tmp/a.mp3','l2');assert.equal(voice.text,'语音文字');const up=w.calls.at(-1);assert.match(up.url,/\/ideas\/media\?kind=voice&clientId=l2$/);assert.equal(up.header.Authorization,'Bearer tok');
 assert.match(box.clientId(),/^l[a-z0-9]{6,}$/);});
test('首页把碎片交给 TA：从碎片箱返回后带 fragmentId 发起对话，选题卡显示碎片来源，采用后标为已用',()=>{
 const js=fs.readFileSync('pages/main/index.js','utf8'),xml=fs.readFileSync('pages/main/index.wxml','utf8'),box=fs.readFileSync('pages/idea-box/index.js','utf8');
 assert.match(box,/setStorageSync\(ideaBox\.FOCUS_KEY,\{id:row\.id,text:row\.text\}\)/);assert.match(js,/if\(!this\.consumeTopicFocus\(\)\)this\.topicRequest\('',true\)/);
 assert.match(js,/fragmentId:focus/);assert.match(js,/ideaBox\.setStatus\(wx,item\.fragment,'used'\)/);assert.match(xml,/topic\.fragmentText/);assert.match(xml,/data-fragment="\{\{topic\.fragmentId\}\}"/);
 assert.match(js,/this\.syncIdeas\(\)/);assert.ok(!xml.includes("'登录后聊天'"));
 const app=JSON.parse(fs.readFileSync('app.json','utf8'));assert.ok(app.pages.includes('pages/idea-box/index'));});
test('碎片箱截图用服务地址加载签名链接，而不是本地页面路径',()=>{const js=fs.readFileSync('pages/idea-box/index.js','utf8');assert.match(js,/require\('..\/..\/utils\/service-endpoints'\)/);assert.match(js,/image:row\.image&&row\.image\.startsWith\('\/'\)\?BASE\+row\.image/);});
