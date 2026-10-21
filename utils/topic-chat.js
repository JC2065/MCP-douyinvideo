const {BASE}=require('./service-endpoints');const service=require('./video-service');
function send(api,path,data){return new Promise((resolve,reject)=>service.send(api,{url:BASE+path,method:'POST',data,timeout:50000,header:{'Content-Type':'application/json'},success:r=>r.statusCode===200?resolve(r.data):reject(Error(r.data&&r.data.error||'选题服务暂不可用')),fail:()=>reject(Error('暂时无法连接选题AI，请稍后重试'))}));}
const requestId=()=>Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,12);
module.exports={requestId,chat:(api,data)=>send(api,'/topics/chat',data),clear:api=>send(api,'/topics/chat/clear',{})};
