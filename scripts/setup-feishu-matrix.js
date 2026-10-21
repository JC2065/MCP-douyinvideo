const fs=require('node:fs'),path=require('node:path');const {tables,bootstrap}=require('../backend/feishu-matrix');
async function main(){
 const args=process.argv.slice(2),arg=name=>{const i=args.indexOf(name);return i<0?null:args[i+1];};
 if(!args.includes('--apply')){console.log(JSON.stringify({mode:'preview',networkCalls:0,tables},null,2));return;}
 const configPath=arg('--config'),statePath=arg('--state');if(!configPath||!statePath)throw Error('真实建表需要 --apply --config <仓库外配置路径> --state <仓库外状态路径>');
 const root=path.resolve(__dirname,'..');for(const file of [configPath,statePath]){const rel=path.relative(root,path.resolve(file));if(rel===''||(!rel.startsWith('..'+path.sep)&&rel!=='..'&&!path.isAbsolute(rel)))throw Error('凭据与状态文件必须位于仓库外');}
 let config;try{config=JSON.parse(fs.readFileSync(configPath,'utf8').replace(/^\uFEFF/,''));}catch{throw Error('无法读取配置：请检查文件路径和 JSON 格式');}fs.mkdirSync(path.dirname(path.resolve(statePath)),{recursive:true});
 const selected=arg('--role');const roles=selected?[selected]:['management','archive'];
 await bootstrap(config,{roles,layout:arg('--layout')||'split',checkpoint:async state=>{let saved={version:1,roles:{}};if(fs.existsSync(statePath)){try{saved=JSON.parse(fs.readFileSync(statePath,'utf8'));}catch{throw Error('原状态文件格式无效，请保留并检查');}}const merged={version:1,roles:{...saved.roles,...state.roles}},temp=statePath+'.tmp';fs.writeFileSync(temp,JSON.stringify(merged,null,2));fs.renameSync(temp,statePath);}});console.log('所选组织的表与字段创建/核对完成；状态已保存。尚未接入业务同步或文件归档。');
}
if(require.main===module)main().catch(e=>{console.error(e.message);process.exitCode=1;});
module.exports={main};
