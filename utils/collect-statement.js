// 用户信息采集声明：登录弹窗里展示，勾选同意后才能手机号验证或生成体验账号。内容与 docs/privacy-creation-board.md 保持一致。
const KEY='youai-collect-consent',VERSION=2;  // v2：手机号完整保存、数据同步飞书、素材截图与低清副本，需重新同意
const ITEMS=[
 '手机号：用于账号注册登录、账号安全，以及在需要时与你联系、核对问题来源。完整号码保存在我们的服务器上，并同步到我们内部使用的飞书多维表格，仅限运营人员查看。',
 '创作内容：你在拆解与创作中的问答、对 AI 理解的纠正、拆解方案、产出路线、灵感碎片和作品数据，会与账号关联保存，并同步到我们内部使用的飞书多维表格长期归档，用于提供服务、改进拆解质量和全站统计。',
 '截图与语音：创作者后台截图只用于识别数字，识别后不保存；语音只用于转成文字，转写后即删除。',
 '公开内容：解析作品链接时读取作品公开信息和公开评论文字，并在内部保存封面、4 张截图和低清视频副本，仅用于核对与归档，不对外提供下载；不保存评论者的昵称、头像和账号。',
 '你可以不回答任何问题、不回传数据；不登录也可以浏览和体验。'];
function agreed(api){try{return Number(api.getStorageSync(KEY))>=VERSION;}catch(_){return false;}}
function setAgreed(api,value){try{api.setStorageSync(KEY,value?VERSION:0);}catch(_){}}
module.exports={KEY,VERSION,ITEMS,agreed,setAgreed};
