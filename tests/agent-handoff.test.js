const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const file='docs/agent-handoff-2026-10-11.md';
const text=fs.readFileSync(file,'utf8');

test('交接说明包含接手、开发、回交和当前运行基线',()=>{
 for(const heading of ['交接基线','当前已实现','关键文件地图','本机运行与密钥边界','已知风险和下一步优先级','接手检查清单','开发期间必须持续记录','未来交回时的强制格式'])assert.match(text,new RegExp(`## ${heading}`));
 for(const marker of ['988f2af','累计第 20 次','TASK-20261011-01','docs/task-ledger.md','wan3.0-video','compose.backend.yml','1800 秒','每 2 秒','docs/agent-return-YYYY-MM-DD.md'])assert.ok(text.includes(marker),marker);
});

test('交接说明不给出密钥并明确付费调用边界',()=>{
 assert.doesNotMatch(text,/sk-[A-Za-z0-9_-]{8,}/);
 assert.match(text,/密钥不得写入仓库/);
 assert.match(text,/真实付费调用只在功能需要且已获用户授权时执行/);
});

test('云端解析交接保留部署差异和未完成验收边界',()=>{
 const handoff=fs.readFileSync('docs/agent-handoff-2026-10-13-cloud-parser.md','utf8');
 for(const marker of ['RUN-20261013-E27','dtk-api-1:8000','457,905,664','第 65 次','临时部署测试会话','手机界面尚未复测','密钥不得写入仓库','尚未导入镜像或启动浏览器'])assert.ok(handoff.includes(marker),marker);
 assert.doesNotMatch(handoff,/sk-[A-Za-z0-9_-]{8,}/);
 assert.ok(handoff.includes('最新续作结果'));
 assert.ok(handoff.includes('仅保留手机确认待办'));
 assert.ok(handoff.includes('不等同于长期自动恢复观测'));
});
