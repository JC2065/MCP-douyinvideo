const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
test('low-cost video understanding plan is handed to Codex with cost guards',()=>{
 const doc=fs.readFileSync('docs/video-understanding-low-cost-plan.md','utf8');
 for(const key of ['video_watch','video_watch_deep','video_chat','content-watch-4','perUserDailyVideos','dailyBudgetYuan','usage','youai_deploy','mock'])assert.ok(doc.includes(key),key);
 assert.match(doc,/不装 librosa/);assert.match(doc,/单个坏字段丢弃/);
 const ledger=fs.readFileSync('docs/task-ledger.md','utf8');assert.ok(ledger.includes('video-understanding-low-cost-plan.md'));
});
