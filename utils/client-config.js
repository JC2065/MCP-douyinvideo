const KEY='youai.client-config.v1';
const VERSION='1.1.0';
const IDS=['download','transcript','audio','eraser','cover'];
const normalize=value=>{
 if(!value||value.schemaVersion!==1)return null;
 const tools={};for(const id of IDS)tools[id]={maintenance:!!(value.tools&&value.tools[id]&&value.tools[id].maintenance===true)};
 return {schemaVersion:1,revision:String(value.revision||'default').slice(0,64),tools};
};
function current(api,base){try{const saved=api.getStorageSync(KEY);if(saved&&saved.base===base&&Date.now()-saved.at<3600000)return normalize(saved.value);}catch(_){}return null;}
function refresh(api,base){
 return new Promise(resolve=>api.request({url:base+'/client-config',timeout:4000,header:{'X-YOUAI-Client-Version':VERSION,'X-YOUAI-Config-Schema':'1'},success:r=>{
  const value=r.statusCode===200?normalize(r.data):null;
  if(value){try{api.setStorageSync(KEY,{base,at:Date.now(),value});}catch(_){}resolve(value);}else resolve(current(api,base));
 },fail:()=>resolve(current(api,base))}));
}
module.exports={KEY,VERSION,normalize,current,refresh};
