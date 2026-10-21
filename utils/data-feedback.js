// 数据监控：YOUAI 作品回传的数据 + 任意抖音作品的数据监控（服务端 /board/works、/board/monitors）。
const service=require('./video-service'),{BASE}=require('./service-endpoints');
const KEYS=[['play','播放'],['likes','点赞'],['comments','评论'],['shares','转发'],['collects','收藏']];
function call(api,path,method='GET',data){return new Promise((resolve,reject)=>service.send(api,{url:BASE+path,method,data,timeout:method==='GET'?20000:70000,header:{'Content-Type':'application/json'},success:r=>r.statusCode===200?resolve(r.data):reject(Error(r.data&&r.data.error||'数据服务暂不可用')),fail:()=>reject(Error('暂时无法连接数据服务，请稍后重试'))}));}
function fmt(n){if(typeof n!=='number'||!isFinite(n))return '—';const a=Math.abs(n);if(a>=1e8)return (n/1e8).toFixed(1).replace(/\.0$/,'')+'亿';if(a>=1e4)return (n/1e4).toFixed(1).replace(/\.0$/,'')+'万';return String(Math.round(n));}
function stats(values={},delta={}){return KEYS.filter(([k])=>typeof values[k]==='number').map(([k,label])=>({key:k,label,value:fmt(values[k]),delta:delta[k]>0?'+'+fmt(delta[k]):''}));}
// 分组：对标作品（benchmark，只有公开数据）/ 我的作品（YOUAI 作品 + 自己发的作品的监控）。
const ROLES=[{id:'own',label:'我的作品',placeholder:'粘贴你自己发布的抖音作品链接'},{id:'benchmark',label:'对标作品',placeholder:'粘贴对标账号的抖音作品链接'}];
const INTERACT=['likes','comments','shares','collects'];
const interactions=(v={})=>INTERACT.reduce((s,k)=>s+(typeof v[k]==='number'?v[k]:0),0);
// 走势小图：最近 14 次公开记录的互动总数（点赞+评论+转发+收藏），高度 8–100%。
function spark(metrics=[]){const rows=metrics.filter(m=>m.source==='public').sort((a,b)=>a.day-b.day).slice(-14).map(m=>interactions(m.values));if(rows.length<2)return [];const max=Math.max(...rows),min=Math.min(...rows);return rows.map(v=>max===min?54:8+Math.round((v-min)/(max-min)*92));}
function decorate(row){const monitor=row.kind==='monitor',s=row.summary,group=monitor&&row.role!=='own'?'benchmark':'own';const gain=s?interactions(s.delta):0;
 return {id:row.id,values:s?s.values:{},delta:s?s.delta:{},hasData:!!s,gain,gainText:gain>0?'+'+fmt(gain):'',spark:spark(row.metrics),kind:monitor?(group==='own'?'own':'benchmark'):'youai',group,badge:monitor?(group==='own'?'我的作品':'对标'):'有AI作品',title:row.title||'未命名作品',author:row.author||'',link:row.link||'',
  stats:s?stats(s.values,s.delta):[],state:!row.link?'待贴回发布链接，开始回传数据':!s?'等待第一次抓取':(s.day?(monitor?'监控第 ':'发布后第 ')+s.day+' 天':(monitor?'刚开始监控':'今天'))+' · 已记录 '+s.snapshots+' 次'};}
// 每日变化表：只保留至少有一天有数据的列（抖音不公开播放量时不显示「播放」）。
function trend(metrics=[]){const rows=metrics.filter(m=>m.source==='public').sort((a,b)=>a.day-b.day);const keys=KEYS.filter(([k])=>rows.some(m=>typeof m.values[k]==='number'));return {labels:keys.map(k=>k[1]),rows:rows.map(m=>({day:m.day,label:m.day?'第 '+m.day+' 天':'添加时',cells:keys.map(([k])=>fmt(m.values[k]))}))};}
function groups(rows){return ROLES.map(r=>({...r,count:rows.filter(x=>x.group===r.id).length}));}
const LABEL=Object.fromEntries(KEYS);
// 数据面板：一个分组的累计数、较上次记录的新增、涨得最快的 3 条。
function panel(rows,group){const list=rows.filter(r=>r.group===group),data=list.filter(r=>r.hasData);const sum=(k,f)=>data.reduce((s,r)=>s+(typeof r[f][k]==='number'?r[f][k]:0),0);
 return {count:list.length,tracked:data.length,totals:INTERACT.map(k=>({key:k,label:LABEL[k],value:fmt(sum(k,'values')),today:sum(k,'delta')>0?'+'+fmt(sum(k,'delta')):''})),
  gain:fmt(data.reduce((s,r)=>s+Math.max(0,r.gain),0)),gainNum:data.reduce((s,r)=>s+Math.max(0,r.gain),0),multi:data.some(r=>r.spark.length),rising:data.filter(r=>r.gain>0).sort((a,b)=>b.gain-a.gain).slice(0,3).map(r=>({id:r.id,title:r.title,badge:r.badge,kind:r.kind,gainText:r.gainText}))};}
// 我的作品 vs 对标作品：平均每条的点赞/评论/转发/收藏，任一组没有数据就不比。
function compare(rows){const avg=(g,k)=>{const d=rows.filter(r=>r.group===g&&r.hasData&&typeof r.values[k]==='number');return d.length?d.reduce((s,r)=>s+r.values[k],0)/d.length:null;};
 const lines=INTERACT.map(k=>{const own=avg('own',k),bench=avg('benchmark',k);if(own===null||bench===null)return null;const top=Math.max(own,bench)||1;return {key:k,label:LABEL[k],own:fmt(own),bench:fmt(bench),ownW:Math.max(2,Math.round(own/top*100)),benchW:Math.max(2,Math.round(bench/top*100)),ratio:bench?Math.round(own/bench*100):null};}).filter(Boolean);
 if(!lines.length)return null;const likes=lines.find(l=>l.key==='likes')||lines[0];return {lines,note:likes.ratio===null?'':'你的作品平均'+likes.label+'是对标作品的 '+likes.ratio+'%'};}
module.exports={KEYS,ROLES,fmt,stats,decorate,trend,groups,panel,compare,spark,
 list:api=>call(api,'/board/works').then(r=>(r.rows||[]).map(decorate)),
 add:(api,url,role='benchmark')=>call(api,'/board/monitors','POST',{url,role}),
 setRole:(api,id,role)=>call(api,'/board/works/'+id+'/role','POST',{role}),
 refresh:(api,id)=>call(api,'/board/works/'+id+'/refresh','POST',{}),
 remove:(api,id)=>call(api,'/board/works/'+id+'/remove','POST',{})};
