// Developer-only setting; never changes the release project configuration.
const fs=require('node:fs');
const path=require('node:path');
const file=path.join(__dirname,'../project.private.config.json');
const config=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8')):{};
config.setting=Object.assign({},config.setting,{urlCheck:false});
fs.writeFileSync(file,JSON.stringify(config,null,2)+'\n');
console.log('Local simulator domain check disabled. Recompile the project. Do not deploy the local HTTP service to production.');
