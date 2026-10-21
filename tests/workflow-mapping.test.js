const test=require('node:test'),assert=require('node:assert/strict');const D=require('../web/admin-workflows/model'),M=require('../web/admin-workflows/mapping');
const complete=p=>{while(M.current(p))M.advance(p,{accepted:true,budgetConfirmed:true,actionId:p.run.id+'-'+p.run.index});};
test('三阶段传递已确认快照，直接产出与先拆解均成立',()=>{
 for(const analyze of [false,true]){const p=M.project();assert.throws(()=>M.start(p,M.release(D.create('production'))),/简报/);M.start(p,M.release(D.create('requirements')));complete(p);assert.ok(p.brief);if(analyze){M.start(p,M.release(D.create('analysis')));complete(p);assert.ok(p.analysis);}M.start(p,M.release(D.create('production')));assert.equal(p.run.input.brief.topic,p.brief.topic);assert.equal(Boolean(p.run.input.analysis),analyze);complete(p);assert.ok(p.work);assert.equal(p.archive,'pending');}
});
test('独立拆解不伪造需求，确认和费用不能跳过',()=>{
 const p=M.project();M.start(p,M.release(D.create('analysis')));while(M.current(p).capability!=='review')M.advance(p);assert.throws(()=>M.advance(p),/明确确认/);M.advance(p,{accepted:true});assert.equal(p.brief,null);assert.ok(p.analysis);assert.throws(()=>M.start(p,M.release(D.create('production'))),/简报/);
 const q=M.project();M.start(q,M.release(D.create('requirements')));complete(q);M.start(q,M.release(D.create('production')));while(M.current(q).capability!=='generate')M.advance(q,{accepted:true});assert.throws(()=>M.advance(q),/费用上限/);
});
test('任务固定版本，失败不推进，重试与幂等不重复完成',()=>{
 const p=M.project(),flow=D.create('requirements'),bundle=M.release(flow,'v1');M.start(p,bundle);bundle.flow.steps[0].title='changed';assert.notEqual(M.current(p).title,'changed');assert.throws(()=>M.start(p,bundle),/当前阶段/);M.fail(p);assert.throws(()=>M.advance(p),/重试/);assert.equal(p.run.index,0);M.retry(p);M.advance(p,{actionId:'once'});M.advance(p,{actionId:'once'});assert.equal(p.run.index,1);assert.equal(p.run.revision,'v1');
});
test('不兼容组件与远程代码不能进入共享流程',()=>{
 const p=M.project(),bundle=M.release(D.create('analysis'));bundle.componentsVersion=2;assert.throws(()=>M.start(p,bundle),/不支持/);const flow=D.create('analysis');flow.steps[1].code='eval';assert.throws(()=>M.release(flow));for(const flow of Object.values(D.defaults))for(const step of flow)assert.ok(M.components[step.capability]);
});
test('阶段最后一步重复回执不重复生成历史',()=>{const p=M.project();M.start(p,M.release(D.create('requirements')));while(M.current(p).capability!=='review')M.advance(p);M.advance(p,{accepted:true,actionId:'final'});M.advance(p,{accepted:true,actionId:'final'});assert.equal(p.history.length,1);});
test('文档声明设计边界并覆盖跨端恢复、权限及飞书补偿',()=>{const fs=require('fs'),doc=fs.readFileSync('docs/workflow-miniapp-mapping.md','utf8'),html=fs.readFileSync('web/admin-workflows/index.html','utf8');for(const field of ['尚未部署生产流程API','expectedRevision','Idempotency-Key','flow_snapshot','其他账号资源统一404','Outbox','未确认的私密对话不写飞书'])assert.ok(doc.includes(field),field);for(const file of ['mapping.js','mapping-ui.js'])assert.ok(html.includes(file));const bundle=M.release(D.create('requirements'));bundle.stage='analysis';assert.throws(()=>M.start(M.project(),bundle),/不支持/);});
