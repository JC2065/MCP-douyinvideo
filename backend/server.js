const {loadConfig}=require('./config');
const {createPool,probe}=require('./database');
const {createHttpServer}=require('./http-server');
const {saveVideoRun}=require('./video-run-store');

async function start(env=process.env){
 const config=loadConfig(env),pool=createPool(config),server=createHttpServer({checkReady:()=>probe(pool),saveVideoRun:(userId,run)=>saveVideoRun(pool,userId,run)});
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(config.port,config.host,resolve);});
 process.stdout.write(JSON.stringify({event:'server_started',environment:config.environment,host:config.host,port:config.port})+'\n');
 let closing=false;
 const close=async signal=>{if(closing)return;closing=true;process.stdout.write(JSON.stringify({event:'server_stopping',signal})+'\n');const timer=setTimeout(()=>process.exitCode=1,config.shutdownTimeoutMs);timer.unref();await new Promise(resolve=>server.close(resolve));await pool.end();clearTimeout(timer);};
 process.once('SIGTERM',()=>void close('SIGTERM'));process.once('SIGINT',()=>void close('SIGINT'));
 return {server,pool,config,close};
}

if(require.main===module)start().catch(error=>{process.stderr.write(JSON.stringify({event:'server_failed',message:error.message})+'\n');process.exitCode=1;});
module.exports={start};
