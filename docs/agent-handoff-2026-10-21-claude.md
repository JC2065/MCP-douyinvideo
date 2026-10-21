# Claude → Claude 交接 · 2026-10-21

## 交接基线

- 仓库：`E:\data\codexYOUAI`，分支 `codex/admin-console`，以 `git log -1` 为准（最后一个功能提交是「台账：仅本次调整的方案统一进「拆解库·仅本次调整」」）。
- 线上 video 服务：最新增量部署即 HEAD（`bash /opt/youai/releases/remote-release.sh live` 查看，platform-<短哈希>）。部署后又手动 `docker restart youai-video-video-1` 一次（为了重载飞书表映射），健康正常。
- 小程序：本轮大量界面改动**尚未上传体验版**（最后一次用户上传是本轮早期）。只能从 `E:\data\codexYOUAI` 上传，版本号接用户上次之后递增。
- 测试批次：`docs/test-batches.md` 记到第 158 次（Codex）。**本轮 Claude 的约 60 个提交没有逐条登记批次**——接手后请补一条汇总记录，并按 AGENTS.md 跑一次完整测试（`node --test tests/*.test.js`）。当前完整测试：441 左右通过，4 个环境项失败（云端 Compose ×2、codex-http-repair、源码归档），与以前相同。

## 工作方式与约束（务必遵守）

- 与用户沟通用中文；用户在手机体验版截图提需求，回复要说清改了什么、在哪看到。
- 部署：`DEPLOY_KEY=E:\data\codexYOUAI-data\claude-deploy\id_ed25519 DEPLOY_KNOWN_HOSTS=...\known_hosts bash scripts/deploy-delta.sh`（用户已授权本轮连续开发与部署；部署前在回复里说明）。Codex 不使用这把 key。
- 不把任何 API Key 写进仓库；不替用户输入密码/密钥；BYOK 用户 Key 不存不记日志；后台数据截图识别后不保存；评论者身份不保存。
- 不提交用户的 `project.config.json` 改动，不提交 Codex 改过的 docs（agent-handoff-2026-10-17/19、agent-return-2026-10-19-codex、test-batches.md 中 Codex 的未提交部分）——提交时只 `git add` 自己改的文件。
- 设备上的 Linux shell **不能删除文件**：git 提交会留下 `.git/*.lock`，每次提交后把它们 `mv` 成 `.git/stale-*`（不要放进 refs）。`.git` 下已有大量 `stale-*` 文件，可请用户删除。另有一个误建的空文件 `tests/video-page.test.js`（未跟踪）请用户删除。
- 编辑 Windows 文件注意换行：`scripts/Dockerfile.video` 用 sed 改会整文件换行变化，导致 deploy-delta 判定"依赖变化需全量部署"。用 Python 按字节替换。
- 用户机器 Python 3.10（无 tomllib），`video-server.py` 相关 Python 测试在本机会报 tomllib 错，属环境项；需在服务器容器（Python 3.12）里验证。
- 测试数据：不要覆盖用户本机 storage（曾经误覆盖过队列，已恢复）。
- ToDesk 远控时 computer-use 无法操作开发者工具；界面改动用浏览器 Playwright 按同样式还原截图自检，再让用户真机看。

## 本轮完成（按模块）

### 1. 爆款拆解页（pages/video、utils/board-page.js、utils/reference-intake.js）
- 动线：看过的内容折叠，新内容在下方生长并自动滚动；等「大致内容」出来后才折叠输入区并滚到进度卡。
- 粘贴：输入框加高突出；空时显示「📋 点这里粘贴链接」（`wx.getClipboardData`，**需在隐私指引声明剪切板**）。删除了「保存开始出片」「下一步只确认…」「1/3·内容拆解」「我的拆解记录 / 我的文字作品」链接。
- 「开始解析」按钮：胶囊流光进度（渐变流动+玻璃高光+扫光），阶段：正在看大致内容（peek，约 2–3 秒）→ 大致内容已出 100% → 正在获取视频 → 进入深度解析后变浅色「完整理解中 · 见下方」。
- 深度解析进度条在大致内容下方，标题「正在进行深度解析……」+ 百分比（估时 `utils/analysis-eta.js`）。
- 创作小提示：💡 + 单行，超长左右滚动（图标固定）；获取视频、看大致内容、深度解析、深度拆解各等待阶段都显示；长按可关闭 24 小时，同账号第 3 次永久关闭（`utils/creation-tips.js`，本机按账号存）。
- 「我看到的是」确认卡：超级拆解/1:1复刻切换；内容出来后 3 秒（最多 5 秒）自动开始拆解，触摸卡片暂停；「对，开始拆解」等三个按钮是胶囊进度「正在深度拆解 xx%」（按本机最近 5 次耗时估算）；部分不对/完全不对按钮矮一半。AI 额度用完或没看成时显示原因 + 「再试一次」+ 购买额度/申请增加额度，不自动确认。
- 拆解完成后「✓ 我看到的」与识别状态合成一张可收起卡片（逐段画面可展开）。
- 超级拆解结果卡：标题「超级拆解结果」+ 方案名，右侧「方案」+ 收起/展开；四部分（结论/怎么学/结构/评论区）带编号、可折叠、默认全部展开；数据依据在顶部默认收起（「我读到的信息」「据此算出的指标」）。
- 评论：服务端取 20 条热评，按热度（赞 + 3×回复）加权、分共识/讨论/长尾，拆解提示词要求以高热度评论为主；卡片先显示 3 条可展开。
- 「接下来做什么」：推荐项一行，其余三个（另一种作品 / 1:1 复刻 / AI 生成）矮一半并排。
- 文字作品卡：复制全部/选择复制；新文案 textarea 可编辑可选中；原文/标题可长按选中。
- 页面底部「我的创作 / 我的作品」切换（过程 vs 成品，与首页同一数据），默认展开可收起，卡片状态与「打开拆解」同一行。
- 返回键：页内有「部分不对/完全不对」状态时先退回选择处（`onBallBack`）；返回失败兜底在开发/体验版弹窗提示（`utils/back-fallback.js`）。

### 2. 悬浮球与后台任务（components/app-navigation、utils/analysis-records.js）
- 点击返回、长按任务面板、角标；新用户提示每 24 小时一次共 3 次。
- 粘贴开始就同步「当前任务」（`analysisRecords.setLive/clearLive`），显示阶段；离开页面时若深度解析在跑会自动转入后台队列。
- 任务面板：主按钮「继续/查看/重新提交」大号胶囊，「移除」放在状态行最前。
- 顶部标题整行居中（返回键绝对定位在左）；首页标题前缀「做内容/做私域/玩私域/要引流」每 3 秒轮换 + 固定「有AI」。

### 3. 首页与品牌（pages/main）
- 用户可见的 YOUAI 全改为「有AI」（YOUAI1: 口令前缀、请求头、内部标识未改）。内容创作页标题「做私域，有AI」。
- 「爆款拆解复刻」首屏大卡片（粘贴链接就能开始 / 开始拆解 ›），另两个入口并排。
- 首页「我的创作」收录爆款拆解与 1:1 复刻（云端 `/creative-assets` 新增 `breakdowns`、`replicas`）。
- 数据监控（我的作品/对标作品）与数据面板 `pages/board-work`。

### 4. 额度
- 每用户每日新视频数（中台「每用户每日新视频数」，当前 10）与全站日预算 ¥20。额度用完的视频可「再试一次」（服务端不缓存失败结果）。
- 申请增加额度：`POST /board/quota/request {amount: 1|5|10, reason}`、`GET /board/quota`；**调试阶段 `Board.QUOTA_AUTO_APPROVE = True`（creation-board.py）申请即到账**，弹「暂时免费」提示。审核模式代码已在（`quota_requests`/`decide_quota`），改回 False 即启用。「购买额度」目前是占位弹窗。

### 5. 速度
- `POST /references/peek {url}`：解析链接（3 分钟内存缓存，与 acquire 共用一次解析）+ 封面 + 文案 → `video_glance`，按作品缓存；实测新链接 2.4 秒。
- acquire 中热评与视频下载并行（省约 5 秒）。
- 识别用时改用完成时刻计算（`finishedAt`）。

### 6. 长期资产：飞书多维表格（scripts/asset-ledger.py，新）
- 飞书 base（管理组织）：<飞书多维表格链接（不公开）> ，与原 作品总表 等同库。
- 表：用户（含完整手机号）、素材库（4 张截图：封面+中段两张+结尾，360p 低清视频附件）、理解卡、拆解库、方法卡（跨视频合并计数）、作品库、数据回流；用户自定义方案另建「拆解库·方案名·ID后4位」（方案每字段一列），「仅本次」调整统一进「拆解库·仅本次调整」。
- 机制：先写 `/data/assets/ledger/ledger.sqlite` 发件箱，后台线程投递，失败指数退避；表映射在 `/data/assets/ledger/feishu-tables.json`；媒体缓存 `/data/assets/ledger/media/`。人工列（我的评分/我的标签/运营备注/优化备注/用过次数/效果评价）系统不写。
- 挂点（video-server.py）：acquire 成功→用户+素材；分析完成→理解卡；/board/breakdown、/board/adjust→拆解库+方法卡(+方案表)；/board/output/text|package→作品库；Board.on_metric→数据回流；/auth/phone→用户。
- 历史已回填（551 行 + 方案表）。飞书 client_token 必须是 UUIDv4 格式（已按稳定哈希生成）。
- 完整手机号：`wechat-auth.py` 新表 `phones`，`AUTH.phone(user)`；**只有本轮之后新绑定/重新授权的用户才有完整号**，老用户只有脱敏号。
- 采集声明升 v2（`utils/collect-statement.js`，需重新同意）：写明完整手机号、同步飞书、内部保存截图与低清副本；链接使用说明同步改。

## 接口与数据变化（汇总）

- 新接口：`POST /references/peek`；`GET /board/history`；`POST /board/quota/request`、`GET /board/quota`；`/creative-assets` 增 `breakdowns`、`replicas`。
- `source_meta` 增 `coverUrl`；`post_context.topComments` ≤20 条带 `heat/share/kind`，新增 `commentStats`；`insight.topComments` ≤20、`insight.commentStats`。
- 本机存储新增：`youai.analysis.live.v1.*`（当前任务）、`youai-tips-off-v1.*`（小提示关闭）、`youai-breakdown-pace-v1`（拆解耗时）、`youai-back-fallback-log`。
- 服务端新表：board.sqlite `quota_requests`；auth.sqlite `phones`；ledger.sqlite（outbox/uploads/methods/sources）。

## 未完成事项（建议顺序）

1. **补测试批次记录 + 完整测试**（见基线）。
2. **用户待办提醒**：上传体验版；微信隐私指引补「剪切板」「手机号/第三方平台（飞书）存储」等；提交审核前关闭体验版测试账号；轮换 dtk 解析密钥（2026-10-18 在输出中出现过一次）；检查飞书 base 分享权限（含全量手机号）；删除 `.git/stale-*` 与 `tests/video-page.test.js`。
3. **额度审核与微信通知**：中台/小程序管理员「额度申请」页 + 订阅消息（需要用户提供两个模板 ID：申请提交通知、审核结果通知，以及管理员账号）；审核上线时把 `QUOTA_AUTO_APPROVE` 改为 False。「购买额度」接支付（用户说后期自己接）。
4. **方法卡复用**：生成创作包/文字作品时从方法卡取该类目下用得多、数据好的方法优先使用；数据回流给方法打分；飞书月度复盘仪表盘。
5. `docs/privacy-creation-board.md` 与采集声明 v2 保持一致（目前只改了小程序内文案）。
6. 可选：拆解页标题也做前缀轮换（用户只要求了首页）。

## 回滚点

- 后端：`bash /opt/youai/releases/remote-release.sh switch platform-<上一个>`；本轮较早的稳定点有 platform-b0c6aa5、platform-2160bf3（台账之前）、platform-3b4f4b0。
- 台账可单独停用：去掉 `video-server.py` 里 `LEDGER.start()` 即不再投递（发件箱仍会记录）。

## 回交格式

按 `docs/agent-return-YYYY-MM-DD-*.md`：回交基线、完成内容、接口与数据变化、测试证据、运行状态、密钥与费用、未完成事项、回滚点。

## 可直接发给下一个 Claude 的提示词

> 接手 `E:\data\codexYOUAI`（分支 codex/admin-console）。先读 `AGENTS.md` 和 `docs/agent-handoff-2026-10-21-claude.md`，遵守其中「工作方式与约束」。第一步：在 `docs/test-batches.md` 补记本轮汇总并跑一次完整测试；然后按「未完成事项」继续（额度审核与微信通知需要先向用户要两个订阅消息模板 ID 和管理员账号）。部署用 claude-deploy 目录的 key 和 `scripts/deploy-delta.sh`，部署前告诉用户。用中文和用户沟通，改界面后用截图说明在哪里能看到。

---

## 续 · 2026-10-21 会话（Claude 接手后随做随写）

### 进度（按提交）

| 次 | 提交 | 内容 | 状态 |
| --- | --- | --- | --- |
| 159 | 231a43f | 补登记上一轮 72 个提交；完整测试 444 项 440 通过（4 环境项） | 完成 |
| 160 | 70ff70e | 隐私文档与采集声明 v2 逐字同步 + 一致性测试；完整测试 446/442 | 完成；4 环境项待 Windows+Docker 补测后关闭本批 |
| 161 | 2af4eda、5e9029c | 方法卡复用（见下） | 代码与测试完成；**未部署** |
| 162 | 705ba1b | `docs/PROJECT-MAP.md` 项目地图；AGENTS/CLAUDE/README 指向；creation-board-plan M14–M19 | 完成 |

### 方法卡复用（第161次）怎么工作

- `scripts/creation-board.py`：board.sqlite 新表 `methods(cat,name,how,level,assets,count,used,last)`、`method_results(work,cat,name,ratio,at)`。
- 拆解完成 → `record_methods`：「能不能学」里高/中的方法按理解卡类型（`method_category` 去分隔符）入库，按素材去重计数。
- 文字作品/创作包 → `methods_for`：同类目、出现在 ≥1 条其它爆款、不含本片已拆出的；同类目不足 2 条时跨类目补位（≥3 条其它爆款）；≥2 条作品回流且播放中位数 <0.8 倍的停推。payload 增 `methods`，模型回填 `usedMethods`（只认提供过的名字）。
- `create_work` 记下用上的方法；`save_metrics` 后 `score_methods` 按 `review.ratio` 打分；`admin_dashboard.methods` 前 20。
- 启动时 `BOARD.backfill_methods()` 一次性回填历史拆解（cache 键 `methods-backfill-v1`）。
- 小程序：两张输出卡底部「借鉴同类爆款方法：…」（`utils/board-page.js` `methodNote`）。
- 不依赖飞书台账；飞书「方法卡」表仍由台账独立维护。

### 运行状态 / 卡点

- 线上仍是上一轮的 HEAD（1954057 对应版本）。本会话设备 shell 连不上 `182.61.14.185:22`（Network is unreachable），无法用 claude-deploy 发布；请用户双击 `deploy-platform.cmd`（默认增量，会发 `platform-<HEAD短哈希>`），或放开网络后由 agent 执行 `scripts/deploy-delta.sh`。
- 部署后需在服务器容器里补跑：`python3 -m unittest test-breakdown-quality test-video-server test-creation-board`（本机 Python 3.10 无 tomllib）。
- 已获项目文件夹删除权限并清理 `.git/stale-*`（100 个）与 `tests/video-page.test.js`。

### 未完成事项（更新后）

1. 部署 161 及以后版本，并在容器补测（见上）。
2. 用户待办：上传体验版；微信隐私指引按 `docs/privacy-creation-board.md` 最后一节填写；提交审核前关闭体验版测试账号；轮换 dtk 解析密钥；检查飞书 base 分享权限。
3. 额度审核 + 订阅消息（M18）：等用户给两个模板 ID 与管理员账号。
4. 飞书月度复盘仪表盘（M19）；中台展示 `admin_dashboard.methods`（目前只在接口里）。
5. 第160批的 4 个环境项在 Windows+Docker 本机补测后关闭本批。

### 续 2 · 2026-10-21 第二个会话

- 部署：设备 shell 到 `182.61.14.185:22` 仍 `Network is unreachable`，**HEAD 仍未部署**（线上仍是 1954057 对应版本）。请用户双击 `deploy-platform.cmd`（默认增量）或放开账号网络后用 `scripts/deploy-delta.sh`。
- 补测（第163次）：本机用 tomllib 垫片跑 `test-breakdown-quality` `test-video-server` `test-creation-board`，62/62 通过；修了 `test-video-server` 一处测试间 `_PARSE_CACHE` 串扰（只改测试文件）。方法写进 PROJECT-MAP 第5节。部署后仍需在容器里复跑一次同样命令。
- 清理：一次未设环境变量的运行在 `scripts/E:/` 建了空目录，已删除。
- 03:44 已部署 platform-3bb8bbf（容器 healthy，备份 platform-1954057）。注：该次部署工具报告被用户中断，但实际已执行完毕——中断后务必先查服务器 `remote-release.sh live` 再下结论。
- 网络：同一账号「所有域名」下，有的会话环境能直连服务器、有的只能走代理（22 端口被拒），原因未查明；连不上时用 `deploy-platform.cmd`。
- 第164次：文字作品补「发布正文」（见 test-batches）。后端待部署；小程序改动需用户上传体验版。
- 第165次：文字作品/创作包卡顶部附压缩原视频（新接口 `POST /board/preview`）。164、165 后端待部署；小程序需上传体验版。
- 04:34 已部署 platform-c79e8ef（含 164、165），健康正常，备份 platform-3bb8bbf。预览转码实测：19 秒/4.7MB → 0.84MB 用时 8.6 秒；81 秒/60MB → 2.5MB 用时 65 秒（首次打开长视频需等约 1 分钟，可优化为分析时后台预生成或复用台账 low.mp4）。
- 第166次：「接下来做什么」上方也放压缩原视频（仅小程序）。
- 第167次：裂变功能（文字作品卡「裂变 3 条」，`POST /board/variants`）。后端待部署，小程序需上传体验版。
- 第168次：原视频只在最新完成的板块显示（仅小程序）。
- 第169次：远程 MCP，见 `docs/mcp-remote.md`。dtk 已建 `youai-mcp` 密钥、服务器 config.json 已写；后端（含 167 裂变）待部署。
- 第170次：MCP 工具 download_video（服务器托管下载链接）。167/169/170 后端待一起部署。
- 2026-10-22 00:00 部署 platform-3936e72（含第167、169、170次），健康 200，modules ok 27，备份 platform-c79e8ef。公网验证：无令牌/错令牌 401；initialize 200（dtk 5.1.3，SSE）；tools/list 9 个工具（含 download_video）；download_video 真实链接 4.2 秒返回（作品 7693845706146340337，1080×1920，6.76 秒，2,206,939 字节），签名链接下载 200 video/mp4 字节一致，篡改签名 403；pool_status 正常；网关当日计数 1，dtk request_log 记在 youai-mcp 名下。
