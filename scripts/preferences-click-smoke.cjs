const assert=require('node:assert/strict');const path=require('node:path');
const a=require(process.env.YOUAI_AUTOMATOR_MODULE||'miniprogram-automator');
async function run(){const m=await a.connect({wsEndpoint:'ws://127.0.0.1:9420'});let original;
try{
 const p=await m.navigateTo('/pages/preferences/index?section=video');original=await p.data('state');
 const chips=await p.$$('.card .chip');await chips[1].tap();await p.waitFor(250);
 await m.pageScrollTo(700);await p.waitFor(250);await(await p.$('.pref-save')).tap();await p.waitFor(300);assert.equal(await p.data('saved'),true);
 const v=await m.navigateTo('/pages/video/index?idea='+encodeURIComponent('窗边的下午'));await(await v.$('button.primary')).tap();await v.waitFor(300);assert.match(await v.data('summary'),/30 秒/);
 await m.screenshot({path:path.join(require('node:os').tmpdir(),'youai-preference-video.png')});
 await m.navigateBack();await m.navigateBack();let main=await m.currentPage();while(main.path!=='pages/main/index'){await m.navigateBack();main=await m.currentPage();}await(await main.$$('.nav-item'))[4].tap();await m.pageScrollTo(0);await main.waitFor(300);
 await m.screenshot({path:path.join(require('node:os').tmpdir(),'youai-creator-profile.png')});
 console.log('PASS: preference selection, save, video default, profile summary');
}finally{if(original)await m.evaluate(data=>wx.setStorageSync('youai-creator-preferences-v1',data),original);m.disconnect();}}
run().catch(e=>{console.error(e);process.exitCode=1;});
