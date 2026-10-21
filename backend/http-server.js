const http=require('node:http');
const {randomUUID}=require('node:crypto');

const REQUEST_ID=/^[A-Za-z0-9._:-]{1,100}$/;
function send(response,status,body,requestId){
 const data=Buffer.from(JSON.stringify(body));
 response.writeHead(status,{'content-type':'application/json; charset=utf-8','content-length':data.length,'x-content-type-options':'nosniff','cache-control':'no-store','x-request-id':requestId});response.end(data);
}
function createHttpServer(options={}){
 const checkReady=options.checkReady||(async()=>{}),saveVideoRun=options.saveVideoRun;const makeId=options.makeId||randomUUID;const clock=options.clock||(()=>new Date().toISOString());
 return http.createServer(async(request,response)=>{
  const supplied=request.headers['x-request-id'];const requestId=typeof supplied==='string'&&REQUEST_ID.test(supplied)?supplied:makeId();
  const path=new URL(request.url,'http://service').pathname;
  if(request.method==='GET'&&path==='/health/live')return send(response,200,{status:'ok',service:'youai-api',time:clock()},requestId);
  if(request.method==='GET'&&path==='/health/ready'){
   try{await checkReady();return send(response,200,{status:'ready',service:'youai-api',time:clock()},requestId);}
   catch(_){return send(response,503,{status:'unavailable',error:{code:'DEPENDENCY_UNAVAILABLE',message:'服务依赖尚未就绪',requestId}},requestId);}
  }
  if(request.method==='POST'&&path==='/api/v1/video-runs'&&saveVideoRun){let raw='';for await(const chunk of request){raw+=chunk;if(Buffer.byteLength(raw)>262144)return send(response,413,{error:{code:'PAYLOAD_TOO_LARGE',message:'资产清单过大',requestId}},requestId);}try{const body=JSON.parse(raw),saved=await saveVideoRun(String(request.headers['x-youai-user-id']||''),body);return send(response,201,saved,requestId);}catch(_){return send(response,422,{error:{code:'VIDEO_RUN_INVALID',message:'视频资产保存失败',requestId}},requestId);}}
  send(response,404,{error:{code:'NOT_FOUND',message:'接口不存在',requestId}},requestId);
 });
}

module.exports={createHttpServer,REQUEST_ID};
