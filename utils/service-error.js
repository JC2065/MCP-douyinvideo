function network(error){
 const raw=String(error&&error.errMsg||error&&error.message||'未返回错误详情')
  .replace(/https?:\/\/[^\s，。]+/gi,'[服务地址]')
  .replace(/Bearer\s+\S+/gi,'Bearer [已隐藏]')
  .replace(/((?:token|secret|api[_-]?key|authorization)\s*[=:]\s*)[^\s,;]+/gi,'$1[已隐藏]').slice(0,200);
 let hint='暂时无法连接服务，请切换网络后重试';
 if(/domain|合法域名/i.test(raw))hint='请求域名未获微信允许，请核对 request 合法域名配置';
 else if(/privacy|scope|隐私/i.test(raw))hint='微信隐私授权未完成，请查看隐私指引并重试';
 else if(/login|登录|session|会话/i.test(raw))hint='登录会话未就绪，请重新登录后重试';
 else if(/timeout|timed out|超时/i.test(raw))hint='服务响应超时，请稍后重试';
 else if(/ssl|tls|certificate|证书/i.test(raw))hint='HTTPS连接校验失败，请检查设备时间和网络';
 const value=Error(hint+'。错误详情：'+raw);value.transportFailure=true;return value;
}
function response(result){
 const status=Number(result&&result.statusCode)||0;
 const message=result&&result.data&&typeof result.data.error==='string'?result.data.error:'服务返回异常';
 return Error(message+'（HTTP '+status+'）');
}
module.exports={network,response};
