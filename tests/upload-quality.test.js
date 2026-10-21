const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const app=JSON.parse(fs.readFileSync('app.json','utf8'));
function files(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(path.join(dir,e.name)):[path.join(dir,e.name)]);}
test('组件按需注入已开启，学习专用模块只属于分包且每个依赖可解析',()=>{
 assert.equal(app.lazyCodeLoading,'requiredComponents');
 for(const name of ['offline-video','study-page'])assert.equal(fs.existsSync('utils/'+name+'.js'),false);
 for(const {root} of app.subpackages){
  for(const file of files(root).filter(f=>f.endsWith('.js')))for(const [,dep] of fs.readFileSync(file,'utf8').matchAll(/require\(['"]([^'"]+)['"]\)/g)){
   if(!dep.startsWith('.'))continue;assert.ok(fs.existsSync(path.resolve(path.dirname(file),dep)+'.js'),file+': '+dep);
  }
  assert.deepEqual(Object.keys(require('../'+root+'/study-page')),['create']);
 }
});
test('所有上传分包的媒体合计低于200KB，案例资源全部可达',()=>{
 const roots=app.subpackages.map(p=>p.root),media=/\.(jpg|jpeg|png|svg|mp3|mp4|wav)$/i;
 const main=files('assets').filter(f=>media.test(f));assert.ok(main.reduce((sum,f)=>sum+fs.statSync(f).size,0)<200*1024);
 const packagedMedia=['assets',...roots].flatMap(folder=>files(folder).filter(f=>media.test(f)));const total=packagedMedia.reduce((sum,f)=>sum+fs.statSync(f).size,0);assert.ok(total<200*1024,'all packages media: '+total);
 for(const file of packagedMedia)assert.ok(fs.statSync(file).size<200*1024,file);
 for(const c of require('../utils/local-cases'))for(const url of [c.poster,...c.segments.map(s=>s.image)])assert.ok(fs.existsSync('.'+url),url);
});
