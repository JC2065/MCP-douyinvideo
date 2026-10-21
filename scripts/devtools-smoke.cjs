// Run against an already connected WeChat simulator; no uploads or cache resets.
const assert=require('node:assert/strict');
const path=require('node:path');
const os=require('node:os');
const fs=require('node:fs');
const automator=require(process.env.YOUAI_AUTOMATOR_MODULE||'miniprogram-automator');
const ideaCalendar=require('../utils/idea-calendar');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(fn,label){const end=Date.now()+15000;while(Date.now()<end){const result=await fn();if(result)return result;await delay(150);}throw Error('Timed out: '+label);}
async function clickVisible(mini,page,element){assert.ok(element,'element exists');await mini.pageScrollTo(0);await delay(150);const offset=await element.offset();if(offset.top>420)await mini.pageScrollTo(Math.max(0,offset.top-150));await delay(200);await element.tap();}
async function run(){
 const mini=await automator.connect({wsEndpoint:process.env.YOUAI_AUTOMATOR_WS||'ws://127.0.0.1:9420'});
 const errors=[];mini.on('exception',e=>errors.push(e.message||e.description||JSON.stringify(e)));
 const output=process.env.YOUAI_SMOKE_OUTPUT||path.join(os.tmpdir(),'youai-smoke');fs.mkdirSync(output,{recursive:true});
 const key='youai-analysis-preferences-v1';let preferences;let captured=false;
 try{
  preferences=await mini.evaluate(k=>wx.getStorageSync(k),key);captured=true;
  let main;
  for(let i=0;i<2;i++){
   try{await mini.reLaunch('/pages/main/index');}catch(e){/* cli auto 重启后旧页面引用可能失效，reLaunch 重新绑定 */}
   main=await mini.currentPage();
   try{await main.data('tab');break;}catch(e){await delay(800);}
  }
  assert.equal(main.path,'pages/main/index','Run from the YOUAI project');
  const names=['灵感','创作','学习','任务','我的'];
  for(let i=0;i<names.length;i++){await(await main.$$('.nav-item'))[i].tap();await until(async()=>await main.data('tab')===names[i],names[i]+' navigation');}
  console.log('PASS: all five navigation buttons');
  const today=ideaCalendar.dayKey();
  await(await main.$$('.nav-item'))[0].tap();await until(async()=>await main.data('tab')==='灵感','inspiration route');
  const modes=await main.$$('.record-switch button');assert.equal(modes.length,4,'favorites, works, idea and calendar switch');
  await clickVisible(mini,main,modes[3]);await until(async()=>await main.data('recordMode')==='calendar','calendar view');
  assert.equal((await main.data('calendar.days')).length%7,0,'calendar grid is whole weeks');
  await clickVisible(mini,main,await main.$('.calendar-toolbar button'));
  await until(async()=>await main.data('calendarMonth')===ideaCalendar.shiftMonth(today.slice(0,7),-1),'previous month');
  await clickVisible(mini,main,await main.$('.calendar-today'));
  await until(async()=>await main.data('calendarDay')===today,'back to today');
  const day=(await main.data('calendar.days')).find(d=>d.key===today);assert.ok(day&&day.today,'today cell marked');
  await clickVisible(mini,main,(await main.$$('.record-switch button'))[0]);
  await until(async()=>await main.data('recordMode')==='favorites','favorites view');
  await until(async()=>{const w=await main.$('.record-panel');return !!w;},'favorites panel rendered');
  await clickVisible(mini,main,(await main.$$('.record-switch button'))[1]);
  await until(async()=>await main.data('recordMode')==='works','works view');
  await clickVisible(mini,main,(await main.$$('.record-switch button'))[2]);
  await until(async()=>await main.data('recordMode')==='list','list view');
  console.log('PASS: idea calendar switches views, works view renders, changes month and returns to today');
  await(await main.$$('.nav-item'))[4].tap();await until(async()=>await main.data('tab')==='我的','profile route');
  await clickVisible(mini,main,await main.$('.settings-entry'));
  let settings=await until(async()=>{const p=await mini.currentPage();return p.path==='pages/settings/index'?p:null},'settings route');
  const select=await settings.$('.preset-card button');await clickVisible(mini,settings,select);
  await until(async()=>await settings.data('prefs.mode')==='manual','manual preset selection');
  const auto=(await settings.$$('.chips .chip'))[0];await clickVisible(mini,settings,auto);
  await until(async()=>await settings.data('prefs.mode')==='auto','automatic preset selection');
  console.log('PASS: settings opens, manual and automatic mode clicks respond');
  await mini.navigateBack();main=await mini.currentPage();await(await main.$$('.nav-item'))[2].tap();await until(async()=>await main.data('tab')==='学习','learning route');
  for(const id of [87,201,202,203,204]){
   const card=(await main.$$('.case-list-item'))[[87,201,202,203,204].indexOf(id)];await clickVisible(mini,main,card);
   const route=id===87?'case-study/index':'study-'+id+'/index';
   const study=await until(async()=>{const p=await mini.currentPage();return p.path===route?p:null},route);
   await until(async()=>!(await study.data('loading')),'video preparation '+id);assert.equal(await study.data('error'),false,'video load '+id);
   for(const i of [1,2,0]){await clickVisible(mini,study,(await study.$$('.study-tabs view'))[i]);await until(async()=>await study.data('section')===['看懂作品','逐段拆解','跟着练习'][i],'study tab '+id);}
   assert.equal(await study.data('analysis.version'),'framework-v1.1');
   await clickVisible(mini,study,await study.$('.base-toggle'));
   await until(async()=>await study.data('detailsOpen')===true,'base details expand '+id);
   await clickVisible(mini,study,await study.$('.base-toggle'));
   await until(async()=>await study.data('detailsOpen')===false,'base details collapse '+id);
   if((await study.data('analysis.supplements')).length){
    await clickVisible(mini,study,await study.$('.supplement-toggle'));
    await until(async()=>await study.data('supplementsOpen')===true,'supplements expand '+id);
    await clickVisible(mini,study,await study.$('.supplement-toggle'));
    await until(async()=>await study.data('supplementsOpen')===false,'supplements collapse '+id);
   }
   console.log('PASS: case '+id+' opens, video source loads, all three content tabs respond');
   if(id===204){await mini.pageScrollTo(0);await mini.screenshot({path:path.join(output,'case-204.png')});}
   await mini.navigateBack();main=await mini.currentPage();
  }
  assert.deepEqual(errors,[],'no runtime exceptions during real taps');
  await mini.pageScrollTo(0);await mini.screenshot({path:path.join(output,'learning.png')});
  console.log('PASS: simulator click smoke test; screenshots in '+output);
 }finally{
  if(captured)await mini.evaluate((k,value)=>{if(value==='')wx.removeStorageSync(k);else wx.setStorageSync(k,value);},key,preferences);
  mini.disconnect();
 }
}
run().catch(e=>{console.error(e.stack||e.message);process.exitCode=1;});
