const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const ledger=fs.readFileSync('docs/task-ledger.md','utf8');

test('任务台账在实施前记录当前任务基线、阶段和交接入口',()=>{
 for(const value of ['TASK-20261011-01','状态：`active`','9c0c643','用户确认的目标','已确认的产品规则','实施阶段','当前决策与限制','继续工作入口','完成信息'])assert.ok(ledger.includes(value),value);
 for(const stage of ['建立媒体、分析、故事板','真实参考素材获取与质量门禁','ReferenceAnalysis v1','故事板审核','Provider 能力接口','用户反馈、偏好摘要'])assert.ok(ledger.includes(stage),stage);
});

test('任务台账约束每次任务先登记并保留付费、资产和用户控制边界',()=>{
 assert.match(ledger,/每次新任务开始前先新增一条记录/);
 assert.match(ledger,/普通验证使用 Mock Provider/);
 assert.match(ledger,/失败只重做局部/);
 assert.match(ledger,/可查看、可修改、可删除/);
 const apiKeyPattern=/(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{8,}/;
 assert.doesNotMatch(ledger,apiKeyPattern);
 assert.doesNotMatch('tests/task-interest.test.js',apiKeyPattern);
});

test('阶段 C 在编码前登记媒体获取门禁、回退和验收证据',()=>{
 for(const value of ['RUN-20261011-C','起始提交：`bd6dce2`','识别、获取、校验三个独立状态','要求用户上传原视频','SHA-256','ffprobe','服务重启后的任务/资产可恢复'])assert.ok(ledger.includes(value),value);
});

test('解析配置恢复任务在编码前登记入口、失效和密钥边界',()=>{
 for(const value of ['RUN-20261011-C2','起始提交：`e1e5e39`','我的 → 工具接口管理 → 视频下载','连接检测结果和失效提示','令牌不出现在状态和错误中'])assert.ok(ledger.includes(value),value);
});

test('解析器部署任务在实施前记录选型、真实联调与失败边界',()=>{
 for(const value of ['RUN-20261012-C3','起始提交：`f98b7d7`','优先自托管开源方案','同一条抖音短链','OpenAPI 检测通过','不得伪报成功'])assert.ok(ledger.includes(value),value);
});

test('解析等待反馈任务在实施前记录阶段、计时和真实性边界',()=>{
 for(const value of ['RUN-20261012-C4','起始提交：`e4b46dd`','链接识别、平台解析、素材下载还是视频校验','已等待时长','不把估算阶段冒充服务端确认状态'])assert.ok(ledger.includes(value),value);
});

test('内容分析任务在实施前记录输出契约、资产复用和证据边界',()=>{
 for(const value of ['RUN-20261012-C5','起始提交：`8478808`','ReferenceAnalysis v1','镜头时间、代表帧、音轨/文案线索','同一 SHA-256 可复用结果','不得用抖音标题或模型猜测冒充视频事实'])assert.ok(ledger.includes(value),value);
});

test('失效短链任务在实施前记录诊断、恢复动作和禁止静默替换边界',()=>{
 for(const value of ['RUN-20261012-C6','起始提交：`da53df0`','short_link_dead_end','解析器优先','不得静默匹配或替换','重新复制新链接或上传原视频'])assert.ok(ledger.includes(value),value);
});

test('生成请求失败任务在实施前记录真实失败层、载荷边界和验收条件',()=>{
 for(const value of ['RUN-20261012-C7','起始提交：`1aceca2`','本机 `/jobs` 请求解析层','约 6.4 KB','统一设置 4 KB 上限','生成必需的参考分析和资产标识'])assert.ok(ledger.includes(value),value);
});

test('生成前沟通任务在实施前记录动态提问、故事板门禁和资产边界',()=>{
 for(const value of ['RUN-20261012-E1','起始提交：`893dac0`','分析 → 方向沟通 → 故事板审核 → 生成 → 反馈学习','必须出现和不要出现','明确确认后才能创建生成任务','普通测试使用本地纯文字 Provider'])assert.ok(ledger.includes(value),value);
});

test('视频资产包任务在实施前记录持久化范围、去重、血缘和产品入口',()=>{
 for(const value of ['RUN-20261012-E2','起始提交：`23a1487`','PostgreSQL 七张视频资产表均为 0 条记录','代表帧','脱敏生成请求','媒体按 SHA-256 去重','查看本次资产','尚未持久化'])assert.ok(ledger.includes(value),value);
});
