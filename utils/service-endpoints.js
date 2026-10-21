// One reviewed API contract for native clients and the domestic gateway.
const ORIGIN='https://youai888.top';
const BASE=ORIGIN+'/youai';
const LOCAL_DEBUG_KEY='youai.debug.local-backend';
function videoBase(api){
 try{
  // Only the simulator may opt into a local backend; release clients stay on HTTPS.
  if(api&&api.getSystemInfoSync().platform==='devtools'&&api.getStorageSync(LOCAL_DEBUG_KEY)===true)return 'http://127.0.0.1:8765';
 }catch(_){}
 return BASE;
}
module.exports={ORIGIN,BASE,LOCAL_DEBUG_KEY,videoBase};
