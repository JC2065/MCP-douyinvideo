// Bounded offline demo assets only; replace with CDN playback URLs in production.
function prepare(api,asset,id,force=false){
 const fs=api.getFileSystemManager(),filePath=api.env.USER_DATA_PATH+'/youai-'+id+'-'+asset.version+'.mp4';
 return new Promise((resolve,reject)=>{const write=()=>fs.writeFile({filePath,data:asset.base64,encoding:'base64',success:()=>resolve(filePath),fail:reject});if(force)return write();fs.stat({path:filePath,success:r=>r.stats.size===asset.bytes?resolve(filePath):write(),fail:write});});
}
module.exports={prepare};
