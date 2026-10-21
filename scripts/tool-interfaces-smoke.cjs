const assert=require('node:assert/strict');
const path=require('node:path');
const os=require('node:os');
const automator=require(process.env.YOUAI_AUTOMATOR_MODULE||'miniprogram-automator');
const {KEY}=require('../utils/tool-interfaces');
const pause=()=>new Promise(resolve=>setTimeout(resolve,650));
async function run(){
 const mini=await automator.connect({wsEndpoint:process.env.YOUAI_AUTOMATOR_WS||'ws://127.0.0.1:9420'});
 let main,originalState,originalConfig,backedUp=false;
 const waitRoute=async route=>{for(let i=0;i<16;i++){const page=await mini.currentPage();if(page.path===route)return page;await pause();}throw Error('Navigation timed out: '+route);};
 try{
  while((await mini.currentPage()).path!=='pages/main/index'){await mini.navigateBack();await pause();}
  main=await mini.currentPage();originalState=await main.data('state');originalConfig=await mini.callWxMethod('getStorageSync',KEY);backedUp=true;await mini.callWxMethod('setStorageSync',KEY,{});
  await main.setData({tab:'我的',view:'',accountMore:false});await pause();
  const role=await main.$('.account-role-switch');assert.ok(role);await role.tap();await pause();assert.notEqual((await main.data('state')).role,originalState.role);
  await role.tap();await pause();assert.equal((await main.data('state')).role,originalState.role);
  await mini.callWxMethod('hideToast');await mini.screenshot({path:path.join(os.tmpdir(),'youai-interface-account.png')});
  await(await main.$('.account-more .account-row')).tap();await pause();
  await(await main.$$('.account-more .account-row'))[2].tap();let page=await waitRoute('pages/tool-interfaces/index');assert.equal(page.path,'pages/tool-interfaces/index');
  assert.equal((await page.$$('.interface-tool')).length,6);assert.equal(await page.data('source'),'public');assert.equal(await page.$('input'),null);
  await mini.screenshot({path:path.join(os.tmpdir(),'youai-interface-public.png')});
  await(await page.$$('.interface-sources button'))[1].tap();await pause();
  assert.equal(await page.data('source'),'personal');await(await page.$('input')).input('https://api.example.com/tool');await pause();
  await page.callMethod('save',{detail:{value:{url:'https://api.example.com/tool'}}});await pause();assert.equal(await page.data('error'),'');assert.equal(await page.data('dirty'),false);await mini.callWxMethod('hideToast');
  assert.equal((await mini.callWxMethod('getStorageSync',KEY)).download.source,'personal');
  await mini.screenshot({path:path.join(os.tmpdir(),'youai-interface-personal.png')});
  console.log('PASS: role switch and personal configuration saved');
  await(await page.$$('.interface-tools button'))[1].tap();await pause();assert.equal(await page.data('selected'),'transcript');
  await(await page.$$('.interface-tools button'))[0].tap();await pause();assert.equal((await page.data('form')).url,'https://api.example.com/tool');
  console.log('PASS: switch tool and reopen saved configuration');
  await mini.navigateBack();await pause();main=await mini.currentPage();await main.setData({tab:'创作',view:''});await pause();
  await(await main.$$('.tool-item'))[2].tap();page=await waitRoute('pages/tool-interfaces/index');assert.equal(page.path,'pages/tool-interfaces/index');assert.equal(await page.data('selected'),'audio');
  console.log('PASS: role switch, more settings, six tools, read-only public, personal save/reopen, creation entry');
 }finally{
  if(backedUp){
   await mini.callWxMethod('setStorageSync',KEY,originalConfig||{});
   while((await mini.currentPage()).path!=='pages/main/index'){await mini.navigateBack();await pause();}
   main=await mini.currentPage();await main.setData({state:originalState,tab:'我的',view:'',accountMore:false});await main.callMethod('persist');
  }
  mini.disconnect();
 }
}
run().catch(error=>{console.error(error);process.exitCode=1;});
