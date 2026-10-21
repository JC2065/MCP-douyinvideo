const {BASE}=require('./service-endpoints');
let token='';
function clear(){token='';}
function request(wx,path,data){return new Promise((resolve,reject)=>wx.request({url:BASE+'/admin-api/'+path,method:data?'POST':'GET',data,timeout:/\/probe$/.test(path)?50000:15000,header:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},success(result){if(result.statusCode===401)clear();if(result.statusCode!==200)return reject(new Error(result.data&&result.data.error||'管理请求失败'));resolve(result.data);},fail(){reject(new Error('无法连接管理服务，请稍后重试'));}}));}
async function login(wx,username,password){const value=await request(wx,'login',{username,password});token=value.token;return value;}
module.exports={BASE,request,login,clear};
