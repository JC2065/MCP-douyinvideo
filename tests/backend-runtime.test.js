const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const {loadConfig}=require('../backend/config');
const {createHttpServer}=require('../backend/http-server');
const migrations=require('../backend/migration-runner');
const root=path.resolve(__dirname,'..');

function request(server,url,headers={}){return new Promise((resolve,reject)=>{const req=http.request({host:'127.0.0.1',port:server.address().port,path:url,headers},response=>{let body='';response.setEncoding('utf8');response.on('data',chunk=>body+=chunk);response.on('end',()=>resolve({status:response.statusCode,headers:response.headers,body:JSON.parse(body)}));});req.on('error',reject);req.end();});}
function post(server,url,body,headers={}){return new Promise((resolve,reject)=>{const data=JSON.stringify(body),req=http.request({host:'127.0.0.1',port:server.address().port,path:url,method:'POST',headers:{'content-type':'application/json','content-length':Buffer.byteLength(data),...headers}},response=>{let raw='';response.setEncoding('utf8');response.on('data',chunk=>raw+=chunk);response.on('end',()=>resolve({status:response.statusCode,body:JSON.parse(raw)}));});req.on('error',reject);req.end(data);});}
async function running(options,callback){const server=createHttpServer(options);await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));try{return await callback(server);}finally{await new Promise(resolve=>server.close(resolve));}}

test('环境配置限制端口、数据库 TLS 和生产安全基线',()=>{
 const local=loadConfig({APP_ENV:'local',DATABASE_URL:'postgres://local/db',PORT:'9000',DATABASE_POOL_MAX:'5'});
 assert.equal(local.port,9000);assert.equal(local.databasePoolMax,5);assert.equal(local.databaseSsl,false);
 assert.throws(()=>loadConfig({APP_ENV:'production',DATABASE_URL:'postgres://cloud/db',DATABASE_SSL_MODE:'disable'}),/verify-full/);
 assert.throws(()=>loadConfig({APP_ENV:'staging',DATABASE_URL:'postgres://cloud/db',DATABASE_SSL_MODE:'verify-full'}),/DATABASE_CA/);
 const cloud=loadConfig({APP_ENV:'production',DATABASE_URL:'postgres://cloud/db',DATABASE_SSL_MODE:'verify-full',DATABASE_CA:'CERT\\nLINE'});
 assert.equal(cloud.databaseSsl.rejectUnauthorized,true);assert.match(cloud.databaseSsl.ca,/\n/);
});

test('存活和就绪检查返回请求标识且不泄露数据库错误',async()=>{
 await running({clock:()=> '2026-10-10T00:00:00.000Z',makeId:()=> 'generated-id',checkReady:async()=>{}},async server=>{
  const live=await request(server,'/health/live',{'x-request-id':'client-123'});assert.equal(live.status,200);assert.equal(live.headers['x-request-id'],'client-123');assert.equal(live.body.status,'ok');
  const ready=await request(server,'/health/ready');assert.equal(ready.status,200);assert.equal(ready.body.status,'ready');
  const missing=await request(server,'/private');assert.equal(missing.status,404);assert.equal(missing.body.error.requestId,'generated-id');
 });
 await running({makeId:()=> 'failed-id',checkReady:async()=>{throw Error('password=secret host=internal');}},async server=>{
  const result=await request(server,'/health/ready');assert.equal(result.status,503);assert.equal(result.body.error.code,'DEPENDENCY_UNAVAILABLE');assert.doesNotMatch(JSON.stringify(result.body),/secret|internal/);
 });
});
test('视频资产清单通过内部用户边界写入且错误不泄露数据库信息',async()=>{let captured;await running({saveVideoRun:async(user,run)=>{captured={user,run};return {status:'saved',generationJobId:'job-db'};}},async server=>{const result=await post(server,'/api/v1/video-runs',{runId:'run-1'},{'x-youai-user-id':'00000000-0000-4000-8000-000000000001'});assert.equal(result.status,201);assert.equal(result.body.status,'saved');assert.equal(captured.run.runId,'run-1');});await running({saveVideoRun:async()=>{throw Error('password=secret database=internal');}},async server=>{const result=await post(server,'/api/v1/video-runs',{runId:'bad'},{'x-youai-user-id':'bad'});assert.equal(result.status,422);assert.doesNotMatch(JSON.stringify(result.body),/secret|internal/);});});

test('迁移成对、顺序稳定且首批身份数据包含隔离、索引和回滚',()=>{
 const list=migrations.discover();assert.deepEqual(list.map(item=>item.version),['001_identity_and_ideas','002_video_asset_pipeline','003_reference_video_mode']);const [{up,down}]=list;assert.match(list[2].up,/reference-video/);assert.match(list[2].down,/visual-style/);
 for(const table of ['users','user_identities','sessions','ideas','change_log','idempotency_keys']){assert.match(up,new RegExp(`create table ${table}\\b`));assert.match(down,new RegExp(`drop table if exists ${table}\\b`));}
 for(const text of ['unique(provider,subject)','refresh_token_hash text not null unique','ideas_user_updated_idx','change_log_user_cursor_idx','primary key(user_id,resource,action,key)','enable row level security','force row level security',"current_setting('app.user_id'"])assert.ok(up.includes(text),text);
 assert.doesNotMatch(up,/\b(budget|earnings|merchant|orders|payments)\b/i);
});

test('容器、运行脚本和云迁移文档形成可部署基座',()=>{
 const pkg=JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8')),docker=fs.readFileSync(path.join(root,'backend/Dockerfile'),'utf8'),compose=fs.readFileSync(path.join(root,'compose.backend.yml'),'utf8'),doc=fs.readFileSync(path.join(root,'docs/cloud-runtime-design.md'),'utf8');
 assert.equal(pkg.dependencies.pg,'8.23.1');assert.equal(pkg.scripts['backend:migrate'],'node backend/migrate.js up');assert.match(pkg.packageManager,/^pnpm@/);
 for(const text of ['USER node','backend/server.js','--frozen-lockfile'])assert.ok(docker.includes(text),text);
 for(const text of ['postgres:16-alpine','condition: service_healthy','127.0.0.1:8080:8080','restart: unless-stopped','/health/ready'])assert.ok(compose.includes(text),text);
 assert.equal((compose.match(/restart: unless-stopped/g)||[]).length,2);
 for(const text of ['尚未迁入云环境','托管 PostgreSQL','RPO 不超过 15 分钟','RTO 不超过 4 小时','微信小程序合法域名','双账号隔离'])assert.ok(doc.includes(text),text);
});
