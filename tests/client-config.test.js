const test=require('node:test'),assert=require('node:assert/strict');
const c=require('../utils/client-config');
test('configuration accepts only known data and rejects unsupported schema',()=>{
 assert.equal(c.normalize({schemaVersion:2}),null);
 const x=c.normalize({schemaVersion:1,script:'bad',tools:{audio:{maintenance:true,url:'evil'},newTool:{maintenance:true}}});
 assert.equal(x.tools.audio.maintenance,true);assert.equal(x.script,undefined);assert.equal(x.tools.newTool,undefined);assert.equal(x.tools.audio.url,undefined);
});
test('remote config caches per backend with expiry and survives network failure',async()=>{
 let saved;const api={getStorageSync:()=>saved,setStorageSync:(_,v)=>saved=v,request:o=>o.success({statusCode:200,data:{schemaVersion:1,tools:{audio:{maintenance:true}}}})};
 await c.refresh(api,'https://a');assert.equal(c.current(api,'https://a').tools.audio.maintenance,true);assert.equal(c.current(api,'https://b'),null);
 api.request=o=>o.fail();assert.equal((await c.refresh(api,'https://a')).tools.audio.maintenance,true);
 saved.at-=3600001;assert.equal(await c.refresh(api,'https://a'),null);
});
test('unknown server schema retains last valid configuration',async()=>{
 const saved={base:'a',at:Date.now(),value:{schemaVersion:1,revision:'good'}};
 const api={getStorageSync:()=>saved,request:o=>o.success({statusCode:200,data:{schemaVersion:2}})};
 assert.equal((await c.refresh(api,'a')).revision,'good');
});
