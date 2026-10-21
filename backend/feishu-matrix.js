const field=(name,type=1,extra={})=>({name,type,...extra});
const tables=[
 {id:'works',role:'management',name:'作品总表',fields:[field('作品ID'),field('标题'),field('用户业务ID'),field('来源'),field('阶段'),field('成片资产ID'),field('方案版本',2),field('用户反馈')]},
 {id:'plans',role:'management',name:'创作方案',fields:[field('方案ID'),field('作品ID'),field('分析版本'),field('沟通答案'),field('文案'),field('分镜'),field('提示词'),field('版本',2),field('确认时间',5),field('关联作品',18,{target:'works'})]},
 {id:'pools',role:'management',name:'存储资源池',fields:[field('资源池ID'),field('组织'),field('套餐'),field('总容量字节',2),field('已用容量字节',2),field('API总额度',2),field('API不限总次数',7),field('API已用次数',2),field('额度有效期',5),field('核验时间',5),field('告警状态')]},
 {id:'feedback',role:'management',name:'成本与反馈',fields:[field('反馈ID'),field('作品ID'),field('模型'),field('预估费用元',2),field('实际费用元',2),field('费用已核实',7),field('用户评价'),field('修改原因'),field('采纳项'),field('关联作品',18,{target:'works'})]},
 {id:'assets',role:'archive',name:'资产目录',fields:[field('资产ID'),field('作品ID'),field('SHA256'),field('类型'),field('大小字节',2),field('来源资产ID'),field('资源池ID'),field('存储文件标识'),field('引用次数',2),field('校验状态'),field('归档时间',5)]},
 {id:'archive_jobs',role:'archive',name:'归档与恢复任务',fields:[field('任务ID'),field('资产ID'),field('源资源池ID'),field('目标资源池ID'),field('状态'),field('校验结果'),field('失败原因'),field('重试次数',2),field('下次重试时间',5),field('完成时间',5),field('关联资产',18,{target:'assets'})]},
];
function validateConfig(config,roles=['management','archive']){
 if(!config||typeof config!=='object')throw Error('配置格式无效');
 if(!roles.length||roles.some(role=>!['management','archive'].includes(role)))throw Error('组织选择无效');
 for(const role of roles){
  const c=config[role];if(!c||!/^cli_[a-zA-Z0-9]+$/.test(c.appId||'')||typeof c.appSecret!=='string'||c.appSecret.length<8||!/^[a-zA-Z0-9]+$/.test(c.baseToken||'')||[c.appId,c.appSecret,c.baseToken].some(v=>/REPLACE|填写/i.test(v)))throw Error(`${role} 缺少有效 App ID、App Secret 或多维表格 baseToken`);
 }
 if(roles.length===2&&config.management.appId===config.archive.appId)throw Error('两个组织必须使用独立应用');
 return config;
}
class FeishuClient{
 constructor(config,{fetchImpl=fetch,now=Date.now}={}){this.config=config;this.fetch=fetchImpl;this.now=now;this.token=null;this.expires=0;}
 async request(method,path,body){
  if(!this.token||this.now()>=this.expires){
   let r;try{r=await this.fetch('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({app_id:this.config.appId,app_secret:this.config.appSecret}),signal:AbortSignal.timeout(30000)});}catch{throw Error('飞书鉴权网络连接失败');}
   let d;try{d=await r.json();}catch{throw Error('飞书鉴权响应格式无效');}if(!r.ok||d.code!==0||!d.tenant_access_token)throw Error(`飞书鉴权失败（HTTP ${r.status}，code ${d.code??'unknown'}）`);
   this.token=d.tenant_access_token;this.expires=this.now()+Math.max(0,Number(d.expire||0)-60)*1000;
  }
  let r;try{r=await this.fetch('https://open.feishu.cn/open-apis'+path,{method,headers:{Authorization:'Bearer '+this.token,'Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(30000)});}catch{throw Error(`飞书接口网络失败：${method} ${path.split('?')[0]}`);}
  let d;try{d=await r.json();}catch{throw Error('飞书接口响应格式无效');}if(!r.ok||d.code!==0)throw Error(`飞书接口失败：${method} ${path.split('?')[0]}（HTTP ${r.status}，code ${d.code??'unknown'}）；检查权限/频率后重跑`);
  return d.data||{};
 }
 async list(path){const rows=[];let token='';const seen=new Set();do{const data=await this.request('GET',path+'?page_size=100'+(token?'&page_token='+encodeURIComponent(token):''));rows.push(...(data.items||[]));if(!data.has_more)break;token=data.page_token;if(!token||seen.has(token))throw Error('飞书分页状态异常');seen.add(token);}while(token);return rows;}
}
async function bootstrap(config,{roles=['management','archive'],layout='split',clientFactory=c=>new FeishuClient(c),checkpoint=async()=>{},pause=()=>new Promise(r=>setTimeout(r,250))}={}){
 if(!['split','unified'].includes(layout)||layout==='unified'&&roles.length!==1)throw Error('统一六表必须选择一个组织');
 validateConfig(config,roles);const output={version:1,roles:{}};
 for(const role of roles){
  const client=clientFactory(config[role]),prefix='/bitable/v1/apps/'+config[role].baseToken;
  const existing=await client.list(prefix+'/tables'),mapping={};output.roles[role]={baseToken:config[role].baseToken,tables:mapping};
  const selected=tables.filter(t=>layout==='unified'||t.role===role);
  for(const table of selected){
   const matches=existing.filter(t=>t.name===table.name);if(matches.length>1)throw Error(`存在重复表：${table.name}，请先人工确认`);
   let id=matches[0]?.table_id;
   if(!id){const result=await client.request('POST',prefix+'/tables',{table:{name:table.name,default_view_name:'全部记录',fields:[{field_name:table.fields[0].name,type:table.fields[0].type}]}});id=result.table_id;if(!id)throw Error(`创建表未返回ID：${table.name}`);await pause();}
   mapping[table.id]={id,name:table.name,fields:{}};await checkpoint(output);
  }
  for(const table of selected){
   const entry=mapping[table.id],path=prefix+'/tables/'+entry.id+'/fields',fields=await client.list(path);
   for(const f of table.fields){
    const matches=fields.filter(x=>x.field_name===f.name);if(matches.length>1)throw Error(`字段重名：${table.name}/${f.name}`);
    let existing=matches[0];
    if(existing&&existing.type!==f.type)throw Error(`字段类型冲突：${table.name}/${f.name}`);
    if(existing&&f.target&&existing.property?.table_id!==mapping[f.target].id)throw Error(`关联目标冲突：${table.name}/${f.name}`);
    if(!existing){const body={field_name:f.name,type:f.type,...(f.target?{property:{table_id:mapping[f.target].id,multiple:true}}:{})};const result=await client.request('POST',path,body);existing=result.field;if(!existing?.field_id)throw Error(`创建字段未返回ID：${table.name}/${f.name}`);await pause();}
    entry.fields[f.name]=existing.field_id;await checkpoint(output);
   }
  }
 }
 return output;
}
module.exports={tables,validateConfig,FeishuClient,bootstrap};
