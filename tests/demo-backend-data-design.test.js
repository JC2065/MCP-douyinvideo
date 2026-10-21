const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const model=JSON.parse(fs.readFileSync(path.join(root,'docs/demo-backend-data-model.json'),'utf8'));
const design=fs.readFileSync(path.join(root,'docs/demo-backend-data-design.md'),'utf8');
const read=file=>fs.readFileSync(path.join(root,file),'utf8');

test('Demo 后端数据模型覆盖账号、核心内容、设置、工具和同步',()=>{
 const names=model.tables.map(table=>table.name),unique=new Set(names);
 assert.equal(unique.size,names.length);
 for(const name of ['users','user_identities','sessions','ideas','projects','project_versions','learning_cases','learning_records','creator_profiles','user_settings','assets','tool_runs','credential_refs','change_log','idempotency_keys'])assert.ok(unique.has(name),name);
 for(const table of model.tables){const fieldCount=table.fields.includes('common user columns')?table.fields.length-1+model.conventions.userRecordColumns.length:table.fields.length;assert.match(table.phase,/^[A-D]$/);assert.ok(fieldCount>=4,table.name);assert.ok(table.purpose,table.name);}
 assert.deepEqual(model.firstMigration,['users','user_identities','sessions','ideas','change_log','idempotency_keys']);
});

test('当前所有本机存储都有明确迁移、延后、重录或仅本机策略',()=>{
 const keys=new Set(model.localStorage.map(item=>item.key));
 for(const [file,key] of [['utils/store.js','youai-demo-v1'],['utils/creator-preferences.js','youai-creator-preferences-v1'],['utils/analysis-presets.js','youai-analysis-preferences-v1'],['utils/ai-config.js','youai-ai-config-v1'],['utils/tool-interfaces.js','youai-tool-interfaces-v1'],['utils/video-history.js','youai-video-history'],['components/app-navigation/index.js','youai-nav-ball']]){
  assert.ok(read(file).includes(key),file);assert.ok(keys.has(key),key);
 }
 for(const item of model.localStorage){assert.ok(item.strategy);assert.ok(Object.keys(item.mappings).length,item.key);}
});

test('延期业务不会进入首批数据库，密钥不能随内容自动上传',()=>{
 const first=model.firstMigration.join(' '),allTables=model.tables.map(table=>table.name).join(' ');
 for(const field of ['tasks','budget','earnings','merchant','orders','payments']){assert.ok(model.deferredDemoFields.includes(field));assert.ok(!first.includes(field));assert.ok(!allTables.includes(field));}
 const ai=model.localStorage.find(item=>item.key==='youai-ai-config-v1');const tools=model.localStorage.find(item=>item.key==='youai-tool-interfaces-v1');
 assert.match(ai.mappings['keys + custom keys'],/require_reentry/);assert.match(tools.mappings.tokens,/require_reentry/);
 assert.match(design,/明文个人密钥不随内容迁移/);
});

test('方案说明 Demo 映射、项目版本、同步冲突和分批实现',()=>{
 for(const text of ['Demo 数据不能整包上传','projects` 和 `project_versions','历史版本只追加','UUIDv7','期望版本','change_log','第一批迁移只创建','双写观察','两个账号、小程序和 Web'])assert.ok(design.includes(text),text);
 for(const file of ['docs/backend-data-platform.md','docs/development-master-plan.md'])assert.ok(read(file).includes('demo-backend-data-design.md'),file);
 assert.ok(read('README.md').includes('demo-backend-data-design.md'));
});
