const assert=require('node:assert/strict');
const automator=require(process.env.YOUAI_AUTOMATOR_MODULE||'miniprogram-automator');
async function run(){const mini=await automator.connect({wsEndpoint:process.env.YOUAI_AUTOMATOR_WS||'ws://127.0.0.1:9420'});try{
 const errors=[];mini.on('exception',e=>errors.push(e.message||String(e)));
 const page=await mini.reLaunch('/pages/hotspots/index');
 await page.waitFor(async()=>((await page.data('rows'))||[]).length>0);
 const rows=await page.data('rows');assert.ok(rows.length>0);assert.ok(rows.every(r=>r.url&&r.rank>0));
 assert.equal(await page.data('mode'),'rising');const rising=await page.data('visible');assert.ok(rising.every(r=>!r.stale&&r.rankChange>0));await mini.screenshot({path:require('node:path').join(require('node:os').tmpdir(),'youai-trends-list.png')});
 const keyword=rows[0].title.slice(0,2);
 await page.callMethod('mode',{currentTarget:{dataset:{mode:'chat'}}});
 await(await page.$('input')).input(keyword);await(await page.$('.search-row button')).tap();await page.waitFor(300);
 assert.ok((await page.data('visible')).every(r=>r.title.includes(keyword)));
 await(await page.$('.trend-heading')).tap();await page.waitFor(200);assert.ok(await page.data('selected'));
 await mini.screenshot({path:process.env.YOUAI_HOTSPOT_SCREEN||require('node:path').join(require('node:os').tmpdir(),'youai-hotspots-live.png')});
 await page.callMethod('close');await page.callMethod('mode',{currentTarget:{dataset:{mode:'rank'}}});
 await page.callMethod('platform',{currentTarget:{dataset:{platform:'抖音'}}});assert.ok((await page.data('visible')).every(r=>r.platform==='抖音'));
 const main=await mini.reLaunch('/pages/main/index');await main.waitFor(async()=>((await main.data('hotspotRows'))||[]).length>0);
 assert.ok((await main.data('hotspotVisible')).every(r=>!r.stale&&r.rankChange>0));assert.ok((await main.data('hotspotVisible')).length<=12);await mini.pageScrollTo(450);await main.waitFor(200);await mini.screenshot({path:require('node:path').join(require('node:os').tmpdir(),'youai-trends-main.png')});assert.match(await main.data('hotspotStatus'),/更新/);
 assert.equal(errors.length,0,errors.join(';'));console.log(JSON.stringify({ok:true,rows:rows.length,mainRows:(await main.data('hotspotRows')).length,search:true,detail:true,filter:true,exceptions:errors.length}));
 }finally{mini.disconnect();}}
run().catch(e=>{console.error(e);process.exitCode=1;});
