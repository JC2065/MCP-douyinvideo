const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const feedback=require('../utils/data-feedback');
test('数据监控：数字缩写、监控和 YOUAI 作品的卡片文案、每日变化表',()=>{
 assert.equal(feedback.fmt(12345),'1.2万');assert.equal(feedback.fmt(30000),'3万');assert.equal(feedback.fmt(999),'999');assert.equal(feedback.fmt(undefined),'—');
 const m=feedback.decorate({id:'a',kind:'monitor',title:'下班做饭',author:'阿禾',link:'l',summary:{day:2,values:{play:52000,likes:300,comments:0},delta:{likes:120,play:0},snapshots:3}});
 assert.equal(m.badge,'对标');assert.equal(m.group,'benchmark');assert.equal(feedback.decorate({id:'m',kind:'monitor',role:'own',link:'l'}).badge,'我的作品');assert.equal(feedback.decorate({id:'m',kind:'monitor',role:'own',link:'l'}).group,'own');assert.equal(m.state,'监控第 2 天 · 已记录 3 次');assert.deepEqual(m.stats.map(s=>[s.label,s.value,s.delta]),[['播放','5.2万',''],['点赞','300','+120'],['评论','0','']]);
 const own=feedback.decorate({id:'b',title:'',link:'',summary:null});assert.equal(own.badge,'有AI作品');assert.equal(own.group,'own');assert.deepEqual(feedback.groups([m,own]).map(g=>[g.id,g.count]),[['own',1],['benchmark',1]]);assert.equal(own.title,'未命名作品');assert.equal(own.state,'待贴回发布链接，开始回传数据');
 assert.equal(feedback.decorate({id:'c',kind:'monitor',link:'l',summary:{day:0,values:{likes:1},delta:{},snapshots:1}}).state,'刚开始监控 · 已记录 1 次');
 const rows=feedback.trend([{day:1,source:'public',values:{play:20000,likes:5}},{day:0,source:'public',values:{play:100}},{day:1,source:'backend',values:{play:1}}]);
 assert.deepEqual(rows.labels,['播放','点赞']);assert.deepEqual(rows.rows.map(r=>r.label),['添加时','第 1 天']);assert.deepEqual(rows.rows[1].cells,['2万','5']);assert.deepEqual(rows.rows[0].cells,['100','—']);
});
test('首页创作区有数据监控和监控入口，在「我的创作」之前；数据页能添加、刷新、移除监控',async()=>{
 const xml=fs.readFileSync('pages/main/index.wxml','utf8');assert.ok(xml.indexOf('数据监控')<xml.indexOf('>我的创作<'));for(const h of ['addMonitor','monitorInput','openFeedback','openFeedbackWork'])assert.ok(xml.includes('"'+h+'"'),h);
 const calls=[],routes=[],sent=[];let def;const wx={navigateTo:o=>routes.push(o.url),showToast(){},showModal(o){o.success({confirm:true});},setClipboardData(){},navigateBack(){}};
 const responses={'/board/monitors':{id:'d'.repeat(32),kind:'monitor',title:'t',metrics:[],summary:null},['/board/works/'+'d'.repeat(32)+'/refresh']:{id:'d'.repeat(32),kind:'monitor',title:'t',link:'l',metrics:[{day:0,source:'public',values:{likes:3}}],summary:{day:0,values:{likes:3},delta:{},snapshots:1}},['/board/works/'+'d'.repeat(32)+'/remove']:{removed:true}};
 vm.runInNewContext(fs.readFileSync('pages/board-work/index.js','utf8'),{Page:p=>def=p,wx,setTimeout:f=>f(),require:n=>n.endsWith('data-feedback')?feedback:n.endsWith('video-service')?{baseUrl:'https://x',send:(api,o)=>{const path=o.url.slice('https://x'.length);calls.push([path,o.method]);sent.push(o);o.success({statusCode:200,data:responses[path]||{rows:[]}});}}:{response:r=>Error('e'),network:()=>Error('n')}});
 const page={...def,data:{...def.data},setData(v){Object.assign(this.data,v);}};
 page.onLoad({tab:'benchmark'});await new Promise(r=>setImmediate(r));assert.equal(page.data.navTitle,'数据面板');assert.equal(page.data.tab,'benchmark');
 page.linkInput({detail:{value:'https://v.douyin.com/abc/'}});await page.addMonitor();assert.equal(routes[0],'/pages/board-work/index?id='+'d'.repeat(32));assert.deepEqual(calls.find(c=>c[0]==='/board/monitors'),['/board/monitors','POST']);assert.equal(sent.find(o=>o.url.endsWith('/board/monitors')).data.role,'benchmark');
 page.data.id='d'.repeat(32);await page.refreshNow();assert.equal(page.data.monitor,true);assert.equal(page.data.benchmark,true);assert.equal(page.data.navTitle,'对标作品');assert.ok(!fs.readFileSync('pages/board-work/index.wxml','utf8').includes('<view class="card"><view class="strong">{{monitor?\'上传'),'对标作品不显示后台截图');assert.equal(page.data.trend.length,1);
 page.removeMonitor();await new Promise(r=>setImmediate(r));assert.ok(calls.some(c=>c[0].endsWith('/remove')));
});
test('数据面板：分组汇总、较上次新增、涨得最快、我的 vs 对标、走势小图',()=>{
 const raw=[{id:'a',kind:'monitor',role:'own',title:'我1',link:'l',summary:{day:1,values:{likes:100,comments:10},delta:{likes:20},snapshots:2},metrics:[{day:0,source:'public',values:{likes:80,comments:10}},{day:1,source:'public',values:{likes:100,comments:10}}]},
  {id:'b',kind:'monitor',title:'对1',link:'l',summary:{day:2,values:{likes:1000,comments:50},delta:{likes:300,comments:5},snapshots:3},metrics:[]},
  {id:'c',title:'没链接',link:'',summary:null,metrics:[]}];
 const rows=raw.map(feedback.decorate);
 assert.deepEqual(rows[0].spark,[8,100]);assert.deepEqual(rows[1].spark,[]);assert.equal(rows[1].gain,305);assert.equal(rows[1].gainText,'+305');
 const own=feedback.panel(rows,'own');assert.equal(own.count,2);assert.equal(own.tracked,1);assert.deepEqual(own.totals.map(t=>[t.label,t.value,t.today]),[['点赞','100','+20'],['评论','10',''],['转发','0',''],['收藏','0','']]);assert.equal(own.gain,'20');assert.deepEqual(own.rising.map(r=>r.id),['a']);
 const cmp=feedback.compare(rows);assert.deepEqual(cmp.lines.map(l=>[l.label,l.own,l.bench,l.ownW,l.benchW]),[['点赞','100','1000',10,100],['评论','10','50',20,100]]);assert.equal(cmp.note,'你的作品平均点赞是对标作品的 10%');
 assert.equal(feedback.compare(rows.filter(r=>r.group==='own')),null,'只有一边有数据时不对比');
 const xml=fs.readFileSync('pages/board-work/index.wxml','utf8');for(const c of ['class="card panel"','涨得最快','我的作品 vs 对标作品','class="spark"'])assert.ok(xml.includes(c),c);
 assert.ok(fs.readFileSync('pages/main/index.wxml','utf8').includes('数据面板 ›'));
});
test('我的创作默认收起，标题行可展开',()=>{const xml=fs.readFileSync('pages/main/index.wxml','utf8'),js=fs.readFileSync('pages/main/index.js','utf8');assert.match(xml,/bindtap="toggleCreative"/);assert.ok(xml.includes('<block wx:if="{{creativeOpen}}"><view wx:if="{{creativeError}}"'));assert.match(js,/creativeOpen:false/);});
