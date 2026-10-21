const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const plan=fs.readFileSync(path.join(root,'docs/development-master-plan.md'),'utf8');
const registry=JSON.parse(fs.readFileSync(path.join(root,'docs/feature-registry.json'),'utf8'));
const readme=fs.readFileSync(path.join(root,'README.md'),'utf8');

test('主导方案固定核心闭环、四入口、真实产物和延期边界',()=>{
 for(const text of ['灵感 / 学习案例 / 用户素材','创建创作项目','保存版本并标记完成','复盘产生新灵感','灵感、创作、学习、我的','不能用模拟结果宣称功能可用'])assert.ok(plan.includes(text),text);
 const deferredLine=plan.split('\n').find(line=>line.includes('全部延期'))||'';for(const text of ['商家','订单','金额','支付','运营后台'])assert.ok(deferredLine.includes(text),text);
 assert.match(plan,/回答不了的功能不进入当前开发/);
});

test('功能登记表编号唯一、依赖有效且每项具备验收结果',()=>{
 const ids=registry.features.map(item=>item.id),known=new Set(ids);
 assert.equal(known.size,ids.length);assert.ok(ids.length>=12);
 for(const item of registry.features){
  assert.match(item.id,/^[A-Z]+-\d{2}$/);assert.ok(registry.allowedStatuses.includes(item.status),item.id);assert.match(item.priority,/^P[0-2]$/);assert.ok(item.outcome.length>=10,item.id);assert.ok(item.acceptance.length>=3,item.id);assert.ok(item.clients.length>=1,item.id);
  for(const dependency of item.dependsOn)assert.ok(known.has(dependency),`${item.id} -> ${dependency}`);
  assert.ok(plan.includes(item.id),`${item.id} must be routed by master plan`);
 }
});

test('延期业务没有被登记为开发功能，主入口可从 README 到达',()=>{
 const names=registry.features.map(item=>`${item.id} ${item.name} ${item.area}`).join('\n').toLowerCase();
 for(const deferred of registry.deferred)assert.ok(!names.includes(deferred),deferred);
 assert.ok(readme.includes('[开发主导方案](docs/development-master-plan.md)'));
 assert.equal(registry.sourceOfTruth,'docs/development-master-plan.md');
});

test('主导方案包含准入、完成、联调、变更和下一开发包',()=>{
 for(const heading of ['## 6. 接下来直接执行的开发包','## 7. 需求准入规则','## 8. 完成标准','## 9. 联调与发布关卡','## 10. 变更控制'])assert.ok(plan.includes(heading),heading);
 for(const reference of ['product-plan.md','backend-data-platform.md','web-app-design.md','feature-registry.json','../AGENTS.md'])assert.ok(plan.includes(reference),reference);
});
