const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const pipeline=require('../backend/video-pipeline');
const migrations=require('../backend/migration-runner');
const root=path.resolve(__dirname,'..');

test('视频资产迁移覆盖可复用资产、分析、分镜、生成、血缘与反馈',()=>{
 const item=migrations.discover().find(entry=>entry.version==='002_video_asset_pipeline');assert.ok(item);
 for(const table of ['media_assets','reference_analyses','video_shots','storyboards','generation_jobs','video_artifacts','creation_feedback']){
  assert.match(item.up,new RegExp(`create table ${table}\\b`));assert.match(item.down,new RegExp(`drop table if exists ${table}\\b`));
 }
 for(const marker of ['unique(user_id,sha256)','reference_mode','estimated_cost_cny','actual_cost_cny','request_snapshot','lineage','enable row level security','force row level security',"current_setting(''app.user_id''"])assert.ok(item.up.includes(marker),marker);
});

test('引用模式、生成状态和成本遵循审核后逐镜头生成契约',()=>{
 assert.deepEqual(pipeline.REFERENCE_MODES,['reference-video','content-structure','visual-style','same-topic']);
 assert.equal(pipeline.transitionJob('draft','queued'),'queued');assert.equal(pipeline.transitionJob('failed','queued'),'queued');
 assert.throws(()=>pipeline.transitionJob('succeeded','running'),/INVALID_JOB_TRANSITION/);
 assert.deepEqual(pipeline.normalizeCost({estimatedCny:18.12345,actualCny:20}),{estimatedCny:18.1234,actualCny:20,currency:'CNY'});
 assert.throws(()=>pipeline.normalizeCost({estimatedCny:-1}),/INVALID_COST/);
});

test('资产哈希可稳定去重，请求快照去密钥且产物必须保留来源',()=>{
 assert.equal(pipeline.stableHash(Buffer.from('same')),pipeline.stableHash(Buffer.from('same')));
 const safe=pipeline.sanitizeProviderRequest({prompt:'画面',apiKey:'x',nested:{Authorization:'Bearer x',model:'wan'}});
 assert.deepEqual(safe,{prompt:'画面',nested:{model:'wan'}});
 assert.deepEqual(pipeline.artifactLineage({sourceAssetIds:['a','a','b'],analysisId:'analysis'}).sourceAssetIds,['a','b']);
 assert.throws(()=>pipeline.artifactLineage(),/SOURCE_ASSET_REQUIRED/);
});

test('资产契约文档明确阶段、保留边界、显式反馈和成本',()=>{
 const text=fs.readFileSync(path.join(root,'docs/video-asset-pipeline.md'),'utf8');
 for(const marker of ['链接已识别','媒体已获取','分析成功','reference-video','content-structure','visual-style','same-topic','显式反馈','实际成本','API Key','临时抽帧'])assert.ok(text.includes(marker),marker);
});
