// 识别等待时的创作小提示：短句、可执行，4–6 秒轮换一条，点一下换下一条。
const TIPS=[
 '前 3 秒决定去留：先给结果或冲突，再讲过程。',
 '一条视频只讲一件事，信息越少越好记。',
 '字幕放在画面中下方，避开右侧按钮和底部文案区。',
 '评论区是第二个视频：发布后 1 小时内回复前 10 条评论。',
 '置顶一条“问问题”的评论，比“求关注”更能带互动。',
 '同一个选题换 3 种开头各拍一版，数据会告诉你哪种对。',
 '复刻爆款学结构，不学原句：文案改写成自己的话。',
 '竖屏拍摄，人物眼睛放在画面上三分之一处。',
 '手机贴近光源，侧前方的窗光比顶灯好看得多。',
 '收藏率高的内容，通常给了“以后用得上”的信息。',
 '转发率高的内容，往往替观众说出了想说的话。',
 '结尾留一个问题，让观众有话可评。',
 '低粉也能爆：单人单机位、真实场景，更容易复刻。',
 '标题写“你”比写“我”更容易让人停下来。',
 '剪掉每段开头和结尾的 0.3 秒，节奏会快很多。',
 '背景音乐音量压到人声的三分之一以下。',
 '同类视频连发 5 条，比随机发 10 条更容易被推荐。',
 '发布时间跟着你的观众走：看后台的粉丝活跃时段。',
 '情景演绎记得在文案里标注，避免被判误导。',
 '拍之前先写好 3 句字幕，现场就不会卡壳。'];
function pick(index){const n=TIPS.length;return TIPS[((index%n)+n)%n];}
// 关闭小提示：每次关闭 24 小时内不显示；同一账号累计关闭 3 次后永久不显示（按账号分开记在本机）。
const OFF_PREFIX='youai-tips-off-v1.',DAY=86400000;
function scope(api){try{const p=api.getStorageSync('youai.account.profile.v1'),s=api.getStorageSync('youai.video.session.v1');return String(p&&p.userId||s&&s.userId||'local-preview');}catch(_){return 'local-preview';}}
function state(api){try{const v=api.getStorageSync(OFF_PREFIX+scope(api));return v&&typeof v==='object'?v:{};}catch(_){return {};}}
function hidden(api,now=Date.now()){const v=state(api);return !!v.permanent||(Number(v.until)||0)>now;}
function close(api,now=Date.now()){const v=state(api),count=(Number(v.count)||0)+1,next={count,until:now+DAY,permanent:count>=3};try{api.setStorageSync(OFF_PREFIX+scope(api),next);}catch(_){}return next;}
module.exports={TIPS,pick,hidden,close,OFF_PREFIX};
