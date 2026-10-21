const KEY='youai-analysis-preferences-v1';
const templates=require('./analysis-templates');
const observers=new WeakMap();
const presets=[
 {id:'structure',name:'通用结构',description:'先看懂作品，再提炼开头、展开与收尾。',dimensions:['hook','benefit','cta'],steps:['开场：用一个相关问题或画面说明主题。','展开：用真实细节解释核心内容。','收尾：给一个符合目标的下一步。']},
 {id:'emotion',name:'情绪场景',description:'拆解使用情境、情绪投射与文案视角。',dimensions:['scene','emotion','visual'],steps:['情境：写一个与你的受众有关的具体时刻。','情绪：用自己的语言描述期待或感受，不编造他人评价。','承接：把产品放进场景，明确想象与已验证事实的区别。']},
 {id:'benefit',name:'卖点表达',description:'检查卖点是否清楚，画面是否提供对应支持。',dimensions:['benefit','proof','limits'],steps:['卖点：只选一个可核实的产品信息。','画面：拍摄能看清该信息的细节。','边界：删除无法证明的功效和保证。']},
 {id:'offer',name:'优惠转化',description:'看清价格、数量、门槛和行动引导。',dimensions:['offer','proof','cta'],steps:['信息：填写真实价格、规格、适用条件与有效期。','展示：用产品和包装画面说明交付内容。','行动：给出真实购买入口，不照搬原片折扣或稀缺话术。']},
 {id:'evidence',name:'演示证据',description:'区分观察、演示、评价与未经验证的主张。',dimensions:['proof','limits','benefit'],steps:['问题：说明本次演示具体观察什么。','过程：展示操作、条件与前后状态。','结论：只写画面支持的结果，并保留未验证事项。']},
 {id:'visual',name:'镜头节奏',description:'分析构图、切换、字幕层级与观看负担。',dimensions:['visual','hook','scene'],steps:['镜头表：列出主体、景别、时长和字幕。','变化：只在需要补充信息时切换角度或画面。','自检：确认字幕可读，标出声音仍需核验的部分。']}
];
const labels={hook:'开头与注意力',benefit:'卖点与表达',cta:'行动与收尾',scene:'使用场景',emotion:'情绪与视角',visual:'画面与节奏',proof:'画面支持了什么',limits:'证据边界',offer:'优惠与条件'};
function valid(id,rows=presets){return rows.some(p=>p.id===id);}
function normalize(raw){const r=raw&&typeof raw==='object'?raw:{},extra=templates.normalize(r,labels),rows=presets.concat(extra.customTemplates),overrides={};if(r.overrides&&typeof r.overrides==='object')for(const k of Object.keys(r.overrides).slice(0,200)){if(/^[a-zA-Z0-9_-]{1,80}$/.test(k)&&!['__proto__','prototype','constructor'].includes(k)&&(r.overrides[k]==='auto'||valid(r.overrides[k],rows)))overrides[k]=r.overrides[k];}return{...extra,mode:r.mode==='manual'?'manual':'auto',preset:valid(r.preset,rows)?r.preset:'structure',overrides};}
function catalog(raw){return presets.concat(normalize(raw).customTemplates);}
function load(api){return normalize(api.getStorageSync(KEY));}
function save(api,p,notify=true){const value=normalize(p);api.setStorageSync(KEY,value);if(notify&&observers.has(api))observers.get(api)(value);return value;}
function observe(api,handler){observers.set(api,handler);return()=>{if(observers.get(api)===handler)observers.delete(api);};}
function connect(api,status){return typeof api.login==='function'&&typeof api.request==='function'?require('./analysis-sync').open(api,status):null;}
function recommend(item){const f=item.features||{};if(f.demo)return{id:'evidence',reason:'检测到操作演示与结果展示，优先区分可观察事实和效果主张。'};if(f.offer)return{id:'offer',reason:'画面突出数量、折扣或价格信息，适合检查优惠条件与购买动机。'};if(f.emotion)return{id:'emotion',reason:'长段场景文案承担主要表达，适合分析情绪投射与产品关联。'};if(f.selling)return{id:'benefit',reason:'人物或字幕集中介绍产品特点，适合检查卖点与画面对应。'};return{id:'structure',reason:'先用通用结构理解主题、展开与结尾。'};}
function analyze(item,raw){
 const prefs=normalize(raw),rows=catalog(prefs),override=prefs.overrides[item.id],rec=recommend(item);
 const materialType=prefs.materialOverrides[item.id]||(prefs.materialType==='auto'?templates.detect(item):prefs.materialType),type=templates.types.find(type=>type.id===materialType);
 const mode=override==='auto'?'auto':valid(override,rows)?'manual':prefs.mode;
 const id=mode==='auto'?(prefs.typeDefaults[materialType]||type.preset):valid(override,rows)?override:prefs.preset;
 const preset=rows.find(p=>p.id===id),insights=item.insights||{},missing=item.missingDimensions||[];
 const chosen=prefs.goalOverrides[item.id]||prefs.typeGoals[materialType]||prefs.goals,goalIds=chosen.length?chosen:(preset.goalIds&&preset.goalIds.length?preset.goalIds:templates.defaults[preset.id]||['structure']),goals=templates.goals.filter(goal=>goalIds.includes(goal.id));
 const keys=[...new Set([...preset.dimensions,...goals.flatMap(goal=>goal.dimensions)])];
 const section=key=>{const custom=(preset.sections||[]).find(row=>row.key===key),evidence=Object.prototype.hasOwnProperty.call(insights,key)&&typeof insights[key]==='string'?insights[key]:'';return{key,title:custom?custom.title:labels[key],question:custom?custom.question:templates.questions[key],text:evidence||'未观察到足够信息，暂不生成该维度结论。',status:missing.includes(key)||!evidence?'未观察到':'已有观察与分析'};};
 const f=item.features||{},candidates=[];
 if(f.offer)candidates.push('offer');
 if(f.demo)candidates.push('proof');
 if(f.emotion)candidates.push('proof');
 if(f.selling)candidates.push('benefit');
 if(f.process||f.selling)candidates.push('visual');
 const extra=mode==='auto'?[...new Set(candidates)].filter(k=>!keys.includes(k)&&insights[k]&&!missing.includes(k)).slice(0,2):[];
 const practice=preset.steps.join('\n')+(chosen.length||goals.length>1?'\n拆解目标：'+goals.map(goal=>goal.name).join('、'):'')+(preset.custom?'\n我的拆解问题：\n'+preset.sections.map(row=>row.title+'：'+row.question).join('\n'):'');
 return{preset,goals,materialType,materialLabel:type.name,goalText:goals.map(goal=>goal.name).join('、'),mode,override:override||'default',reason:mode==='auto'?(prefs.typeDefaults[materialType]||prefs.materialType!=='auto'?'按'+type.name+'的默认模板拆解。':rec.reason):'遵循用户指定的方案；缺少依据的栏目标注未观察到，不自动换方案。',engine:'规则匹配 + 已整理案例内容',sections:keys.map(section),supplements:extra.map(section),supplementLabel:extra.map(k=>labels[k]).join('、'),base:{source:item.filename||'用户提供视频',duration:item.duration,observation:'抽帧画面与可见字幕；声音未核验',facts:(item.segments||[]).map(s=>({time:s.label,text:s.fact})),unknown:item.pitfall||'实际传播效果与未提供的信息待核实。'},segmentation:item.segmentation||{label:'按镜头与表达阶段',note:'时间点是教学近似划分，不代表精确切点。'},practice,version:'framework-v2'};
}
function plan(analysis){return{templateId:analysis.preset.id,templateName:analysis.preset.name,version:analysis.preset.version||1,materialType:analysis.materialType,goalIds:analysis.goals.map(goal=>goal.id),questions:analysis.sections.map(row=>({key:row.key,title:row.title,question:row.question})),steps:analysis.preset.steps.slice()};}
function practiceCase(item,id,analysis){const a=analysis||analyze(item,{mode:'manual',preset:id});return Object.assign({},item,{analysisPreset:a.preset.id,analysisProfile:JSON.parse(JSON.stringify({template:a.preset,goals:a.goals,goalText:a.goalText,materialType:a.materialType})),method:item.method+'\n本次拆解预设：'+a.preset.name,practice:a.practice});}
module.exports={KEY,presets,labels,normalize,load,save,recommend,analyze,practiceCase,catalog,templates,plan,observe,connect};
