const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
test('creation board plan keeps the decisions the user confirmed',()=>{
 const doc=fs.readFileSync('docs/creation-board-plan.md','utf8');
 for(const text of ['[上传原视频] [放弃查看] [我知道了]','倒计时 8 秒','不做匿名化','原内容','快看','细看','样片归纳','自动匹配','套版成片','激励','全站汇总','第 3 次起','只做**抖音**','## 11. 里程碑与进度'])assert.ok(doc.includes(text),text);
 assert.ok(fs.readFileSync('docs/task-ledger.md','utf8').includes('creation-board-plan.md'));
});
