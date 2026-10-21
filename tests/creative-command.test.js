const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
const commands=require('../utils/creative-command');const learning=require('../utils/learning');const store=require('../utils/store');
const event=dataset=>({currentTarget:{dataset}});
test('口令跨人复制后保持方法，替换全部主题，不执行文本',()=>{
 const c={version:1,name:'对比法',idea:'先展示差异，再解释原因',template:'{{主题}}：先看结果；再看{{主题}}的过程。<script>test</script>'};
 const parsed=commands.decode(commands.encode(c));assert.deepEqual(parsed,c);assert.equal(commands.render(parsed,'面包'),'面包：先看结果；再看面包的过程。<script>test</script>');
 for(const c of learning.cases)assert.ok(commands.render(commands.decode(commands.encode(commands.fromCase(c))),'新主题').includes(c.method));
});
test('损坏、未知版本、超限、缺少字段及空主题均被拒绝',()=>{
 for(const value of ['',null,'YOUAI1:%xx','YOUAI1:%7B','YOUAI1:'+encodeURIComponent(JSON.stringify({version:2})), 'x'.repeat(100001)])assert.throws(()=>commands.decode(value));
 assert.throws(()=>commands.encode({version:1,name:'a',idea:'b',template:'没有主题占位符'}));
 const c=commands.fromCase(learning.cases[0]);assert.throws(()=>commands.render(c,' '));assert.throws(()=>commands.render(c,'a'.repeat(101)));
 assert.throws(()=>commands.encode({...c,template:'{{主题}}'+'x'.repeat(8000)}));
 const poisoned=JSON.parse(JSON.stringify(c));poisoned.sourceUrl='https://example.com';assert.equal(commands.decode(commands.encode(poisoned)).sourceUrl,undefined);
});
test('口令入口 → 草稿 → 保存 → 重开改主题 → 导出复用，直接创作不串入旧口令',()=>{
 let p,saved,clipboard;const local={...store,save:s=>{saved=JSON.parse(JSON.stringify(s));}};
 vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:n=>n.endsWith('/creator-preferences')?require('../utils/creator-preferences'):n.endsWith('/daily-pick')?require('../utils/daily-pick'):n.endsWith('/day-feed')?require('../utils/day-feed'):n.endsWith('/idea-calendar')?require('../utils/idea-calendar'):n.endsWith('/analysis-presets')?require('../utils/analysis-presets'):n.endsWith('/local-cases')?require('../utils/local-cases'):n.endsWith('/case87')?require('../utils/case87'):n.endsWith('/video-cases')?require('../utils/video-cases'):n.endsWith('/creative-command')?commands:n.endsWith('/learning')?learning:local,Page:x=>{p=x;},wx:{showToast(){},setClipboardData:o=>{clipboard=o.data;o.success();}}});p.setData=function(x){Object.assign(this.data,x);};
 p.commandEntry();p.commandExample(event({id:2}));p.data.commandTheme='产品布光';p.useCommand();assert.equal(p.data.source.type,'创作口令');assert.ok(p.data.draft.includes('产品布光'));assert.equal(p.data.workId,null);
 p.saveWork(event({}));const id=saved.works[0].id;assert.equal(saved.works[0].status,'草稿');assert.ok(saved.works[0].commandTemplate);
 p.editor(event({id}));p.data.title='饰品拍摄';p.generate();assert.ok(p.data.draft.includes('饰品拍摄'));assert.ok(!p.data.draft.includes('产品布光'));p.saveWork(event({complete:true}));
 p.copyCommand(event({work:id}));assert.ok(commands.render(commands.decode(clipboard),'书本拍摄').includes('书本拍摄'));
 p.editor(event({}));assert.equal(p.data.commandTemplate,null);p.inspire(event({id:1}));assert.equal(p.data.commandTemplate,null);
 p.commandEntry();p.data.commandInput='broken';p.parseCommand();assert.equal(p.data.commandPreview,null);p.useCommand();assert.equal(p.data.view,'command');
});
test('三条指定素材保留独立来源与证据限制，生成口令只复用方法',()=>{
 const videos=require('../utils/video-cases');assert.equal(videos.length,3);
 assert.deepEqual(videos.map(v=>v.id),[101,102,103]);
 for(const v of videos){assert.ok(v.url.startsWith('https://'));assert.ok(v.evidence.includes('核实'));assert.ok(v.metric.includes('转化')||v.metric.includes('引流'));const code=commands.encode(commands.fromCase(v));assert.ok(commands.render(commands.decode(code),'我的主题').includes(v.method));assert.ok(!commands.decode(code).author);}
 assert.ok(videos[0].url.endsWith('pJWK-ZEy5_A'));assert.ok(videos[1].url.endsWith('7455163670146911546'));assert.ok(videos[2].url.endsWith('7453441501838740776'));
});
