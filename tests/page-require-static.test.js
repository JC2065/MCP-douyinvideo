const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
// WeChat DevTools (ignoreDevUnusedFiles) does not see require() written inside an object spread,
// so the module is dropped and the page white-screens ("module ... is not defined").
test('page modules are required as top-level constants, never spread inline',()=>{
 const files=[];const walk=d=>{for(const f of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,f.name);if(f.isDirectory())walk(p);else if(p.endsWith('.js'))files.push(p);}};
 for(const dir of ['pages','utils','components'])if(fs.existsSync(dir))walk(dir);
 for(const file of files)assert.doesNotMatch(fs.readFileSync(file,'utf8'),/\.\.\.\s*require\(/,file);
 assert.match(fs.readFileSync('pages/video/index.js','utf8'),/^const watchPage=require\('\.\.\/\.\.\/utils\/watch-page'\);/m);
});
