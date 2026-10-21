const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const document=fs.readFileSync(path.join(root,'docs/product-plan.md'),'utf8');

test('产品方案的 Demo 基线可追溯，六个工具范围与基线代码一致',t=>{
 const hash=document.match(/基线提交：`([a-f0-9]{40})`/)[1];
 // The public repository is a history-free snapshot; the baseline commit only exists in the full development history.
 try{execFileSync('git',['cat-file','-e',hash+'^{commit}'],{cwd:root,stdio:'ignore'});}catch(_){return t.skip('基线提交不在当前仓库历史中（公开快照无历史）');}
 const source=execFileSync('git',['show',hash+':utils/tool-interfaces.js'],{cwd:root,encoding:'utf8'});
 const tools=[...source.matchAll(/\{id:'([^']+)',name:'([^']+)'\}/g)];
 assert.equal(tools.length,6);
 for(const [,id,name] of tools)assert.ok(document.includes(`| ${id} | ${name} |`),name);
 const routes=JSON.parse(execFileSync('git',['show',hash+':app.json'],{cwd:root,encoding:'utf8'}));
 assert.ok(routes.pages.includes('pages/tool-interfaces/index'));
});

test('产品方案的本地证据链接有效，README 提供可达入口',()=>{
 assert.ok(fs.readFileSync(path.join(root,'README.md'),'utf8').includes('(docs/product-plan.md)'));
 const links=[...document.matchAll(/\]\(([^)]+)\)/g)].map(match=>match[1]);
 assert.ok(links.length>=6);
 for(const link of links){const target=path.resolve(root,'docs',link);assert.ok(target.startsWith(root+path.sep));assert.ok(fs.statSync(target).isFile(),link);}
});

test('首阶段聚焦三个业务板块和我的管理中心，明确暂缓商家与金额能力',()=>{
 for(const section of ['灵感','创作','学习','我的'])assert.ok(document.includes(`| ${section} |`),section);
 for(const group of ['内容管理','创作设置','数据管理','账户与通用'])assert.ok(document.includes(`| ${group} |`),group);
 assert.match(document,/后端首阶段采用模块化单体 API 服务/);
 assert.match(document,/不建设商家运营后台/);
 assert.match(document,/金额字段、商家身份字段和订单状态不进入首阶段模型/);
 assert.match(document,/整个流程没有商家或金额依赖/);
 const readme=fs.readFileSync(path.join(root,'README.md'),'utf8');
 assert.match(readme,/先完善灵感、创作、学习和“我的”/);
 assert.match(readme,/商家与金额功能暂缓/);
});
