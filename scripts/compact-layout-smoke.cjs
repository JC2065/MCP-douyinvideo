const assert=require('node:assert/strict');
const path=require('node:path');
const automator=require(process.env.YOUAI_AUTOMATOR_MODULE||'miniprogram-automator');
async function run(){
 const mini=await automator.connect({wsEndpoint:process.env.YOUAI_AUTOMATOR_WS||'ws://127.0.0.1:9420'});
 const output=process.env.YOUAI_SMOKE_OUTPUT||require('node:os').tmpdir();
 try{
  let page=await mini.currentPage();
  while(page.path!=='pages/main/index'){await mini.navigateBack();page=await mini.currentPage();}
  for(const [index,name] of ['灵感','创作','学习','任务','我的'].entries()){
   await(await page.$$('.nav-item'))[index].tap();await mini.pageScrollTo(0);await page.waitFor(250);
   assert.equal(await page.data('tab'),name);
   const shell=await(await page.$('.shell')).size();
   for(const card of await page.$$('.card')){const size=await card.size();assert.ok(Number(size.width)<=Number(shell.width),'card stays inside shell');}
   if(index===2){const cover=await(await page.$('.case .cover')).size();const row=await(await page.$('.case')).size();assert.ok(Number(cover.width)<Number(row.width)*.4,'learning uses thumbnail rows');assert.ok(Number(row.height)<160,'case row stays compact');}
   await mini.screenshot({path:path.join(output,`youai-compact-${index}.png`)});
  }
  page=await mini.navigateTo('/pages/video/index?idea='+encodeURIComponent('路上看到一朵花'));
  await(await page.$('button.primary')).tap();await page.waitFor(250);
  assert.equal(await page.data('stage'),'interview');
  const button=await page.$('button.primary');const offset=await button.offset();const size=await button.size();
  assert.ok(Number(offset.top)+Number(size.height)<700,'interview action fits typical phone first screen');
  await mini.screenshot({path:path.join(output,'youai-compact-interview.png')});
  console.log('PASS: five compact pages, thumbnail rows, no oversized cards, first-screen interview action');
 }finally{mini.disconnect();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
