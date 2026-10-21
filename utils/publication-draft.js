const scope=require('./analysis-records').scope;
const catalog=require('./content-boundaries').catalog;
const KEY='youai.publication.drafts.v1.';
function load(api,id){try{const rows=api.getStorageSync(KEY+scope(api));return rows&&typeof rows==='object'&&!Array.isArray(rows)?rows[id]||null:null;}catch(_){return null;}}
function save(api,id,value){if(!id)return;const key=KEY+scope(api),rows=api.getStorageSync(key)||{};rows[id]={title:String(value.title||'').slice(0,80),coverPath:value.coverPath||'',platforms:value.platforms||[],updatedAt:Date.now()};const latest=Object.entries(rows).sort((a,b)=>b[1].updatedAt-a[1].updatedAt).slice(0,30);api.setStorageSync(key,Object.fromEntries(latest));}
function platforms(ids){return catalog.platforms.map(p=>({id:p.id,name:p.name,selected:ids.includes(p.id),canLaunch:false}));}
function caption(title,text){return [String(title||'').trim(),String(text||'').trim()].filter(Boolean).join('\n\n');}
module.exports={load,save,platforms,caption};
