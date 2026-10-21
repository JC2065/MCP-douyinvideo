const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const doc=fs.readFileSync(path.join(root,'docs/backend-data-platform.md'),'utf8');
const plan=fs.readFileSync(path.join(root,'docs/product-plan.md'),'utf8');
const readme=fs.readFileSync(path.join(root,'README.md'),'utf8');

test('中台设计覆盖三端、身份、存储、同步、安全与部署',()=>{
 for(const text of ['微信小程序','Web','App','user_identities','PostgreSQL','对象存储','Idempotency-Key','version','/sync/changes','staging','production'])assert.ok(doc.includes(text),text);
 assert.match(doc,/模块化单体/);assert.match(doc,/其他账号的数据统一返回 404/);
 assert.match(doc,/它不是生产数据库实现/);
});

test('产品方案和 README 指向多端数据中台且继续隔离商家金额',()=>{
 assert.ok(plan.includes('[多端数据中台](backend-data-platform.md)'));
 assert.match(plan,/微信小程序、Web 和 App 共用的数据中台/);
 assert.ok(readme.includes('[多端数据中台设计](docs/backend-data-platform.md)'));
 for(const text of ['商家、订单、金额、支付、结算和运营审批暂不建模','客户端不能提交或修改 `user_id`'])assert.ok(doc.includes(text),text);
});

test('账号资产设计保留现有归属并约束迁移授权、恢复及实施状态',()=>{
 const account=fs.readFileSync(path.join(root,'docs/account-asset-system.md'),'utf8');
 for(const text of ['尚未实施统一账号迁移','utils/store.js','pages/video-assets/index.js','legacy_user_aliases','unique(provider,issuer,subject)','Idempotency-Key','expectedVersion','删除墓碑','源账号和目标账号控制权','未提交的目标资产不可见','失败保留本机原件','新节点写入后回退','两部真机'])assert.ok(account.includes(text),text);
 assert.match(account,/不能将既有契约当作所有业务已接通/);
 assert.match(account,/不在设计阶段修改线上返回/);
 assert.ok(doc.includes('(account-asset-system.md)'));
});

test('星球会员设计明确未实施边界、核验来源与权益资产分离',()=>{
 const membership=fs.readFileSync(path.join(root,'docs/membership-entitlements.md'),'utf8');
 for(const text of ['尚未实现绑定','membership_bindings','entitlement_grants','usage_ledger','同一星球成员同时只绑定一个','verified_until','不自动复制付费资格','部分或失败名单缺人不能直接撤销','不因会员失效被锁','不收集用户知识星球密码','续期退款','https://doc.zsxq.com/zsxq-faq.html'])assert.ok(membership.includes(text),text);
 assert.match(membership,/不能与本小程序OpenID直接等同/);
 assert.match(membership,/当前不设价格、不启用限额/);
 assert.ok(fs.readFileSync(path.join(root,'docs/account-asset-system.md'),'utf8').includes('(membership-entitlements.md)'));
});
