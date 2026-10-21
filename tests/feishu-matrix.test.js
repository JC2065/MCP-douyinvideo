const test=require('node:test'),assert=require('node:assert/strict'),{spawnSync}=require('node:child_process');
const {tables,bootstrap,validateConfig,FeishuClient}=require('../backend/feishu-matrix');
const config={management:{appId:'cli_management',appSecret:'private-management',baseToken:'baseManagement'},archive:{appId:'cli_archive',appSecret:'private-archive',baseToken:'baseArchive'}};
test('六表分工和关联仅在同一组织，预演无需凭据或网络',()=>{
 assert.doesNotThrow(()=>validateConfig({management:config.management},['management']));assert.throws(()=>validateConfig(config,['wrong']),/组织选择无效/);
 assert.equal(tables.length,6);assert.equal(tables.filter(t=>t.role==='management').length,4);
 for(const table of tables)for(const f of table.fields)if(f.target)assert.equal(tables.find(t=>t.id===f.target).role,table.role);
 const result=spawnSync(process.execPath,['scripts/setup-feishu-matrix.js'],{encoding:'utf8'});assert.equal(result.status,0);const data=JSON.parse(result.stdout);assert.equal(data.networkCalls,0);assert.equal(data.tables.length,6);
 assert.throws(()=>validateConfig(require('../docs/feishu-matrix-config.example.json')),/缺少有效/);
 assert.throws(()=>validateConfig({...config,archive:config.management}),/独立应用/);
});
test('建表重跑与中断恢复不重复创建，类型或关系冲突就停止',async()=>{
 const stores=new Map();let writes=0,checkpointCount=0,fail=true;
 function factory(c){if(!stores.has(c.baseToken))stores.set(c.baseToken,[]);const list=stores.get(c.baseToken);return {
  async list(path){const id=path.match(/tables\/([^/]+)\/fields/)?.[1];return id?list.find(t=>t.table_id===id).fields:list;},
  async request(method,path,body){assert.equal(method,'POST');writes++;
   if(body.table){assert.ok(body.table.fields?.length,'default_view_name requires fields');const row={name:body.table.name,table_id:'tbl'+list.length,fields:body.table.fields.map((f,i)=>({...f,field_id:'initial'+i}))};list.push(row);return {table_id:row.table_id};}
   if(fail&&body.field_name==='提示词'){fail=false;throw Error('simulated interruption');}
   const id=path.match(/tables\/([^/]+)\/fields/)[1],row={...body,field_id:'fld'+writes};list.find(t=>t.table_id===id).fields.push(row);return {field:row};
  }
 };}
 const options={clientFactory:factory,checkpoint:async state=>{checkpointCount++;assert.equal(JSON.stringify(state).includes('private-'),false);},pause:async()=>{}};
 await assert.rejects(bootstrap(config,options),/interruption/);const state=await bootstrap(config,options);const before=writes;await bootstrap(config,options);assert.equal(writes,before);assert.equal(Object.keys(state.roles.management.tables).length,4);assert.ok(checkpointCount>6);
 stores.get('baseManagement')[0].fields[0].type=2;await assert.rejects(bootstrap(config,options),/字段类型冲突/);
});
test('鉴权 token 缓存且错误不暴露服务端正文中的密钥',async()=>{
 let auth=0,now=0;const client=new FeishuClient(config.management,{now:()=>now,fetchImpl:async(url,options)=>{
  if(url.includes('/auth/')){auth++;return {ok:true,status:200,json:async()=>({code:0,tenant_access_token:'private-access',expire:7200})};}
  assert.equal(options.headers.Authorization,'Bearer private-access');return {ok:true,status:200,json:async()=>({code:0,data:{items:[]}})};
 }});await client.list('/bitable/v1/apps/base/tables');await client.list('/bitable/v1/apps/base/tables');assert.equal(auth,1);now=7200000;await client.list('/bitable/v1/apps/base/tables');assert.equal(auth,2);
 client.fetch=async()=>({ok:false,status:403,json:async()=>({code:999,msg:'private-management private-access'})});await assert.rejects(client.request('GET','/failure'),e=>e.message.includes('403')&&!e.message.includes('private-'));
});
test('统一布局只调用所选组织并创建完整六表与内部关系',async()=>{
 const rows=[];const client={async list(p){const id=p.match(/tables\/([^/]+)\/fields/)?.[1];return id?rows.find(r=>r.table_id===id).fields:rows;},async request(m,p,b){if(b.table){const row={name:b.table.name,table_id:'tbl'+rows.length,fields:b.table.fields.map((f,i)=>({...f,field_id:'first'+i}))};rows.push(row);return {table_id:row.table_id};}const id=p.match(/tables\/([^/]+)\/fields/)[1],row={...b,field_id:'field'+Math.random()};rows.find(r=>r.table_id===id).fields.push(row);return {field:row};}};
 const c={management:config.management};const result=await bootstrap(c,{roles:['management'],layout:'unified',clientFactory:()=>client,pause:async()=>{}});assert.equal(rows.length,6);assert.equal(Object.keys(result.roles.management.tables).length,6);const n=rows.reduce((n,r)=>n+r.fields.length,0);await bootstrap(c,{roles:['management'],layout:'unified',clientFactory:()=>client,pause:async()=>{}});assert.equal(rows.reduce((n,r)=>n+r.fields.length,0),n);assert.equal(rows.find(r=>r.name==='归档与恢复任务').fields.find(f=>f.field_name==='关联资产').property.table_id,rows.find(r=>r.name==='资产目录').table_id);
 await assert.rejects(bootstrap(config,{layout:'unified'}),/选择一个组织/);
});
