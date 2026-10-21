const test=require('node:test');
const assert=require('node:assert/strict');
const engine=require('../utils/analysis-presets');
const cases=require('../utils/local-cases');
test('自动补充维度有上限、不重复主方案，手动仅输出指定栏目且基础事实一致',()=>{
 for(const item of cases){
  const auto=engine.analyze(item);
  assert.ok(auto.supplements.length<=2);
  assert.ok(auto.supplements.every(s=>!auto.preset.dimensions.includes(s.key)));
  for(const preset of engine.presets){
   const manual=engine.analyze(item,{mode:'manual',preset:preset.id});
   assert.deepEqual(manual.sections.map(s=>s.key),preset.dimensions);
   assert.deepEqual(manual.supplements,[]);
   assert.deepEqual(manual.base,auto.base);
  }
 }
 assert.ok(engine.analyze(cases[3]).supplements.some(s=>s.key==='offer'));
});
test('缺少证据的维度明确标注，不编造结论',()=>{
 const output=engine.analyze(cases[0],{mode:'manual',preset:'offer'});
 for(const key of ['offer','cta'])assert.equal(output.sections.find(s=>s.key===key).status,'未观察到');
 const empty=engine.analyze({id:999});
 assert.ok(empty.sections.every(s=>s.status==='未观察到'&&s.text.includes('暂不生成')));
 assert.deepEqual(empty.supplements,[]);
});
test('固定画面按整体文案分析，变化场景保留多个观察段落',()=>{
 for(const item of cases.slice(0,2)){
  assert.equal(item.segments.length,1);
  assert.equal(item.segments[0].start,0);
  assert.equal(item.segments[0].end,item.duration);
  assert.equal(engine.analyze(item).segmentation.label,'整体画面与文案层次');
 }
 for(const item of cases.slice(2))assert.ok(item.segments.length>1);
});
test('详情信息与补充维度可展开收起，切换方案关闭旧补充内容',()=>{
 const api={getStorageSync(){},setStorageSync(){},showToast(){}};
 const page=require('../case-study/study-page').create(cases[3],()=>{},api);
 page.setData=function(v){Object.assign(this.data,v)};
 page.refreshAnalysis();
 page.toggleDetails();assert.equal(page.data.detailsOpen,true);
 page.toggleDetails();assert.equal(page.data.detailsOpen,false);
 page.toggleSupplements();assert.equal(page.data.supplementsOpen,true);
 page.chooseAnalysis({detail:{value:2}});
 assert.equal(page.data.supplementsOpen,false);
});
