const ENVIRONMENTS=new Set(['local','test','staging','production']);

function integer(value,fallback,name,min,max){
 const number=value==null||value===''?fallback:Number(value);
 if(!Number.isInteger(number)||number<min||number>max)throw Error(`${name} 必须是 ${min}-${max} 的整数`);
 return number;
}

function loadConfig(env=process.env,options={}){
 const environment=env.APP_ENV||'local';
 if(!ENVIRONMENTS.has(environment))throw Error('APP_ENV 必须是 local、test、staging 或 production');
 const databaseUrl=String(env.DATABASE_URL||'').trim();
 if(!databaseUrl&&!options.allowMissingDatabase)throw Error('缺少 DATABASE_URL');
 const sslMode=env.DATABASE_SSL_MODE||'disable';
 if(!['disable','require','verify-full'].includes(sslMode))throw Error('DATABASE_SSL_MODE 必须是 disable、require 或 verify-full');
 if(['staging','production'].includes(environment)&&sslMode!=='verify-full')throw Error('staging 和 production 必须使用 DATABASE_SSL_MODE=verify-full');
 const databaseCa=String(env.DATABASE_CA||'').replace(/\\n/g,'\n');
 if(sslMode==='verify-full'&&!databaseCa)throw Error('verify-full 需要 DATABASE_CA');
 return Object.freeze({
  environment,host:env.HOST||'127.0.0.1',port:integer(env.PORT,8080,'PORT',1,65535),databaseUrl,
  databaseSsl:sslMode==='disable'?false:{rejectUnauthorized:sslMode==='verify-full',...(databaseCa?{ca:databaseCa}:{})},
  databasePoolMax:integer(env.DATABASE_POOL_MAX,10,'DATABASE_POOL_MAX',1,50),
  databaseTimeoutMs:integer(env.DATABASE_TIMEOUT_MS,5000,'DATABASE_TIMEOUT_MS',500,30000),
  shutdownTimeoutMs:integer(env.SHUTDOWN_TIMEOUT_MS,10000,'SHUTDOWN_TIMEOUT_MS',1000,60000)
 });
}

module.exports={loadConfig,ENVIRONMENTS};
