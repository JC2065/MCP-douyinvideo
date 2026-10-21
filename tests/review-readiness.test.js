const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
function wxmlFiles(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.name==='node_modules'||e.name.startsWith('.')?[]:e.isDirectory()?wxmlFiles(path.join(dir,e.name)):e.name.endsWith('.wxml')?[path.join(dir,e.name)]:[]);}
test('video 组件的 poster 只能是网络地址：本地封面会在审核时产生渲染层报错',()=>{
 for(const file of wxmlFiles('.')){
  for(const tag of fs.readFileSync(file,'utf8').match(/<video\b[^>]*>/g)||[]){
   const poster=(tag.match(/poster="([^"]*)"/)||[])[1];
   if(poster)assert.match(poster,/^https:\/\//,file+' uses a non-network poster: '+poster);
  }
 }
});
