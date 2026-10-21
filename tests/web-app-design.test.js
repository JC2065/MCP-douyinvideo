const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'web/index.html'),'utf8');
const css=fs.readFileSync(path.join(root,'web/styles.css'),'utf8');
const js=fs.readFileSync(path.join(root,'web/app.js'),'utf8');
const doc=fs.readFileSync(path.join(root,'docs/web-app-design.md'),'utf8');

test('网页版只保留创作者四入口并为每个入口提供页面',()=>{
 for(const [id,label] of [['inspiration','灵感'],['creation','创作'],['learning','学习'],['account','我的']]){assert.ok(html.includes(`data-view="${id}"`),id);assert.ok(html.includes(`data-page="${id}"`),id);assert.ok(html.includes(`<span>${label}</span>`),label);}
 const nav=html.slice(html.indexOf('<nav class="primary-nav">'),html.indexOf('</nav>'));
 assert.doesNotMatch(nav,/任务|商家|订单|收益|金额/);assert.equal((nav.match(/class="nav-item/g)||[]).length,4);
});

test('桌面、收窄和移动布局均有明确断点与导航变化',()=>{
 assert.match(css,/grid-template-columns:224px minmax\(520px,1fr\) 284px/);assert.match(css,/@media\(max-width:1100px\)/);assert.match(css,/@media\(max-width:760px\)/);assert.match(css,/\.rail\{position:fixed;top:auto/);assert.match(css,/grid-template-columns:repeat\(4,1fr\)/);
});

test('原型脚本可解析，真实动作保持待联调表达',()=>{
 new vm.Script(js);assert.ok(html.includes('data-mode="prototype"'));assert.match(html,/接入数据中台后显示真实同步状态/);assert.match(js,/将在接入对应服务后联调/);assert.doesNotMatch(js,/保存成功|同步成功|登录成功/);
});

test('网页引用的本地图片存在，设计方案明确共享和分离边界',()=>{
 const sources=[...html.matchAll(/src="(\.\.\/assets\/[^"]+)"/g)].map(match=>match[1]);assert.ok(sources.length>=10);
 for(const source of new Set(sources))assert.ok(fs.statSync(path.resolve(root,'web',source)).isFile(),source);
 for(const text of ['共享前端业务核心，分别实现展示层','WXML/WXSS','浏览器','wechat-adapter','web-adapter','760px'])assert.ok(doc.includes(text),text);
});
