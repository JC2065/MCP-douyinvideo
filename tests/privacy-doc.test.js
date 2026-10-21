const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs');
const doc=fs.readFileSync('docs/privacy-creation-board.md','utf8');
test('隐私说明与小程序内采集声明、链接说明、首次告知逐字一致',()=>{
 const statement=require('../utils/collect-statement'),notice=require('../utils/link-notice');
 for(const item of statement.ITEMS)assert.ok(doc.includes(item),'采集声明条目未同步到文档：'+item.slice(0,12));
 assert.ok(doc.includes('VERSION='+statement.VERSION),'文档需写明当前采集声明版本');
 assert.ok(doc.includes(notice.TEXT),'链接使用说明未同步');
 const w=fs.readFileSync('pages/video/board.wxml','utf8'),m=w.match(/class="card board-privacy"><view class="muted">(.*?)<\/view>/);
 assert.ok(m&&doc.includes(m[1]),'首次使用告知未同步');
});
test('隐私说明覆盖剪切板、完整手机号与飞书第三方存储，供微信隐私指引填写',()=>{
 for(const t of ['| 剪切板 |','| 手机号 |','第三方存储（飞书多维表格）','phones','asset-ledger.py','最多 20 条'])assert.ok(doc.includes(t),t);
 assert.match(fs.readFileSync('utils/reference-intake.js','utf8')+fs.readFileSync('pages/video/index.js','utf8'),/getClipboardData/,'仍在使用剪切板，指引条目不能删');
});
