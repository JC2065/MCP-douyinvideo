const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const learning=require('../utils/learning');
const store=require('../utils/store');
const event=dataset=>({currentTarget:{dataset}});
function harness(cached){
 let page,saved=cached,confirm=true;
 const localStore={...store,load:()=>saved||store.initial(),save:s=>{saved=JSON.parse(JSON.stringify(s));}};
 vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:n=>n.endsWith('/account-sheet')?require('../utils/account-sheet'):n.endsWith('/creator-preferences')?require('../utils/creator-preferences'):n.endsWith('/daily-pick')?require('../utils/daily-pick'):n.endsWith('/day-feed')?require('../utils/day-feed'):n.endsWith('/idea-calendar')?require('../utils/idea-calendar'):n.endsWith('/analysis-presets')?require('../utils/analysis-presets'):n.endsWith('/local-cases')?require('../utils/local-cases'):n.endsWith('/case87')?require('../utils/case87'):n.endsWith('/video-cases')?require('../utils/video-cases'):n.endsWith('/creative-command')?require('../utils/creative-command'):n.endsWith('/learning')?learning:localStore,Page:p=>{page=p;},wx:{pageScrollTo(){},showToast(){},showModal:o=>o.success({confirm})},console});
 page.setData=function(p){Object.assign(this.data,p);};page.onLoad();
 return {page,saved:()=>saved,cancel:()=>{confirm=false;}};
}
test('个人灵感 → 案例方法 → 完成方案 → 复盘 → 新灵感，重载后保留关联',()=>{
 const h=harness(),p=h.page;p.data.input='家门口的早餐店';p.idea();const id=p.data.state.ideas[0].id;
 p.inspire(event({id}));p.learnForDraft();p.caseDetail(event({id:1}));p.applyCase();
 assert.equal(p.data.title,'家门口的早餐店');assert.equal(p.data.source.id,id);
 assert.ok(p.data.draft.includes(learning.cases[0].cta));assert.ok(p.data.draft.includes(learning.cases[0].method));
 p.saveWork(event({complete:true}));let w=h.saved().works[0];assert.equal(w.status,'已完成');assert.equal(w.caseId,1);assert.equal(w.versions[0].source.id,id);
 const reloaded=harness(h.saved()).page;reloaded.editor(event({id:w.id}));assert.equal(reloaded.data.caseId,1);assert.equal(reloaded.data.source.id,id);
 p.reviewWork(event({id:w.id}));p.data.review='尚未发布，下一条突出步行路线';p.saveReview();
 assert.equal(p.data.tab,'灵感');assert.equal(h.saved().ideas[0].reviewWorkId,w.id);
 p.reviewWork(event({id:w.id}));p.data.review='补拍真实路线';p.saveReview();
 assert.equal(h.saved().ideas.filter(i=>i.reviewWorkId===w.id).length,1);
 assert.equal(h.saved().works[0].review,'补拍真实路线');
});
test('热点可直接创作或收藏到记录，重复保存不会产生重复记录',()=>{
 const {page:p}=harness();p.saveHot(event({id:'tips'}));p.saveHot(event({id:'tips'}));assert.equal(p.data.state.ideas.filter(i=>i.hotspotId==='tips').length,1);
 p.inspire(event({hot:'tips'}));assert.equal(p.data.source.type,'热点推荐');assert.equal(p.data.title,learning.hotspots[1].title);
 p.learnForDraft();p.caseDetail(event({id:2}));p.applyCase();p.saveWork(event({}));
 assert.equal(p.data.state.works[0].source.id,'tips');assert.equal(p.data.state.works[0].caseId,2);
 p.learnHot(event({hot:'renew'}));p.applyCase();assert.equal(p.data.source.id,'renew');assert.equal(p.data.title,learning.hotspots[2].title);assert.equal(p.data.caseId,3);
});
test('取消替换与退出学习保留未保存内容，独立案例创作不覆盖旧作品',()=>{
 const h=harness(),p=h.page;p.inspire(event({id:1}));p.data.draft='我自己的开头';p.learnForDraft();p.caseDetail(event({id:3}));h.cancel();p.applyCase();
 assert.equal(p.data.draft,'我自己的开头');assert.equal(p.data.caseId,null);p.close();assert.equal(p.data.view,'editor');
 p.saveWork(event({}));const oldId=p.data.workId;p.tab(event({tab:'拆学'}));p.caseDetail(event({id:3}));p.applyCase();
 assert.equal(p.data.workId,null);assert.equal(p.data.source.type,'学习案例');assert.equal(p.data.caseId,3);assert.equal(p.data.state.works.find(w=>w.id===oldId).text,'我自己的开头');
 p.editor(event({tool:'脚本创作'}));assert.equal(p.data.source,null);assert.equal(p.data.caseId,null);
});
test('旧缓存作品仍能打开；空白主题、内容和复盘不能保存',()=>{
 const old=store.initial();old.works=[{id:42,title:'旧作品',text:'旧内容',status:'已完成',versions:[{text:'旧内容'}]}];
 const h=harness(old),p=h.page;p.editor(event({id:42}));assert.equal(p.data.source,null);assert.equal(p.data.caseId,null);
 p.reviewWork(event({id:42}));p.data.review=' ';p.saveReview();assert.equal(p.data.state.ideas.length,1);
 p.editor(event({}));p.data.title=' ';p.data.draft='内容';p.saveWork(event({complete:true}));assert.equal(p.data.state.works.length,1);
});
test('三类案例与推荐一一可达，脚本保留引导与验证指标',()=>{
 assert.equal(learning.cases.length,3);assert.equal(new Set(learning.cases.map(c=>c.tag)).size,3);
 for(const c of learning.cases){for(const k of ['audience','goal','hook','structure','method','cta','metric','pitfall','script','practice'])assert.ok(c[k]);const {page:p}=harness();p.caseDetail(event({id:c.id}));p.applyCase();p.data.title='我的主题';p.generate();assert.ok(p.data.draft.includes('我的主题'));assert.ok(p.data.draft.includes(c.metric));}
 for(const h of learning.hotspots)assert.ok(learning.cases.some(c=>c.id===h.caseId));
});
test('页面事件都有处理函数，WXML 标签结构闭合',()=>{
 const {page}=harness();const xml=fs.readFileSync('pages/main/index.wxml','utf8');
 for(const match of xml.matchAll(/(?:bind|catch)(?:tap|input|change)="([^"]+)"/g))assert.equal(typeof page[match[1]],'function',match[1]);
 const stack=[];
 for(const match of xml.matchAll(/<\/?[a-z][\w-]*(?:\s+(?:[^<>"']|"[^"]*"|'[^']*')*)?\s*\/?>/g)){
  const tag=match[0],name=tag.match(/^<\/?([\w-]+)/)[1];
  if(tag.startsWith('</'))assert.equal(stack.pop(),name,tag);else if(!tag.endsWith('/>'))stack.push(name);
 }
 assert.deepEqual(stack,[]);
});
