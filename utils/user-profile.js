// Long-term creator profile stored on YOUAI's server (kept when the AI model or key changes).
const {BASE}=require('./service-endpoints');const service=require('./video-service');
function call(api,path,data){return new Promise((resolve,reject)=>service.send(api,{url:BASE+path,method:data===undefined?'GET':'POST',data,timeout:15000,header:{'Content-Type':'application/json'},success:r=>r.statusCode===200?resolve(r.data):reject(Error(r.data&&r.data.error||'个性化服务暂不可用')),fail:()=>reject(Error('暂时无法连接，请稍后重试'))}));}
module.exports={
 signal:(api,kind,topic)=>call(api,'/profile/signal',{kind,title:String(topic.title||'').slice(0,60),angle:String(topic.angle||'').slice(0,120)}),
 view:api=>call(api,'/profile'),
 remove:(api,facet,value)=>call(api,'/profile/remove',{facet,value}),
 setEnabled:(api,enabled)=>call(api,'/profile/settings',{enabled:!!enabled}),
 clear:api=>call(api,'/profile/clear',{})
};
