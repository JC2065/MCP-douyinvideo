// 模型测评与免费信息：静态策展数据，帮助用户判断「哪个模型好、哪个能免费用」。
// 来源：2026 年公开测评（综合能力梯队）与各厂商公开免费政策，于 2026-10 整理；演示参考，非实时榜单。
const updated='2026-10';
const insights={
 deepseek:{score:95,tier:'第一梯队',freeApp:'网页 / App 完全免费',freeApi:'API 新用户赠额度，之后按量极低价',goodFor:['daily','script'],oneLiner:'国产推理天花板，代码与数学能力强，拆解逻辑类内容最稳。'},
 qwen:{score:93,tier:'第一梯队',freeApp:'网页 / App 免费',freeApi:'API 新用户 100 万 token（3 个月）',goodFor:['script','copy','idea'],oneLiner:'全栈能力最均衡，超长上下文，电商文案与阿里生态衔接好。'},
 kimi:{score:90,tier:'第一梯队',freeApp:'网页 / App 免费',freeApi:'新用户赠 15 元额度',goodFor:['copy','daily'],oneLiner:'长文本王者（约 200 万字上下文），拆长视频文案、读资料最强。'},
 doubao:{score:87,tier:'第二梯队',freeApp:'网页 / App 免费',freeApi:'每日 200 万+ token 按天重置',goodFor:['hotspot','idea'],oneLiner:'最懂短视频语境，网感好、上手快，抖音生态联动方便。'},
 glm:{score:85,tier:'第二梯队',freeApp:'网页 / App 免费',freeApi:'GLM-Flash 永久免费 + 注册送 2000 万 token',goodFor:['hotspot','idea'],oneLiner:'实力派，工具调用稳定；Flash 版永久免费，最适合零成本试用 API。'},
 wenxin:{score:84,tier:'第二梯队',freeApp:'基础写作免费',freeApi:'ERNIE Speed/Lite 免费',goodFor:['hotspot','copy'],oneLiner:'搜索增强第一、中文润色细腻，查实时热点与资讯整合方便。'}};
function forModel(id){const v=insights[id];return v?Object.assign({id},v):null;}
function sorted(){return Object.keys(insights).map(forModel).sort((a,b)=>b.score-a.score);}
module.exports={updated,insights,forModel,sorted};
