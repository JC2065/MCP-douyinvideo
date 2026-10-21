const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
test('design handoff covers every registered page and functional boundaries',()=>{
 const app=JSON.parse(fs.readFileSync('app.json','utf8'));const inventory=fs.readFileSync('docs/frontend-inventory.md','utf8');const doc=fs.readFileSync('docs/frontend-design-handoff.md','utf8');
 const routes=app.pages.concat(app.subpackages.flatMap(p=>p.pages.map(r=>p.root+'/'+r)));
 for(const route of routes)assert.ok(inventory.includes('## '+route),route);
 for(const text of ['加载','失败','返回','分镜','导出 MP3','维护','归档','不是生产灾备','功能开发现已暂停'])assert.ok(doc.includes(text),text);
 for(const view of ['casePicker','earnings','editor','publish','review'])assert.ok(doc.includes(view),view);
});
