// 返回兜底提醒：本该返回上一页却走了兜底（回首页 / 换页）时，在开发版和体验版弹窗提示，方便发现问题后截图反馈。
// 正式版不打扰用户，只记录到本机（最近 20 条，key: youai-back-fallback-log）。
const LOG='youai-back-fallback-log';
function env(api){try{return api.getAccountInfoSync().miniProgram.envVersion||'release';}catch(_){return 'release';}}
function stack(){try{return typeof getCurrentPages==='function'?getCurrentPages().map(p=>p.route):[];}catch(_){return [];}}
function report(api,{from,reason,action},then){
 const pages=stack(),row={at:Date.now(),from:from||pages[pages.length-1]||'',reason:String(reason||''),action:action||'回到首页',stack:pages};
 try{const old=api.getStorageSync(LOG);api.setStorageSync(LOG,[row,...(Array.isArray(old)?old:[])].slice(0,20));}catch(_){}
 const go=()=>{if(typeof then==='function')then();};
 if(env(api)==='release'||typeof api.showModal!=='function')return go();
 api.showModal({title:'返回走了兜底（测试提示）',content:`本该返回上一页，但${row.reason}，已改为${row.action}。\n页面：${row.from||'未知'}\n页面栈：${pages.length} 层${pages.length?'（'+pages.join(' > ')+'）':''}\n请截图发给 Claude 排查。正式版不会弹出此提示。`,showCancel:false,confirmText:'知道了',complete:go});
 return row;}
module.exports={LOG,env,report};
