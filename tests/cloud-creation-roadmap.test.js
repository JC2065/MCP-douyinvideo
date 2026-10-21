const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const file='docs/cloud-creation-roadmap.md',plan=fs.readFileSync(file,'utf8');
test('云端规划保持创作者主线、当前阻塞和可验证阶段边界',()=>{
 for(const text of ['点子、抖音参考链接或模板口令','可发布的视频成片','P0','P1','P2','P3','P4','P5','手机移动网络','两个账号资产隔离','2027-03-10','额度来源','飞书故障','重复点击不重复收费','归档不等同备份','明确区分本机通过、云端通过、手机正式版通过','云端部署、正式手机闭环、飞书应用与六表创建、自动归档'])assert.ok(plan.includes(text),text);
 for(const [,target] of plan.matchAll(/\]\(([^)]+\.md)\)/g))assert.ok(fs.existsSync(path.resolve('docs',target)),target);
});
test('主入口与交接都指向唯一专项规划且六张矩阵表完整',()=>{
 for(const file of ['README.md','docs/development-master-plan.md','docs/agent-handoff-2026-10-11.md'])assert.ok(fs.readFileSync(file,'utf8').includes('cloud-creation-roadmap.md'),file);
 for(const name of ['作品总表','资产目录','创作方案','存储资源池','归档与恢复任务','成本与反馈'])assert.ok(plan.includes('| '+name+' |'),name);
});
