// 大模型与技能配置：模型清单、全局默认模型、按功能场景的模型覆盖与提示词。
// 演示阶段仅本机存储，不发起网络请求；API Key 等敏感信息保存在本机存储，接入后端后应迁移到服务端。
const KEY='youai-ai-config-v1';
const models=[
 {id:'deepseek',name:'DeepSeek',vendor:'深度求索',desc:'推理与长文拆解能力强，成本低'},
 {id:'qwen',name:'通义千问',vendor:'阿里',desc:'中文创作均衡，电商文案见长'},
 {id:'doubao',name:'豆包',vendor:'字节跳动',desc:'懂短视频语境，网感好'},
 {id:'kimi',name:'Kimi',vendor:'月之暗面',desc:'长文本整理与资料归纳'},
 {id:'glm',name:'智谱 GLM',vendor:'智谱 AI',desc:'工具调用与结构化输出稳定'},
 {id:'wenxin',name:'文心一言',vendor:'百度',desc:'搜索热点与资讯整合方便'}];
const scenes=[
 {id:'hotspot',name:'AI 找热点',desc:'按你的领域与关键词发现选题'},
 {id:'script',name:'视频脚本',desc:'把点子扩写成分镜脚本'},
 {id:'daily',name:'每日一拆',desc:'拆解推荐案例的底层逻辑'},
 {id:'copy',name:'文案提取',desc:'从视频或链接提取口播文案'},
 {id:'idea',name:'灵感扩写',desc:'把一句话点子补全为完整选题'}];
function knownIds(state){return new Set([...models.map(m=>m.id),...(state.custom||[]).map(c=>c.id)]);}
function normalize(raw){
 raw=raw&&typeof raw==='object'?raw:{};
 const custom=(Array.isArray(raw.custom)?raw.custom:[]).filter(c=>c&&typeof c.id==='string').slice(0,3).map(c=>({id:String(c.id).slice(0,30),name:String(c.name||'自定义模型').slice(0,12),baseUrl:String(c.baseUrl||'').slice(0,200),model:String(c.model||'').slice(0,60),key:String(c.key||'').slice(0,200)}));
 const state={version:1,defaultModel:'deepseek',keys:{},custom,scenes:{},bundles:[]};
 for(const m of models){const v=raw.keys&&raw.keys[m.id];state.keys[m.id]=typeof v==='string'?v.slice(0,200):'';}
 const ids=knownIds(state);
 if(typeof raw.defaultModel==='string'&&ids.has(raw.defaultModel))state.defaultModel=raw.defaultModel;
 // MCPB 工具包：链接安装或本地上传；演示阶段只保存清单元数据，不实际下载/解压。
 state.bundles=(Array.isArray(raw.bundles)?raw.bundles:[]).filter(b=>b&&typeof b.id==='string'&&typeof b.name==='string'&&b.name.trim()&&(b.source==='link'||b.source==='file')).slice(0,5).map(b=>({id:String(b.id).slice(0,30),name:String(b.name).slice(0,30),version:String(b.version||'').slice(0,20),publisher:String(b.publisher||'').slice(0,30),source:b.source,url:String(b.url||'').slice(0,300),fileName:String(b.fileName||'').slice(0,100),tools:(Array.isArray(b.tools)?b.tools:[]).filter(t=>typeof t==='string').slice(0,20).map(t=>t.slice(0,30)),enabled:b.enabled!==false}));
 const bundleIds=new Set(state.bundles.map(b=>b.id));
 for(const s of scenes){const v=raw.scenes&&raw.scenes[s.id];const item=v&&typeof v==='object'?v:{};state.scenes[s.id]={enabled:item.enabled!==false,model:typeof item.model==='string'&&ids.has(item.model)?item.model:'',prompt:String(item.prompt||'').slice(0,500)};if(Array.isArray(item.bundles))state.scenes[s.id].bundles=item.bundles.filter(x=>bundleIds.has(x)).slice(0,5);}
 return state;
}
function load(api){try{return normalize(api.getStorageSync(KEY));}catch(e){return normalize({});}}
function save(api,data){const value=normalize(data);api.setStorageSync(KEY,value);return value;}
function modelName(state,id){const hit=models.find(m=>m.id===id)||(state.custom||[]).find(c=>c.id===id);return hit?hit.name:'未选择';}
// 解析某场景最终生效的配置：场景模型优先，空则跟随全局默认；
// 工具包：场景未单独勾选时跟随「全部已启用」，勾选后按场景清单（全局停用的包始终排除）。
function enabledBundles(state){return (state.bundles||[]).filter(b=>b.enabled);}
function resolve(state,sceneId){const s=state.scenes[sceneId];if(!s)return null;const modelId=s.model||state.defaultModel;const bundles=s.bundles?state.bundles.filter(b=>b.enabled&&s.bundles.includes(b.id)):enabledBundles(state);return {enabled:s.enabled,modelId,modelName:modelName(state,modelId),prompt:s.prompt,overridden:!!s.model,bundles,bundlesCustomized:!!s.bundles};}
module.exports={KEY,models,scenes,normalize,load,save,resolve,modelName,enabledBundles};
