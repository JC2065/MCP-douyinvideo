// Platform policy is shipped with the app, never merged from personal storage.
// Public credentials belong on the server, not in this registry or client storage.
const KEY = 'youai-tool-interfaces-v1';
const tools = Object.freeze([
  {id:'download',name:'视频下载 / 参考解析'}, {id:'transcript',name:'文案提取'},
  {id:'audio',name:'音频提取'}, {id:'eraser',name:'去水印'},
  {id:'cover',name:'封面提取'}, {id:'teleprompter',name:'提词器'}
].map(tool => Object.freeze({...tool, allowCustom:true, publicServiceId:tool.id==='download'?'youai-reference-parser-v1':''})));
const empty = () => ({source:'public',url:'',method:'POST',auth:'none',token:'',checkStatus:'unchecked',checkedAt:0});
function policy(id) {
  const tool = tools.find(item => item.id === id);
  if (!tool) throw Error('工具不存在');
  return tool;
}
function validate(value) {
  if (!/^https:\/\/[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::\d{1,5})?(?:[/?][^\s#]*)?$/i.test(value.url) || value.url.length > 500) throw Error('请输入有效的 HTTPS 接口地址');
  if (!['GET','POST'].includes(value.method)) throw Error('请选择 GET 或 POST');
  if (!['none','bearer'].includes(value.auth)) throw Error('请选择有效的认证方式');
  if (value.auth === 'bearer' && (!value.token.trim() || /[\r\n]/.test(value.token) || value.token.length > 2000)) throw Error('请填写有效的访问令牌');
}
function normalize(raw) {
  const state = {};
  for (const tool of tools) {
    const value = raw && raw[tool.id];
    const item = value && typeof value === 'object' ? value : {};
    state[tool.id] = {
      source:tool.allowCustom && item.source === 'personal' ? 'personal' : 'public',
      url:typeof item.url === 'string' ? item.url.trim().slice(0,500) : '',
      method:item.method === 'GET' ? 'GET' : 'POST',
      auth:item.auth === 'bearer' ? 'bearer' : 'none',
      token:item.auth === 'bearer' && typeof item.token === 'string' ? item.token.slice(0,2000) : '',
      checkStatus:['passed','failed'].includes(item.checkStatus)?item.checkStatus:'unchecked',
      checkedAt:Number.isFinite(item.checkedAt)&&item.checkedAt>0?item.checkedAt:0
    };
  }
  return state;
}
function load(api) {
  try { return normalize(api.getStorageSync(KEY)); } catch (_) { return normalize(null); }
}
function save(api,id,input) {
  const tool = policy(id);
  if (!input || !['public','personal'].includes(input.source)) throw Error('请选择接口来源');
  if (input.source === 'personal' && !tool.allowCustom) throw Error('此工具不允许个人配置');
  const value = {...empty(),...input,url:String(input.url || '').trim(),token:String(input.token || '').trim()};
  if (value.source === 'personal') validate(value);
  const state = load(api);
  // Selecting public preserves the saved personal configuration, not unsaved edits.
  state[id] = value.source === 'public' ? {...state[id],source:'public'} : {...normalize({[id]:value})[id],checkStatus:'unchecked',checkedAt:0};
  api.setStorageSync(KEY,state);
  return state;
}
function clear(api,id) {
  policy(id);
  const state = load(api); state[id] = empty();
  api.setStorageSync(KEY,state);
  return state;
}
function resolve(state,id) {
  const tool = policy(id), value = normalize(state)[id];
  if (value.source === 'public') return {source:'public',ready:!!tool.publicServiceId,serviceId:tool.publicServiceId,status:tool.publicServiceId?'平台已配置':'平台暂未配置'};
  try {
    validate(value);
    if(id!=='download')return {source:'personal',ready:true,status:'个人配置已保存'};
    const stale=value.checkedAt&&Date.now()-value.checkedAt>7*24*60*60*1000;
    if(value.checkStatus==='passed'&&!stale)return {source:'personal',ready:true,status:'个人配置已检测'};
    if(value.checkStatus==='failed')return {source:'personal',ready:false,status:'连接检测失败，请更新配置'};
    if(stale)return {source:'personal',ready:false,status:'连接检测已过期，请重新检测'};
    return {source:'personal',ready:false,status:'配置已保存，等待连接检测'};
  }
  catch (_) { return {source:'personal',ready:false,status:'个人配置待完善'}; }
}
function markCheck(api,id,passed,now=Date.now()){
  policy(id);const state=load(api);validate(state[id]);state[id]={...state[id],checkStatus:passed?'passed':'failed',checkedAt:now};api.setStorageSync(KEY,state);return state;
}
function connection(state,id){const value=normalize(state)[id];validate(value);return {baseUrl:value.url,token:value.auth==='bearer'?value.token:''};}
module.exports = {KEY,tools,policy,normalize,load,save,clear,resolve,markCheck,connection};
