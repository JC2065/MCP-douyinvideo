const test=require('node:test'),assert=require('node:assert/strict'),errors=require('../utils/service-error');
test('network errors retain actionable cause but remove credentials and source URLs',()=>{
 for(const [raw,hint] of [['request:fail url not in domain list','合法域名'],['request:fail timeout','超时'],['request:fail api scope is not declared in the privacy agreement','隐私'],['无法连接登录服务','会话'],['request:fail ssl certificate error','HTTPS'],['request:fail socket is not connected','无法连接']]){
  const value=errors.network({errMsg:raw});assert.equal(value.transportFailure,true);assert.ok(value.message.includes(hint));assert.ok(value.message.includes(raw));
 }
 const value=errors.network({errMsg:'request:fail https://example.test/x?token=private Bearer secret key=unused api_key=private'});
 assert.ok(!value.message.includes('private'));assert.ok(!value.message.includes('Bearer secret'));assert.ok(!value.message.includes('example.test'));
 assert.ok(errors.network(null).message.includes('错误详情'));
});
test('HTTP failures accept empty or non-JSON responses without masking status',()=>{
 assert.match(errors.response({statusCode:502,data:'gateway error'}).message,/HTTP 502/);
 assert.match(errors.response({statusCode:422,data:{error:'短链失效'}}).message,/短链失效.*HTTP 422/);
 assert.match(errors.response({statusCode:503,data:null}).message,/HTTP 503/);
});
