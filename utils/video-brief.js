const boundaries=require('./content-boundaries');
const command=require('./creative-command');
const analysisEngine=require('./analysis-presets');
const sourceModes=[
  {id:'idea',label:'说个点子',hint:'一句话描述你想做的内容'},
  {id:'douyin',label:'参考视频',hint:'粘贴抖音分享链接'},
  {id:'command',label:'模板口令',hint:'复用一套已经验证的方法'}
];
const questions = [
  {key:'goal',title:'这次内容最重要的结果？',options:['吸引看完','讲清卖点','引导行动']},
  {key:'audience',title:'主要说给谁看？',options:['泛兴趣用户','目标客户','已有粉丝']},
  {key:'hookStyle',title:'开头怎么抓住人？',options:['先给结果','提出问题','制造反差']},
  {key:'tone',title:'希望是什么语气？',options:['自然真实','清晰专业','轻松有趣']},
  {key:'visualStyle',title:'主要用什么画面？',options:['AI 生成画面','纯文字画面']},
  {key:'cta',title:'结尾希望观众做什么？',options:['看完即可','评论互动','关注账号','了解产品']}
];
const referenceQuestion={key:'referenceMode',title:'这条参考视频要借鉴到什么程度？',options:['高度参考原片','画面风格','内容结构','同题新作']};
const defaults={goal:'吸引看完',audience:'泛兴趣用户',hookStyle:'先给结果',tone:'自然真实',visualStyle:'AI 生成画面',cta:'看完即可',referenceMode:'画面风格'};
const generationDefaults=Object.freeze({mode:'all-purpose',resolution:'720P',ratio:'9:16',audio:true,promptExtend:true,watermark:false});
const generationOptions=Object.freeze({mode:['all-purpose','first-last-frame'],resolution:['480P','720P','1080P'],ratio:['adaptive','21:9','16:9','4:3','1:1','3:4','9:16']});
function clampDuration(value){const number=typeof value==='string'?Number.parseFloat(value):Number(value);return Number.isFinite(number)?Math.min(30,Math.max(2,Math.round(number))):2;}
function smartDuration(source){if(source.type==='command')return clampDuration(Math.ceil((source.script||'').length/18));if(source.type==='douyin')return clampDuration(source.reference?.analysis?.summary?.durationSeconds||15);return clampDuration(Math.ceil(source.idea.length/3)+4);}
function normalizeSource(input){
 if(typeof input==='string')return {type:'idea',label:'点子',value:input,idea:input};
 const type=String(input&&input.type||'idea'),value=String(input&&input.value||'').trim();
 if(type==='idea')return {type,label:'点子',value,idea:value};
 if(type==='douyin'){
  const reference=input&&input.reference&&typeof input.reference==='object'?input.reference:null;
  const uploaded=reference&&reference.platform==='upload'&&reference.asset&&/^[a-f0-9]{64}$/.test(reference.asset.sha256||'');
  const match=uploaded?['upload:'+reference.asset.sha256]:value.length<=2000&&value.match(/https:\/\/(?:v\.|www\.|m\.)?(?:douyin|iesdouyin)\.com\/[^\s]+/i);
  if(!match)throw Error('请粘贴有效的抖音分享链接或上传原视频');
  const title=String(reference&&reference.title||'').replace(/#[^\s#]+/g,'').replace(/\s+/g,' ').trim().slice(0,160);
  return {type,label:'抖音视频',value:match[0],idea:String(reference?.analysis?.understanding?.overview||title||'参考视频创作').slice(0,160),reference};
 }
 if(type==='command'){
  const parsed=command.decode(value),theme=String(input&&input.theme||'').trim();
  const script=command.render(parsed,theme);
  return {type,label:'模板口令',value,idea:theme,method:parsed.name,script};
 }
 throw Error('请选择一种创作起点');
}
function brief(idea,answers={}) {
  const source=normalizeSource(idea),text=String(source.idea||'').trim();
  if(!text||text.length>160)throw Error('请输入 1–160 字的点子');
  const explicitMood=/治愈|温柔|安静/.test(text)?'温柔治愈':/活力|明亮/.test(text)?'活力明亮':null;
  const structured=typeof idea!=='string',explicitDuration=text.match(/(\d{1,2})\s*秒/),smart=structured&&(answers.duration==='智能'||answers.duration==null);
  const duration=answers.durationOverride?clampDuration(answers.duration):explicitDuration?clampDuration(explicitDuration[1]):smart?smartDuration(source):clampDuration(answers.duration);
  const result={idea:text,mood:explicitMood||(answers.mood||'温柔治愈'),duration,durationMode:explicitDuration?'manual':smart?'smart':'manual'};
  if(typeof idea==='string')return {idea:result.idea,mood:result.mood,duration:result.duration};
  const allowed=Object.fromEntries([...questions,referenceQuestion].map(item=>[item.key,item.options]));
  const choices=Object.fromEntries(Object.keys(defaults).map(key=>[key,typeof answers[key]==='string'&&answers[key].trim()&&answers[key].length<=120&&(key!=='referenceMode'&&key!=='visualStyle'||(allowed[key]||[]).includes(answers[key]))?answers[key].trim():defaults[key]]));
  const requested=answers.generation&&typeof answers.generation==='object'?answers.generation:{};
  const generation={mode:generationOptions.mode.includes(requested.mode)?requested.mode:generationDefaults.mode,resolution:generationOptions.resolution.includes(requested.resolution)?requested.resolution:generationDefaults.resolution,ratio:generationOptions.ratio.includes(requested.ratio)?requested.ratio:generationDefaults.ratio,audio:requested.audio!==false,promptExtend:requested.promptExtend!==false,watermark:requested.watermark===true,smartDuration:smart};
  if((answers.outputType||'video')==='video'&&generation.mode==='first-last-frame'&&(source.type!=='douyin'||!source.reference||!source.reference.asset||!source.reference.asset.sha256))throw Error('首尾帧模式需要已验证的参考原片');
  return Object.assign(result,choices,{generation,...(answers.analysisPlan?{analysisPlan:JSON.parse(JSON.stringify(answers.analysisPlan))}:{}),...(answers.boundaryPlatforms?{contentBoundaries:boundaries.normalize(answers.boundaryPlatforms)}:{}),imageRatio:['adaptive','1:1','3:4','4:3','9:16','16:9'].includes(answers.imageRatio)?answers.imageRatio:'adaptive',creativeIntent:String(answers.creativeIntent||'').trim().slice(0,1000),referenceNotes:String(answers.referenceNotes||'').trim().slice(0,1000),mustInclude:String(answers.mustInclude||'').trim().slice(0,120),avoid:String(answers.avoid||'').trim().slice(0,120),aiPreference:String(answers.aiPreference||'').trim().slice(0,500),source:{type:source.type,label:source.label,value:source.value,method:source.method||'',script:source.script||'',reference:source.reference||null}});
}
function storyboard(idea,answers={},version=1){
 const plan=brief(idea,answers),duration=plan.duration,bounds=[0,Number((duration*.25).toFixed(1)),Number((duration*.72).toFixed(1)),duration];
 const subject=plan.mustInclude||plan.idea,ending=plan.cta==='看完即可'?'自然收束，不额外要求互动':`明确引导${plan.cta}`;
 let shots=[
  {role:'开场',start:bounds[0],end:bounds[1],narration:`${plan.hookStyle}：${subject}`,visual:`用${plan.visualStyle}在第一眼交代核心结果`},
  {role:'展开',start:bounds[1],end:bounds[2],narration:`面向${plan.audience}讲清：${plan.idea}`,visual:`以${plan.tone}的节奏展开关键信息`},
  {role:'收束',start:bounds[2],end:bounds[3],narration:ending,visual:`回到核心信息并${ending}`}
 ];
 const segments=plan.source.reference?.analysis?.understanding?.segments||[];
 if(segments.length&&segments.length<=12){const total=segments.reduce((sum,s)=>sum+Math.max(.01,s.end-s.start),0);let cursor=0;shots=segments.map((segment,i)=>{const start=cursor;cursor+=Math.max(.01,segment.end-segment.start)/total*duration;return {role:'内容段落 '+(i+1),start:Number(start.toFixed(2)),end:i===segments.length-1?duration:Number(cursor.toFixed(2)),narration:String(segment.description).slice(0,240),visual:String(segment.description).slice(0,240)};});}
 const referenceMode=plan.source.type==='douyin'?({'高度参考原片':'reference-video','内容结构':'content-structure','画面风格':'visual-style','同题新作':'same-topic'}[plan.referenceMode]):'same-topic';
 const referenceDuration=Number(((((plan.source.reference||{}).analysis||{}).summary||{}).durationSeconds)||0),normalizeBoundary=referenceDuration>15&&referenceDuration<=15.5;
 const referenceInputs=plan.generation.mode==='first-last-frame'?{label:'首帧与尾帧',count:2,note:'模型会严格使用原片首尾画面，中间内容按新分镜生成'}:referenceMode==='reference-video'?{label:normalizeBoundary?'规范后的原视频':'原视频',count:1,note:normalizeBoundary?`原片精确时长 ${referenceDuration.toFixed(2)} 秒，提交时自动安全裁至 14.9 秒，其余主体、场景和镜头保持不变`:'模型会看到原视频，重点保持主体、场景、动作和镜头语言'}:referenceMode==='visual-style'?{label:'代表帧',count:Math.min(3,Number((((plan.source.reference||{}).analysis||{}).shots||{}).representativeFrameCount)||0),note:'模型会看到代表帧，重点保持构图、色彩和视觉风格'}:referenceMode==='content-structure'?{label:'结构分析',count:1,note:'模型只借鉴节奏和段落，不保证人物与画面相似'}:{label:'无参考媒体',count:0,note:'只保留主题重新创作，画面可能与原片明显不同'};
 return {version,status:'draft',referenceMode,referenceInputs,shots,...(plan.contentBoundaries?{contentBoundaries:plan.contentBoundaries}:{}),...(plan.analysisPlan?{analysisPlan:plan.analysisPlan}:{})};
}
function generationBrief(idea,answers={},approvedStoryboard){
 const result=brief(idea,answers),reference=result.source&&result.source.reference;
 if(!approvedStoryboard||approvedStoryboard.status!=='approved'||!Array.isArray(approvedStoryboard.shots)||approvedStoryboard.shots.length<1||approvedStoryboard.shots.length>12)throw Error('请先确认分镜草案');
 if(approvedStoryboard.shots.every(s=>Number.isFinite(s.end))&&approvedStoryboard.shots.at(-1).end!==result.duration)throw Error('成片时长已改变，请重新确认分镜');
 if(result.analysisPlan&&JSON.stringify(result.analysisPlan)!==JSON.stringify(approvedStoryboard.analysisPlan))throw Error('拆解方案已改变，请重新确认分镜');
 if(JSON.stringify(result.contentBoundaries||null)!==JSON.stringify(approvedStoryboard.contentBoundaries||null))throw Error('内容边界已改变，请重新确认分镜');result.storyboard=approvedStoryboard;
 if(!reference||result.source.type!=='douyin')return result;
 const asset=reference.asset&&reference.asset.sha256?{sha256:String(reference.asset.sha256)}:undefined;
 result.source.reference={status:reference.status,analysis:reference.analysis,...(asset?{asset}: {})};
 return result;
}
function interview(idea,outputType='video') {
  const source=normalizeSource(idea);
  const visible=questions.filter(q=>q.key!=='visualStyle');
  const suggestions=source.reference?.analysis?.understanding?.recommendations?.[outputType]||[];
  return (source.type==='douyin'&&outputType==='video'?[referenceQuestion,...visible]:visible).map(q=>({...q,options:[...new Set([...suggestions.filter(r=>r.key===q.key).map(r=>r.value),...q.options])]}));
}
module.exports={sourceModes,generationDefaults,generationOptions,normalizeSource,clampDuration,smartDuration,brief,storyboard,generationBrief,interview,analysisEngine};
