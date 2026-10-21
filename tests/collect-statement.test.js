const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs');
const statement=require('../utils/collect-statement');
test('登录弹窗展示用户信息采集声明，勾选同意后才能手机号验证或生成体验账号',async()=>{
 const xml=fs.readFileSync('pages/main/index.wxml','utf8');
 assert.ok(xml.indexOf('用户信息采集声明')<xml.indexOf('open-type="getPhoneNumber"'));assert.match(xml,/wx:if="\{\{ready&&!authAgree\}\}" class="auth-button auth-button-off" bindtap="needAgree"/);assert.match(xml,/bindtap="toggleAgree"/);
 for(const t of ['手机号','创作内容','截图与语音','公开内容'])assert.ok(statement.ITEMS.some(i=>i.startsWith(t)),t);
 const store={};const api={getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;}};assert.equal(statement.agreed(api),false);statement.setAgreed(api,true);assert.equal(statement.agreed(api),true);
 const vm=require('vm');const ctx={module:{exports:{}},wx:api,require:n=>n.endsWith('collect-statement')?statement:{canTrial:()=>true,createTrial:async()=>{ctx.created=true;return {};}}};vm.runInNewContext(fs.readFileSync('utils/account-sheet.js','utf8'),ctx);const sheet=ctx.module.exports;
 const page={...sheet,data:{...sheet.data},setData(v){Object.assign(this.data,v);}};statement.setAgreed(api,false);
 await page.openLogin();assert.equal(page.data.authAgree,false);await page.trialLogin();assert.match(page.data.error,/勾选同意/);assert.ok(!ctx.created,'未同意不能生成体验账号');
 page.toggleAgree();assert.equal(page.data.authAgree,true);assert.equal(statement.agreed(api),true,'同意会记住');
});
test('采集声明 v2：写明完整手机号、同步飞书、内部保存截图与低清副本；版本升级需重新同意',()=>{
 const statement=require('../utils/collect-statement');assert.equal(statement.VERSION,2);
 const all=statement.ITEMS.join('');for(const t of ['完整号码','飞书多维表格','4 张截图和低清视频副本','不对外提供下载'])assert.ok(all.includes(t),t);
 const store={'youai-collect-consent':1};const api={getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;}};assert.equal(statement.agreed(api),false,'同意过 v1 也要重新确认');
 assert.match(require('node:fs').readFileSync('utils/link-notice.js','utf8'),/内部保存截图和低清副本/);
});
