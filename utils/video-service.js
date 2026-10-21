// Cloud debugging is the default; local simulator testing is an explicit opt-in.
const session=require('./video-session');
const config=require('./client-config');
const baseUrl=require('./service-endpoints').videoBase(typeof wx==='undefined'?null:wx);
const simulator=baseUrl.startsWith('http://127.0.0.1:');
module.exports={baseUrl,send:(api,options)=>session.send(api,baseUrl,{...options,header:{...options.header,'X-YOUAI-Client-Version':config.VERSION,'X-YOUAI-Config-Schema':'1'}}),downloadFile:(api,options)=>{
 if(simulator)return api.downloadFile(options);
 session.session(api,baseUrl).then(login=>api.downloadFile({...options,header:{...options.header,Authorization:'Bearer '+login.token}})).catch(error=>options.fail&&options.fail({errMsg:error.message}));
}};
