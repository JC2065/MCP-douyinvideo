const test=require('node:test');
const assert=require('node:assert/strict');
const {DataService,DataError}=require('../backend/data-service');
const {CLIENT_TYPES,ENTITY_TYPES,API_ROUTES}=require('../backend/contracts');

function service(){let tick=0,id=0;return new DataService({clock:()=>`2026-10-10T00:00:${String(++tick).padStart(2,'0')}.000Z`,makeId:()=>`id-${++id}`});}
const mini={userId:'user-a',client:'wechat-mini'};
const web={userId:'user-a',client:'web'};
const app={userId:'user-a',client:'app'};
const other={userId:'user-b',client:'wechat-mini'};

test('微信小程序、网页端和 App 使用同一用户数据与统一契约',()=>{
 const db=service();
 const idea=db.create('ideas',mini,{text:'跨端灵感',tags:['生活']},{idempotencyKey:'idea-1'});
 assert.equal(db.get('ideas',web,idea.id).text,'跨端灵感');
 assert.equal(db.update('ideas',app,idea.id,{text:'App 修改'},{expectedVersion:1}).version,2);
 assert.equal(db.get('ideas',mini,idea.id).text,'App 修改');
 assert.deepEqual(CLIENT_TYPES,['wechat-mini','web','app']);
 for(const entity of ['ideas','projects','learning_records','user_settings','assets','tool_runs'])assert.ok(ENTITY_TYPES.includes(entity));
});

test('账号隔离隐藏其他用户数据，客户端不能伪造归属或金额字段',()=>{
 const db=service();const idea=db.create('ideas',mini,{text:'私有内容'},{idempotencyKey:'private'});
 assert.throws(()=>db.get('ideas',other,idea.id),error=>error instanceof DataError&&error.code==='NOT_FOUND'&&error.status===404);
 assert.deepEqual(db.list('ideas',other),[]);
 for(const field of ['id','version','createdAt','userId','ownerId','merchantId','amount','budget','token','apiKey'])assert.throws(()=>db.create('ideas',mini,{text:'x',[field]:'bad'},{idempotencyKey:field}),error=>error.code==='RESERVED_FIELD');
});

test('创建幂等、更新检测版本冲突、删除产生同步墓碑',()=>{
 const db=service();
 const first=db.create('projects',mini,{title:'第一条作品'},{idempotencyKey:'project-1'});
 const retry=db.create('projects',mini,{title:'重复请求不会覆盖'},{idempotencyKey:'project-1'});
 assert.deepEqual(retry,first);assert.equal(db.list('projects',mini).length,1);
 const updated=db.update('projects',web,first.id,{title:'网页修改'},{expectedVersion:1});
 assert.throws(()=>db.update('projects',mini,first.id,{title:'旧版本覆盖'},{expectedVersion:1}),error=>error.code==='VERSION_CONFLICT'&&error.status===409&&error.details.current.version===2);
 const deleted=db.remove('projects',app,first.id,{expectedVersion:updated.version});
 assert.equal(deleted.version,3);assert.throws(()=>db.get('projects',mini,first.id),/数据不存在/);
 const feed=db.pullChanges(mini,0);
 assert.deepEqual(feed.changes.map(item=>item.operation),['upsert','upsert','delete']);
 assert.equal(feed.nextCursor,3);assert.equal(feed.hasMore,false);
});

test('增量游标按账号隔离并支持分页，API 不包含商家和金额资源',()=>{
 const db=service();
 db.create('ideas',mini,{text:'a'},{idempotencyKey:'a'});
 db.create('ideas',other,{text:'b'},{idempotencyKey:'b'});
 db.create('learning_records',mini,{caseId:201,favorited:true},{idempotencyKey:'c'});
 const first=db.pullChanges(web,0,1);assert.equal(first.changes.length,1);assert.equal(first.hasMore,true);
 const second=db.pullChanges(app,first.nextCursor,10);assert.equal(second.changes.length,1);assert.equal(second.hasMore,false);
 const paths=API_ROUTES.map(([,path])=>path).join('\n');
 assert.doesNotMatch(paths,/\/(merchants|orders|payments|earnings|budgets)(?:\/|$)/);
 assert.ok(paths.includes('/api/v1/sync/operations'));
 assert.ok(paths.includes('/api/v1/projects/{id}/versions'));
 const caughtUp=db.pullChanges(other,2,10);assert.equal(caughtUp.changes.length,0);assert.equal(caughtUp.nextCursor,3);
});
