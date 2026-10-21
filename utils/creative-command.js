const PREFIX='YOUAI1:';
const MAX_CODE=100000;
function validate(value){
 if(!value||typeof value!=='object'||Array.isArray(value)||value.version!==1)throw Error('口令版本不支持，请使用有AI创作口令');
 const limits={name:80,idea:1000,template:8000};const result={version:1};
 for(const key of Object.keys(limits)){
  if(typeof value[key]!=='string'||!value[key].trim()||value[key].length>limits[key])throw Error('口令内容不完整或过长');
  result[key]=value[key].trim();
 }
 if(!result.template.includes('{{主题}}'))throw Error('口令模板缺少主题位置');
 return result;
}
function encode(value){return PREFIX+encodeURIComponent(JSON.stringify(validate(value)));}
function decode(code){
 if(typeof code!=='string'||code.length>MAX_CODE||!code.trim().startsWith(PREFIX))throw Error('请粘贴完整的有AI创作口令');
 let parsed;try{parsed=JSON.parse(decodeURIComponent(code.trim().slice(PREFIX.length)));}catch(e){throw Error('口令损坏，请重新复制');}
 return validate(parsed);
}
function render(value,title){
 const c=validate(value);if(typeof title!=='string'||!title.trim())throw Error('请填写你自己的主题');
 if(title.trim().length>100)throw Error('主题请控制在 100 字以内');
 const result=c.template.split('{{主题}}').join(title.trim());
 if(result.length>10000)throw Error('生成内容过长，请缩短主题或模板');
 return result;
}
function fromCase(c){return validate({version:1,name:c.tag+'创作方法',idea:c.method,template:`主题：{{主题}}\n\n核心思路\n${c.method}\n\n开场：提出与「{{主题}}」有关的具体问题。\n展开：展示「{{主题}}」的真实过程、证据与结果。\n节奏参考：${c.structure}\n收尾参考（按自己的业务改写）：${c.cta}\n\n创作检查：${c.practice}\n复盘：${c.metric}`});}
function fromWork(w,idea){
 if(!w||!w.title||!w.text)throw Error('请先保存一份创作方案');
 const template=w.text.split(w.title).join('{{主题}}');
 return validate({version:1,name:w.title.slice(0,80),idea:idea||'沿用这份方案的表达顺序、内容证据和行动引导，替换为自己的主题。',template:template.includes('{{主题}}')?template:'主题：{{主题}}\n\n'+template});
}
module.exports={encode,decode,render,fromCase,fromWork};
