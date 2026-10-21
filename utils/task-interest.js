const {BASE}=require('./service-endpoints');
const session=require('./video-session');
function support(api){return new Promise((resolve,reject)=>session.send(api,BASE,{url:BASE+'/task-interest',method:'POST',data:{},timeout:20000,header:{'Content-Type':'application/json'},success:r=>r.statusCode===200?resolve(r.data):reject(Error(r.data?.error||'提交失败，请重试')),fail:()=>reject(Error('网络连接失败，请重试'))}));}
module.exports={support};
