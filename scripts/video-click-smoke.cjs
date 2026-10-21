// Real developer-tool taps, no method invocation or request mocking.
const assert=require('node:assert/strict');
const path=require('node:path');
const automator=require(process.env.YOUAI_AUTOMATOR_MODULE||'miniprogram-automator');
async function until(fn,label){const end=Date.now()+30000;while(Date.now()<end){if(await fn())return;await new Promise(r=>setTimeout(r,250));}throw Error('Timeout: '+label);}
async function run(){
 const mini=await automator.connect({wsEndpoint:process.env.YOUAI_AUTOMATOR_WS||'ws://127.0.0.1:9420'});
 const errors=[];mini.on('exception',e=>errors.push(e.message||e.description));
 try{
  console.log('Opening video page');const page=await mini.navigateTo('/pages/video/index');
  console.log('Entering idea');const input=await page.$('textarea');await input.tap();await input.input('路上走着看到了一朵杜鹃花');
  console.log('Submitting idea');await(await page.$('button.primary')).tap();
  await until(async()=>await page.data('stage')==='interview','first click opens optional interview');
  assert.equal(await page.data('idea'),'路上走着看到了一朵杜鹃花');
  const button=await page.$('button.primary');const offset=await button.offset();await mini.pageScrollTo(Math.max(0,offset.top-350));await page.waitFor(300);await button.tap();
  await until(async()=>{const error=await page.data('error');if(error)throw Error(error);return await page.data('stage')==='result';},'zero-answer MP4 generation');
  const video=await page.$('video');assert.ok(video);assert.match(await page.data('videoUrl'),/\/media\/[a-f0-9]+\.mp4$/);
  await mini.pageScrollTo(0);await mini.screenshot({path:path.join(require('node:os').tmpdir(),'youai-video-click-pass.png')});
  assert.deepEqual(errors,[]);console.log('PASS: actual input + first button tap + skip interview + local MP4 result, no runtime exceptions');
 }finally{mini.disconnect();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
