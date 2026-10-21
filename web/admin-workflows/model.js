(function(root,factory){const value=factory();if(typeof module==='object'&&module.exports)module.exports=value;else root.WorkflowDesign=value;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 const boards=[
  {id:'hotspots',name:'热点推荐',desc:'来源采集、搜索词与热点总结',items:['平台来源与更新状态','搜索词与账号兴趣','升温 / 新上榜 / 完整榜','AI总结与选题转化'],note:'已有热榜与总结接口；来源异常必须显示，不补造热点。'},
  {id:'tools',name:'创作工具调用',desc:'工具能力、路由与任务状态',items:['下载 / 转写 / 音频 / 封面 / 提词','供应商路由与健康状态','权限、限流与费用上限','错误分类与人工重试'],note:'沿用稳定工具ID；图片去水印仍需接入真实图片处理能力。'},
  {id:'mcp',name:'MCP 包管理',desc:'把稳定工程能力封装成可复用工具',items:[],note:'设计示例包，尚未安装或真实调用。'},
  {id:'data',name:'数据积累',desc:'账号资产与飞书归档',items:['素材与资产索引','拆解、脚本和版本快照','飞书字段映射与归档队列','失败补偿与重复记录核对'],note:'业务数据库保留权限与主索引；飞书承接经授权的结构化记录和归档。'},
  {id:'requirements',name:'确认需求设计',desc:'把用户想法整理成可确认的创作简报',flow:true},
  {id:'analysis',name:'作品拆解',desc:'基于素材证据提炼结构与可复用方法',flow:true},
  {id:'production',name:'作品产出',desc:'从已确认方案到可追踪的作品资产',flow:true}
 ];
 const capabilities={input:'输入采集',skill:'Skill协作',review:'用户确认',evidence:'证据提取',generate:'作品生成',package:'作品编排',archive:'资产归档'};
 const step=(id,title,capability,required=false)=>({id,title,capability,required});
 const defaults={
  requirements:[step('input','接收灵感 / 热点 / 口令','input',true),step('clarify','确认目标、受众、平台与时长','skill'),step('brief','形成主题、风格和交付清单','skill'),step('confirm','用户确认需求简报','review',true)],
  analysis:[step('source','选择素材与拆解模板','input',true),step('evidence','提取画面、语音与来源证据','evidence',true),step('analyze','按目标拆解结构、卖点和镜头','skill'),step('reuse','提炼可复用方法与原创方向','skill'),step('confirm','用户确认拆解方案','review',true)],
  production:[step('brief','读取已确认简报与拆解快照','input',true),step('script','生成脚本、分镜与素材清单','skill'),step('confirm','确认分镜与费用上限','review',true),step('generate','生成文字 / 图片 / 视频','generate',true),step('package','匹配音乐、字幕与标题','package'),step('review','预览并确认作品','review',true),step('archive','归集资产与飞书归档事件','archive',true)]
 };
 const clone=value=>JSON.parse(JSON.stringify(value));
 function create(stage,mode='default'){if(!defaults[stage])throw Error('未知流程');return{schemaVersion:1,stage,mode,revision:1,baseVersion:'default-v1',requirements:'',steps:clone(defaults[stage])};}
 function validate(flow){if(!flow||!defaults[flow.stage]||!Array.isArray(flow.steps)||flow.steps.length>12)return['流程结构无效'];const errors=[],seen=new Set();for(const row of flow.steps){if(!row||typeof row.id!=='string'||seen.has(row.id)){errors.push('步骤ID重复或无效');continue;}seen.add(row.id);if(!capabilities[row.capability])errors.push('不支持的能力');if(typeof row.title!=='string'||!row.title.trim()||row.title.length>80)errors.push('步骤标题无效');if(row.script||row.url||row.code)errors.push('流程不能携带远程代码或调用地址');}for(const required of defaults[flow.stage].filter(s=>s.required)){const row=flow.steps.find(s=>s.id===required.id);if(!row||row.capability!==required.capability||!row.required)errors.push('必须保留：'+required.title);}const before=(a,b)=>flow.steps.findIndex(s=>s.id===a)<flow.steps.findIndex(s=>s.id===b);if(flow.stage==='production'&&(!before('confirm','generate')||!before('generate','review')||!before('review','archive')))errors.push('必须先确认、再生成、再验收归档');if(flow.stage!=='production'&&flow.steps.at(-1)?.id!=='confirm')errors.push('流程必须以用户确认为终点');return errors;}
 function propose(stage,need){if(typeof need!=='string'||!need.trim()||need.trim().length>1000)throw Error('请填写1–1000字需求');const flow=create(stage,'custom');flow.requirements=need.trim();if(/简洁|快速|精简/.test(need)&&stage==='requirements')flow.steps=flow.steps.filter(s=>s.id!=='brief');if(/图文|图片/.test(need)&&stage==='production')flow.steps.find(s=>s.id==='generate').title='生成图文作品与配图';if(/口播/.test(need)&&stage==='production')flow.steps.find(s=>s.id==='script').title='生成口播脚本与拍摄分镜';return flow;}
 function move(flow,index,delta){const next=clone(flow),target=index+delta;if(target<0||target>=next.steps.length)return next;[next.steps[index],next.steps[target]]=[next.steps[target],next.steps[index]];const errors=validate(next);if(errors.length)throw Error(errors[0]);return next;}

 const packages=[
  {id:'youai-video-reader',name:'视频读取包',version:'1.0.0-design',tool:'read_video',capability:'video.read',inputType:'video_asset',outputContract:'video-evidence.v1',scopes:['asset:read'],enabled:true,approved:true,healthy:true,cost:0,priority:100,functions:['元信息与时长','代表帧采样','音轨与字幕引用']},
  {id:'youai-transcript',name:'视频文案包',version:'1.0.0-design',tool:'transcribe_video',capability:'video.transcribe',inputType:'video_asset',outputContract:'transcript.v1',scopes:['asset:read','ai:transcribe'],enabled:true,approved:true,healthy:true,cost:1,priority:90,functions:['提取音轨','语音转写','时间戳与置信度']},
  {id:'youai-feishu-archive',name:'飞书归档包',version:'1.0.0-design',tool:'archive_assets',capability:'archive.feishu',inputType:'archive_event',outputContract:'archive-receipt.v1',scopes:['archive:write'],enabled:true,approved:true,healthy:true,cost:0,priority:80,functions:['字段映射','幂等写入','回执与失败补偿']}
 ];
 function resolveMcp(request,registry=packages){
  if(!request||!Array.isArray(request.scopes)||!Number.isFinite(request.budget)||request.budget<0)return{status:'blocked',reason:'调用上下文或预算无效'};
  const candidates=registry.filter(p=>p.enabled&&p.approved&&p.healthy&&p.capability===request.capability&&p.inputType===request.inputType&&p.outputContract===request.outputContract&&p.scopes.every(scope=>request.scopes.includes(scope))&&Number.isFinite(p.cost)&&p.cost<=request.budget);
  candidates.sort((a,b)=>b.priority-a.priority||a.cost-b.cost||a.id.localeCompare(b.id));
  return candidates.length?{status:'matched',package:clone(candidates[0]),execution:'design-only'}:{status:'blocked',reason:'没有已批准、健康且满足权限/预算/契约的包；保留步骤并提示处理，不自动下载或换包'};
 }
 return{packages,resolveMcp,boards,capabilities,defaults,create,validate,propose,move,clone};
});
