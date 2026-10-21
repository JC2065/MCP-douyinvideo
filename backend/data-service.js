const {randomUUID}=require('node:crypto');
const {CLIENT_TYPES,ENTITY_TYPES}=require('./contracts');

const FORBIDDEN_FIELDS=new Set([
 'id','type','userId','ownerId','version','createdAt','updatedAt','deletedAt',
 'merchantId','orderId','amount','budget','price','token','apiKey','secret','password'
]);

class DataError extends Error{
 constructor(code,message,status=400,details){
  super(message);this.name='DataError';this.code=code;this.status=status;
  if(details!==undefined)this.details=details;
 }
}

function copy(value){return value===undefined?undefined:JSON.parse(JSON.stringify(value));}
function plain(value){return value&&typeof value==='object'&&!Array.isArray(value);}

class DataService{
 constructor(options={}){
  this.clock=options.clock||(()=>new Date().toISOString());
  this.makeId=options.makeId||randomUUID;
  this.records=new Map();
  this.idempotency=new Map();
  this.changes=[];
  this.sequence=0;
 }

 context(value){
  if(!plain(value)||typeof value.userId!=='string'||!value.userId.trim())throw new DataError('UNAUTHENTICATED','需要有效登录会话',401);
  if(!CLIENT_TYPES.includes(value.client))throw new DataError('INVALID_CLIENT','不支持的客户端类型');
  return {userId:value.userId.trim(),client:value.client};
 }

 entity(type){
  if(!ENTITY_TYPES.includes(type))throw new DataError('INVALID_ENTITY','不支持的数据类型');
  return type;
 }

 payload(value){
  if(!plain(value))throw new DataError('INVALID_PAYLOAD','数据必须是对象');
  for(const field of Object.keys(value))if(FORBIDDEN_FIELDS.has(field))throw new DataError('RESERVED_FIELD',`字段 ${field} 不能由客户端写入`);
  let encoded;
  try{encoded=JSON.stringify(value);}catch(_){throw new DataError('INVALID_PAYLOAD','数据无法序列化');}
  if(encoded.length>256*1024)throw new DataError('PAYLOAD_TOO_LARGE','单条数据不能超过 256KB',413);
  return copy(value);
 }

 key(type,id){return `${type}:${id}`;}

 own(type,id,userId){
  const record=this.records.get(this.key(type,id));
  if(!record||record.userId!==userId||record.deletedAt)throw new DataError('NOT_FOUND','数据不存在',404);
  return record;
 }

 change(record,operation){
  const item={cursor:++this.sequence,userId:record.userId,entity:record.type,entityId:record.id,version:record.version,operation,updatedAt:record.updatedAt};
  this.changes.push(item);return item;
 }

 create(type,context,input,options={}){
  type=this.entity(type);const actor=this.context(context),data=this.payload(input);
  const idempotencyKey=String(options.idempotencyKey||'').trim();
  if(!idempotencyKey)throw new DataError('IDEMPOTENCY_REQUIRED','创建数据必须提供幂等键');
  const retryKey=`${actor.userId}:${type}:${idempotencyKey}`;
  const existingId=this.idempotency.get(retryKey);
  if(existingId)return copy(this.own(type,existingId,actor.userId));
  const id=this.makeId(),now=this.clock();
  const record={...data,id,type,userId:actor.userId,version:1,createdAt:now,updatedAt:now,deletedAt:null};
  this.records.set(this.key(type,id),record);this.idempotency.set(retryKey,id);this.change(record,'upsert');
  return copy(record);
 }

 get(type,context,id){
  type=this.entity(type);const actor=this.context(context);
  return copy(this.own(type,String(id),actor.userId));
 }

 list(type,context){
  type=this.entity(type);const actor=this.context(context);
  return [...this.records.values()].filter(item=>item.type===type&&item.userId===actor.userId&&!item.deletedAt).sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt)).map(copy);
 }

 update(type,context,id,input,options={}){
  type=this.entity(type);const actor=this.context(context),data=this.payload(input),record=this.own(type,String(id),actor.userId);
  const expected=Number(options.expectedVersion);
  if(!Number.isInteger(expected)||expected<1)throw new DataError('VERSION_REQUIRED','更新数据必须提供当前版本');
  if(record.version!==expected)throw new DataError('VERSION_CONFLICT','数据已在其他设备更新',409,{current:copy(record)});
  Object.assign(record,data,{version:record.version+1,updatedAt:this.clock()});this.change(record,'upsert');
  return copy(record);
 }

 remove(type,context,id,options={}){
  type=this.entity(type);const actor=this.context(context),record=this.own(type,String(id),actor.userId);
  const expected=Number(options.expectedVersion);
  if(!Number.isInteger(expected)||expected<1)throw new DataError('VERSION_REQUIRED','删除数据必须提供当前版本');
  if(record.version!==expected)throw new DataError('VERSION_CONFLICT','数据已在其他设备更新',409,{current:copy(record)});
  record.version+=1;record.updatedAt=this.clock();record.deletedAt=record.updatedAt;this.change(record,'delete');
  return {id:record.id,version:record.version,deletedAt:record.deletedAt};
 }

 pullChanges(context,cursor=0,limit=100){
  const actor=this.context(context);cursor=Number(cursor)||0;limit=Math.max(1,Math.min(500,Number(limit)||100));
  const visible=this.changes.filter(item=>item.userId===actor.userId&&item.cursor>cursor),changes=visible.slice(0,limit).map(copy);
  const hasMore=visible.length>changes.length;
  return {changes,nextCursor:hasMore?changes.at(-1).cursor:this.sequence,hasMore};
 }
}

module.exports={DataService,DataError,FORBIDDEN_FIELDS};
