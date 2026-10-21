const test=require('node:test');const assert=require('node:assert');
const fb=require('../utils/back-fallback');
function api(env){const s={},calls=[];return{calls,s,getAccountInfoSync:()=>({miniProgram:{envVersion:env}}),getStorageSync:k=>s[k],setStorageSync:(k,v)=>{s[k]=v;},showModal:o=>{calls.push(o);o.complete&&o.complete();}};}
test('体验版弹窗提示并继续兜底',()=>{global.getCurrentPages=()=>[{route:'pages/video/index'}];const a=api('trial');let ran=0;fb.report(a,{reason:'没有上一页'},()=>ran++);assert.equal(ran,1);assert.equal(a.calls.length,1);assert.match(a.calls[0].content,/没有上一页/);assert.match(a.calls[0].content,/pages\/video\/index/);assert.match(a.calls[0].content,/1 层/);assert.equal(a.s[fb.LOG].length,1);});
test('开发版也弹窗',()=>{global.getCurrentPages=()=>[];const a=api('develop');fb.report(a,{reason:'x'},()=>{});assert.equal(a.calls.length,1);});
test('正式版不弹窗只记录',()=>{global.getCurrentPages=()=>[];const a=api('release');let ran=0;fb.report(a,{reason:'x'},()=>ran++);assert.equal(ran,1);assert.equal(a.calls.length,0);assert.equal(a.s[fb.LOG].length,1);});
test('日志最多 20 条',()=>{global.getCurrentPages=()=>[];const a=api('release');for(let i=0;i<25;i++)fb.report(a,{reason:'r'+i});assert.equal(a.s[fb.LOG].length,20);assert.equal(a.s[fb.LOG][0].reason,'r24');});
