(function(root,factory){const value=factory(typeof module==='object'&&module.exports?require('./model'):root.WorkflowDesign);if(typeof module==='object'&&module.exports)module.exports=value;else root.WorkflowMapping=value;})(typeof globalThis!=='undefined'?globalThis:this,function(D){
 const clone=D.clone;
 const components={input:'素材与信息表单',skill:'AI协作与结果编辑',review:'确认卡',evidence:'视频证据卡',generate:'生成任务进度',package:'作品预览编辑',archive:'资产回执'};
 const contracts={
  requirements:{entry:'我想记 / 和TA聊 / 看热点 / 一句话生成作品',input:'source_ref、用户想法、已有偏好',output:'brief_snapshot：主题、受众、平台、时长、风格、交付清单',next:'确认后选择直接创作，或补充参考视频进入拆解'},
  analysis:{entry:'拆学 → 拆一条视频 / 创作 → 参考一条视频',input:'asset_ref、模板版本、可选 brief_snapshot',output:'analysis_snapshot：证据、结构、可复用方法、原创方向',next:'有简报则进入产出；独立拆解先保存，再补充创作需求'},
  production:{entry:'已确认需求 / 已确认拆解 → 用于创作',input:'brief_snapshot、可选 analysis_snapshot、素材引用',output:'work_version：文字、图片、视频及来源；archive_event',next:'保存到我的资产；飞书归档异步执行，不阻塞作品保存'}
 };
 function release(flow,revision='preview-v1'){
  const errors=D.validate(flow);if(errors.length)throw Error(errors[0]);
  return {revision,stage:flow.stage,flow:clone(flow),componentsVersion:1,scope:flow.mode==='custom'?'user':'global',execution:'design-only'};
 }
 function project(){return {id:'project-preview',brief:null,analysis:null,work:null,run:null,history:[],receipts:{},archive:'not_requested'};}
 function start(p,bundle){
  if(p.run&&p.run.status==='running')throw Error('请先完成或结束当前阶段');
  if(bundle.stage==='production'&&!p.brief)throw Error('请先确认需求简报');
  const errors=D.validate(bundle.flow);if(errors.length||bundle.stage!==bundle.flow.stage||bundle.componentsVersion!==1)throw Error('客户端不支持该流程，请保留当前版本');
  p.run={stage:bundle.stage,revision:bundle.revision,flow:clone(bundle.flow),input:{brief:clone(p.brief),analysis:clone(p.analysis)},index:0,status:'running',outputs:[],id:'run-'+(p.history.length+1)};
  return clone(p.run);
 }
 function current(p){return p.run&&p.run.status==='running'?clone(p.run.flow.steps[p.run.index]):null;}
 function advance(p,{accepted=false,budgetConfirmed=false,actionId}={}){
  const r=p.run;if(!r)throw Error('没有运行中的阶段');
  const key=r.id+':'+actionId;if(actionId&&p.receipts[key])return clone(p.receipts[key]);
  if(r.status!=='running')throw Error('没有运行中的阶段');
  if(r.error)throw Error('请先重试失败步骤');
  const step=current(p);if(step.capability==='review'&&!accepted)throw Error('需要用户明确确认');
  if(step.capability==='generate'&&!budgetConfirmed)throw Error('需要确认生成方案与费用上限');
  const result={stepId:step.id,component:components[step.capability],status:'confirmed',example:true};r.outputs.push(result);r.index++;
  if(r.index===r.flow.steps.length){
   r.status='completed';const snapshot={version:p.history.length+1,flowRevision:r.revision,example:true};
   if(r.stage==='requirements'){p.brief={...snapshot,topic:'咖啡店的第一杯早晨',audience:'通勤上班族',duration:15,platform:'微信视频号',deliverables:['口播脚本','视频']};p.analysis=null;p.work=null;}
   if(r.stage==='analysis'){p.analysis={...snapshot,source:'示例视频资产',evidence:['开头3秒特写','产品细节与环境声'],method:'细节切入 → 场景展开 → 一句话收束'};p.work=null;}
   if(r.stage==='production'){p.work={...snapshot,title:p.brief.topic,assets:['脚本示例','分镜示例','视频占位结果']};p.archive='pending';}
   p.history.push(clone(r));
  }
  const receipt={...result,runStatus:r.status};if(actionId)p.receipts[key]=receipt;return clone(receipt);
 }
 function fail(p){if(!current(p))throw Error('没有运行中的步骤');p.run.error='示例：能力接口超时。已完成步骤保留，可重试当前步骤。';}
 function retry(p){if(!p.run?.error)throw Error('当前没有失败');delete p.run.error;}
 return {components,contracts,release,project,start,current,advance,fail,retry};
});
