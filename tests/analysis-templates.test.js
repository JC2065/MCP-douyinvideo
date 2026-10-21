const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const e=require('../utils/analysis-presets'),cases=require('../utils/local-cases');
function api(){const data={};return{getStorageSync:key=>data[key],setStorageSync:(key,value)=>data[key]=JSON.parse(JSON.stringify(value)),showToast(){},showModal:o=>o.success({confirm:true}),navigateTo(){},navigateBack(){},pageScrollTo(){}};}
function settings(wx=api()){let page;vm.runInNewContext(fs.readFileSync('pages/settings/index.js','utf8'),{require:()=>e,Page:value=>page=value,wx});page.data=JSON.parse(JSON.stringify(page.data));page.setData=value=>Object.assign(page.data,value);page.onShow();return{page,wx};}
test('six materials have independent default templates and independent multi-goal choices',()=>{
 const custom=e.templates.clone(e.presets[2],'product',e.labels);custom.name='我的卖点拆解';
 const prefs=e.normalize({customTemplates:[custom],typeDefaults:{product:custom.id},typeGoals:{product:['selling','trust'],voice:['structure','visual']}});
 assert.equal(e.analyze({materialType:'product'},prefs).preset.id,custom.id);assert.equal(e.analyze({materialType:'voice'},prefs).preset.id,'structure');
 assert.deepEqual(e.analyze({materialType:'product'},prefs).goals.map(row=>row.id),['selling','trust']);
 for(const type of e.templates.types)assert.equal(e.analyze({materialType:type.id}).preset.id,type.preset);
 const combined=e.analyze(cases[0],{goalOverrides:{201:['emotion','trust']}});assert.ok(combined.sections.some(row=>row.key==='proof'));assert.equal(new Set(combined.sections.map(row=>row.key)).size,combined.sections.length);
});
test('DIY editor duplicates without mutating builtins, reorders, validates, saves and deletes with safe fallback',()=>{
 const {page,wx}=settings(),before=JSON.stringify(e.presets);page.diy();page.field({currentTarget:{dataset:{field:'name'}},detail:{value:'我的镜头问题'}});page.addSection();page.saveTemplate();assert.match(page.data.error,/填写/);
 const i=page.data.editor.sections.length-1;page.sectionField({currentTarget:{dataset:{index:i,field:'question'}},detail:{value:'哪个道具可以用我自己的素材替换？'}});page.move({currentTarget:{dataset:{index:i,direction:-1}}});page.saveTemplate();const saved=e.load(wx).customTemplates[0];assert.equal(saved.name,'我的镜头问题');assert.ok(saved.sections.at(-2).question.includes('道具'));assert.equal(JSON.stringify(e.presets),before);
 page.useForType();assert.equal(e.load(wx).typeDefaults.voice,saved.id);page.edit({currentTarget:{dataset:{id:saved.id}}});page.field({currentTarget:{dataset:{field:'name'}},detail:{value:'新的模板名称'}});page.saveTemplate();assert.equal(e.load(wx).customTemplates[0].version,2);
 page.removeTemplate({currentTarget:{dataset:{id:saved.id}}});assert.equal(e.load(wx).customTemplates.length,0);assert.equal(e.analyze({materialType:'voice'},e.load(wx)).preset.id,'structure');
});
test('custom questions stay unobserved, invalid config is bounded and prototype keys cannot become evidence',()=>{
 const custom=e.templates.clone(e.presets[0],'voice',e.labels);custom.sections=[{key:'question-own',title:'自定义',question:'实际成交是否可证明？'},{key:'constructor',title:'边界',question:'不要从继承属性读取证据'}];
 const prefs=e.normalize({customTemplates:[custom],mode:'manual',preset:custom.id,goalOverrides:JSON.parse('{"__proto__":["trust"]}')});const output=e.analyze({id:1},prefs);
 assert.ok(output.sections.every(row=>row.status==='未观察到'));assert.ok(output.sections.every(row=>typeof row.text==='string'));assert.equal(Object.getPrototypeOf(prefs.goalOverrides),Object.prototype);
 assert.equal(e.normalize({customTemplates:Array.from({length:25},(_,i)=>({...custom,id:'custom-validabc'+i}))}).customTemplates.length,20);
});
test('DIY snapshot survives template editing/deletion and saved-work regeneration',()=>{
 const wx=api(),custom=e.templates.clone(e.presets[5],'story',e.labels);custom.name='独有镜头模板';custom.steps=['独有问题：用自己的道具重新组织镜头'];e.save(wx,{customTemplates:[custom],mode:'manual',preset:custom.id});
 let main;const store=require('../utils/store'),repo={...store,load(){return store.initial();},save(value){this.saved=JSON.parse(JSON.stringify(value));}};
 vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:name=>name.endsWith('/store')?repo:require(path.resolve('pages/main',name)),Page:value=>main=value,wx});main.setData=value=>Object.assign(main.data,value);
 const study=require('../case-study/study-page').create(cases[0],()=>{},wx,repo,()=>[main,study]);study.setData=value=>Object.assign(study.data,value);study.onShow();study.theme({detail:{value:'我的新产品'}});study.create();main.saveWork({currentTarget:{dataset:{complete:true}}});const saved=repo.saved.works[0];assert.equal(saved.analysisProfile.template.name,'独有镜头模板');assert.ok(saved.versions[0].analysisPractice.includes('独有问题'));
 e.save(wx,{});main.editor({currentTarget:{dataset:{id:saved.id}}});main.data.title='再换一个主题';main.generate();assert.ok(main.data.draft.includes('独有问题'));assert.ok(main.data.draft.includes('独有镜头模板'));main.editor({currentTarget:{dataset:{}}});assert.equal(main.data.analysisProfile,null);
});
test('reference plan remains attached to approved storyboard and changed plans require review again',()=>{
 const brief=require('../utils/video-brief'),analysis=e.analyze(cases[0],{goals:['emotion','trust']}),plan=e.plan(analysis),source={type:'idea',value:'自己的新主题'},answers={analysisPlan:plan,visualStyle:'纯文字画面'},board=brief.storyboard(source,answers);board.status='approved';const data=brief.generationBrief(source,answers,board);assert.deepEqual(data.analysisPlan.goalIds,['emotion','trust']);
 assert.throws(()=>brief.generationBrief(source,{...answers,analysisPlan:{...plan,templateName:'另一个模板'}},board),/重新确认/);
});

test('stale DIY editor preserves newer saved version and supports explicit save as new',()=>{
 const {page,wx}=settings();page.diy();page.saveTemplate();const original=e.load(wx).customTemplates[0];page.edit({currentTarget:{dataset:{id:original.id}}});const newer=e.load(wx);newer.customTemplates[0].version++;newer.customTemplates[0].name='云端较新版本';e.save(wx,newer);page.saveTemplate();assert.match(page.data.error,/其他设备更新/);assert.equal(e.load(wx).customTemplates[0].name,'云端较新版本');page.saveAsNew();assert.equal(e.load(wx).customTemplates.length,2);assert.notEqual(e.load(wx).customTemplates[1].id,original.id);assert.equal(page.data.editor,null);
});

test('默认模板入口展示六套方法，选择可预览且不覆盖原有DIY库',()=>{
 const fs=require('fs'),vm=require('vm');let page;const engine=require('../utils/analysis-presets');const saved={customTemplates:[]};const wx={getStorageSync:()=>saved,setStorageSync(){},showToast(){}};
 vm.runInNewContext(fs.readFileSync('pages/settings/index.js','utf8'),{require:()=>engine,Page:p=>page=p,wx});page.setData=function(d){Object.assign(this.data,d)};page.onShow();
 for(const preset of engine.presets){page.defaultTemplate({currentTarget:{dataset:{id:preset.id}}});assert.equal(page.data.preview.preset.id,preset.id);assert.ok(page.data.preview.sections.length>=3);}
 assert.equal(saved.customTemplates.length,0);assert.ok(fs.readFileSync('pages/settings/index.wxml','utf8').includes('默认拆解模板'));
});
