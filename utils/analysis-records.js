const PREFIX='youai.analysis.records.v1.';
function scope(api){const profile=api.getStorageSync('youai.account.profile.v1'),session=api.getStorageSync('youai.video.session.v1');return String(profile&&profile.userId||session&&session.userId||'local-preview');}
function load(api){const rows=api.getStorageSync(PREFIX+scope(api));return Array.isArray(rows)?rows:[];}
function save(api,{reference,sourceValue,plan,sampling}){
 if(!reference||reference.status!=='analyzed'||!reference.analysis||!reference.asset?.sha256)throw Error('请先完成内容拆解');
 const asset=reference.asset,ref={status:'analyzed',title:reference.title||'',asset:{sha256:asset.sha256,media:asset.media||{},sizeBytes:asset.sizeBytes||0},analysis:reference.analysis};
 const id=asset.sha256+':'+(sampling||'smart')+':'+JSON.stringify(plan||{}),rows=load(api),previous=rows.find(r=>r.id===id),now=Date.now();
 const sem=reference.analysis.understanding||{};const item={id,time:previous?.time||now,updatedAt:now,stage:previous?.stage||'已识别内容',text:previous?.text||(sem.status==='ready'?String(sem.overview||'').slice(0,120):''),title:reference.title||(sem.status==='ready'?String(sem.overview||'').slice(0,40):'')||'我的视频拆解',sourceValue:String(sourceValue||''),reference:ref,plan:plan||null,sampling:sampling||'smart'};
 const next=[item,...rows.filter(r=>r.id!==id)].slice(0,30);try{api.setStorageSync(PREFIX+scope(api),next);}catch(_){throw Error('拆解记录保存失败，请清理存储后重试');}return item;
}
// 拆解有进展时更新同一条视频的记录（我的创作里显示进度和结论），并挪到最前。
function note(api,sha,patch){if(!sha)return false;patch=Object.fromEntries(Object.entries(patch||{}).filter(([,v])=>v!==undefined));const rows=load(api);let hit=false;const next=rows.map(r=>{if(r.reference&&r.reference.asset&&r.reference.asset.sha256===sha){hit=true;return {...r,...patch,updatedAt:Date.now()};}return r;});if(!hit)return false;next.sort((a,b)=>(b.updatedAt||b.time)-(a.updatedAt||a.time));try{api.setStorageSync(PREFIX+scope(api),next);}catch(_){return false;}return true;}
function understanding(reference){
 const a=reference&&reference.analysis;if(!a)return '';
 const semantic=a.understanding;if(semantic?.status==='ready')return semantic.overview+'\n'+(semantic.uncertainties||[]).map(x=>'待核对：'+x).join('\n');
 const s=a.summary||{},seconds=s.durationSeconds||reference.asset?.media?.durationSeconds;
 return `画面内容尚未识别完成，不能据此生成具体画面方案。${semantic?.error||'请重试内容识别或补充你看到的主体和动作。'}\n仅确认视频${seconds?'约'+Number(seconds).toFixed(1)+'秒，':''}${s.orientation||'画幅待确认'}。音轨转写可能包含歌词、背景人声或误识别，不作为人物口播或画面文案。`;
}
const QUEUE='youai.analysis.queue.v1.';
// 当前正在进行的拆解（还没进后台队列）：粘贴链接一开始就让悬浮球显示，离开页面或完成时清掉。
const LIVE='youai.analysis.live.v1.';
function live(api){try{const v=api.getStorageSync(LIVE+scope(api));return v&&v.id?v:null;}catch(_){return null;}}
function setLive(api,patch){const cur=live(api)||{};const next={...cur,...patch,id:cur.id||('live-'+Date.now()),updated:Date.now()};try{api.setStorageSync(LIVE+scope(api),next);}catch(_){}return next;}
function clearLive(api){try{api.setStorageSync(LIVE+scope(api),null);}catch(_){}}
function queued(api){const rows=api.getStorageSync(QUEUE+scope(api));return Array.isArray(rows)?rows:[];}
function enqueue(api,value){if(!/^[a-f0-9]{32}$/.test(value.jobId||''))throw Error('请等待视频素材获取并创建拆解任务');const rows=queued(api);const row={...value,status:'running',time:Date.now()};api.setStorageSync(QUEUE+scope(api),[row,...rows.filter(r=>r.jobId!==value.jobId)].slice(0,30));return row;}
async function sync(api,request){const owner=scope(api),rows=queued(api);for(const row of rows){if(scope(api)!==owner)return;if(row.status==='done')continue;try{const job=await request('/reference-analyses/'+row.jobId);if(scope(api)!==owner)return;if(job.status==='done'){save(api,{reference:job.reference,sourceValue:row.sourceValue,plan:row.plan,sampling:row.sampling});row.status='done';delete row.error;}else if(job.status==='failed'){row.status='failed';row.error=job.error||'拆解失败，请重新提交';}else row.status='running';}catch(e){if(e&&(e.statusCode===403||e.statusCode===404)){row.status='failed';row.error='任务已失效';}else row.error='暂时无法刷新，请稍后重试';}}
 if(scope(api)===owner)api.setStorageSync(QUEUE+owner,rows);return rows;
}
function markSeen(api,jobId){const rows=queued(api).map(r=>r.jobId===jobId?{...r,seen:true}:r);api.setStorageSync(QUEUE+scope(api),rows);return rows;}
function dismiss(api,jobId){const rows=queued(api).filter(r=>r.jobId!==jobId);api.setStorageSync(QUEUE+scope(api),rows);return rows;}
module.exports={live,setLive,clearLive,note,scope,load,save,understanding,queued,enqueue,sync,dismiss,markSeen};
