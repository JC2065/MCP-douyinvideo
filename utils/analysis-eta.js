// 内容识别预计时长：按本机最近几次识别的「耗时 / 视频秒数」中位数估算；记录不足时按视频时长估（约 30 秒 + 每秒视频 5 秒）。
const KEY='youai-analysis-pace-v1';
function duration(reference){const d=Number(reference&&reference.asset&&reference.asset.media&&reference.asset.media.durationSeconds);return d>0?d:0;}
function history(api){try{const rows=api.getStorageSync(KEY);return Array.isArray(rows)?rows.filter(r=>r>0&&isFinite(r)):[];}catch(_){return [];}}
function estimate(api,reference){const d=duration(reference),ratios=history(api).slice(-8).sort((a,b)=>a-b);
 const raw=d&&ratios.length>=2?d*ratios[Math.floor(ratios.length/2)]:d?30+d*5:120;return Math.round(Math.min(600,Math.max(20,raw)));}
function record(api,reference,seconds){const d=duration(reference),s=Number(seconds);if(!d||!(s>0))return;try{api.setStorageSync(KEY,[...history(api),s/d].slice(-8));}catch(_){}}
function clock(s){s=Math.round(s);return s<60?s+' 秒':Math.floor(s/60)+' 分'+(s%60?' '+s%60+' 秒':'');}
function text(elapsed,eta){const e=Number(elapsed)||0;if(!eta)return `已等待 ${e} 秒`;return e>eta*1.1?`已等待 ${e} 秒 · 比预计慢一些，快好了`:`已等待 ${e} 秒 · 预计约 ${clock(eta)}`;}
// 胶囊进度：预计时间内走到 90%，超时后缓慢逼近 99%，完成时由页面设为 100%。
function percent(elapsed,eta){const e=Math.max(0,Number(elapsed)||0);if(!eta)return 0;const p=e<=eta?e/eta*90:90+9*(1-Math.exp(-(e-eta)/eta));return Math.max(2,Math.min(99,Math.round(p)));}
module.exports={KEY,duration,estimate,record,clock,text,percent};
