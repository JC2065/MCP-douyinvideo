// The usage notice shown when a link is pasted; "1 小时内不再提示" is a per-phone choice (免责需要频繁确认).
// It also covers starting content recognition, so accepting it starts the analysis without a second confirm.
const KEY='youai-link-notice-v2',HOUR=3600*1000;
function shouldShow(api,now=Date.now()){try{const until=Number(api.getStorageSync(KEY));return !(until>now);}catch(_){return true;}}
function snooze(api,now=Date.now()){try{api.setStorageSync(KEY,now+HOUR);}catch(_){}}
const TEXT='链接解析仅用于你个人学习、分析爆款创作手法，有AI不对外提供原视频的下载或二次分发（为方便核对，会在内部保存截图和低清副本）。请尊重原作者的著作权与肖像权，创作时请改写文案、使用自己的素材；因不当使用产生的法律责任由使用者自行承担。你也可以直接上传有权使用的视频。';
const RECOGNITION='确认后会自动开始内容识别：抽取代表帧并结合音轨，调用多模态模型理解视频内容，可能产生模型费用。';
module.exports={KEY,HOUR,shouldShow,snooze,TEXT,RECOGNITION};
