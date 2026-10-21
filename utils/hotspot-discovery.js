// Live ranking snapshots; no bundled ranking fallback.
const platforms=['综合','微博','抖音','今日头条','快手'];
const rows=[];
const {BASE:baseUrl}=require('./service-endpoints');
function filter(items,platform){return platform==='综合'?items:items.filter(r=>r.platform===platform);}
function clock(at){const d=new Date(at*1000);return String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');}
function decorate(items){return items.map(r=>{
 const minutes=Math.max(1,Math.round((r.comparisonSeconds||0)/60));
 const trendLabel=r.stale?'缓存，趋势暂停':r.trend==='rising'?'↑ 上升'+r.rankChange+'位':r.trend==='new'?'新入采集榜':r.trend==='falling'?'↓ 下降'+Math.abs(r.rankChange)+'位':r.trend==='steady'?'位置持平':'等待对比';
 return {...r,trendLabel,comparisonLabel:r.comparedAt?minutes+'分钟采集对比':'尚无有效对比',evidence:r.previousRank?'第'+r.previousRank+'位 → 第'+r.rank+'位':'当前第'+r.rank+'位',trail:(r.rankTrail||[]).map(p=>({...p,label:clock(p.at),position:p.rank?'第'+p.rank+'位':'未入采集榜'}))};
});}
function select(items,platform,mode){const list=filter(items,platform);if(mode==='rising')return list.filter(r=>!r.stale&&r.trend==='rising'&&r.rankChange>0).sort((a,b)=>b.rankChange-a.rankChange||a.rank-b.rank);if(mode==='new')return list.filter(r=>!r.stale&&r.trend==='new').sort((a,b)=>a.rank-b.rank);return list;}
function search(message,previous={},items=rows){
 const text=String(message||'').trim();if(!text||text.length>100)throw Error('请输入 1–100 字的关键词或问题');
 const results=items.filter(r=>r.title.toLowerCase().includes(text.toLowerCase()));
 return {context:{topic:text,modifiers:[]},results,message:results.length?`在当前榜单找到 ${results.length} 条相关话题。`:'没有匹配结果，可更换关键词；搜索范围仅限当前已同步榜单。'};
}
function load(api){return new Promise(resolve=>{
 if(!api||typeof api.request!=='function')return resolve({rows:[],sources:{},error:'暂未连接热榜服务'});
 api.request({url:baseUrl+'/hotspots',timeout:12000,success:r=>{
  const v=r.data;if(r.statusCode===200&&v&&v.schemaVersion===1&&Array.isArray(v.rows)&&v.sources){resolve(v);}else resolve({rows:[],sources:{},error:'热榜服务暂不可用'});
 },fail:()=>resolve({rows:[],sources:{},error:'网络异常，请稍后刷新'})});
});}
function status(feed,platform){
 if(!feed)return '正在同步热榜…';if(feed.error)return feed.error;
 const sources=Object.values(feed.sources||{}).filter(s=>platform==='综合'||s.platform===platform);
 if(!sources.length)return '该平台尚未接入';
 const updated=Math.max(...sources.map(s=>s.fetchedAt||0));const delayed=sources.filter(s=>s.status!=='fresh').map(s=>s.platform);
 return (updated?'更新 '+clock(updated):'等待同步')+(delayed.length?' · '+delayed.join('、')+'更新延迟':' · 每10分钟同步');
}
function start(page,api,apply){
 stop(page);let cancelled=false;const tick=()=>load(api).then(feed=>{if(!cancelled)apply(feed);});
 tick();const timer=typeof setInterval==='function'?setInterval(tick,600000):null;
 page._stopHotspots=()=>{cancelled=true;if(timer)clearInterval(timer);};
}
function stop(page){if(page._stopHotspots)page._stopHotspots();page._stopHotspots=null;}
function content(api,id,retry=false){return new Promise(resolve=>{
 if(!/^(douyin|weibo|toutiao|kuaishou)-[a-f0-9]{20}$/.test(id)||!api||typeof api.request!=='function')return resolve({status:'error',items:[],notice:'话题内容暂不可用'});
 api.request({url:baseUrl+'/hotspot-content/'+id+(retry?'?retry=1':''),timeout:12000,success:r=>resolve(r.statusCode===200&&r.data&&Array.isArray(r.data.items)?r.data:{status:'error',items:[],notice:'内容服务暂不可用'}),fail:()=>resolve({status:'error',items:[],notice:'网络异常，请稍后重试'})});
});}
function summarize(api,platform,preference=''){return new Promise((resolve,reject)=>require('./video-service').send(api,{url:baseUrl+'/hotspots/summary',method:'POST',data:{platform,preference:String(preference||'').slice(0,500)},timeout:45000,success:r=>r.statusCode===200?resolve(r.data):reject(Error(r.data&&r.data.error||'热点总结暂不可用')),fail:()=>reject(Error('热点总结连接失败，请稍后重试'))}));}
function lookup(api,query){return new Promise((resolve,reject)=>api.request({url:baseUrl+'/hotspots/search?q='+encodeURIComponent(query),timeout:30000,success:r=>r.statusCode===200?resolve(r.data):reject(Error(r.data&&r.data.error||'搜索暂不可用')),fail:()=>reject(Error('热点搜索连接失败，请稍后重试'))}));}
function watchRequest(api,method,data,query='',remove=false){return new Promise((resolve,reject)=>require('./video-service').send(api,{url:baseUrl+'/hotspot-watch'+(remove?'/remove':'')+(query?'?q='+encodeURIComponent(query):''),method,data,timeout:15000,success:r=>r.statusCode===200?resolve(r.data):reject(Error(r.data&&r.data.error||'关注记录同步失败')),fail:()=>reject(Error('关注记录连接失败，请稍后重试'))}));}
module.exports={lookup,watches:(api,q)=>watchRequest(api,'GET',undefined,q),follow:(api,keyword)=>watchRequest(api,'POST',{keyword}),unfollow:(api,keyword)=>watchRequest(api,'POST',{keyword},'',true),summarize,platforms,rows,search,filter,load,status,start,stop,decorate,select,content};
