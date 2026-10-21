const KEY='youai-video-history';
const SOURCE_LABELS={idea:'点子创作',douyin:'抖音参考',command:'模板口令'};
function compact(value,max=24){return String(value||'').replace(/https?:\/\/\S+/g,'').replace(/#[^\s#]+/g,'').replace(/\s+/g,' ').trim().replace(/[，。！？、；：,.!?;:]+$/,'').slice(0,max);}
function stamp(time){const date=new Date(Number(time)||Date.now());return `${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`;}
function sourceLabel(type){return SOURCE_LABELS[type]||'视频创作';}
function titleFor({sourceType,idea,reference,theme,time}){const label=sourceLabel(sourceType);let value='';if(sourceType==='douyin')value=compact(reference&&reference.title)||compact(reference&&reference.analysis&&reference.analysis.summary&&reference.analysis.summary.detectedSpeech);else if(sourceType==='command')value=compact(theme)||compact(idea);else value=compact(idea);return value||`${label} · ${stamp(time)}`;}
function normalize(item={}){const time=Number(item.time)||Date.now(),sourceType=SOURCE_LABELS[item.sourceType]?item.sourceType:'idea';return {...item,time,sourceType,sourceLabel:sourceLabel(sourceType),title:compact(item.title,32)||titleFor({...item,sourceType,time}),assetStatus:item.assetUrl?'已保存资产包':'仅保留成片记录',timeLabel:stamp(time)};}
function load(wx){const rows=wx.getStorageSync(KEY);return Array.isArray(rows)?rows.map(normalize):[];}
function save(wx,rows){const normalized=(Array.isArray(rows)?rows:[]).map(normalize).slice(0,50);wx.setStorageSync(KEY,normalized);return normalized;}
function create(values){const time=Number(values.time)||Date.now();return normalize({...values,time,title:titleFor({...values,time})});}
module.exports={KEY,SOURCE_LABELS,sourceLabel,titleFor,normalize,load,save,create};
