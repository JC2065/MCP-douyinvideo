const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
test('项目地图列出的文件和目录都存在，接手入口写在 AGENTS.md 和 CLAUDE.md 里',()=>{
 const map=fs.readFileSync('docs/PROJECT-MAP.md','utf8');
 const paths=[...map.matchAll(/`((?:docs|scripts|tests|pages|utils|components|deploy|backend|web|tools)\/[^`*<>\s]+)`/g)].map(m=>m[1].replace(/\/$/,''));
 assert.ok(paths.length>30,'地图里应列出主要文件');
 for(const p of new Set(paths))assert.ok(fs.existsSync(p),'项目地图里的路径不存在，请更新 docs/PROJECT-MAP.md：'+p);
 for(const f of ['AGENTS.md','CLAUDE.md'])assert.ok(fs.readFileSync(f,'utf8').includes('docs/PROJECT-MAP.md'),f+' 应指向项目地图');
});
