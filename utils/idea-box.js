// Inspiration fragment box client (docs/idea-box-plan.md). Text goes to /ideas; screenshots and voice upload to /ideas/media.
const {BASE}=require('./service-endpoints');
const sessions=require('./video-session');
const service=require('./video-service');
const FOCUS_KEY='youai-ta-focus';
function call(api,path,data){return new Promise((resolve,reject)=>service.send(api,{url:BASE+path,method:data?'POST':'GET',data,timeout:30000,header:{'Content-Type':'application/json'},success:r=>r.statusCode===200?resolve(r.data):reject(Error(r.data&&r.data.error||'碎片箱暂不可用，请稍后重试')),fail:()=>reject(Error('网络不稳定，请稍后重试'))}));}
function upload(api,kind,filePath,clientId){return new Promise((resolve,reject)=>sessions.session(api,BASE).then(login=>api.uploadFile({url:BASE+'/ideas/media?kind='+kind+'&clientId='+encodeURIComponent(clientId||''),filePath,name:'file',header:{Authorization:'Bearer '+login.token},timeout:120000,success:r=>{let data={};try{data=JSON.parse(r.data||'{}');}catch(_){}r.statusCode===200&&data.id?resolve(data):reject(Error(data.error||(r.statusCode===413?'文件太大，请换一张或说短一点':'上传失败，请重试')));},fail:()=>reject(Error('网络中断，未上传'))})).catch(reject));}
// Voice input for chat boxes: returns text only, nothing is saved on the server.
function transcribe(api,filePath){return new Promise((resolve,reject)=>sessions.session(api,BASE).then(login=>api.uploadFile({url:BASE+'/voice/transcribe',filePath,name:'file',header:{Authorization:'Bearer '+login.token},timeout:90000,success:r=>{let data={};try{data=JSON.parse(r.data||'{}');}catch(_){}r.statusCode===200&&data.text?resolve(data):reject(Error(data.error||'没听清，请再说一次'));},fail:()=>reject(Error('网络中断，语音未识别'))})).catch(reject));}
const clientId=()=>'l'+Date.now().toString(36)+Math.random().toString(36).slice(2,8);
module.exports={FOCUS_KEY,clientId,upload,transcribe,
 add:(api,text,id,createdAt)=>call(api,'/ideas',{text,clientId:id,createdAt}),
 sync:(api,items)=>call(api,'/ideas/sync',{items}),
 list:(api,status)=>call(api,'/ideas'+(status?'?status='+status:'')),
 setStatus:(api,id,status)=>call(api,'/ideas/'+id+'/status',{status}),
 remove:(api,id)=>call(api,'/ideas/'+id+'/delete',{})};
