# 测试批次记录

执行规则见 [AGENTS.md](../AGENTS.md)。每次完成的逻辑改动登记一行，与对应代码一起提交，可通过 `git log -- docs/test-batches.md` 查找对应提交。修复或重试更新原行，不新增计数。

## 批次 1（进行中：10/10；累计 10 次）

| 次数 | 日期 | 改动内容及影响范围 | 定向测试与结果 |
| --- | --- | --- | --- |
| 1 | 2026-10-10 | 调整 AGENTS.md 和 README 验证规则，新增批次记录及规则一致性测试；影响开发验证流程 | `node --test tests/test-policy.test.js`：2/2 通过；`git diff --check`：通过；无业务界面改动，界面验证不适用 |
| 2 | 2026-10-10 | 调整为每次定向、每五次范围汇总、每十次完整验证，重合时完整测试优先；影响规则、说明、批次记录及一致性测试 | `node --test tests/test-policy.test.js`：2/2 通过；`git diff --check`：通过；无业务界面改动，界面验证不适用 |
| 3 | 2026-10-10 | 删除创作工具、我的创作、每日一拆右侧辅助文案，清理主页面、热点、视频、模型与偏好设置、共享拆解入口的测试及开发阶段提示；保留功能状态、样例来源与教学内容 | `node --test --test-reporter=tap tests/interface-copy.test.js tests/creation-tools.test.js tests/analysis-presets.test.js tests/hotspot-discovery.test.js tests/creative-flow.test.js tests/creative-command.test.js tests/demo.test.js tests/account-layout.test.js tests/daily-pick.test.js tests/video-generation.test.js tests/creator-preferences.test.js tests/ai-config.test.js tests/model-insights.test.js tests/action-buttons.test.js tests/record-switch.test.js tests/liquid-glass.test.js`：70/70 通过；`git diff --check`：通过；通过 miniprogram-automator 检查四个主导航、编辑/发布/收益/关于视图及热点/创作档案/模型/拆解设置/视频/案例201六个页面；创作与学习截图目视确认标题及布局正常。初次界面检查的页面栈等待及教学文案匹配问题已修正后通过 |
| 4 | 2026-10-10 | 新增六工具接口管理页与只读公共/本机个人配置隔离，支持 HTTPS、请求方式、令牌、分工具保存清除及输入校验；工具入口直达配置；头像旁切换商家/创作者；补充接口权限边界说明 | `node --test --test-reporter=tap tests/tool-interfaces.test.js tests/creation-tools.test.js tests/account-layout.test.js tests/interface-copy.test.js tests/navigation.test.js tests/demo.test.js tests/creative-flow.test.js tests/analysis-presets.test.js tests/liquid-glass.test.js tests/action-buttons.test.js tests/test-policy.test.js`：48/48 通过；`node scripts/tool-interfaces-smoke.cjs`（YOUAI_AUTOMATOR_MODULE 指向外部依赖）：通过真实点击验证双向身份切换、更多设置入口、公共只读、个人配置保存重开及创作入口，并恢复原数据；截图目视通过；修复重复输入事件误标未保存及校验脚本等待/滚动问题后通过；`git diff --check`：通过。未执行接口网络调用，本轮不实现账号服务端鉴权 |
| 5 | 2026-10-10 | 删除“我的”快捷入口数量、查看任务提示、六项偏好摘要及更多设置副标题；保留名称、图标、箭头和交互 | 按第 5 次规则执行下方合并范围测试：87/87 通过；模拟器检查四个快捷入口、偏好列表及更多设置展开收起通过，截图目视确认无残留文案及空白占位；`git diff --check` 通过 |
| 6 | 2026-10-10 | 确认首阶段聚焦灵感、创作、学习及“我的”管理中心；补充前后端、同步、数据模型、接口、迁移和分阶段验收方案，明确暂缓商家、金额及独立中台 | `node --test tests/product-plan.test.js`：3/3 通过；`git diff --check`：通过；本次只更新方案与约束测试，无业务界面改动，界面验证不适用 |
| 7 | 2026-10-10 | 设计微信小程序、Web、App 共用的数据中台，新增统一资源与 API 契约、无依赖领域服务基线，并验证多端共享、账号隔离、幂等写入、版本冲突、删除墓碑及增量同步 | `node --test tests/backend-data-platform.test.js tests/backend-data-platform-doc.test.js tests/product-plan.test.js`：9/9 通过；`git diff --check`：通过；本次未改小程序界面，界面验证不适用 |

### 第 8 次：Codex HTTP 修复工具包

| 次数 | 日期 | 改动内容及影响范围 | 定向测试与结果 |
| --- | --- | --- | --- |
| 8 | 2026-10-10 | 新建独立 Codex HTTP 修复 MCP 服务、CLI、备份恢复与 MCPB 构建；默认 OpenAI 使用保留认证的 HTTP provider，自定义 provider 只关闭 WebSocket；小程序打包排除 tools/dist，补充入口说明 | `node --test tests/codex-http-repair.test.js tests/demo.test.js tests/test-policy.test.js`：19/19 通过；`git diff --check` 通过。首次测试发现 TOML null-prototype 比较与 Windows 子进程清理顺序问题，已修复并重跑本次完整范围通过。MCPB 官方清单校验与打包通过；解压实际包后 MCP 初始化、检查、修复、恢复通过；真实本机 Codex 对 localhost 模拟 Responses 服务直接 HTTP POST（无 Upgrade）通过。本机用户配置已备份并应用且 Codex 加载通过，真实外网连接效果待完全重启后确认，不记为已通过；未改业务 UI，无界面验证项 |
| 9 | 2026-10-10 | 基于 Demo 设计响应式网页版，新增四入口静态交互原型、桌面/移动布局、共享前端核心边界和实施顺序；明确小程序与 Web 分开展示层 | `node --test tests/web-app-design.test.js`：4/4 通过；`git diff --check`：通过；浏览器实际验证四入口切换、记录筛选和新增灵感通过，390px 移动视口确认底部四栏导航并隐藏右侧概览；首次桌面检查发现记录筛选文字受挤压，改为标题下方排列后复查通过 |
| 10 | 2026-10-10 | 新增开发主导方案与机器可检查的功能登记表，固定核心闭环、范围边界、阶段路线、需求准入、完成标准、联调关卡和变更控制；开发目录从小程序上传包排除，体积测试按实际打包规则计算 | 按第 10 次规则只执行完整测试 `node --test tests/*.test.js`：142/142 通过；先后发现延期文案断言过严、体积测试未读取打包排除项及批次规则固定短语缺失，修正后完整重跑通过；`git diff --check`：通过；本次无业务界面改动，界面验证不适用 |

### 第 5 次阶段检查（累计第 5 次）

- 最近五次汇总：第 1–2 次为测试规则和记录一致性；第 3 次为主页面、热点、视频、设置及拆解提示清理；第 4 次为工具接口配置、校验和身份切换；第 5 次为我的页面辅助文案精简。
- 范围测试命令与结果：`node --test --test-reporter=tap tests/test-policy.test.js tests/interface-copy.test.js tests/creation-tools.test.js tests/analysis-presets.test.js tests/hotspot-discovery.test.js tests/creative-flow.test.js tests/creative-command.test.js tests/demo.test.js tests/account-layout.test.js tests/daily-pick.test.js tests/video-generation.test.js tests/creator-preferences.test.js tests/ai-config.test.js tests/model-insights.test.js tests/action-buttons.test.js tests/record-switch.test.js tests/liquid-glass.test.js tests/tool-interfaces.test.js tests/navigation.test.js`：19 个文件，87/87 通过，替代本次定向测试。
- 必要集成或界面验证：第 3–4 次已完成相关页面及接口配置模拟器验证；本次补验我的页面精简布局、四个快捷入口和更多设置展开收起，截图目视通过。接口网络调用与服务端鉴权不在本批实现范围。
- 阶段状态：通过；继续累计，不关闭十次批次。

### 第 10 次完整检查（累计第 10 次）

- 整批汇总：第 1–2 次建立测试周期与记录规则；第 3–5 次精简界面文案、补齐工具接口管理与“我的”布局；第 6–10 次依次固定创作者三板块范围、统一多端数据契约、提供 Codex HTTP 修复工具包、完成响应式网页版原型、建立开发主导方案与功能登记表。最近五次（第 6–10 次）共同把产品范围、后端契约、开发环境、Web 展示和执行路线连成可追踪基线。
- 全量测试命令与结果：`node --test tests/*.test.js`（等价于 `npm test`）：142/142 通过；按完整测试优先规则不额外执行改动部位测试。
- 必要集成或界面验证：第 3–5 次的小程序页面和第 9 次的桌面/移动 Web 原型已完成实际交互与目视验证；第 6、7、10 次为方案、契约和登记表，无新增业务界面；第 8 次本地 MCP、配置备份恢复、模拟 Responses HTTP 请求和真实 Codex 本地 HTTP 链路已验证。
- 批次状态：完整测试通过；第 8 次修复后的真实外网连接仍需完全重启 Codex 后确认，按规则保留为待验证，本批暂不关闭且不重置计数。

## 批次 2（进行中：1/10；累计 11 次）

批次 1 的完整测试已经通过，但第 8 次外部连接验证仍保持待确认；后续改动继续按累计次数记录，不清除该待验证项。

| 次数 | 累计 | 日期 | 改动内容及影响范围 | 定向测试与结果 |
| --- | --- | --- | --- | --- |
| 1 | 11 | 2026-10-10 | 从 Demo 本机状态建立后端数据设计基线和机器可检查的数据目录；明确账号、灵感、项目版本、学习、设置、工具与同步表，旧数据拆分迁移、延期字段丢弃、密钥重录和首批六表范围 | `node --test tests/demo-backend-data-design.test.js tests/backend-data-platform-doc.test.js tests/development-master-plan.test.js tests/product-plan.test.js tests/test-policy.test.js`：15/15 通过；首次运行发现测试未展开通用用户字段组，修正后重跑通过；`git diff --check`：通过；本次无业务界面改动，界面验证不适用 |
| 2 | 12 | 2026-10-10 | 建立可部署后端运行基座、环境校验、数据库连接、存活/就绪检查、请求标识、迁移器、首批六表 PostgreSQL 正向/回滚迁移、本地 Compose 和长期云运行方案 | `node --test tests/backend-runtime.test.js tests/backend-data-platform.test.js tests/backend-data-platform-doc.test.js tests/demo-backend-data-design.test.js`：14/14 通过；首次运行发现默认异步检查缺少括号，修正后重跑通过；随后 `node --test tests/test-policy.test.js tests/backend-runtime.test.js`：6/6 通过，pnpm 锁定安装及后端数据库驱动、服务和迁移模块加载验证通过；`git diff --check`：通过。当时本机没有 Docker/PostgreSQL，容器与真实迁移验证留待第 13 次完成；本次无业务界面改动 |
| 3 | 13 | 2026-10-11 | 安装 Docker Desktop 与 WSL，构建并启动 PostgreSQL、YOUAI API 两个容器；执行首批迁移，增加双容器自动恢复策略和 API 健康检查 | `node --test tests/backend-runtime.test.js tests/test-policy.test.js`：6/6 通过；Docker Desktop 4.94.0、Engine 29.8.2、Compose 5.5.1 安装完成；两个容器构建与启动通过，`001_identity_and_ideas` 已应用，六张首批表与迁移记录表存在，ideas/change_log/idempotency_keys RLS 开启；受控重启后两个容器均为 healthy，迁移仍存在，live=ok、ready=ready、重启策略均为 unless-stopped；`git diff --check`：通过；本次无业务界面改动 |
| 4 | 14 | 2026-10-11 | 将视频创作入口统一为点子、抖音分享链接和模板口令三种来源；只确认内容目标、画面形式与时长，提交时保留来源和成片意图；影响视频页、创作档案默认值、口令解析与本机视频服务说明 | `node --test tests/video-generation.test.js tests/creator-preferences.test.js tests/creative-command.test.js tests/creation-tools.test.js tests/test-policy.test.js`：23/23 通过；`git diff --check`：通过。已检查三入口、三阶段、全部页面事件及统一任务载荷；开发者工具自动化因当前环境没有 `miniprogram-automator` 未执行，界面实机布局与三类真实输入联调保持待验证；本机合成服务仍只支持纯文字视频，文档已明确能力边界 |
| 5 | 15 | 2026-10-11 | 将创作首页突出展示的三个入口改为点子、抖音参考视频和模板口令，并携带来源参数直达视频创作页对应输入状态；保留灵感列表中的点子直达能力 | 按第 15 次规则执行下方最近五次合并范围测试：62/62 通过；`git diff --check`：通过。自动测试验证三个入口、来源路由、视频工作流、主页面既有创作闭环及第 11–13 次后端设计和运行基座；当前环境仍缺少 `miniprogram-automator`，开发者工具实际点击与截图复查保持待验证 |
| 6 | 16 | 2026-10-11 | 将成片时长改为 2–30 秒滑杆并增加智能时长模式；抖音链接粘贴后请求读取判定，展示读取中、成功或失败，未成功时阻止继续；本机服务同步支持任意 2–30 秒整数，并补齐 `/references/read` 的短链展开、视频 ID 与页面信息读取 | `node --test tests/video-generation.test.js tests/creator-preferences.test.js tests/creative-command.test.js tests/test-policy.test.js`：22/22 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：4/4 通过并实际生成、完整解码 MP4；`POST http://127.0.0.1:8765/references/read` 使用截图中的真实短链返回 `status=read`、视频 ID `7397005934863732019` 与页面标题；`git diff --check`：通过。读取成功证明服务可访问并识别视频页面，不等同于已完成视频语义分析 |
| 7 | 17 | 2026-10-11 | 视频创作默认时长改为手动 2 秒并迁移旧默认值；“AI 生成画面”接入已配置的千问 wan3.0-video 异步生成，“纯文字画面”保留本机合成；抖音页面标题和描述随任务进入 AI 提示词；补写 README 最近两日能力、启动方法和边界 | `node --test tests/video-generation.test.js tests/creator-preferences.test.js tests/test-policy.test.js`：18/18 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：5/5 通过；真实千问任务 `3f826597-e33e-4c90-87a0-3c0713317c56` 成功，下载 MP4 为 1,598,211 字节，解码信息为 H.264、720×1280、2.02 秒；服务重启后 `/health` 返回 `qianwen-video` 与 `local-text-renderer`；`git diff --check`：通过 |
| 8 | 18 | 2026-10-11 | 建立跨 Agent 双向交接说明，固化当前功能与运行基线、文件地图、密钥和付费边界、已知风险、接手检查、持续记录规则及未来回交契约；README 增加统一交接入口 | `node --test tests/agent-handoff.test.js tests/test-policy.test.js`：4/4 通过；视频服务 `/health` 返回 `qianwen-video` 与 `local-text-renderer`，`codexyouai-api-1` 和 `codexyouai-postgres-1` 均为 healthy；`git diff --check`：通过；本次只更新交接资料与约束测试，无业务界面改动，界面验证不适用 |
| 9 | 19 | 2026-10-11 | 生成等待页增加提交、排队、生成画面、取回成片的阶段反馈，展示真实等待时长和任务号缩写；服务端返回阶段与耗时，前端每 2 秒轮询并将等待上限由 180 秒对齐为 1800 秒；同步更新 README 和 Agent 交接状态 | `node --test tests/video-generation.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：16/16 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：5/5 通过，覆盖 PENDING、RUNNING、SUCCEEDED 和下载阶段；服务重启后 `/health` 返回正常；`git diff --check`：通过。自动测试验证状态文案、等待时间格式、三阶段和超时配置；当前未运行微信开发者工具，动画和窄屏视觉效果待模拟器复查 |
| 10 | 20 | 2026-10-11 | 建立每次任务实施前登记的任务台账，记录起始提交、用户目标、产品规则、分阶段状态、决策限制、交接入口和完成信息；登记参考视频分析到成片工作流升级任务，并同步 README 与 Agent 交接入口 | 按第 20 次规则只执行完整测试；当前 PowerShell 环境没有 `npm` 命令，改用规则声明的等价命令 `node --test tests/*.test.js`：160/160 通过；`git diff --check`：通过；本次只建立任务与交接基线，无业务界面改动，界面验证不适用 |

### 第 15 次阶段检查（累计第 15 次）

- 最近五次汇总：第 11 次建立 Demo 后端数据设计基线；第 12 次建立可部署后端运行与迁移基座；第 13 次完成 Docker、PostgreSQL 和 API 双容器运行验证；第 14 次统一三种视频创作输入及成片意图；第 15 次让创作首页三个入口分别直达对应输入。
- 范围测试命令与结果：`node --test tests/demo-backend-data-design.test.js tests/backend-data-platform-doc.test.js tests/development-master-plan.test.js tests/product-plan.test.js tests/test-policy.test.js tests/backend-runtime.test.js tests/backend-data-platform.test.js tests/video-generation.test.js tests/creator-preferences.test.js tests/creative-command.test.js tests/creation-tools.test.js tests/navigation.test.js tests/demo.test.js tests/creative-flow.test.js`：14 个文件，62/62 通过，替代本次定向测试。
- 必要集成或界面验证：第 13 次已完成真实容器、数据库迁移和健康检查；第 14–15 次已通过页面事件、来源路由和任务载荷自动测试。当前环境缺少 `miniprogram-automator`，小程序开发者工具中的三个入口实际点击和视觉布局仍待验证。
- 阶段状态：范围测试通过；界面验证限制保留记录，继续累计至第 20 次完整测试。

批次 2 累计第 15 次执行最近五次范围测试，第 20 次执行完整测试；批次 1 的外部验证结果补记在原批次，不改变本批计数。

### 第 20 次完整检查（累计第 20 次）

- 整批汇总：第 11–13 次建立后端数据设计、数据库迁移和 Docker 运行基座；第 14–17 次打通三种创作入口、时长控制、参考链接识别与千问视频生成；第 18–20 次补齐跨 Agent 交接、生成进度反馈和任务启动台账。最近五次（第 16–20 次）覆盖参考读取、模型路由、任务交接、等待反馈与本轮升级入口。
- 全量测试命令与结果：当前 PowerShell 环境没有 `npm` 命令，执行规则声明的等价命令 `node --test tests/*.test.js`：160/160 通过；按完整测试优先规则未额外执行定向测试。
- 必要验证：第 16–17 次已完成真实参考链接读取、本机 MP4 解码和千问真实任务；第 18、20 次为文档与约束，无业务界面；第 19 次的动画与窄屏视觉仍需微信开发者工具复查。批次 1 的 Codex 外网重连验证仍按原记录保留。
- 批次状态：完整测试通过；累计计数关闭至第 20 次，下一项逻辑改动从累计第 21 次开始。

## 批次 3（已完成：10/10；累计 30 次）

后续改动从累计第 21 次登记；第 25 次执行最近五次范围测试，第 30 次执行完整测试。

| 次数 | 累计 | 日期 | 改动内容及影响范围 | 定向测试与结果 |
| --- | --- | --- | --- | --- |
| 1 | 21 | 2026-10-11 | 建立参考视频到成片的持久化资产图谱：新增媒体哈希去重、版本化分析、镜头、三种参考方式故事板、生成任务、产物血缘、显式反馈和成本表；增加状态转换、请求脱敏、成本与血缘领域契约及长期/临时资产说明 | `node --test tests/video-asset-pipeline.test.js tests/backend-runtime.test.js tests/backend-data-platform.test.js tests/test-policy.test.js`：14/14 通过；首次运行仅发现 JavaScript 浮点四舍五入断言期望不符，修正断言后同范围重跑通过；重建 API 容器后真实应用 `002_video_asset_pipeline`，7 张新表均存在且 RLS、强制 RLS 开启，`/health/live` 与 `/health/ready` 正常；`git diff --check`：通过；本次无业务界面改动 |
| 2 | 22 | 2026-10-11 | 在实现前登记阶段 C 的起始提交、媒体获取状态、失败上传回退、非付费测试范围和可恢复验收标准，确保跨 Agent 中断后可从同一边界继续 | `node --test tests/task-ledger.test.js tests/test-policy.test.js`：5/5 通过；`git diff --check`：通过；本次只登记实施任务，无业务界面改动 |
| 3 | 23 | 2026-10-11 | 将参考链接处理拆为识别与媒体获取：新增自托管解析器适配器、HTTPS/内网地址/200MB/FFmpeg 解码门禁、SHA-256 去重落盘；页面只有 `acquired` 才显示素材就绪，获取失败要求上传，且在内容分析完成前禁止把网页元数据提交给生成模型 | `C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：8/8 通过，包含真实 2 秒 MP4 下载、哈希、重复获取、解码和禁止网页元数据冒充分析；`node --test tests/video-generation.test.js tests/creator-preferences.test.js tests/creative-command.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：28/28 通过；视频服务受控重启后 `/health` 正常；`git diff --check`：通过；自托管解析器尚未部署，真实抖音媒体获取和小程序上传入口待后续完成 |
| 4 | 24 | 2026-10-11 | 在编码前登记解析服务未配置的现场问题，明确“我的 → 工具接口管理 → 视频下载”为易失效地址、凭据、检测状态和恢复入口，并固定密钥不落库、不进日志与历史的边界 | `node --test tests/task-ledger.test.js tests/test-policy.test.js`：6/6 通过；`git diff --check`：通过；本次只登记实施任务，无业务界面改动 |
| 5 | 25 | 2026-10-11 | 将易失效的参考解析器地址、Bearer 凭据、连接结果和过期状态放入“我的 → 工具接口管理 → 视频下载 / 参考解析”；新增 OpenAPI 契约检测、7 天复检门禁、创作页临时传递配置和失败时直达配置入口 | 按第 25 次规则执行下方最近五次合并范围测试；Python 视频服务测试 9/9 通过；服务受控重启及配置检测路由验证通过；`git diff --check`：通过 |
| 6 | 26 | 2026-10-12 | 在部署前登记解析器选型、本机隔离部署、重启恢复、“我的”配置和真实短链媒体获取验收标准，并明确平台风控时保留诊断和上传回退 | `node --test tests/task-ledger.test.js tests/test-policy.test.js`：7/7 通过；`git diff --check`：通过；本次只登记部署任务，无业务界面改动 |
| 7 | 27 | 2026-10-12 | 部署 Douyin_TikTok_Download_API v5.1.3 完整栈与浏览器身份池，将平台公共参考解析服务接入“我的”和视频创作入口；视频服务支持回环 HTTP 上游、DTK 等待式解析响应和仓库外密钥启动脚本 | `node --test tests/tool-interfaces.test.js tests/video-generation.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：30/30 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：9/9 通过；真实链接取得 6,230,796 字节 H.264、1080×1920、29.87 秒视频并完成 SHA-256 与 FFmpeg 验证；Docker 服务均 healthy；`git diff --check`：通过 |
| 8 | 28 | 2026-10-12 | 在实施前登记参考解析等待进度任务，明确四阶段、等待计时、失败阶段、重试清理及不把估算当服务端状态的边界 | `node --test tests/task-ledger.test.js tests/test-policy.test.js`：8/8 通过；`git diff --check`：通过；本次只登记实施任务，无业务界面改动 |
| 9 | 29 | 2026-10-12 | 参考视频解析输入卡增加识别、解析、下载、校验四阶段和逐秒等待反馈；成功显示媒体摘要，失败保留所在阶段，输入变化和离页清理计时 | `node --test tests/video-generation.test.js tests/task-ledger.test.js tests/test-policy.test.js`：21/21 通过；真实 DTK 与 YOUAI 视频服务健康检查通过；`git diff --check`：通过；当前环境没有 `miniprogram-automator`，窄屏阶段条需在开发者工具复查 |
| 10 | 30 | 2026-10-12 | 在实施前登记 ReferenceAnalysis v1 内容分析闭环，明确分析任务、结构化证据、长期资产、同源复用、页面进度和禁止网页元数据冒充分析的边界 | 按第 30 次规则只执行下方完整测试；本次只登记实施任务，无业务界面改动 |

### 第 30 次完整检查（累计第 30 次）

- 整批汇总：第 21–23 次建立视频资产图谱和真实媒体获取门禁；第 24–27 次补齐解析配置恢复、自托管 DTK 部署与公共服务接入；第 28–29 次登记并实现解析等待反馈；第 30 次登记内容分析闭环。最近五次（第 26–30 次）覆盖解析器部署、公共服务、解析进度和内容分析入口。
- 全量测试命令与结果：按完整测试优先规则执行 `node --test tests/*.test.js`：171/171 通过；未重复执行本次定向测试。
- 必要验证：本次只登记实施任务，无业务界面改动；`git diff --check` 通过。第 27 次已完成真实 DTK 媒体获取，第 29 次解析进度的开发者工具窄屏复查限制继续保留。
- 批次状态：完整测试通过，累计计数关闭至第 30 次；下一项逻辑改动从累计第 31 次开始。

## 批次 4（进行中：1/10；累计 31 次）

后续改动从累计第 31 次登记；第 35 次执行最近五次范围测试，第 40 次执行完整测试。

| 次数 | 累计 | 日期 | 改动内容及影响范围 | 定向测试与结果 |
| --- | --- | --- | --- | --- |
| 1 | 31 | 2026-10-12 | 打通 ReferenceAnalysis v1：服务端异步抽帧、画面变化检测、faster-whisper 音轨转写、结构化证据与 SHA 缓存；小程序展示三阶段分析进度、摘要、策略和失败重试，分析完成后进入方向确认 | `node --test tests/video-generation.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：24/24 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：10/10 通过；真实 29.87 秒视频完成 6 帧、5 个变化点和中文音轨转写；`git diff --check`：通过；开发者工具视觉复查待执行 |
| 2 | 32 | 2026-10-12 | 实施前登记失效抖音短链诊断与恢复任务：区分短链失效、解析器故障和配置异常，明确解析器优先、错误码保留、凭据保护与禁止仅凭分享文案静默替换视频 | `node --test tests/task-ledger.test.js tests/test-policy.test.js`：10/10 通过；`git diff --check`：通过；本次只登记任务，不改业务行为 |
| 3 | 33 | 2026-10-12 | 修复失效抖音短链诊断：解析器优先接收原短链，保留并映射上游失败原因；页面区分短链过期与配置失效，提供重新复制、上传或接口检测动作；清理链接尾随中文标点 | `node --test tests/video-generation.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：26/26 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：11/11 通过；服务重启后 `/health` 正常，同一失效短链真实返回 `short_link_expired` 与 `replace_or_upload`；`git diff --check`：通过 |
| 4 | 34 | 2026-10-12 | 实施前登记参考分析提交生成任务失败修复：确认真实分析结果超过统一 4 KB POST 上限，计划按接口设置上限、裁剪生成载荷并返回明确超限错误 | `node --test tests/task-ledger.test.js tests/test-policy.test.js`：11/11 通过；`git diff --check`：通过；本次只登记任务，不改业务行为 |
| 5 | 35 | 2026-10-12 | 修复参考分析提交生成任务被统一 4 KB 上限拒绝：按接口设置 8–64 KB 上限，区分超限与 JSON 错误；生成载荷只保留分析证据与素材哈希，移除本地路径及重复媒体信息 | 按第 35 次规则执行下方最近五次范围测试，不重复执行本次定向测试；真实 4,619 字节分析生成请求由 `local-text` 成功完成，未触发付费模型 |
| 6 | 36 | 2026-10-12 | 实施前登记生成前沟通与可编辑故事板任务：动态补充受众、核心信息、开场、语气、行动与内容边界，要求故事板审核通过后才生成，并保留版本和本次修改 | `node --test tests/task-ledger.test.js tests/test-policy.test.js`：12/12 通过；`git diff --check`：通过；本次只登记任务，不改业务行为 |
| 7 | 37 | 2026-10-12 | 将三阶段生成升级为四阶段沟通闭环：按来源动态确认结果、受众、开场、语气、画面、结尾和参考模式，支持必须出现/不要出现；生成可编辑三段故事板并设置批准门禁；服务端校验并把批准分镜与约束写入提示词，纯文字成片也按分镜文案生成 | `node --test tests/video-generation.test.js tests/creator-preferences.test.js tests/creative-command.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：40/40 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：13/13 通过；真实批准任务由 `local-text` 完成，未批准任务返回“请先确认分镜草案”，未调用付费模型；`git diff --check`：通过；当前未运行微信开发者工具，窄屏故事板视觉复查待执行 |
| 8 | 38 | 2026-10-12 | 实施前登记单条视频资产包与持久化血缘任务：长期保存参考原片、分析、代表帧、沟通答案、故事板、脱敏请求、实际提示词、Provider 任务、成片、成本与血缘，并在成片页提供查看入口 | `node --test tests/task-ledger.test.js tests/test-policy.test.js`：13/13 通过；`git diff --check`：通过；本次只登记任务，不改业务行为 |
| 9 | 39 | 2026-10-12 | 建立单条视频持久资产包：原片按 SHA 去重、保留分析与 6 张代表帧、沟通答案、批准故事板、脱敏请求、实际提示词、Provider 信息、长期成片和血缘；事务写入 PostgreSQL 六类资产表，成片页可查看资产摘要，服务重启后仍可回看 | `node --test tests/video-generation.test.js tests/backend-runtime.test.js tests/video-asset-pipeline.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：42/42 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：14/14 通过；真实本地运行 `3b4521a1141f489da1434e802688254c` 持久化成功，数据库记录为媒体 2、分析 1、镜头 3、故事板 1、任务 1、产物 1；视频服务重启后资产清单可查且成片 Range 请求返回 206；`git diff --check`：通过；未调用付费模型 |
| 10 | 40 | 2026-10-12 | 修复抖音解析成功后 CDN 下载 403：视频候选优先、抖音来源页请求头、备用地址回退和安全的下载受限错误；清理占用端口的旧服务子进程并完成同一短链真实复测 | 按第 40 次规则只执行下方完整测试；Python 服务测试 16/16 通过；真实取得 3,481,097 字节 H.264、1080×1920、14.63 秒视频并完成 SHA-256 与 FFmpeg 校验；未调用付费模型 |

### 第 40 次完整检查（累计第 40 次）

- 整批汇总：第 31–35 次完成参考内容分析、失效短链诊断和生成载荷修复；第 36–37 次完成生成前沟通与故事板门禁；第 38–39 次完成持久资产包；第 40 次修复解析成功后的 CDN 下载限制。最近五次（第 36–40 次）覆盖沟通、故事板、资产持久化和参考媒体可靠获取。
- 全量测试命令与结果：当前 shell 无 `npm` 命令，使用其等价命令 `C:\Users\one\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --test tests/*.test.js`：181/181 通过；按完整测试优先规则未重复执行 Node 定向测试。
- 必要验证：`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：16/16 通过；服务清理旧子进程并受控重启后 `/health` 正常，截图短链真实返回 `acquired`，作品 `7694499467496319331` 为 3,481,097 字节、H.264、1080×1920、14.63 秒且有音轨；未调用付费模型。`git diff --check` 通过。
- 批次状态：完整测试通过，累计计数关闭至第 40 次；下一项逻辑改动从累计第 41 次开始。

## 批次 5（进行中：1/10；累计 41 次）

后续改动从累计第 41 次登记；第 45 次执行最近五次范围测试，第 50 次执行完整测试。

| 次数 | 累计 | 日期 | 改动内容及影响范围 | 定向测试与结果 |
| --- | --- | --- | --- | --- |
| 1 | 41 | 2026-10-12 | 最近生成按点子、抖音原视频标题或模板主题形成可辨识标题并标注来源，兼容旧历史；新增“我的 → 视频资产”集中入口，查看、重开、展开资产详情和移除本机索引，并说明本机索引、长期文件和数据库元数据的存储边界 | `node --test tests/video-history.test.js tests/video-generation.test.js tests/account-layout.test.js tests/navigation.test.js tests/project-config.test.js tests/task-ledger.test.js tests/test-policy.test.js`：43/43 通过；`git diff --check`：通过 |
| 2 | 42 | 2026-10-12 | 修复成片页资产摘要无法点击：五类资产可逐项展开，原片和代表帧通过受控接口预览，故事板、脱敏提示词和血缘可读；公开资产清单移除服务器绝对路径并校验文件位于资产根目录 | `node --test tests/video-generation.test.js tests/video-history.test.js tests/task-ledger.test.js tests/test-policy.test.js`：34/34 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：17/17 通过；真实运行 `4867d983d67a4eaa97523da73b945a28` 的原片返回 206、代表帧返回 200，公开清单无绝对路径；`git diff --check`：通过 |
| 3 | 43 | 2026-10-12 | 修复参考媒体没有真正进入生成模型：默认把最多 3 张代表帧作为 `reference_image` 提交；高度参考原片改用 30 分钟签名 HTTPS URL，并在缺配置、过期或超过 15 秒时于付费调用前明确拦截；生成前展示模型实际收到的素材 | `node --test tests/video-generation.test.js tests/video-asset-pipeline.test.js tests/backend-runtime.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：42/42 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：18/18 通过；真实资产 `294bc5603d1d…` 无付费干跑生成 3 个 `reference_image`（载荷约 50 KB、48 KB、47 KB）；未调用付费模型；`git diff --check`：通过 |
| 4 | 44 | 2026-10-12 | 修复 24 小时内第三次“无法解析”：确认本次为 Docker、DTK 和视频网关均未启动；新增依赖感知的一键恢复脚本、登录与每 5 分钟运行的 Windows 计划任务、并发锁、日志和卸载入口 | `node --test tests/video-stack-watchdog.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：16/16 通过；Windows PowerShell 实机恢复 Docker 与 DTK 后 `/readyz`、`/health` 均为 200；截图链接真实取得 4,148,666 字节 H.264 1080×1920、14.57 秒视频；未调用付费模型；`git diff --check`：通过 |
| 5 | 45 | 2026-10-12 | 打通低成本“高度参考原片”：独立最小权限媒体中继、仓库外随机密钥、30 分钟 HMAC URL、Cloudflare HTTPS Tunnel 与守护恢复；方向页实时检测通道，未就绪时禁选 | 按第 45 次规则执行下方最近五次范围测试，不重复执行本次定向测试；真实 4,148,666 字节参考原片通过公网签名 URL Range 读取 1,024 字节，返回 206 与正确 Content-Range；未调用付费模型 |
| 6 | 46 | 2026-10-12 | 将首页六个创作工具从接口配置入口改成可执行工作台：视频下载、音轨转写、MP3、无水印原片和代表封面共享链接索引与 SHA 原片缓存；新增白名单资产接口；提词器本地支持滚动、暂停、速度、字号和镜像 | `node --test tests/creation-tools.test.js tests/tool-interfaces.test.js tests/navigation.test.js tests/project-config.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：35/35 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：21/21 通过；真实 14.57 秒抖音视频生成 53,554 字节 JPEG 与 351,287 字节 MP3，后续工具确认复用原片，转写无清晰人声并如实返回空结果；服务重启及 `/health` 通过；`git diff --check`：通过 |
| 7 | 47 | 2026-10-12 | 将 Wan3.0 模式、清晰度、宽高比、手动/智能时长、声音、提示词优化和水印开放给用户确认；参数实际进入 Provider 请求和资产清单；首尾帧模式抽取原片边界帧并与 reference 素材互斥，高度参考校验输入加输出总时长 | `node --test tests/video-generation.test.js tests/creator-preferences.test.js tests/video-asset-pipeline.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：44/44 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：22/22 通过；未调用付费模型；本机纯文字 Provider 的真实 `/jobs` 链路保存 1080P、1:1、`duration=-1`、静音和关闭提示词优化；`git diff --check`：通过 |
| 8 | 48 | 2026-10-12 | 修复代表帧抽取单点失败导致整段分析中止：采样改为分段中点，失败后精确解码重试并允许至少 3 帧的部分降级；新增智能、精简、标准、细致四档，档位进入请求、缓存和分析资产 | `node --test tests/video-generation.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：36/36 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：23/23 通过，包含单采样点连续失败后 5/6 帧降级完成；视频服务受控重启后 `/health` 正常，现场 15.09 秒、2,063,636 字节原片经真实 `/references/analyze` 智能档在 1.26–13.83 秒成功抽取 6/6 帧；未调用付费模型；`git diff --check`：通过 |
| 9 | 49 | 2026-10-12 | 修复页面显示 15 秒但容器精确时长 15.09 秒导致高度参考被拦截：15.00–15.50 秒自动转码为 14.9 秒派生素材，保留原片、派生 SHA 和血缘；明显超长继续在付费调用前阻止，分镜页提前说明规范化 | `node --test tests/video-generation.test.js tests/video-asset-pipeline.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：41/41 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：24/24 通过；现场 15.09 秒、2,063,636 字节原片生成 14.90 秒、5,284,196 字节、H.264 1080×1920 且有音轨的派生素材，原片未覆盖并写入 SHA 血缘；派生 SHA 的公网签名 URL Range 返回 206、1,024 字节及正确 Content-Range；未调用付费模型；`git diff --check`：通过 |

### 第 45 次阶段检查（累计第 45 次）

- 最近五次汇总：第 41 次完成智能标题、来源和资产管理入口；第 42 次让五类资产可查看；第 43 次把代表帧与参考原片真正提交模型；第 44 次建立解析栈自动恢复；第 45 次打通限时签名的原片 HTTPS 中继并增加可用性门禁。
- 范围测试命令与结果：`node --test tests/video-history.test.js tests/video-generation.test.js tests/account-layout.test.js tests/navigation.test.js tests/project-config.test.js tests/video-asset-pipeline.test.js tests/backend-runtime.test.js tests/video-stack-watchdog.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：57/57 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：20/20 通过；按规则未重复执行单项定向测试。
- 必要验证：视频服务受控重启后 `/reference-relay/status` 返回 `ready=true`；真实参考原片通过 TryCloudflare 签名 URL 返回 206、1,024 字节及 `bytes 0-1023/4148666`。中继未公开任务和资产接口，密钥未进入仓库；未调用付费模型；`git diff --check`：通过。
- 阶段状态：最近五次范围测试通过；继续累计至第 50 次完整测试。

### 第 35 次阶段检查（累计第 35 次）

- 最近五次汇总：第 31 次完成 ReferenceAnalysis v1；第 32、34 次分别登记失效短链与生成请求失败任务；第 33 次修复失效短链诊断；第 35 次修复真实分析载荷超过统一请求上限的问题。
- 范围测试命令与结果：`node --test tests/video-generation.test.js tests/creator-preferences.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：5 个文件，33/33 通过；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：12/12 通过；`git diff --check`：通过。
- 必要验证：视频服务受控重启后 `/health` 正常；使用真实 `ReferenceAnalysis v1` 组成 4,619 字节请求提交 `/jobs`，任务成功创建并完成，Provider 为 `local-text`。未调用付费 AI 视频模型。
- 阶段状态：最近五次范围测试通过；继续累计至第 40 次完整测试。

### 第 25 次阶段检查（累计第 25 次）

- 最近五次汇总：第 21 次建立视频资产、分析、分镜、任务、成本、反馈和血缘契约；第 22、24 次分别登记素材获取和配置恢复任务；第 23 次建立真实媒体获取、哈希与解码门禁；第 25 次把解析器配置、检测、过期提醒和恢复入口接入“我的”及创作页。
- 范围测试命令与结果：`node --test tests/video-asset-pipeline.test.js tests/backend-runtime.test.js tests/backend-data-platform.test.js tests/video-generation.test.js tests/tool-interfaces.test.js tests/creation-tools.test.js tests/account-layout.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：10 个文件，47/47 通过，替代本次定向测试；`C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/test-video-server.py`：9/9 通过。
- 必要验证：真实 PostgreSQL 的 `002_video_asset_pipeline` 已应用且强制 RLS；参考媒体下载、SHA-256 去重和 FFmpeg 解码使用真实 2 秒 MP4 验证；配置连接使用 Mock OpenAPI 契约验证。自托管解析器尚未部署，因此真实抖音媒体获取仍待配置后联调。
- 阶段状态：最近五次范围测试通过；视频服务受控重启后 `/health` 正常，`/references/config/check` 对非 HTTPS 配置返回 422；真实解析器联调限制继续保留。

### 第 50 次完整检查（累计第 50 次，面板验证待完成）

- 第 50 次改动：开启组件按需注入；学习专用 JS 移入五个分包；14 张案例详情图片移入对应分包，封面保留主包且图片不重新编码。增加上传质量测试，更新共享学习页面测试路径及旧视频历史存储键测试。
- 最近五次汇总：第 46 次六工具执行工作台；第 47 次 Wan 参数；第 48 次抽帧容错和采样；第 49 次原片时长规范化；第 50 次分包和上传质量优化。
- 最近十次汇总：第 41–45 次标题与资产入口、资产展开、真实参考媒体、解析守护和媒体中继；第 46–50 次见上方最近五次。
- 按完整测试优先规则执行 `node --test tests/*.test.js`：193/193 通过；未另跑定向测试。初次全量发现旧测试仍从 `pages/video/index.js` 读取已迁移的历史存储键，更新为当前 `utils/video-history.js` 后完整范围重跑通过。
- 微信开发者工具 CLI `preview` 成功：主包 431,246 字节；各分包 539,243–1,562,046 字节；总包 5,797,482 字节。主包媒体 164,519 字节。清理编译/文件列表缓存并重新打开项目后，首页及五个学习分包均可读取页面数据，视频准备完成且 `error=false`，代表页截图保存在仓库外 `E:\data\codexYOUAI-data\upload-quality-study.jpg`。
- 限制：桌面窗口截图 API 连续超时，官方模拟器接口可用但未提供代码质量面板结果；三项面板最终绿灯尚待用户重新执行检查并核验。到期必要检查保持待验证，累计第 50 次批次不关闭、不清零。

### 第 50 次同项补充：所有分包媒体总量（2026-10-12）

- 用户质量面板确认前两项通过、媒体项仍失败。修正初次仅约束主包与单文件的遗漏：全部分包 65 个媒体文件共 611,594 字节，现经 JPEG 编码压缩为 187,799 字节，低于 200,000 字节；23 张 JPEG 尺寸不变，主要字幕可读但图片细节有损，原片视频编码不变。
- 原图与 SHA 恢复清单在 `E:\data\codexYOUAI-data\backups\upload-media-20261012`，不进入上传包。
- 测试改为全部上传分包媒体合计门槛；完整范围重跑 `node --test tests/*.test.js`：193/193 通过，`git diff --check` 通过。微信开发者工具重新 preview 成功：主包 333,311 字节，总包 5,399,567 字节；代表学习页正常显示，截图在仓库外 `upload-quality-compressed.jpg`。
- 属于第 50 次逻辑改动修复，不新增次数。面板最终绿灯仍需重新扫描核验；保留第 50 次批次待验证状态。

## 批次 6（累计第 51 次；第 50 次面板验证仍保留待验证）

| 次数 | 累计 | 日期 | 改动内容及影响范围 | 验证 |
| --- | --- | --- | --- | --- |
| 1 | 51 | 2026-10-12 | 云端创作与飞书矩阵专项规划，P0–P5、资源权益、六表、成本/归档/权限/交接标准；README、主导方案和交接入口关联 | `node --test tests/cloud-creation-roadmap.test.js tests/development-master-plan.test.js tests/product-plan.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：24/24 通过；`git diff --check` 通过。第 50 次历史面板验证未关闭；本次只交付规划 |

| 2 | 52 | 2026-10-12 | 用户确认尚未建应用，交付飞书六表契约、两组织建表 CLI 与配置说明；默认预演、token 缓存、按名称续建、字段/关系冲突拦截、仓库外凭据/状态与错误脱敏 | `node --test tests/feishu-matrix.test.js tests/cloud-creation-roadmap.test.js tests/backend-data-platform.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：24/24 通过；零网络六表预演成功；真实飞书建表待应用授权；`git diff --check` 通过 |

| 3 | 53 | 2026-10-12 | 飞书工具支持单组织初始化与状态合并，便于企业四表先建、商业版两表后接；真实 Base 可读但创建被 403/91403 拒绝，实际建表待应用写入权限 | `node --test tests/feishu-matrix.test.js tests/cloud-creation-roadmap.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：20/20 通过；`git diff --check` 通过；真实建表未通过，继续同一任务补充验证 |

第 53 次同项补充：文档应用编辑授权后发现建表请求缺少必需索引字段，已补齐且测试约束该请求组合。真实企业四表创建成功，分别 8/10/11/10 字段，回读无缺失，方案与反馈关联作品验证通过；20/20 定向范围重跑通过。商业版两表、业务同步和文件归档未接通，不新增计数。

| 4 | 54 | 2026-10-12 | 用户改为商业标准版统一六表；工具支持 unified 单组织布局，保留双组织兼容与内部关系；新应用鉴权成功，真实建表待新 Base 链接 | `node --test tests/feishu-matrix.test.js tests/cloud-creation-roadmap.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：21/21 通过；`git diff --check` 通过；旧企业四表保留 |

| 5 | 55 | 2026-10-12 | 商业标准版统一六表真实初始化和回读：61 字段、三项关联、重跑去重；旧企业表和状态保留，不写业务记录 | 按第 55 次规则执行最近五次范围：`node --test tests/feishu-matrix.test.js tests/cloud-creation-roadmap.test.js tests/backend-data-platform.test.js tests/development-master-plan.test.js tests/product-plan.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：32/32 通过；真实接口六表字段类型和关联验证成功，二次运行无重复；`git diff --check` 通过 |

### 第 55 次阶段检查

最近五次（51–55）覆盖云端规划、飞书六表建表工具、企业阶段初始化、统一商业版布局和真实六表创建；上方八文件合并范围测试 32/32 通过。第 50 次历史质量面板待验证仍保留，不清除该限制；下一完整测试点为第 60 次。

| 6 | 56 | 2026-10-12 | 持久归档队列、六表业务同步、分片上传与下载哈希校验、安全恢复、反馈、小程序状态及重试恢复入口 | `node --test tests/asset-lifecycle.test.js tests/video-generation.test.js tests/video-history.test.js tests/feishu-matrix.test.js tests/video-asset-pipeline.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：50/50；`python scripts/test-asset-archive.py`：4/4；`python scripts/test-video-server.py`：24/24。真实飞书样片归档与 9 文件恢复、普通生成自动归档通过；开发者工具状态和按钮截图核验通过；`git diff --check` 通过。第 50 次历史面板限制保留，云端正式手机仍待部署 |

本次截图：仓库外 `E:\data\codexYOUAI-data\asset-lifecycle-ui-bottom.jpg`。真实验证只上传合成样片，无付费模型调用，不自动归档已有用户文件。配置与云端文件令牌保存在仓库外。

| 7 | 57 | 2026-10-12 | 云端只读盘点脚本和生产部署步骤，明确开发密码、用户隔离、Linux 依赖及手机验收门禁 | `node --test tests/cloud-preflight.test.js tests/cloud-creation-roadmap.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：19/19；Git Bash `bash -n scripts/cloud-preflight.sh` 通过；`git diff --check` 通过。真实服务器执行尚待用户登录，不报告已部署 |

第 57 次同项真实验证补充：SSH 严格主机密钥校验登录 root 成功；Docker/Compose 安装 active。本机 Python 镜像 SCP 导入、容器运行、Docker 受控重启与容器再次运行通过。公共 ECR TLS 拉取失败保留记录；后台两健康端点、迁移和正式手机还未部署验证。上述 19 项定向范围重跑通过，不新增计数。

| 8 | 58 | 2026-10-12 | 云端内部生产 Compose、随机凭据/TLS 首次初始化、持久 PostgreSQL 与回环 API | `node --test tests/cloud-deployment.test.js tests/backend-runtime.test.js tests/backend-data-platform.test.js tests/cloud-preflight.test.js tests/cloud-creation-roadmap.test.js tests/task-ledger.test.js tests/agent-handoff.test.js tests/test-policy.test.js`：30/30；Bash 语法与 `git diff --check` 通过。真实数据库 TLS、三迁移 applied、双健康端点、两容器重启健康及迁移保留通过；pg_dump/pg_restore 列表通过。公网鉴权、视频 Worker、手机未接通 |

| 9 | 59 | 2026-10-12 | Linux 视频 Worker 镜像/回环部署、持久 render 路径、环境监听、飞书创建确定性幂等 token | `node --test tests/cloud-deployment.test.js tests/video-generation.test.js tests/video-asset-pipeline.test.js tests/asset-lifecycle.test.js tests/task-ledger.test.js tests/test-policy.test.js`：44/44；`python scripts/test-video-server.py`：24/24；`python scripts/test-asset-archive.py`：5/5；真实云端文字样片/抽帧/归档恢复 9 文件成功，重启状态与健康保留。首次并行验收重复记录已修复创建 token，失败合成记录保留待核对；零付费调用，公网手机未完成；`git diff --check` 通过 |

| 10 | 60 | 2026-10-12 | 双服务器手机上线方案、广州运行状态复核与上线前备份；更新旧部署状态测试 | 按完整测试优先只执行 `node --test tests/*.test.js`：206/206。初次发现 preflight 文档测试仍要求“服务器尚未登录或部署”，改为当前“正式手机尚未接通”后全量重跑通过。广州三容器健康、API/视频端点通过，数据库备份及列表通过，副本下载仓库外；纽约可信指纹/SSH 尚未完成，未报告手机上线；差异检查通过 |

### 第 60 次完整测试检查

最近五次 56–60：资产同步归档恢复与反馈；云端盘点和 Docker；内部 PostgreSQL/API TLS；Linux 视频 Worker 与幂等归档；双服务器上线方案和备份。最近十次 51–60 覆盖云端规划、六表工具/授权/统一布局/真实初始化，以及上述五项。完整测试 206/206，通过后不另跑定向或五次测试。第 60 次代码全量检查完成；正式手机上线仍待实际接入，历史第 50 次面板绿灯限制继续保留，不清零或删除待验证项。

## 批次 7（累计 61 起，历史待验证项保留）

| 次数 | 累计 | 日期 | 改动内容及影响范围 | 验证 |
| --- | --- | --- | --- | --- |
| 1 | 61 | 2026-10-12 | 专用受限 SSH 回环通路、保留纽约旧项目的精确 HTTPS health 路由、配置备份失败回滚工具、微信外部空配置 | `node --test tests/cloud-tunnel.test.js tests/cloud-deployment.test.js tests/cloud-preflight.test.js tests/backend-runtime.test.js tests/task-ledger.test.js tests/test-policy.test.js`：24/24；真实 Nginx -t/reload、新旧 HTTPS health、广州通路受控重启后公网读取通过；`git diff --check` 通过。生成、身份隔离和手机尚未接通，凭据不进入 Git |

| 2 | 62 | 2026-10-13 | 微信 server code 交换、持久 2 小时会话、身份查询和退出，云端镜像/凭据只读挂载 | `node --test tests/cloud-deployment.test.js tests/backend-runtime.test.js tests/video-generation.test.js tests/asset-lifecycle.test.js tests/task-ledger.test.js tests/test-policy.test.js`：45/45；Python video 24/24、archive 5/5、wechat-auth 3/3。真实 wx.login code 在云端交换成功；me、重启保留、logout 后 401 通过；错误不打印凭据，`git diff --check` 通过。仅内部登录，归属门禁和手机仍未完成 |
| 3 | 63 | 2026-10-13 | 微信会话接入小程序、任务/素材/资产归属门禁、短时签名媒体、受保护公网前缀及下载错误诊断 | `node --test tests/video-session.test.js tests/video-generation.test.js tests/video-history.test.js tests/creation-tools.test.js tests/asset-lifecycle.test.js tests/cloud-deployment.test.js tests/cloud-tunnel.test.js tests/tool-interfaces.test.js tests/task-ledger.test.js tests/test-policy.test.js tests/upload-quality.test.js`：63/63；Python video 24/24、archive 5/5、wechat-auth 4/4。公网 health、登录、免费文字视频、签名 Range 和完整下载验证通过；用户真机完成生成、播放和保存到本地，服务端对应播放 206、下载 200。未调用付费模型；`git diff --check` 通过。付费 AI、解析器、转写和正式审核发布不在本次通过范围 |
| 4 | 64 | 2026-10-13 | 新增三分钟进度汇报规范并纳入项目强制规则，规定长任务的时间门槛、四项固定内容、异常等待和完成证据 | `node --test tests/test-policy.test.js tests/task-ledger.test.js`：14/14 通过；`git diff --check` 通过 |

| 5 | 65 | 2026-10-13 | 云端解析器内网接入、HTTP 主机精确允许名单、资源约束与部署交接；用户要求阶段移交 | 最近五次范围测试与必要集成状态见下方；本次保持待验证，不报告全部完成 |

### 第 65 次五次范围检查（阶段交接，必要集成待验证）

最近五次 61–65：纽约受保护 SSH/HTTPS 通路、微信持久会话、手机归属和签名下载、三分钟汇报规范、云端 DTK 解析接入。去重测试范围增加交接说明测试：

`node --test tests/cloud-tunnel.test.js tests/cloud-deployment.test.js tests/cloud-preflight.test.js tests/backend-runtime.test.js tests/task-ledger.test.js tests/test-policy.test.js tests/video-generation.test.js tests/asset-lifecycle.test.js tests/video-session.test.js tests/video-history.test.js tests/creation-tools.test.js tests/tool-interfaces.test.js tests/upload-quality.test.js tests/agent-handoff.test.js`

- 结果：交接收尾上述合并范围 **74/74 通过**；Python 视频 25/25、微信认证 4/4、归档 5/5 通过；`git diff --check` 通过。代码测试通过不关闭下列必要集成待验证项。
- 已完成集成：广州视频 `parser-65` 与 DTK 四组件健康；真实作品 `7693845706146340337` 下载 1,725,435 字节，H.264 576×1024、6.76 秒，SHA `feaafc9376ea98d150be4e7bdb59345cf95184a38fe5f84abc02820396bc06d9`。公网临时部署测试会话解析与归属通过，随后清理测试会话，未假称真实 wx.login 或手机验收。
- 未完成：自动身份维护浏览器尚未导入/启动；两个本地 Compose 修正未同步；重启恢复、身份更新及用户手机界面复测待接手方完成。第 65 次检查维持待验证，沿用同一逻辑改动补充，不增加次数；下一个完整检查点仍为 70。历史第 50 次面板限制保留。

第 65 次续作补充（同一改动，不新增计数）：上述浏览器部署、配置同步、身份创建和容器重启验证均已完成。真实新增身份任务 done，9 个抖音身份重启后保留；公网原片 SHA/归属一致，新旧 health 200，未鉴权解析 401。尚待用户确认手机界面解析结果，因此必要验收仍保持待验证；未重复付费调用。更新交接说明测试后重跑同一五次范围 **74/74 通过**，`git diff --check` 通过。

第 65 次手机验收补充：2026-10-13 用户明确确认视频解析、下载均可使用；该检查点的手机待办完成。内容分析质量、转写和音频导出分别验证，不从此次确认推断。

| 批内序号 | 累计 | 日期 | 改动 | 验证 |
| --- | --- | --- | --- | --- |
| 6 | 66 | 2026-10-13 | 云端离线语音识别依赖与兼容解码器、失败转写重试、手机本地 MP3 播放与微信文件导出 | `node --test tests/audio-asset.test.js tests/creation-tools.test.js tests/video-session.test.js tests/video-generation.test.js tests/video-asset-pipeline.test.js tests/cloud-deployment.test.js tests/cloud-speech.test.js tests/task-ledger.test.js tests/test-policy.test.js`：57/57；Python `scripts/test-video-server.py` 25/25、`scripts/test-wechat-auth.py` 4/4；云端 `scripts/test-video-image.py` 通过；真实 21.2 秒原片返回转写、509276 字节 MP3 公网 Range/下载/解码通过，受控重启后复测通过，新旧 health 200。微信 preview 成功；手机新版音频播放和导出待用户复测，tiny 转写错字需校对；自动化端口未建立，视觉验证未完成。 |

| 7 | 67 | 2026-10-14 | 受限远程配置、启动刷新与缓存降级、版本上报、旧工具服务端维护门禁和双轨发布方案 | `node --test tests/client-config.test.js tests/audio-asset.test.js tests/creation-tools.test.js tests/video-session.test.js tests/video-generation.test.js tests/cloud-deployment.test.js tests/task-ledger.test.js tests/test-policy.test.js`：55/55；Python video 25/25、auth 4/4、client-config 1/1；公网 schema 1 默认配置已验证。体验版配置和通用异步任务迁移尚未完成，详见发布方案。 |
- 兼容集成补充：公网不带客户端版本头的旧式 `/tools/run` 请求仍返回音频与转写；MP3 509276 字节、Range 206、完整解码通过，health 200。微信 preview 打包成功；未提交审核或设置体验成员。本次 `git diff --check` 通过。

| 8 | 68 | 2026-10-14 | 停止功能开发，整理全项目视觉设计交接说明与14路由事件状态清单 | `node --test tests/frontend-handoff.test.js tests/task-ledger.test.js tests/test-policy.test.js`：15/15；仅文档/交接测试改动，业务代码与云服务不变。源码包从提交快照生成，逐文件 SHA-256/ZIP 校验结果随包存于 verification.json；不包含生产数据或凭据。 |

| 9 | 69 | 2026-10-14 | 项目1独立布局MVP：灵感/创作/学习/我的四页、创作确认与预设分镜、工具布局、浏览器点子保存；新增 web/project-1，不修改正式小程序与既有 web 入口 | `node --test tests/layout-project1.test.js`：3/3；Playwright + Edge 验证四页 × 320/375/390/430px 无横向溢出，创作流程、灵感保存/刷新/文本转义、学习筛选空态通过，无脚本错误；创作截图已检查。`git diff --check` 通过。仅浏览器原型，未验证微信真机或云端；历史待验证项继续保留。 |

| 10 | 70 | 2026-10-14 | 项目1补齐五主入口及37页面/案例入口：灵感日历、热点、创作分镜/等待/结果、六工具、学习、配置、作品复盘、资产、存量合作流程；独立浏览器数据模型，正式小程序不变 | 第70次只运行完整 `node --test tests/*.test.js`：228/228。npm 不在 PATH，使用规则允许的等价命令。浏览器37入口×4宽度、创作失败重试、本地保存、提词器、五工具结果、本机音频播放、任务验收、模型/接口校验与删除取消通过；截图检查与 `git diff --check` 通过。云端调用、微信真机和真实交易未接入，历史待验证项继续保留。 |

### 第 70 次完整测试检查

最近五次 66–70：音频/转写；受限远程配置；视觉设计交接；项目1初始布局；项目1完整页面与本地交互。最近十次 61–70 还涵盖受限通路、公网手机接入及解析交付。完整测试 228/228，未额外执行本次或五次定向测试。第70次代码与浏览器原型检查完成；历史第50次面板和各项未完成的线上/真机验证仍保留，不据本次浏览器结果关闭。下一次累计71，批内1/10。

### 第 71 次 · 热点同步

| 批内序号 | 累计 | 日期 | 改动 | 验证 |
| --- | --- | --- | --- | --- |
| 1 | 71 | 2026-10-14 | DailyHotApi 内网部署、600秒持久快照、来源失败降级、首页与热点页真实榜单/搜索/保存来源 | 定向 JS 81/81，Python热点5/5、视频25/25；公网榜单、两轮600秒间隔、重启恢复、开发者工具搜索/详情/筛选与首页加载通过，截图已检查；preview编译成功。快手间歇失败显示缓存；未提交审核，微信真机待验收。 |

命令：`node --test tests/hotspot-discovery.test.js tests/creator-preferences.test.js tests/interface-copy.test.js tests/inspiration-header.test.js tests/account-layout.test.js tests/creative-flow.test.js tests/record-switch.test.js tests/ai-config.test.js tests/video-generation.test.js tests/cloud-deployment.test.js tests/task-ledger.test.js tests/test-policy.test.js`；Python运行 `scripts/test-hotspot-feed.py`、`scripts/test-video-server.py`。遵循第71次定向范围，不额外全量。历史待验收项保持原状态。

### 第 72 次 · 热点升温工作台

| 批内序号 | 累计 | 日期 | 改动 | 验证 |
| --- | --- | --- | --- | --- |
| 2 | 72 | 2026-10-14 | 优先回答“哪些话题正在升温”：最近6轮同源位置历史、上升/新入榜/长间隔边界、首页12条升温与完整页、变化详情、简洁状态与来源查证 | 定向JS59/59；Python热点7/7。云端trends-72已部署，真实快照产生上升、新入榜及等待对比；开发者工具首页/筛选/搜索/详情通过，无脚本异常，截图已检查；preview编译通过。真机与正式审核仍待完成，不把榜内升位称为播放量增长。 |

命令：`node --test tests/hotspot-discovery.test.js tests/creator-preferences.test.js tests/interface-copy.test.js tests/inspiration-header.test.js tests/account-layout.test.js tests/creative-flow.test.js tests/record-switch.test.js tests/ai-config.test.js tests/cloud-deployment.test.js tests/task-ledger.test.js tests/test-policy.test.js`；Python `scripts/test-hotspot-feed.py` 7/7，覆盖真实前后位置、新入榜、失败/过期、初次基线、30分钟断档、6轮上限和重启持久载入。下一批次检查点75，完整检查点80，历史待验收项保持。

### 第 73 次 · 话题内容详情

| 批内序号 | 累计 | 日期 | 改动 | 验证 |
| --- | --- | --- | --- | --- |
| 3 | 73 | 2026-10-15 | 按需来源摘录、原文链接、异步状态/并发/持久缓存、负缓存重试、具体抖音视频链接带入现有工具、关闭与离榜反馈 | 定向JS55/55，Python内容6/6、视频25/25；真实公网ready返回6条摘录，empty/expired亦已验证。界面与最终preview结果后补充，真机未验收。 |

命令：`node --test tests/hotspot-content.test.js tests/hotspot-discovery.test.js tests/creation-tools.test.js tests/audio-asset.test.js tests/creator-preferences.test.js tests/interface-copy.test.js tests/inspiration-header.test.js tests/creative-flow.test.js tests/cloud-deployment.test.js tests/task-ledger.test.js tests/test-policy.test.js`；Python `scripts/test-hotspot-content.py`、`scripts/test-video-server.py`。第73次只执行定向范围；历史待验收项保持。

- 界面验收补充：开发者工具真实内容ready，6条摘录均带来源与原文链接，无脚本异常；滚动详情截图已检查。关闭空值在自动化协议中为undefined，脚本按空值修正后通过。服务受控重启后同一retrievedAt与6条缓存保留，health正常；最终preview成功。微信真机与正式发布仍待完成。

### 第 73 次续作 · 修复来源摘录空结果（同一功能，不新增计数）

完整标题/分词标题/备用入口最多3次检索，保持相关性校验；旧负缓存失效，区分上游失败与真正空结果。用户截图原话题“中朝新鸭绿江大桥将开通”真实公网ready返回6条（含新华网、北京日报、第一财经）。部署标签content-74为镜像版本，不代表累计改动次数。

沿用第73次定向范围：JS55/55；Python内容9/9。同一交付修复、重试不新增计数；下一次新逻辑改动为74，75汇总最近五次范围，80完整测试。界面验收结果继续补充，手机仍待用户复测，不据此承诺所有话题均被公开索引。

- 同一话题界面补充：开发者工具ready返回6条，无脚本异常；已检查大桥话题截图，显示新华网等摘录与原文链接。手机需用户在原版本点击重新获取确认。

### 第 74 次 · 项目基线与中台迭代交接

| 批内序号 | 累计 | 日期 | 改动 | 验证 |
| --- | --- | --- | --- | --- |
| 4 | 74 | 2026-10-15 | 基线源码/Git打包与逐文件校验脚本，私有云端恢复材料，中台第一阶段范围和验收定义 | `node --test tests/project-package.test.js tests/task-ledger.test.js tests/test-policy.test.js`：15/15。YOUAI与DTK数据库均在同版本独立临时库实际恢复成功，测试库清理；最终归档完整性报告在交付目录生成后确认。中台管理后台仍为新迭代范围，未声称已实现。 |

下一逻辑改动75需汇总71–75范围测试，80完整测试。源码打包提交之后生成Git快照归档；verification.json作为最终文件校验证据，历史手机待验收状态不据打包关闭。

第74次打包收尾：Windows自动换行转换已修正并增加真实Git仓库用例；同一逻辑补充不新增计数。最终350个源码文件、Git bundle、线上两个数据库实际恢复、生产文件SHA与两个ZIP CRC均通过；冻结提交d26621d，完整证据在交付目录verification.json。新迭代分支codex/admin-console建立，后台功能尚未实现。

### 第75次 · 中台管理后台与原生手机入口

最近五次71–75影响范围：真实热点采集；升温历史与展示；话题来源检索/解析工具衔接；基线打包；独立管理员鉴权、工具维护配置发布/回滚、管理网页及小程序“我的”入口。合并去重覆盖热点、创作流程、共享配置、主页面、媒体工具、云部署、交接、打包、台账与测试规则。

本次仅执行五次合并范围，不额外完整测试。命令：`node --test --test-reporter=tap tests/admin-console.test.js tests/frontend-handoff.test.js tests/hotspot-discovery.test.js tests/creator-preferences.test.js tests/interface-copy.test.js tests/inspiration-header.test.js tests/account-layout.test.js tests/creative-flow.test.js tests/record-switch.test.js tests/ai-config.test.js tests/video-generation.test.js tests/cloud-deployment.test.js tests/task-ledger.test.js tests/test-policy.test.js tests/hotspot-content.test.js tests/creation-tools.test.js tests/audio-asset.test.js tests/project-package.test.js`。Python：`scripts/test-admin-console.py`、`scripts/test-hotspot-feed.py`、`scripts/test-hotspot-content.py`、`scripts/test-video-server.py`、`scripts/test-client-config.py`。最终JS100/100，Python52/52（管理10、热点7、内容9、视频25、配置1），git diff --check通过。第75次阶段范围检查完成，不重置十次周期。

必要验证：公网匿名及普通微信令牌401，独立管理员登录/退出、同状态发布/409冲突/回滚、审计脱敏通过，未改变生产工具可用状态。Playwright/Edge检查5管理页，320/390/1280宽度与无脚本异常；截图检查。原生开发者工具“我的 → 管理中台”、真实登录、五标签、工具差异、话题状态、退出通过。重建期间一次原生请求失败，待服务健康后重新执行完整原生验证通过。受控重启后配置/版本保留、旧会话撤销；视频health及数据API ready正常。最终preview构建通过；真机登录与正式审核未完成。历史第50次及其他待验证项继续保留，不据本次关闭；下一完整检查为80。

### 第76次 · 管理员密码调整

用户指定8位密码，登录长度支持8–256位，仍保留PBKDF2、限流和独立会话。凭据仅保存在仓库外及云端哈希文件，不登记明文。影响范围：管理员登录、旧密码拒绝、会话撤销、部署和台账。

本次定向 `node --test --test-reporter=tap tests/admin-console.test.js tests/cloud-deployment.test.js tests/task-ledger.test.js tests/test-policy.test.js` 21/21；Python `scripts/test-admin-console.py` 11/11。admin-76真实公网验证新密码登录/管理读取/退出成功、旧密码401、旧会话401；health正常，本机凭据同步。git diff --check通过，不改客户端、不改变生产工具状态。下一五次范围检查80与完整检查重合，届时仅完整测试。

### 第77次 · 多目标拆解与DIY模板

影响范围：旧六预设/素材默认映射、多目标、DIY模板存储/编辑、共享案例页、主创作草稿/版本快照、参考视频方案/批准分镜、服务端校验/提示词/资产请求快照和部署。

定向命令：`node --test --test-reporter=tap tests/analysis-templates.test.js tests/analysis-presets.test.js tests/analysis-framework.test.js tests/video-generation.test.js tests/creative-flow.test.js tests/creator-preferences.test.js tests/demo.test.js tests/creative-command.test.js tests/video-asset-pipeline.test.js tests/asset-lifecycle.test.js tests/audio-asset.test.js tests/cloud-deployment.test.js tests/frontend-handoff.test.js tests/task-ledger.test.js tests/test-policy.test.js tests/account-layout.test.js tests/record-switch.test.js tests/interface-copy.test.js tests/inspiration-header.test.js`：103/103。Python运行test-analysis-plan.py、test-video-server.py、test-asset-archive.py、test-wechat-auth.py、test-admin-console.py：48/48。同一实现修正不新增计数，未额外完整测试；下次80执行完整检查。

必要验证：开发者工具创作入口 → 工作台、多目标、DIY栏目排序/保存/设默认、案例套用 → 创作草稿、参考模板选择通过，无脚本异常，截图检查。旧作品快照在删除模板后仍可重新生成的自动测试通过。云端analysis-77 healthy；真实微信登录、方案变更未重批分镜400、免费2秒文字成片done、生产request.json保存完整DIY/多目标快照通过，未重复生成、未调用付费模型。首次快照路径读错，修正为assets/runs后验证同一个任务成功。最终preview通过（主包377.1KB，总包5.2MB）。git diff --check通过。

DIY库为本机保存，账号云同步未完成；本次没有真实付费模型验收，真机DIY操作与正式审核待用户完成。历史未验收项继续保留。


### 第78次 · 微信账号模板云同步

影响范围：账号模板SQLite持久化/鉴权/版本冲突；本机缓存迁移、账号隔离、失败重试、页面关闭上传、冲突备份恢复；工作台、共享案例页、参考视频方案及旧快照兼容。

定向命令：node --test --test-reporter=tap tests/analysis-sync.test.js tests/analysis-templates.test.js tests/analysis-presets.test.js tests/analysis-framework.test.js tests/video-generation.test.js tests/creative-flow.test.js tests/creator-preferences.test.js tests/demo.test.js tests/creative-command.test.js tests/video-asset-pipeline.test.js tests/asset-lifecycle.test.js tests/audio-asset.test.js tests/cloud-deployment.test.js tests/frontend-handoff.test.js tests/task-ledger.test.js tests/test-policy.test.js tests/account-layout.test.js tests/record-switch.test.js tests/interface-copy.test.js tests/inspiration-header.test.js。114/114。Python：test-analysis-preferences.py、test-analysis-plan.py、test-video-server.py、test-asset-archive.py、test-wechat-auth.py、test-admin-console.py，共53/53。未额外运行完整测试，80到期执行。

必要验证：analysis-78云端健康；真实微信身份三份独立缓存恢复DIY模板/素材默认/多选目标，并发写冲突与云端选择备份通过。原生开发者工具保存提示、重开恢复和截图检查通过，无脚本异常，临时数据恢复原状。自动化读取状态曾超时，改为直接核对数据库后完成受控重启；持久化前后一致，SQLite在线备份integrity_check为ok。物理两部手机换机仍待用户验收；未进行付费生成。二维码构建与diff检查结果在最终收尾登记。

最终收尾：preview构建通过，主包387.4KB、总包5.2MB；新二维码analysis-cloud-preview-20261015.jpg。git diff --check通过，文档更新后的交接/台账/规则15项复核通过。

### 第79次 · 统一账号与资产迁移设计

影响范围：数据中台设计补充、现状核对、账号/资产归属、换机/双账号迁移/服务器恢复、任务台账。仅设计文档，不执行生产账号绑定、合并或搬迁。定向命令：node --test tests/backend-data-platform-doc.test.js tests/task-ledger.test.js tests/test-policy.test.js。最终17/17通过；新增文档断言首次用词与方案不一致，改为校验实际双主体控制权要求后重跑本次范围。git diff --check通过；文档引用检查通过。累计79，下次80执行完整测试并保留76–80范围汇总；历史真机待验收项不关闭。

### 第80次 · 知识星球会员权益方案与完整检查

最近五次76–80汇总：管理员密码长度及轮换；多目标拆解/DIY模板与参考分镜校验；微信账号模板云同步及冲突备份；统一账号/资产/迁移设计；知识星球核验、有效期、退款、服务端权益及额度、资产保留设计。最近十次71–80另包含热点采集/升温历史/来源检索、基线打包和管理中台。

到期只执行完整测试：node --test tests/*.test.js，不另跑本次或五次范围测试。当前80只改设计文档与文档检查，未接入知识星球、未部署账号系统、未改生产权限。知识星球资料来自官方成员/到期/退款说明；通用授权成员API尚未确认。完整测试结果待登记，历史真机与正式审核待验收项继续保留。

完整检查首次256/257：历史导航断言要求所有页面使用自定义组件，但管理中台已明确配置系统导航。修正文档之外的测试兼容性：逐页验证原生导航有标题且不重复自定义导航，其余仍必须有共享组件；不改变产品界面。修复后重新执行完整测试，结果待登记。

第80次最终完整测试257/257通过（node --test tests/*.test.js），无跳过；可选页面JSON采用合法的app全局导航配置后重新完整执行通过。git diff --check与新增文档引用核对通过。此次必要验证为设计与现状/官方资料核对，没有运行账号/会员生产迁移。第80次完整检查完成，下一批从1/10开始，累计下次81；历史真机待验收项继续保留。

### 第81次 · youai888.top 国内 HTTPS 入口

影响范围：DNS实查、Nginx TLS/HTTP跳转、现有视频API代理与鉴权透传、证书部署及回滚说明。证书和私钥仅在仓库外。定向 `node --test tests/domain-https.test.js tests/cloud-deployment.test.js tests/test-policy.test.js` 8/8通过；当前为新批1/10，下次五次范围85、完整90。

必要验证：证书SAN/有效期/密钥匹配通过，nginx -t通过，公网严格证书校验HTTPS200、HTTP301、健康200、匿名业务401；Nginx受控重启及开机启用确认通过，重启后公网health200，内部数据API ready正常，旧公网health200。未切换小程序、媒体签名地址或管理员Origin；www无解析，api子域名不在证书范围。历史真机待办保留。安装首次命令受传输末行影响失败，改用独立SSH命令安装通过，不重复计数。

### 第82次 · 国内中台、后端与网站统一部署（微信白名单及真机待验）

影响范围：小程序视频/登录/下载、管理员、模板同步、热点共享国内入口；模拟器默认云端和显式本机调试；中台Origin与媒体基础地址；Nginx静态资源白名单、原管理/鉴权代理；项目合法域名检查、部署/回滚和后续中台优先策略。继续沿用既有数据库与飞书，不迁移用户身份、不新增付费调用。当前新批2/10，85范围检查、90完整检查，历史待验收项不关闭。

最终定向命令：`node --test tests/domestic-deployment.test.js tests/domain-https.test.js tests/cloud-deployment.test.js tests/admin-console.test.js tests/video-session.test.js tests/video-generation.test.js tests/analysis-sync.test.js tests/hotspot-discovery.test.js tests/hotspot-content.test.js tests/client-config.test.js tests/layout-project1.test.js tests/project-package.test.js tests/test-policy.test.js`，70/70通过。Python本机缺少imageio_ffmpeg，改用已有tools-66-fixed镜像挂载当前scripts只读、network none，直接执行test-admin-console.py与test-client-config.py，11+1=12/12通过；unittest discover无法识别带连字符脚本，未把0测试计为通过。git diff --check通过。

必要验证：中台公网登录、同状态发布、409冲突、回滚、退出、五页与320/390/1280宽度通过；网站37入口×390/1280、全部引用图片、私有路径404通过并看图。首轮网站脚本只统计导航图条目，补齐主入口/案例/详情后完成37入口检查，未改变产品范围。原生我的入口/登录/五页/草稿/退出在关闭域名检查时通过；开启urlCheck后明确报url not in domain list，随后原生登录等待超时，不报告合法域名或手机通过，保持待验状态。

真实wx.login凭证经国内公网登录、模板读取、免费成片18892字节、签名Range206/下载200、飞书归档及4文件恢复通过。重启后配置/版本保留、旧管理会话失效、新旧health200通过。备份：PostgreSQL dump目录可读、4个SQLite integrity_check ok、管理配置与入口备份；没有覆盖性恢复。preview构建通过，主包387.6KB/总包5.2MB，二维码及证据在仓库外domestic-82目录。微信白名单配置/真机/正式审核未完成，不标记整体验收完成。

### 第83次 · 微信手机号账号与灵感页底部授权

唯一微信登录、微信服务端手机号验证、持久随机头像/文字昵称、原UUID和资源归属保留；客户端直接进入灵感页，通过底部弹窗授权，成功原地收起，不提供独立登录页。受保护业务校验手机号绑定，管理员独立鉴权。累计83，新批3/10，85范围检查、90完整检查。

定向命令：node --test tests/phone-account.test.js tests/video-session.test.js tests/video-generation.test.js tests/analysis-sync.test.js tests/admin-console.test.js tests/domestic-deployment.test.js tests/cloud-deployment.test.js tests/account-layout.test.js tests/demo.test.js tests/creative-flow.test.js tests/record-switch.test.js tests/interface-copy.test.js tests/inspiration-header.test.js tests/navigation.test.js tests/project-package.test.js tests/test-policy.test.js tests/backend-data-platform-doc.test.js。最终90/90通过。旧页面测试的require mock未加载新增模块，修正mock后重跑整个范围。Python在云端隔离network none容器挂载当前scripts只读，执行test-phone-account.py、test-wechat-auth.py、test-video-server.py、test-admin-console.py、test-analysis-preferences.py，48/48通过。本机Docker不可用，云端测试不挂生产数据或凭据。

必要验证：phone-83已部署健康，部署前无生成任务，4个SQLite在线备份完整。真实wx.login经国内公网获得稳定随机资料、未授权业务403、客户端伪造手机号400通过，没有真实手机号接口调用或付费生成。开发者工具确认灵感页底部弹窗布局；preview成功主包393.7KB/总包5.2MB。用户已确认合法域名、手机号组件和隐私声明；开发者工具仍无法连接登录服务，真实手机授权尚未验收，不报告端到端通过，历史待办继续保留。证据位于仓库外phone-83目录。git diff --check通过。

### 第84次 · 开发者工具页面调试入口

仅platform=devtools且envVersion=develop时显示“开发工具：先调试页面”。点击后本次运行内收起授权弹窗，返回首页/前台不重复拦截；不写入已绑定状态、不伪造身份、不放开云端手机号鉴权。真机开发版、体验版、正式版和环境读取异常均不允许跳过。

定向node --test tests/phone-account.test.js tests/creative-flow.test.js tests/navigation.test.js tests/domestic-deployment.test.js tests/video-session.test.js tests/test-policy.test.js，26/26通过，覆盖环境组合、会话内预览、未绑定状态保留及正常登录。开发者工具真实点击后收起、进入设置再返回仍可操作，截图检查通过。首次自动化读取早于渲染更新，等待后核实通过；没有修改产品以绕过失败。git diff --check通过。云端登录连接问题仍未修复，预览入口只用于本地页面/交互，不代表云端功能或手机号通过。累计84，下一次85汇总81–85范围测试。

### 第85次 · 微信小程序开发大赛作品说明文档

最近五次汇总：81国内HTTPS入口；82国内中台/后端/网站部署；83微信手机号账号与灵感授权；84开发者工具页面调试；85参赛文档、可复现Word生成器及文档检查。关联产品主线CORE-01、CRT-01、CRT-02、LEARN-01，仅描述现有设计和验证边界，不改变功能状态。

到期五次去重范围命令：node --test tests/account-layout.test.js tests/admin-console.test.js tests/analysis-sync.test.js tests/backend-data-platform-doc.test.js tests/client-config.test.js tests/cloud-deployment.test.js tests/creative-flow.test.js tests/demo.test.js tests/domain-https.test.js tests/domestic-deployment.test.js tests/hotspot-content.test.js tests/hotspot-discovery.test.js tests/inspiration-header.test.js tests/interface-copy.test.js tests/layout-project1.test.js tests/navigation.test.js tests/phone-account.test.js tests/project-package.test.js tests/record-switch.test.js tests/test-policy.test.js tests/video-generation.test.js tests/video-session.test.js tests/competition-document.test.js tests/task-ledger.test.js 。125/125通过，无跳过。本次文档已核对产品方案与最新81–84记录；Word共4页，已逐页渲染检查。标准render_docx.py因缺少LibreOffice失败，改用本机Office成功导出PDF并由Poppler生成PNG；Office退出时RPC报错，导出文件完整，4页均已检查。移除模板标题横线后重新渲染。文件小于100MB。

必要集成限制：本次未重跑云端Python、生产部署和真机流程；历史手机号授权、开发者工具登录、两真机换机和正式审核仍待验收。五次自动化范围检查通过，但真实环境待验证项保持待验证，不关闭十次周期。累计85，新批5/10，下次90完整检查。git diff --check通过。原有project.config.json修改不纳入提交。

### 第86次 · YOUAI参赛授权书

新增一页通用授权书Markdown、Word及独立生成脚本，预填截图中的作品名YOUAI和AppID wx8ae5d4f3ea8d0d8b，姓名、电话、签字和日期留空。不含代签或永久权利转让。官方赛事页无法读取，未核实官方模板，交付明确为通用拟稿。

定向命令：node --test tests/competition-document.test.js tests/test-policy.test.js，5/5通过。复用本机Office转PDF、Poppler转PNG的已验证流程，单页排版人工检查通过；Office退出RPC提示不影响已完成的导出。git diff --check通过。本次不变更小程序功能，不涉及外部提交；已有页面及测试修改不纳入本次提交。累计86，新批6/10，下次90完整测试。历史真机待验证项保留。

### 第85次 · 我的记录归位、拆学工作台与统一设置入口

最近五次81–85范围汇总：国内HTTPS/Nginx入口；国内三端与域名切换；微信手机号账号/灵感底部授权；开发版模拟器页面预览；记录区迁至我的快捷入口下方，拆学工作台替代每日一拆，创作偏好与更多设置合并为一个折叠入口。记录数据与全部四种视图保留，模板/视频入口沿用既有能力。

到期合并范围命令：node --test tests/domestic-deployment.test.js tests/domain-https.test.js tests/cloud-deployment.test.js tests/admin-console.test.js tests/video-session.test.js tests/video-generation.test.js tests/analysis-sync.test.js tests/hotspot-discovery.test.js tests/hotspot-content.test.js tests/client-config.test.js tests/layout-project1.test.js tests/project-package.test.js tests/test-policy.test.js tests/phone-account.test.js tests/account-layout.test.js tests/demo.test.js tests/creative-flow.test.js tests/record-switch.test.js tests/interface-copy.test.js tests/inspiration-header.test.js tests/navigation.test.js tests/backend-data-platform-doc.test.js tests/daily-pick.test.js。最终118/118通过。历史每日推荐/位置断言按新需求更新，保留记录操作/案例/模板路由测试。未重复执行本次定向测试或全量测试。

必要验证：开发工具灵感、我的、拆学三屏截图已检查；修正工作台按钮文字挤压后再次看图。我的记录切换、设置展开状态通过；preview构建主包394.7KB/总包5.2MB。模板路由API与源码处理函数测试通过，但模拟器自动点击未到预期页面，随后开发工具自动化runtime报cant find runtimeid，点击验收保持待验证。域名/真实手机号等历史真机项目继续保留；第85次范围自动测试通过，必要交互验证未完成，不标记整体验收完成。证据在仓库外layout-85文件，git diff --check通过。下次累计86，90执行完整测试。

### 第86次 · 我的四项快捷入口精简

删除周目标/调整目标栏、作品与草稿及我的收藏快捷入口、头像下方商家切换文字。快捷入口依次为视频资产、偏好设置、商家认证、任务进度；偏好设置在快捷区下方展开原有设置项。商家入口明确认证未开通，确认后仅切换既有商家体验功能，不伪造认证状态。记录中的作品/收藏保留。

定向node --test tests/account-layout.test.js tests/record-switch.test.js tests/creative-flow.test.js tests/demo.test.js tests/interface-copy.test.js tests/test-policy.test.js，最终27/27通过。覆盖四项顺序、删除文案、设置折叠、资源入口、商家取消/确认以及原记录操作。初次编辑换行边界导致标签结构失败，修复后重跑本次范围通过。开发者工具我的页面截图已核对四项顺序、周目标移除和记录区保留；未进行真实商家认证。git diff --check通过。累计86，下次90完整检查；85模板自动点击和历史真机待验项目继续保留。

### 第87次 · 灵感记录输入框加高50%

仅覆盖主页面输入区高度，由120rpx变为180rpx，宽度、两个按钮和输入保存行为保留。定向node --test tests/inspiration-header.test.js tests/creative-flow.test.js tests/test-policy.test.js，15/15通过。重新启动开发工具自动化连接后截图核对通过，输入框加高且按钮并排、热点顺延无重叠。git diff --check通过。累计87，下次90完整检查；历史待验事项保留。

### 第88次 · 搜热点、AI总结、创作入口与默认模板

突出搜热点、推荐区显示本次页面最近六个去重关键词并支持重搜，新增AI最近热点总结；三个榜单模式保留。参考视频移到主入口，一句话入口移到右侧并更名一句话生成作品；六工具高度约缩减三分之一、删除辅助解释、按要求更名。工作台展示六套既有稳定ID默认模板，可点选预览并继续设默认/DIY，不覆盖已有模板。

定向node --test tests/creation-tools.test.js tests/hotspot-discovery.test.js tests/hotspot-content.test.js tests/inspiration-header.test.js tests/creative-flow.test.js tests/analysis-templates.test.js tests/analysis-presets.test.js tests/analysis-sync.test.js tests/video-generation.test.js tests/test-policy.test.js，80/80通过。隔离network none容器只读挂载当前源码，test-hotspot-summary.py、test-video-server.py、test-wechat-auth.py共32/32通过；覆盖总结来源过滤、无数据/未配置失败、上游错误脱敏、限流、缓存和未绑手机号403。远程测试末行CR首次导致文件名错误，修正传输后整个范围重跑通过。

必要验证：开发工具三屏截图核对，修复旧150rpx固定宽度导致总结按钮竖排后重看通过；来源/关键词截图使用明确界面样本，不作为真实热榜证明。preview主包约399KB/总包5.2MB。生产feature-88镜像部署健康，原环境及Compose备份在/opt/youai/backups/feature-88。用户提供的百炼凭据仅写服务器credentials/hotspot-ai.json，不入仓库或客户端；北京国内入口qwen3.8-max小范围真实调用成功，91 tokens。当前服务端无非过期热榜快照，总结返回无数据提示，未报告真实热点摘要端到端通过。

工具名称本次仅调整入口显示；全网视频下载仍依赖解析服务的平台范围，图片去水印尚未接入图片修复，现有eraser能力为视频原片解析，不能报告新增图片去水印通过。原微信合法域名/真实手机号及历史待验继续保留。git diff --check通过。累计88，90完整检查。

### 第89次 · 六板块中台与三阶段个人流程设计

设计交付：热点推荐、创作工具调用、数据积累（飞书）、确认需求设计、作品拆解、作品产出。三阶段默认/个人流程、Skill澄清与结构化草案、管理员发布和用户确认、共享定义映射小程序、任务/资产快照及飞书Outbox接口方案。本地可交互设计稿位于web/admin-workflows，未修改或部署生产中台/Skill执行器/小程序动态渲染。

定向node --test tests/workflow-platform-design.test.js tests/backend-data-platform-doc.test.js tests/test-policy.test.js，13/13通过，覆盖默认副本隔离、个人草案不改全局、必要确认/排序、未知能力和远程代码拒绝。Edge无头浏览器六板块×1440/390两种宽度通过，无横向溢出和页面脚本错误；自定义需求→流程建议→同数据手机预览→校验交互通过，截图看图完成。真实Skill/飞书写入、账号流程持久化、微信端渲染尚未实现，不把本地建议生成计作AI验证。

本地预览服务仅127.0.0.1:8899，HTTP200；设计说明和现有中台文档互相衔接。git diff --check通过。累计89；下一次90执行完整测试并汇总86–90，历史真机和模板自动点击待验项保留。

### 第90次 · MCP包管理设计与完整检查

最近五次86–90汇总：我的四快捷入口/商家入口说明；灵感输入框加高50%；热点搜索/AI总结/创作入口与默认模板；六板块中台/三阶段个人流程设计；MCP公共能力管理、候选包与能力路由设计。最近十次81–90另含国内HTTPS/部署、微信手机号授权和开发者工具页面预览。

到期只执行完整node --test tests/*.test.js，不另跑本次或最近五次定向范围。首次282/283，旧tool-interfaces界面断言要求已于86移除的头像商家切换，更新为新商家入口和折叠设置断言，保留角色不提升接口权限及实际路由验证。修正后完整283/283通过，无跳过，git diff --check通过。

本次设计新增MCP包管理公共导航、视频读取/文案/飞书归档三种规划包、输入输出契约/权限/预算/启用/健康过滤与稳定选择预览，作品拆解证据节点显示video.read候选能力。方案涵盖版本锁、Schema校验、受控调用/隔离部署、幂等与超时核对、无匹配阻断、准入及回滚接口。参考官方MCP协议工具和JSON Schema说明，不将自定义manifest声称为协议标准。

必要验证：Edge 1440/390宽度下候选匹配与禁用后阻断交互通过，无溢出或脚本错误；截图看图通过。未安装真实MCP包、未部署网关、不进行生产工具调用，不把本地规划包当真实可用工具。现有project.config.json工作区变化未纳入提交。90本次设计与完整检查完成，下一批从1/10开始、累计91；历史手机号/真机/模板点击/真实热点总结待验继续保留。

### 第91次 · 灵感区AI选题推荐与多轮对话

新批1/10。原热点区域改为账号AI选题聊天，进入灵感页通过已核验且手机号已绑定账号自动推荐，支持继续碰撞主题、主题带入创作、确认后清空；原平台/关键词/榜单保留折叠入口。只读取有归属的云端生成请求摘要、云端拆解偏好和本人对话，不读取共享本机旧记录。历史SQLite持久化，每账号最近30轮；十分钟自动推荐缓存，失败不虚构，账号隔离/旧响应丢弃/幂等重试与限流。

定向node --test tests/topic-chat.test.js tests/hotspot-discovery.test.js tests/hotspot-content.test.js tests/inspiration-header.test.js tests/creative-flow.test.js tests/phone-account.test.js tests/video-generation.test.js tests/test-policy.test.js，58/58通过。Python隔离network none容器挂载当前scripts只读运行test-topic-chat.py、test-video-server.py、test-wechat-auth.py共33/33通过；覆盖个人历史、跨账号隔离、重启读取、缓存、消息校验、失败不落假结果、清空不影响他人、手机号未绑403。首次Windows SQLite连接未关闭导致临时目录清理失败，改为上下文管理器显式关闭，重跑通过。

必要验证：小程序对话框使用明确界面示例看图，调整发送按钮宽度后重看；不把示例消息当AI实测。topic-91镜像部署健康，部署前无进行中生成任务；原env及SQLite在线备份在/opt/youai/backups/topic-91。生产同模块受控冷启动真实Qwen调用返回3个主题、110字回复，historyCount0/hasHotspotsfalse；测试账号数据随后清除，不触碰真实用户对话。普通手机号授权后的真机完整对话仍待验，未把直接模型调用当真机端到端成功。preview主包408.2KB/总包5.2MB，后续客户端收尾仅清理身份失败时的私密画面。git diff --check通过；下一次95范围检查、100完整检查，历史未验项保留。

### 第92次 · 我和TA聊天式推荐窗口

“我的记录”改“我想记”，“和AI碰撞一个好选题”改“和TA聊”；明确聊天滚动窗口、TA/用户气泡与输入区。每次进入由TA先以本人云端记录、选题对话及可用真实热榜推荐；有新对话后不能复用旧开场，短时无新上下文可复用最近开场，回复不覆盖正在输入的草稿。

定向node --test tests/topic-chat.test.js tests/inspiration-header.test.js tests/hotspot-discovery.test.js tests/creative-flow.test.js tests/phone-account.test.js tests/test-policy.test.js，34/34通过；Python隔离容器test-topic-chat.py和test-wechat-auth.py共9/9通过。覆盖重入首条为AI、复用开场可见、新对话后重建开场、草稿保留与账号隔离。开发工具双气泡窗口截图看图通过；验证示例已清除并恢复实际页面，不把示例消息当模型实测。

topic-92云端部署健康，部署前无进行中生成任务，原env和对话SQLite备份在/opt/youai/backups/topic-92；不改用户身份或调用权限。preview构建结果见最终收尾；当前真实热榜不可用与真机手机号授权后完整对话仍待验，未报告为通过。git diff --check通过。累计92，95范围检查、100完整检查。
第92次收尾：preview构建通过，主包约409KB/总包5.2MB；新回复使用随请求变化的滚动锚点定位到聊天底部，34项本次范围重跑通过。

### 第93次 · 灵感页三个思路入口排版

我想记、和TA聊、看热点独立为统一层级卡片，标题/间距/按钮调整，聊天区不再承载榜单切换；第三热点板块默认展开并可独立折叠，保留平台、关键词、AI总结及三个榜单。聊天滚动窗口适度压缩，输入框保留180rpx高度，折叠榜单后重置吸顶定位。

定向node --test tests/inspiration-header.test.js tests/topic-chat.test.js tests/hotspot-discovery.test.js tests/creative-flow.test.js tests/phone-account.test.js tests/test-policy.test.js，35/35通过。开发工具顶部和下方热点区截图核对、独立折叠通过；首次截图复用了滚动位置，明确回到顶部后重新看图。preview构建通过，无后端修改或新AI付费调用。git diff --check通过，累计93，95范围检查、100完整检查；原历史真机待验保留。

### 第94次 · 热点关键词真实搜索、置顶关注与榜位监测

搜索从仅匹配本机榜单改为服务端真实网页检索加采集榜位两类；关键词置于平台栏前，按账号保存最近20个关注、支持恢复/取消，独立后台每10分钟采样并保存7天观测。真实榜位升降只比较相同话题且有效间隔<=30分钟；来源异常unknown，不记假掉榜或虚构排名。并发检索上限2、缓存5分钟，关键词限定1–40字。

定向node --test tests/hotspot-discovery.test.js tests/hotspot-content.test.js tests/inspiration-header.test.js tests/topic-chat.test.js tests/creative-flow.test.js tests/phone-account.test.js tests/test-policy.test.js，最终41/41通过。Python隔离network none只读挂当前scripts：test-hotspot-watch.py、test-hotspot-feed.py、test-hotspot-content.py、test-wechat-auth.py，共25/25通过，覆盖持久化/账号隔离/关注上限/重复采样/真实升降/来源失败/不同话题不误比/搜索与排名分离/未绑定403。未额外全量测试。

watch-94部署健康，原env/Compose/SQLite在线备份在/opt/youai/backups/watch-94。公网及原生模拟器实际向日葵查询均返回6条来源，读取199条采集榜单；原生词条排首截图已看图。实际微信新会话确认phoneBound=true，云端关注首项向日葵、四平台观测恢复：微博/抖音/头条未入已采集榜、快手来源unknown。未宣称向日葵当前有榜位，也未把单次观测当真实升降验收；升降逻辑使用受控样本验证。

原生首次恢复断言误按preview本机模式检查，实际是已绑定账号的云端关注；改为真实会话读取云端并恢复UI列表后验证通过。本机忽略文件project.private.config.json仅关闭开发工具域名检查以恢复联调，发布配置urlCheck=true不改，普通服务鉴权保留。合并网络/CLI命令曾被自动审批拦截（仅返回blocked by policy），改用独立只读Node请求和独立官方CLI安全完成验证。

preview构建通过主包约422KB/总包5.3MB；最后加入20项上限客户端提示与空榜措辞后相关范围重跑41/41通过，最终二维码收尾更新。git diff --check通过。累计94，下次95合并91–95范围检查、100完整检查。实际物理手机跨设备关注与后续真实升降仍待验证，历史待办不凭本次关闭。

### 第95次 · 灵感AI统一配置与接口状态

最近五次91–95汇总：账号AI推荐与多轮对话；TA开场与聊天窗口；三个思路入口排版；真实热点搜索与账号关注/榜位监测；本次三场景模型统一配置、持久版本与脱敏状态。到期执行五次范围合并，不额外全量，100次才执行下一次完整检查。

统一管理TA主动推荐、继续对话、热点总结的启停/现有连接/模型/超时/输出Token/补充风格，网页与原生中台同源读取。新增独立配置版本、CAS、回滚、缓存版本失效、业务与手动检测分离、错误分类、最近30条脱敏记录及1000条保留上限。密钥继续服务器只读管理，不传用户对话到日志；普通微信身份不能访问管理员接口。本机流程设计稿添加实际中台链接并明确设计边界。

范围命令：node --test tests/topic-chat.test.js tests/hotspot-discovery.test.js tests/hotspot-content.test.js tests/inspiration-header.test.js tests/creative-flow.test.js tests/phone-account.test.js tests/video-generation.test.js tests/test-policy.test.js tests/admin-console.test.js tests/inspiration-ai-config.test.js tests/workflow-platform-design.test.js，78/78通过，无跳过。Python隔离容器network none挂scripts只读，test-inspiration-ai.py、test-topic-chat.py、test-hotspot-watch.py、test-hotspot-feed.py、test-hotspot-content.py、test-wechat-auth.py、test-video-server.py、test-hotspot-summary.py、test-admin-console.py，共76/76通过。首次远程测试命令的PowerShell变量展开为空，修正为单引号脚本并完整重跑；不把命令失败算业务失败。

必要验证：网页受控样例390/1280宽度验证3场景、发布payload/expectedRevision、检测失败后刷新红色状态、无溢出与脚本错误，截图看图；公网实际管理员手机宽度页面显示3场景与真实千问检测成功，退出登录完成。公网401隔离、同值发布、旧revision409、配置恢复验证通过，实际参数保持原值。ai-95容器healthy，部署前无进行中生成/分析任务，原env/Compose、SQLite在线及管理配置备份在/opt/youai/backups/ai-95。单次真实Qwen检测HTTP200只证明连接，首次上线业务统计未追溯伪造历史。

微信preview构建通过：主包427.5KB/总包5.3MB；git diff --check通过。物理手机完整授权聊天、其他历史待验不由本次模型探测关闭。现有project.config.json变化未纳入提交。累计95，本阶段完成，不重置十次周期；下次96定向，100完整。

### 第96次 · 三阶段中台与小程序共享流程映射设计

需求设计/作品拆解/作品产出新增同项目交互演练、输入输出契约和固定组件映射；支持需求后直接产出或先拆解，独立拆解不伪造简报。默认与自定义草案可启动固定版本演练，确认/费用节点阻断、超时保留步骤、重试与幂等、最终资产和异步飞书状态均可查看。新增设计文档明确Project/Run/StepRun、个人作用域、CAS发布与回滚、客户端兼容、MCP受控能力、Outbox及跨账号权限；不把本地规则演练当真实Skill或已上线流程API。

定向node --test tests/workflow-platform-design.test.js tests/workflow-mapping.test.js tests/test-policy.test.js，17/17通过；覆盖既有草案/MCP调用方及新增三阶段传递、分支路径、失败重试、重复最终回执、版本固定与不兼容组件拒绝。累计96，按规则只执行本次范围，不额外全量。

必要验证：本地HTTP设计稿首次访问8899连接拒绝，重新启动绑定127.0.0.1的隐藏预览服务后，Edge三阶段完整演练、模拟超时重试、自定义图文草案、1440/390宽度无溢出及无脚本错误通过；两宽度截图已看图。未改生产服务器或小程序原生页面，未调用真实AI/MCP/飞书，不宣称真机闭环完成。git diff --check通过。原project.config.json改动不纳入提交。下一次97定向、100完整。

### 第97次 · 内容拆解入口与拆解记录保存

移除“你现在手里有什么/给一个点子…”介绍，起始标题改为1/2·内容拆解；后续沟通/分镜/生成统一属于2/2创造成片。参考视频按钮改为“保存拆解并开始创造成片”，真实分析完成且保存成功后才进入成片沟通，不跳过分镜/付费确认。新增按账号隔离的本机最近30条拆解记录、同素材采样与计划去重、存储失败阻断，剔除服务器私有素材路径。拆学工作台及视频页可进入“我的拆解记录”；页面明确本机保存、未跨设备同步，不宣称云端记录已上线。

定向node --test tests/analysis-records.test.js tests/video-generation.test.js tests/creative-flow.test.js tests/test-policy.test.js，35/35通过。首次31/32，旧界面断言要求四阶段编号，按新两阶段文案更新并新增保存成功/失败、重复点击、账号隔离与真实拆解校验后重跑通过。无后端、AI供应商或飞书变更。

必要验证：微信IDE首次preview未识别新增WXML；quit/open刷新文件缓存后构建通过，主包431.1KB/总包5.3MB。原生模拟器拆解标题/去除旧介绍与记录页截图看图通过，未提交真实付费模型任务。git diff --check通过。累计97，仅本次范围；下次98定向、100完整。project.config.json已有改动不纳入提交。

### 第98次 · 拆解重点自动/手动收放

拆解重点右上角添加自动/手动，默认自动，隐藏素材、模板、目标、DIY与同步明细，显示按当前偏好完成拆解说明；手动展开原选项。该开关只控制设置复杂度，不覆盖已同步偏好、模板或拆解方案，不新增模型调用。

定向node --test tests/video-generation.test.js tests/analysis-records.test.js tests/analysis-presets.test.js tests/test-policy.test.js，37/37通过。覆盖默认自动、手动展开、非法值忽略、切换不改写方案，以及原有生成、保存与模板行为。累计98，本次定向，100完整。

必要验证：原生模拟器自动隐藏、手动展开、恢复自动通过并截图看图；首次自动化点击在视口外未切换，滚入后重试通过。首次看图发现原生按钮默认宽度挤压标题，限定切换器宽度后重验、重跑范围37/37及重新preview通过，最终主包432.7KB/总包5.3MB。git diff --check通过，无后端或生产部署变化。project.config.json已有变更未纳入提交。

### 第99次 · 代表帧五档采样

代表帧选项改为智能、精简、正常、精细、超细，默认智能，五按钮同排且使用紧凑标签。既有smart/sparse/standard/detailed ID兼容，新增ultra，约1秒采样、12–24帧上限；其他档位密度和数量上限不改。复用旧分析缓存时刷新档位中文标签，不要求为改名重复解析。

定向node --test tests/video-generation.test.js tests/analysis-records.test.js tests/test-policy.test.js，31/31通过；覆盖五档顺序、默认智能、超细请求参数、分析中禁止切换与原有保存/生成调用方。Python隔离network none挂当前scripts只读test-video-server.py，25/25通过，覆盖超细15秒16帧、长视频24帧封顶、短视频点位有效及原有分析/缓存行为。累计99，仅本次范围；下一次100完整并汇总96–100五次范围。

必要验证：原生五档同排及默认智能截图看图通过；使用明确UI样例展示采样区，未发真实分析调用，样例随后恢复。preview通过主包432.8KB/总包5.3MB。部署前无进行中生成/分析任务，env/Compose备份在/opt/youai/backups/sampling-99；sampling-99容器healthy，已核对部署文件五档注册与24帧上限，公网https://youai888.top/youai/health为200。未把配置检查当真实超细视频分析端到端成功。git diff --check通过，project.config.json已有改动不纳入提交。

### 第100次 · 拆解前置设置与完整检查

最近五次96–100汇总：三阶段共享流程/小程序组件映射设计；拆解保存与本机账号记录；重点自动/手动收放；五档采样及超细服务端；本次采样与重点移到粘贴前并压缩布局。最近十次91–100另含账号AI对话、TA聊天窗口、灵感三入口、真实热点关键词监测、统一AI管理配置。按规则只执行完整node --test tests/*.test.js，不另跑本次或五次定向范围。

采样与重点移至来源入口下方、偏好开关与粘贴框之前，参考视频未取得时也显示。删除两区小字解释与同步明细，压缩默认卡片内边距、选项按钮与间距；手动展开时压缩素材/目标间距，未同步好模板时禁用手动入口。预选采样档位无参考素材时不提交分析，实际分析仍使用选定档位。

完整测试首次305/306：第97次新增记录页缺少前端交接页面索引；补齐docs/frontend-inventory.md后完整重跑306/306通过，无跳过。npm不在当前PATH，使用规则明确等价的node --test tests/*.test.js。必要验证：原生空粘贴框前五档与重点可见、预选超细不发分析、手动展开通过，两态截图看图；测试后恢复智能/自动及原状态。preview构建通过主包433KB/总包5.3MB，未调用付费AI，无后端变更/部署。git diff --check通过。原project.config.json变化不纳入提交。

累计100，完整检查与必要验证通过，本批关闭；下一批从1/10开始，累计101定向、105范围、110完整。历史真机手机号/完整生产流程/跨设备拆解记录/真实超细分析端到端待验继续保留，不凭本次界面测试关闭。

### 第101次 · 半高设置、理解摘要与后台拆解收录

新批1/10。五档采样/自动手动按钮覆盖全局88rpx最小高度，改为44rpx，进一步压缩设置区。分析结果前新增TA理解摘要，引用真实时长/画幅/节奏/音轨文案，缺少证据不虚构主题，明确画面主体与含义待核对。底部拆为后台排队/保存开始出片；用户明确后台只完成拆解并存记录，不自动成片。后台按钮复用当前分析任务，保存账号本机索引并进入记录页；完成自动收录，失败/网络异常可见，刷新中换账号不串记录。

服务端创建/进度/完成状态写入持久卷references/jobs，客户端离开不停止工作线程；完成结果重启后可读，未完成任务遇重启明确失败，不假报持续运行。任务索引仍本机保存，未实现跨设备任务列表；当前理解摘要不新增多模态语义模型调用，文档见background-analysis.md。

定向node --test tests/video-generation.test.js tests/analysis-records.test.js tests/creative-flow.test.js tests/test-policy.test.js，42/42通过；涵盖已有保存/生成调用方、排队不生成、完成幂等收录、摘要证据边界、账号切换。Python隔离network none只读挂scripts，test-video-server.py、test-wechat-auth.py，30/30通过；新增后台worker落盘、内存清除后读取完成结果及重启中断失败状态。未额外全量测试。

必要验证：原生双按钮/摘要样例和默认设置截图看图通过；首次截图反映开发工具旧样式缓存，重启后44rpx半高效果确认，样例已恢复，未执行付费生成或虚构真实分析成功。preview构建通过主包439.4KB/总包5.3MB。部署前无进行中生成/分析任务，env/Compose备份/opt/youai/backups/queue-101；queue-101容器healthy，公网/youai/health为200。不把隔离worker/界面样例当真机完整后台拆解端到端验收，历史待验保留。git diff --check通过；project.config.json已有变更不纳入提交。累计101，下次102定向、105范围、110完整。

### 第102次 · 三入口等宽与采样单排

删除说个点子/参考视频/模板口令的小字说明，三入口等宽横排，显式限制原生按钮宽度避免第三项溢出，小屏也保留三列。代表帧采样标题与五档同排，标题/拆解重点统一26rpx，标题与选项保留24rpx间距；选项自适应剩余宽度，保持44rpx按钮和适度64rpx行高。默认智能、原有采样与来源切换逻辑不改。

定向node --test tests/video-generation.test.js tests/creative-flow.test.js tests/test-policy.test.js，37/37通过；新增三个入口仅标题、模板口令切换与输入仍可达，保留生成/采样等调用方范围。原生三入口同屏、实际点击模板口令再返回参考视频成功；五档同排、标题字号与间距截图看图通过，无模型调用。preview通过主包440.1KB/总包5.3MB，git diff --check通过，无后端变更。累计102，下次103定向、105范围、110完整；project.config.json原有变更不纳入提交。

### 第103次 · 预期与内容边界自动/手动及平台多选

预期组和内容边界分别支持默认自动收起/手动展开，切换保留原有偏好和必须出现/不要出现；边界移至预期组后、时长/模型设置前。抖音/视频号/小红书/快手/哔哩哔哩多选，至少一项，默认抖音；不同平台辅助约束合并进入生成提示词，平台变更清除旧分镜，双端检查边界版本与分镜一致。官方资料及视频号专项待核验边界见platform-content-boundaries.md，不保证规则全覆盖或审核通过。

定向node --test tests/video-generation.test.js tests/analysis-records.test.js tests/creative-flow.test.js tests/content-boundaries.test.js tests/test-policy.test.js，最终47/47通过。Python隔离network none只读挂scripts及utils目录：test-content-boundaries.py、test-video-server.py，29/29通过，包含旧客户端无边界兼容、多选合并、可信规则提示词、改平台要求重新确认分镜。未额外全量测试。初次原生节点失败定位为配置加载兼容，改小程序JS目录与服务器JSON并增加一致性测试；Node无法发现该运行时差异，修正后原生两开关、多选、手填展开及截图看图通过。自动化reLaunch后错误navigateBack已改为reLaunch清理，不计业务失败。

preview最终通过主包444.6KB/总包5.3MB。无真实付费生成调用。部署前无进行中生成/分析，env/Compose备份/opt/youai/backups/boundary-103；boundary-103容器healthy，公网管理员总览读取通过。组合CLI/SSH检查命令曾被自动审批blocked by policy，拆为独立官方CLI与只读SSH检查完成，不据此绕过审批。git diff --check通过，project.config.json已有变更未纳入提交。累计103，下次104定向、105范围、110完整；历史真机/付费模型效果待验保留。

### 第104次 · 生成参数与文字/图片/视频产物选择

用户确认三选项指最终作品类型，图片模型明确先不配置。原画面形式问题从预期组移出，生成设置改名生成参数，右上角文字/图片/视频默认视频。文字隐藏视频参数，独立千问文本接口/结果页/复制/账号历史；图片显示待配置并禁用，视频保留原参数与分镜。文字作品SQLite持久化、账号隔离、手机号守卫、32KB限制、并发保护/30秒限流/requestId成功去重，源参考仅传授权分析，不发送服务端路径或密钥。

定向node --test tests/video-generation.test.js tests/creative-flow.test.js tests/content-boundaries.test.js tests/test-policy.test.js，42/42通过。初次旧提问数量断言6需改5，与移除画面形式一致，修正后范围重跑通过。Python隔离network none只读挂scripts及utils：test-text-works.py、test-video-server.py、test-wechat-auth.py，33/33通过；包含HTTP未绑手机号403、绑定后文字生成/历史200、未登录作品401、私有结果持久读取及原有视频路径。隔离模型响应受控，不称真实付费模型实测。

原生三模式切换、标题右侧三按钮、文字隐藏视频时长/参数、图片待配置及禁用、切回视频恢复参数截图看图通过，未发真实生成请求。preview通过主包449.2KB/总包5.3MB。部署前无进行中生成/分析，env/Compose备份/opt/youai/backups/output-104；output-104容器healthy，公网管理员总览通过。git diff --check通过；真实账号完整文字生成仍待验，图片模型不配置，project.config.json原有变更不纳入提交。累计104，下次105汇总101–105范围、110完整。

### 第105次 · 内联分镜与3/3成片发布

最近五次101–105汇总：半高设置/理解摘要/后台拆解收录；三入口与采样单排；预期和平台边界自动手动；文字图片视频产物与文字账号服务；本次内联分镜/时长联动/成品及多平台发布准备。到期只执行五次范围合并，不额外本次定向或全量。

移除成片计划，时长下方加入分镜自动/手动，三段时间轴按所选长度重算，手动文案保留；显式时长选择覆盖点子中旧时长，旧批准分镜长度不符时拒绝生成。成功及历史重开进入3/3，成品分内容/可编辑标题/可选封面；按账号作品保存本机发布草稿。发布区平台多选并复制文案准备上传。App任意直跳未接入，不能把准备或复制当实际发布；明确保留待接入/真机验收，不写造假AppID或Scheme。封面临时路径不声称云端持久化，详见storyboard-publication.md。

范围node --test tests/video-generation.test.js tests/analysis-records.test.js tests/creative-flow.test.js tests/content-boundaries.test.js tests/publication-draft.test.js tests/test-policy.test.js，51/51通过；首次50/51旧断言要求“先看分镜草案”，更新为内联“分镜草案”后完整范围重跑通过。Python隔离network none只读挂当前scripts/utils：test-content-boundaries.py、test-text-works.py、test-video-server.py、test-wechat-auth.py，35/35通过，包含101–104后端调用/权限和持久化变化。当前105没有后端修改或部署，不重复跑全量。

必要验证：原生18秒分镜/手动编辑/3/3内容标题封面与多平台准备截图看图通过；看图发现标题input高度不足，修正后范围重跑并复看截图。测试仅明确UI样例，未生成/发送作品，样例已清除。preview最终通过主包457.2KB/总包5.3MB，git diff --check通过；project.config.json原有变化不纳入提交。

累计105，范围测试及可用界面验证通过；App直跳未实现且不能验收，作为本阶段未完成项保留，不将其标记通过；历史真机发布/真实文字生成等待验继续保留。105不重置十次周期，106定向，110完整。

### 第106次 · 修复文字生成超时

线上真实调用复现qwen3.8-max默认思考模式下40秒超时，原接口将所有异常统一显示为检查模型连接。按阿里云官方混合思考说明，为qwen3.8系列文字创作及灵感对话请求显式设置enable_thinking=false；其他模型保持原参数。文字错误细分超时、凭据、额度、模型、参数、网络及无效响应，不返回供应商异常内容或密钥。无自动重试或重复计费请求。

本次定向node --test tests/video-generation.test.js tests/inspiration-ai.test.js tests/test-policy.test.js，35/35通过。远端network none隔离挂scripts/utils，无生产凭据：test-text-works.py、test-inspiration-ai.py、test-video-server.py、test-wechat-auth.py共42/42通过，覆盖非思考参数、错误脱敏、持久化与账号权限及关联视频调用。

部署前公网管理员预检无进行中任务，私有env/Compose备份/opt/youai/backups/text-106；镜像text-106健康。部署后用生产容器实际TextWorks代码和私有千问连接、独立临时数据库生成测试文案，2.0秒返回84字，保存及读取一致；临时数据自动清除，不写真实用户作品。公网管理员接口预检再次通过。实际小程序账号端点击生成未代用户执行，不将此作为已验收。官方依据https://help.aliyun.com/zh/model-studio/deep-thinking/。git diff --check通过。project.config.json原有改动未纳入提交。累计106，下次107定向、110完整；历史App直跳待接入事项保留。

### 第107次 · 发布区精简与仅保存

删除发布区底部固定说明及复制成功后的长段提示，复制成功改为短Toast，失败仍显示可操作错误。发布作品标题右侧增加仅保存，复用按账号作品隔离的本机发布草稿存储，保留标题、封面路径及平台选择，不调用生成或发布；失败不显示保存成功。原始文字/视频作品沿用已有服务端历史，封面仍为本机路径，不声称新增云端上传。

本次定向node --test tests/video-generation.test.js tests/publication-draft.test.js tests/test-policy.test.js，37/37通过，覆盖成功保存、存储失败、无发布请求及关联成品行为。原生自动化验证按钮可见，截图看图确认标题左右布局、提示段落移除；明确UI样例已清除，未执行真实发布。官方preview通过，主包457.5KB，总包5.3MB。git diff --check通过。无后端改动或部署；project.config.json原有改动不纳入提交。累计107，下次108定向、110完整。

### 第108次 · 任务开放期待统计与文案调整

本次逻辑改动合并执行期间追加的文案要求：口号调整为突出创作价值的版本，入口及资产页展示名改创作资产，和TA聊改和ta聊。任务大厅移除两张示例任务卡，显示期待开放 +1；成功弹出已收到，正在超级加速！。登录及绑定手机号后按账号去重记录，不因失败显示成功、不因重复点击虚增。SQLite置于管理员持久目录，中台总览新增任务开放期待人数，只返回汇总不暴露用户标识。原资产实际支持范围不新增生成能力。

定向node --test tests/task-interest.test.js tests/account-layout.test.js tests/test-policy.test.js，最终9/9通过，含请求失败、准确Toast、重复点击及原入口布局。远端network none隔离test-admin-console.py、test-wechat-auth.py、test-video-server.py共43/43通过，覆盖持久化、去重、后台鉴权、HTTP重复提交及匿名401。首次Windows测试发现SQLite上下文未关闭文件，改closing显式关闭；Windows余下一项因缺imageio_ffmpeg环境失败，转依赖齐全的隔离镜像完整重跑本次Python范围通过，不忽略失败。

原生任务按钮和新口号截图看图通过，preview主包458.5KB/总包5.3MB。部署前无进行中生成分析，env/Compose私有备份/opt/youai/backups/interest-108，线上interest-108 healthy；公网管理员登录后总览taskInterest数字字段及实际HTML统计入口验证通过，不创建测试票污染生产计数。真实用户端点击仍由用户执行，成功弹出交互已单测验证。执行中用户看到Not found时后端尚未部署，本次已完成上线，非吞错或假成功。git diff --check通过，project.config.json原有改动排除。累计108，下次109定向、110完整。

### 第109次 · 创作入口文案与紧凑布局

删除创作页“从一个选题，开始你的短视频创作。”、拆学页“看懂案例，把好方法用进创作。”及其容器占位，任务页原说明保留。三个创作入口按要求改为爆款拆解复刻、一句话出作品、爆款口令，移除小字解释和主入口小标签；保留一主两辅位置及原始data-source点击行为，将入口行184rpx压缩至148rpx并调整内边距和标题间距，拆学工作台顶部间距同步收紧。

本次定向node --test tests/creation-tools.test.js tests/account-layout.test.js tests/task-interest.test.js tests/test-policy.test.js，16/16通过，覆盖三入口名称、说明移除、布局高度、原入口源类型及关联账号/任务页面。原生创作和拆学两页自动化及截图看图通过，三按钮均可见，顶部无删除说明残留。preview通过主包458.4KB/总包5.3MB。git diff --check通过，无后端变更，无部署或模型调用；project.config.json原有变化不纳入提交。累计109，下次110汇总最近五次并只执行完整测试及必要验证。

### 第110次 · 重复期待动效与入口整理（完整验证）

最近五次106–110汇总：千问非思考调用和错误分类；仅保存及发布区精简；期待统计、资产与口号调整；创作三入口紧凑布局；本次重复点击独立提示动画、管理中台归入偏好设置、展开榜单靠右加大字号。最近十次101–110还涵盖拆解后台队列、采样布局、平台内容边界、文字产物、内联分镜和发布草稿。本次到期只执行完整前端测试，不另跑定向或五次范围。

期待按钮保持期待开放 +1且不禁用，每次成功提交创建独立提示节点，短暂停留后上移100rpx并逐渐透明，1.8秒移除；隐藏或卸载页面清理计时器。失败仍提示实际错误，不伪报收到。后台仍按账号去重期待人数，不把重复点击当新用户。管理中台移入accountMore折叠分组。展开文案改为展开榜单 +，展开状态保留收起榜单 −，按钮靠右、27rpx。

完整node --test tests/*.test.js（npm test等价命令，环境无npm）最终325/325通过。首次318/325，7项失败为既有五个预期问题、已删除说明/示例任务、和ta聊改名及本次中台位置导致的旧断言；按已确认产品行为更新断言后完整重跑通过。远端network none隔离后端test-admin-console.py、test-wechat-auth.py、test-video-server.py、test-text-works.py、test-inspiration-ai.py、test-content-boundaries.py共56/56通过，无生产凭据挂载。

原生任务按钮、提示显示/消失、偏好展开/折叠中台、榜单靠右及文案自动化通过，截图看图通过；动效时间线及独立提示清除单测通过，未创建真实期待票。preview通过主包460.0KB/总包5.3MB。git diff --check通过，本次无后端改动/部署，project.config.json原有改动排除。累计110，完整测试和本次必要验证通过，关闭本轮，111从新一轮1/10继续；既有App直跳及真机发布未验事项仍保留。

### 第111次 · 统一创作资产与资料编辑

我的创作原先只读本机旧方案，现合并本机方案、旧视频记录、账号云端文字/视频作品，视频按ID去重、标准化秒/毫秒时间倒序，并复用仅保存后的发布标题和封面信息。保留方案编辑、复制口令和复盘入口，新增文字按ID和云端视频按授权资产清单重开，不将云端记录写入旧共享本机索引。创作资产增加全部/作品/灵感/AI交流/拆解分类、完整内容查看和来源相应入口。云端每类最近100条；本机旧方案/灵感/拆解不声称已云同步，旧数据不做归属迁移。AI交流含提问、回复及推荐主题角度。详见creative-assets-profile.md。

爆款拆解复刻图标和32rpx文字横排；拆学右上书本图标改拆解记录，原记录链接处改优秀案例标题。账号资料支持昵称、预设头像和邮箱保存；用户明确暂无发信服务，邮箱仅保存且emailVerified=false，不伪称绑定。接口以会话账号确定归属，校验字段/昵称长度/头像范围/邮箱格式，不接受客户端账号ID或直接修改手机号。

定向node --test tests/creative-assets.test.js tests/video-history.test.js tests/publication-draft.test.js tests/creation-tools.test.js tests/account-layout.test.js tests/video-generation.test.js tests/creator-preferences.test.js tests/topic-chat.test.js tests/record-switch.test.js tests/test-policy.test.js最终76/76通过。远端network none只读挂当前scripts/utils，无生产凭据，test-wechat-auth.py、test-text-works.py、test-video-server.py共35/35通过，含邮箱持久化/格式/账号隔离、HTTP资料保存、资产匿名401、对话账号隔离及主题角度、既有视频路径。中间看图发现旧方案毫秒时间错误放大排序，修正并加入用例；补充发布草稿标题复用和云端视频重开后按相同范围重跑通过。

原生四页截图看图通过；上线前预检无进行中生成分析，env/Compose私有备份/opt/youai/backups/assets-111。assets-111-final容器healthy；公网实际账号读取文字1/视频7/AI交流22（运行时快照），资料保存及重读保留原值通过，原生实际文字和云端视频重开通过，AI交流分类通过。首次部署前截图出现Not found，部署后重查已清除。未为验证更改真实昵称或邮箱，未新建生成任务。最终preview主包469.4KB/总包5.3MB通过，git diff --check通过；project.config.json原有变化未纳入提交。累计111，新一轮1/10，下次112定向，115五次范围，120完整。历史App直跳和真机发布事项保留。

### 第112次 · 优秀项目切换与入口强调

拆学页新增“优秀作品/优秀项目”切换，作品标签复用现有优秀案例列表，项目标签展示短视频创作加速计划及真实需求共创计划，并注明即将开放/筹备中。我的页商家角色入口显示“切回用户”并直接切换回个人视角；个人角色仍可进入原商家体验确认。创作三个快捷入口高度由148rpx提高至192rpx，增幅约30%。

定向 `node --test tests/creation-tools.test.js tests/account-layout.test.js tests/inspiration-header.test.js tests/test-policy.test.js`：23/23通过，覆盖快捷入口尺寸、标签文案和状态切换、角色入口及相关页面。微信开发者工具preview通过，主包471.6KB、总包5.3MB；`git diff --check`通过。开发者工具自动化端口127.0.0.1:9420未开启，实际页面点击与截图复核受限。无后端变更或部署，`project.config.json`原有改动排除。累计112，下次113定向、115汇总最近五次范围，120完整测试。

### 第113次 · 商家入口文案

个人视角下“我的”页快捷入口文案由“商家认证”改为“切为商家”；商家视角下仍显示“切回用户”，点击行为不变。

定向 `node --test tests/account-layout.test.js tests/test-policy.test.js`：8/8通过；`git diff --check`通过。无后端变更或部署，`project.config.json`原有改动排除。累计113，下次114定向、115汇总最近五次范围，120完整测试。

### 第114次 · 日历纳入创作资产统计

日历月度热力图和当天记录现在统计点子、创作方案、收藏，以及创作资产中的视频作品、文字作品、AI交流和视频拆解；当天明细新增“创作资产”分组。按真实时间归属中国时区日期，无有效时间戳的数据不伪造日期；点子、方案仍展示在原分组，避免重复计数。登录后的云端资产加载完成会刷新日历；云端读取失败时保留本机可统计的内容。

定向 `node --test tests/day-feed.test.js tests/idea-calendar.test.js tests/record-switch.test.js tests/creative-assets.test.js tests/test-policy.test.js`：26/26通过，覆盖日期归属、月格计数、当天明细和现有资产页行为。微信开发者工具preview通过，主包473.4KB、总包5.3MB；`git diff --check`通过。无后端变更或部署，`project.config.json`原有改动排除。累计114，下次115汇总最近五次范围测试，120完整测试。

### 第115次 · 创作偏好覆盖预设与AI调用

偏好按创作方向、视频风格与意图、产物类型、自动/手动工作流、边界平台、生成参数、发布平台与助手节奏组织；加入按选题、热点、文字作品和视频生成分别设置的 AI 表达偏好。选题与热点摘要会取得档案领域、创作目的、受众和关注关键词；文字和视频请求复用对应的结构化创作参数。个人偏好只影响风格和关注方向，不覆盖事实、平台边界或系统安全约束，并由服务端限制为最多 500 字。助手的“先看方案”和“直接生成”分别停在方案审核及进入有费用提示的生成确认。偏好页链接到既有拆解模板、目标与 DIY 设置。图片模型仍未配置，图片暂不可选；模型凭据仍由已有服务配置管理。

按第115次规则执行最近五次（111–115）合并范围：`node --test tests/creative-assets.test.js tests/video-history.test.js tests/publication-draft.test.js tests/creation-tools.test.js tests/account-layout.test.js tests/video-generation.test.js tests/creator-preferences.test.js tests/topic-chat.test.js tests/record-switch.test.js tests/day-feed.test.js tests/idea-calendar.test.js tests/hotspot-discovery.test.js tests/inspiration-header.test.js tests/test-policy.test.js`：109/109通过。Python选题聊天 6/6、热点总结 3/3、文字生成 4/4、项目虚拟环境视频服务 27/27，共40/40通过；JS/Python语法检查通过。微信开发者工具preview通过，主包487.3KB、总包5.3MB；`git diff --check`通过。无生产部署或付费模型调用；`project.config.json`既有改动排除提交。累计115；下一次116执行本次受影响范围，120执行完整 `npm test`。

### 第116次 · 全局口号更新

将首页所有用户可见的口号统一为“创作超简单，作品超有价值！”，并同步断言和历史批次说明，避免旧版口号继续作为产品文案出现。

定向 `node --test tests/task-interest.test.js tests/inspiration-header.test.js tests/test-policy.test.js`：13/13通过；微信开发者工具preview通过，主包487.4KB、总包5.3MB；`git diff --check`通过。累计116；下次117执行本次受影响范围，120执行完整 `npm test`。

### 第117次 · 手机号授权失败反馈

授权按钮点击时显示即时状态；微信快速手机号验证额度耗尽（`errno=1400001`）时解释暂时无法弹出授权框，并指向管理员补充额度的路径；区分用户取消与其他无授权码错误。组件保留微信自己的额度提示，不绕过手机号授权。

定向 `node --test tests/phone-account.test.js tests/account-layout.test.js tests/test-policy.test.js`：14/14通过，覆盖微信授权额度不足、用户取消、其他失败、正常绑定及账号入口回归。微信开发者工具preview通过，主包488.0KB、总包5.3MB；`git diff --check`通过。累计117；下次118执行本次受影响范围，120执行完整 `npm test`。

### 第118次 · 手机号授权失败原因诊断

实际失败回调未返回手机号凭证，但此前界面隐藏了微信具体错误原因。移除授权按钮上的 Toast，避免干扰原生授权交互；额度错误码仍单独处理，其他失败展示经过截断和清理的微信 `errMsg` 与 `errno`，便于区分额度和其他平台配置问题。

定向 `node --test tests/phone-account.test.js tests/account-layout.test.js tests/test-policy.test.js`：14/14通过，覆盖错误码与错误信息展示、取消、额度错误、授权绑定与入口回归。微信开发者工具preview通过，主包488.0KB、总包5.3MB；`git diff --check`通过。真实微信授权仍需用户使用更新后的预览版/体验版再操作，根据实际错误码继续平台侧定位。累计118；下次119执行本次受影响范围，120执行完整 `npm test`。

### 第119次 · 明确手机号快速验证入口

确认登录采用微信“手机号快速验证组件”（`open-type="getPhoneNumber"`）及其 `bindgetphonenumber` 回调，服务端按微信手机号接口兑换动态凭证；明确按钮文案，避免与实时验证混淆。未变更组件 API 或服务端兑换方式。

定向 `node --test tests/phone-account.test.js tests/account-layout.test.js tests/test-policy.test.js`：14/14通过；`python scripts/test-phone-account.py`通过，覆盖服务端动态凭证兑换链路；微信开发者工具preview通过，主包488.0KB、总包5.3MB；`git diff --check`通过。真实手机授权仍需在预览版复测。累计119；下次120执行完整 `npm test`。

### 第120次 · 明确手机号隐私声明缺失错误

依据真机回调 `errno=112` 和 `api scope is not declared in the privacy agreement`，登录页现在明确说明手机号信息未加入微信公众平台的《用户隐私保护指引》，并列出用途“账号注册登录与账号安全”。保留微信手机号快速验证组件；此错误必须由小程序管理员在微信公众平台补齐并提交手机号用途声明，代码不能代替平台设置。另修正台账密钥检测测试的边界，避免把 `task-interest` 文件名误判为 `sk-` API 密钥。

按第120次执行完整测试（覆盖最近十次111–120）：`npm test` 在此环境不可用（未安装 npm），执行等价命令 `node --test tests/*.test.js`：340/340通过；首次失败定位到密钥检测正则将 `task-interest` 误判为疑似密钥，修正边界后完整复测通过。微信开发者工具preview构建通过，主包488.0KB、总包5.3MB；`git diff --check`通过。批次111–120已完成，新批次从累计121开始；实际微信授权待平台隐私声明补齐后复测。

### 第121次 · 游客先浏览与主动手机号登录

首次打开不再自动校验账号、跳转或弹出手机号授权；游客可先浏览公开内容与工具，在“我的”页自主选择登录。尝试 AI 对话、AI热点总结、账号资料编辑等账号能力时才提示手机号快速验证，并可关闭登录层继续浏览。移除 app 前台静默登录入口。

定向 `node --test tests/phone-account.test.js tests/topic-chat.test.js tests/hotspot-discovery.test.js tests/account-layout.test.js tests/inspiration-header.test.js tests/test-policy.test.js`：40/40通过；微信开发者工具preview通过，主包490.4KB、总包5.3MB；`git diff --check`通过。未提交微信审核，真实微信端审核结论待更新版本提交后确认；`project.config.json`既有改动排除。累计121；下次122执行本次受影响范围，125汇总最近五次范围测试，130完整 `npm test`。

### 第122次 · Claude 协作规则入口

新增根目录 `CLAUDE.md`，指向 `AGENTS.md` 作为唯一规则来源，并在 `tests/test-policy.test.js` 增加对应断言。影响范围仅限协作规则文档与规则测试，不涉及小程序页面或后端。

定向 `node --test tests/test-policy.test.js tests/development-master-plan.test.js`：8/8通过；`git diff --check`通过。累计122；下次123执行本次受影响范围，125汇总最近五次范围测试，130完整 `npm test`。

### 第123次 · 配置中心与六板块中台

新增 `scripts/platform-config.py`、`scripts/test-platform-config.py`、`tests/platform-config.test.js`、`scripts/deploy-platform.ps1`、`scripts/check-image-modules.py`；修改 `inspiration-ai.py`（多连接路由、text_works 场景、旧配置补齐、连接检测）、`text-works.py`（经网关调用）、`admin-console.py/html`（平台与流程接口、六板块界面）、`video-server.py`（接入配置中心、服务状态、视频默认与等待上限、解析密钥）、`pages/admin`、`utils/admin-client.js`、`Dockerfile.video`。影响范围：管理中台、灵感AI/话题对话/热点总结、文字作品、视频生成参数、参考解析密钥、镜像构建。

定向测试：`node --test tests/platform-config.test.js tests/admin-console.test.js tests/inspiration-ai-config.test.js tests/workflow-platform-design.test.js tests/workflow-mapping.test.js tests/topic-chat.test.js tests/test-policy.test.js` 35/35通过；Python `test-platform-config`(8)、`test-inspiration-ai`(9)、`test-text-works`(5)、`test-topic-chat`、`test-hotspot-summary` 通过（本机 Python 3.10）；依赖 tomllib 的 `test-admin-console`(12) 与 `test-video-server` 在 Python 3.13 隔离副本运行：admin-console 全过，video-server 26/27，唯一失败为沙箱 FFmpeg 音轨提取，与改动前基线相同。真实 Chromium 走查网页中台9个板块、写入密钥、新增连接、流程发布与非法顺序拦截、390宽度无溢出；部署脚本 PowerShell 语法解析与 DryRun 通过。云端：`platform-3aa5fb3` 部署成功，容器 Healthy、公网 /youai/health 200、未登录访问 /admin-api/platform 返回401；首次候选因镜像缺数据文件被健康检查拦截并自动回滚。真实模型检测与手机原生页面仍未验证。累计123；下次124执行本次受影响范围，125汇总最近五次范围测试，130完整 `npm test`。

### 第124次 · 图文（图片生成）密钥位

修改 `platform-config.py`（image-gen 连接、image 配置校验/回滚/旧配置补齐、image_settings）、`video-server.py`（环境变量兜底）、`admin-console.html`（创作工具图片配置卡、发布携带 image、导航换行）及对应测试。影响范围：配置中心发布与回滚、模型与密钥页、创作工具页。

定向：`node --test tests/platform-config.test.js tests/admin-console.test.js tests/inspiration-ai-config.test.js` 11/11；Python `test-platform-config`（新增2项）、`test-inspiration-ai` 通过（本机3.10），`test-admin-console` 与镜像加载检查在3.13副本通过；Chromium 930宽度走查：写入图片密钥只显示末4位、发布图片模型、10个导航全部可见、无页面错误。未调用真实图片模型。累计124；125汇总最近五次范围测试，130完整 `npm test`。

### 第125次 · 增量发布（只传改动）

新增 `scripts/remote-release.sh`、`scripts/deploy-delta.sh`，重写 `scripts/deploy-platform.ps1` 为默认增量、依赖变化自动整包；`.gitattributes` 固定 `*.sh` 为 LF。影响范围：发布流程（不涉及业务代码）。

第125次为五次范围检查（121–125）：`node --test tests/phone-account.test.js tests/topic-chat.test.js tests/hotspot-discovery.test.js tests/account-layout.test.js tests/inspiration-header.test.js tests/test-policy.test.js tests/platform-config.test.js tests/admin-console.test.js tests/inspiration-ai-config.test.js tests/workflow-platform-design.test.js tests/workflow-mapping.test.js` 66/66通过；Python `test-platform-config`、`test-inspiration-ai`、`test-text-works`、`test-topic-chat`、`test-hotspot-summary` 通过。发布脚本以桩 ssh/scp/docker/curl 端到端模拟：增量发布（312KB）、已是线上版本、健康检查失败自动回滚、依赖变化拒绝增量/自动整包，PowerShell 解析与增量路径通过。真实服务器增量发布待执行。累计125；130完整 `npm test`。

### 第126次 · 首页标签切换回顶与选题字段契约

修改 `pages/main/index.js`（tab 切换回顶），新增 `tests/main-tab-scroll.test.js`（回顶行为、选题对话客户端字段与 `scripts/topic-chat.py` 白名单一致）。影响范围：首页底部标签切换、灵感页选题对话。

定向：`node --test tests/main-tab-scroll.test.js tests/account-layout.test.js tests/topic-chat.test.js tests/hotspot-discovery.test.js tests/navigation.test.js` 32/32通过；微信开发者工具控制台实测五个标签切换后 scrollTop=0、滚到底部内容与悬浮导航间距23px；服务器只读核查旧镜像字段白名单与测试记录归属。需随下一版小程序提交审核生效。累计126；130完整 `npm test`。

### 第127次 · 审核整改：案例视频封面报错

修改 `templates/study.wxml`（移除本地 poster），新增 `tests/review-readiness.test.js`（所有 video poster 必须为 https）。影响范围：case-study 与 study-201~204 案例页。

定向：`node --test tests/review-readiness.test.js tests/case87.test.js` 5/5通过；开发者工具游客视角走查五个标签、点子变视频、拆学案例、文案提取工具，修复后控制台无错误（仅既有警告）。累计127；130完整 `npm test`。

### 第128次 · 个性化记忆

新增 `scripts/user-profile.py`、`scripts/test-user-profile.py`、`utils/user-profile.js`、`tests/user-profile.test.js`、`docs/personalization-memory.md`；修改 `topic-chat.py`（可调轮数/记录数、画像与探索要求注入、缓存键含画像）、`platform-config.py`（personalization 版本化配置）、`video-server.py`（/profile 接口、owned_runs、注入）、`admin-console.html`（个性化规则卡片）、`Dockerfile.video`、灵感页选题反馈与偏好页“TA 的了解”。影响范围：选题对话、配置中心、灵感页、偏好设置页。

定向：`node --test tests/user-profile.test.js tests/main-tab-scroll.test.js tests/topic-chat.test.js tests/account-layout.test.js tests/creator-preferences.test.js tests/platform-config.test.js tests/admin-console.test.js tests/inspiration-ai-config.test.js` 35/35通过；Python `test-user-profile`(11，含切换模型连接后画像一致)、`test-topic-chat`、`test-platform-config`、`test-inspiration-ai`、`test-text-works`、`test-hotspot-summary`、`test-admin-console` 通过，`test-video-server` 26/27（既有 FFmpeg 沙箱限制）；镜像加载检查通过；服务器只读用 jieba 校验选词质量。累计128；130完整 `npm test`。


### 第129次 · Claude → Codex 交接文档

新增 `docs/agent-handoff-2026-10-17-claude.md`、`tests/agent-handoff-claude.test.js`，AGENTS.md / CLAUDE.md 增加交接入口；同时记录第128次已增量发布 `platform-d214e58`（线上 health 200、/profile 未登录 401、日志无错误）。定向 `node --test tests/agent-handoff-claude.test.js tests/agent-handoff.test.js tests/test-policy.test.js` 8/8通过。累计129；**下一次第130次执行完整 `npm test`**。


### 第130次 · 选题回复定位与完整阅读

修复固定高度对话区在回复数据更新、思考占位移除之间定位不稳定的问题：回复与思考状态完成渲染后，定位最新助手回复开头；每轮重置滚动目标，长回复保留全文与主题卡，补充滑动阅读提示。增加长回复与连续轮次 mock 回归。完整测试发现第121/126次行为变更后两个旧测试桩未同步，分别补齐已绑定账号资料和 pageScrollTo mock。

最近五次126–130范围汇总：首页标签回顶/字段契约、案例视频封面、个性化记忆、交接规则、聊天回复显示。最近十次121–130还包括游客浏览、协作规则、配置中心、图片配置与增量发布；依第130次规则只执行完整测试。npm 不在 PATH，使用等价命令 `node --test tests/*.test.js`：358/358通过。首次全量354/356通过，修正旧测试桩并增加本次回归后全量复测通过。开发者工具注入长回复 mock，确认最新回复顶部位于对话区内（421.2px 对416.8px），长文本438.6px可在182px区域内滚动阅读；截图已检查。未点击真实生成或模型探测，IDE已有账号自动开场是否命中缓存未核实。真机仍待更新版本复测；未部署或提交审核。

本次回交文档为 docs/agent-return-2026-10-17-codex.md；两处既有修改 project.config.json 与 Claude交接文档格式排除。累计130，批次121–130关闭；下次131定向、135五次范围、140完整测试。
补充构建验证：微信开发者工具 preview 通过，主包504.1KB、总包5.3MB；git diff --check通过。


### 第131次 · 删除创作节奏并默认日历

删除偏好设置的创作节奏入口及每周目标/默认展示表单，清理目标计算与偏好字段；加载旧档案时忽略weeklyGoal和view，首次进入记录区统一默认日历，手动切换四类记录仍可用。旧节奏深链接回落创作方向，其他档案设置保持。

定向 `node --test tests/creator-preferences.test.js tests/record-switch.test.js tests/day-feed.test.js tests/idea-calendar.test.js tests/user-profile.test.js tests/test-policy.test.js tests/agent-handoff-claude.test.js`：35/35通过。开发者工具preview通过，主包502.9KB、总包5.3MB；git diff --check通过。未部署/提审，未点击付费生成，真机待更新验证。累计131；下次132定向，135五次范围，140完整测试。


### 第132次 · 内容先行的识别推荐与三类产物

以原视频代表帧和转写进行多模态理解，新增独立reference_understanding场景、证据与不确定项校验、按产物区分的有据建议，识别失败可重试或由用户补充。用户本次自由需求与识别纠正进入文字/图片/视频，方向字段支持自写，推荐由用户逐条采用；视频按内容组织1–12段，文字/图片不受视频首尾帧模式限制。图片实现wan2.6-t2i异步提交、SQLite幂等、失败可见、后台恢复、PNG持久保存、签名访问、相册保存、发布草稿和创作资产/日历整合。新增个人图片偏好和默认产物选项，中台可配置视觉理解模型及既有图片连接。详见docs/content-first-creation.md。

影响范围：视频/文字/图片创作页、偏好页、主页面资产与日历、创作资产库、账号签名资源、模型网关、中台场景配置、视频服务和Docker模块列表。定向命令：

`node --test tests/account-layout.test.js tests/admin-console.test.js tests/agent-handoff-claude.test.js tests/analysis-presets.test.js tests/analysis-records.test.js tests/analysis-templates.test.js tests/cloud-deployment.test.js tests/content-boundaries.test.js tests/creation-tools.test.js tests/creative-assets.test.js tests/creative-command.test.js tests/creative-flow.test.js tests/creator-preferences.test.js tests/day-feed.test.js tests/demo-backend-data-design.test.js tests/demo.test.js tests/domestic-deployment.test.js tests/idea-calendar.test.js tests/inspiration-ai-config.test.js tests/main-tab-scroll.test.js tests/phone-account.test.js tests/platform-config.test.js tests/publication-draft.test.js tests/record-switch.test.js tests/task-interest.test.js tests/test-policy.test.js tests/topic-chat.test.js tests/user-profile.test.js tests/video-asset-pipeline.test.js tests/video-generation.test.js tests/video-history.test.js tests/video-session.test.js tests/video-source.test.js`

结果：187/187通过。Python content-understanding 5、image-works 11、creation-flow HTTP集成3、video-server 28、inspiration-ai 10、text-works 6、phone-account 3、admin-console 12，共78/78通过；platform-config在Windows首次出现POSIX权限600断言不适用，在禁网Linux容器中执行10/10通过，合计88项通过。新增模型请求与下载全部mock，HTTP集成覆盖匿名/跨账号/签名下载/伪造参考素材，未运行真实生成。镜像模块加载检查通过；微信preview主包514.6KB/总包5.3MB。隔离预览副本的接口限定本机mock，最新识别依据、自由需求/建议卡、图片结果已截图走查；旧缓存截图与自动化跨上下文数组注入不作为通过证据，修正验证方式后确认新界面。git diff --check通过。

未部署/提审，真实模型质量、连接开通、域名与真机相册待部署后验收；图片是文生图，不声称已支持参考图编辑或飞书归档。project.config.json与Claude交接文档格式两处既有改动排除；未使用部署钥匙。累计132，下次133定向，135汇总最近五次范围，140完整测试。

### 第133次 · 旧版完整备份与新版本部署

新增scripts/backup-production.sh、tests/production-backup.test.js与发布记录，更新回交验证：写入停止后备份文件/SQLite WAL和PostgreSQL，EXIT恢复保护，恢复旧服务后导出镜像，私有权限、归档与SHA校验。影响生产发布、持久数据、回滚、小程序上传与交接。未改生成业务代码，发布的源码为288590f。

定向命令：`node --test tests/production-backup.test.js tests/cloud-deployment.test.js tests/domestic-deployment.test.js tests/platform-config.test.js tests/test-policy.test.js tests/agent-handoff-claude.test.js`。结果18/18通过。真实服务器执行备份脚本：四个SHA-256通过，tar/gzip与pg_restore目录读取通过；SQLite离线quick_check通过。镜像18模块与服务加载通过；platform-288590f健康，公网DNS/HTTPS health200，匿名profile/admin-api/platform/works/image均401；模型配置只读确认，不执行真实生成。微信upload 1.0.133成功，主包514.6KB、总包5.3MB，尚未提审/正式发布；真机和真实模型效果待验收。完整恢复演练未执行。

服务器完整备份/本地源码及Git bundle/慢速副本.partial边界见docs/release-2026-10-17-133.md。git diff --check通过；仅使用用户youai_deploy，排除project.config.json和Claude交接既有格式修改。累计133；下一次134定向，135最近五次范围，140完整测试。

### 第134次 · 视觉模型修正、无口播画面拆解与开源选型

修改视觉默认为目录实际存在的qwen3-vl-plus、关闭该系列思考模式；content-evidence-3失效旧缓存；视觉失败保留错误码，不把原始转写当画面文案或把元数据当成功结构；展示时间段主体/动作/机位。人物运动帧差不直接推断剪辑/音乐节奏。请求错误分类与脱敏、HTTP非JSON失败、连接失败清空假进度并可重复重试。检索官方GitHub仓库与许可，路线记录在video-understanding-open-source.md；没有安装SenseVoice/PySceneDetect或复制上游代码。

定向：`node --test tests/service-error.test.js tests/video-generation.test.js tests/video-session.test.js tests/analysis-records.test.js tests/creator-preferences.test.js tests/asset-lifecycle.test.js tests/platform-config.test.js tests/inspiration-ai-config.test.js tests/video-asset-pipeline.test.js tests/agent-handoff-claude.test.js`，77/77通过。Python test-content-understanding.py 6、test-inspiration-ai.py 10、test-video-server.py 28，44/44通过（本机依赖路径沿用第132次）。首轮旧断言仍期待泛化成功摘要/旧网络文案，已更新为分段与失败真实状态后复测；不隐藏失败。preview通过，主包516.4KB/总包5.3MB，diff检查通过。只读生产日志与GET /models定位模型问题；生成调用全mock，真实舞蹈识别效果、音乐类别判别与真机仍待用户验收。

本次需先备份再部署；最终线上标签与上传回执见最新回交。累计134；下一次135汇总131–135范围，140完整测试。两处既有修改不提交，未使用claude-deploy。

发布补记（同一逻辑改动，不另计数）：服务器完整旧版备份/opt/youai/backups/20261017T141430Z-platform-288590f，四项SHA/tar/gzip/PG目录检查通过；随后部署platform-cbe5b1f，18模块加载及公网health200/admin401通过，线上只读配置确认qwen3-vl-plus。部署脚本-SkipTests仅跳过其重复的自动Python流程，本次44项Python已单独执行通过。微信upload1.0.134成功，回执在services/upload-1.0.134.json；未提审/正式发布。77项Node最终复测通过。video-to-prompt的官方README/SPEC/依赖清单补入选型，未执行上游代码。

### 第135次 · 低成本视频看懂方案（规格文档）

Claude 新增 docs/video-understanding-low-cost-plan.md 与 tests/video-low-cost-plan.test.js、任务台账条目，无业务代码改动。按规则执行131–135最近五次范围测试（第131–134次涉及的全部 Node 测试文件 + 本次新增），结果见下行。未部署、未调用真实模型；project.config.json 与 Claude 交接文档格式两处既有修改不提交。累计135；下一次136定向，140完整测试。

结果：196项中194通过；2项失败均为 cloud-deployment.test.js 调用 `docker compose config`，本执行环境（Claude 的 Linux 工作区）没有 docker（spawnSync docker ENOENT），与本次改动无关，需在装有 Docker Desktop 的本机复测。新增文档契约测试通过。

### 第136次 · 低成本观看配置、场景与持久用量台账
新增usage-ledger.py：SQLite原子预算预留/usage结算、用户每日新视频额度、缓存命中记录和今日/七日汇总。新增video_watch/video_watch_deep/video_chat与videoUnderstanding版本化配置、范围校验与旧配置兼容；COPY新增台账模块。授权仅1次真实多图能力验证成功：qwen3.8-flash，165输入/13输出Token（两张合成图），回执在服务器admin/authorized-flash-multimodal-probe-20261017.json；后续验证全部mock。
Python test-usage-ledger.py 2/2、test-inspiration-ai.py 10/10；Node cloud-deployment/platform-config/inspiration-ai-config 10/10通过。最初旧场景超时边界失败，修正为仅观看场景允许120秒后复测。Docker本机cloud-deployment通过，补第135次环境缺口；本次配置未部署。累计136，下次137定向，140完整。

### 第137次 · 本地预处理、宽松观看与全站共享缓存
新增watch-flow.py与watch/normalize_watch/audio_features：前90秒、约1fps+画面变化候选、32帧/360短边/q70，转写裁剪音频，PCM能量峰/BPM/静音全部标估计；宽松丢弃坏字段，仅JSON无法解析时最多修复1次；不生成三类推荐。缓存键只含素材/观看参数/模型连接提示词/版本，跨用户复用；SQLite pending防并发重复提交。额度异常降级本地，保留转写与特征。Python test-watch-flow 4与test-content-understanding 6共10/10，含CPU合成视频边界、音频合成与跨用户/无关revision；Node platform-config 5/5。未接生产路由/未部署，真实模型测试为mock。累计137，下次138定向，140完整。

### 第138次 · 受控深度观看、对话和确认简报路由
生产分析改走content-watch-4；旧分析器保留给旧记录/回归。接入usage台账；按配置低置信自动升级（默认关闭）、手动每用户每视频一次，深度片段限制时长，10MB内内嵌/否则300秒签名。对话最多4次模型调用（含开场）、requestId幂等、画像与纠正按账号存储；确认brief后服务端核对账号/素材/所选产物。中台接口增加usage汇总。Python watch-flow5/creation-flow HTTP4/网关10/微信5/中台12/视频28，共64/64；HTTP首次被既有图片30秒冷却拦截，隔离测试时间后复测通过。Node platform-config/video-generation/phone-account 54/54。匿名401、跨账号403与错产物拒绝验证通过，模型全mock。累计138，下次139定向，140完整；未部署。

### 第139次 · 视频拆解界面与用量中台
创作页接入 content-watch-4 理解卡、手动深度观看、最多四轮拆解对话和可编辑简报，确认后关联所选产物；原生/网页中台展示 usage 和 videoUnderstanding 配置。修复网页中台单价 JSON 编辑时即时解析的问题，改为发布时校验。

定向：`node --test tests/video-watch-page.test.js tests/video-generation.test.js tests/analysis-records.test.js tests/platform-config.test.js tests/admin-console.test.js tests/creator-preferences.test.js`：待执行。需检查开发者工具 preview；所有生成与对话验证使用 mock。累计139；第140次执行完整 `npm test`，并在 Docker 可用本机执行 `node --test tests/cloud-deployment.test.js`。本次未部署。

### 第140次 · 完整测试与视频拆解集成检查
第131–140次最近十次影响汇总：131创作节奏移除/日历默认；132内容先行的识别与文字、图片、视频产物及资产；133旧版完整备份和部署；134视觉识别失败表达与GitHub选型；135低成本观看规格；136视频观看场景、预算和用量台账；137本地预处理、共享缓存；138深度观看、对话与简报服务端校验；139拆解对话界面和管理中台；140消除识别纠正示例文案与既有展示守护测试的误报。影响创作/拆解、素材与AI服务、版本配置和发布基础设施。

完整命令：`pnpm dlx npm@11 test`（直接 `npm test` 因当前 shell 未安装 npm 命令而不可用；此命令调用 npm 11 CLI 执行仓库的同一 `test` script）。首轮375/376，唯一失败为示例文案中的“产品演示”命中宽泛的开发阶段提示检查；改为“应按动物日常来理解”后复测376/376通过。Docker本机补测：`node --test tests/cloud-deployment.test.js`，3/3通过。第139次定向测试68/68通过。微信IDE/模拟器当前未运行，未做交互preview；未调用真实生成模型、未部署。

累计140；批次131–140关闭；下次141定向，145汇总最近五次范围测试，150执行完整 `npm test`。

### 第140次部署补记
用户批准部署后，以 `31cc679` 增量发布 `platform-31cc679`。发布前完整备份 `/opt/youai/backups/20261017T150944Z-platform-cbe5b1f/` 四项SHA通过；镜像19模块加载通过；容器healthy，公网health200，匿名管理API和/reference/chat均401。真实生成与用户视频识别未触发。详见 `docs/release-2026-10-18-140.md`。

### 小程序开发版上传补记
微信开发者工具 CLI 上传 `1.0.135` 成功，总包5.4MB、主包529.0KB；回执 `E:/data/codexYOUAI-services/upload-1.0.135.json`。仅开发版上传，未提审/正式发布。累计140次批次不变；真机体验验收待用户进行。

### 第141次 · 视频拆解页白屏修复（开发者工具依赖分析）

Claude 在微信开发者工具模拟走查第140次上线版本时，进入“爆款拆解复刻”页白屏，控制台报 `module 'utils/watch-page.js' is not defined`。原因：`pages/video/index.js` 在 `Page({...require('../../utils/watch-page')})` 对象展开里内联 require，开发者工具（ignoreDevUnusedFiles）的依赖分析识别不到，模块被当作未使用文件剔除；重编译、清文件缓存都无效。改为顶层 `const watchPage=require(...)` 后展开，页面正常（onShow 89ms，无报错）。新增 tests/page-require-static.test.js 守护 pages/utils/components 不得内联展开 require。

定向：`node --test tests/page-require-static.test.js tests/video-watch-page.test.js tests/video-session.test.js tests/video-generation.test.js tests/video-source.test.js tests/creative-flow.test.js`，57/57通过。已上传的开发版1.0.135可能同样白屏，需重新上传开发版后真机复测。未部署后端（无后端改动），未调用真实模型。累计141；下次145五次范围，150完整测试。

### 第142次 · 真实走查：理解卡中文输出与拆解对话第二轮失败

用户授权用一条抖音手势舞样片（20.8秒，1080×1920）做真实走查。结果：取素材成功；content-watch-4 理解73秒完成，confidence 0.95，逐段动作/机位/音乐描述准确（比心、剪刀手、wink、静态中景、轻快流行乐），但全部字段是英文。拆解对话第一轮正常（中文复述+3个方向+简报），第二轮用户发“我想拍同款手势舞视频，换成我自己在办公室拍”返回 422“对话暂未返回有效内容”：`watch-flow.py` 对模型回复严格 `json.loads`，后续轮次模型会带围栏或改用纯文字，已付费的回复被丢弃。

修复：WATCH_SYSTEM 要求所有文字字段用简体中文（原文/歌名可保留）；对话提示每轮只输出 JSON 且 reply 用简体中文；新增 `chat_json()` 宽松解析（纯 JSON、```json 围栏、文字中夹带的 {...}），仍无 JSON 时把纯文字作为回复并沿用上一版简报，不再 422。未用网关 json_mode（它按选题对话的 topics 结构校验，会误判）。Bound.complete 透传可选参数。已缓存的英文理解卡需在中台把 promptVersion 改为新值才会重算（否则同视频继续命中旧缓存）。

测试：Python test-watch-flow.py 6/6（新增围栏/纯文字/夹带 JSON 三轮用例）、test-content-understanding.py 通过；test-video-server.py 需 Python 3.11（tomllib），本环境 3.10 未运行，需在 Docker/本机复测。Node 定向 `node --test tests/page-require-static.test.js tests/video-watch-page.test.js tests/platform-config.test.js tests/inspiration-ai-config.test.js` 全部通过。真实费用：理解1次+对话2次（第二次失败但已计费），均为用户授权。未部署。累计142；下次145五次范围。

第142次部署补记（同一改动，不另计数）：用户同意后由 Claude 增量部署 platform-6041d3f（上一版 platform-31cc679，自动备份；19模块加载、容器 healthy、公网 health 200、匿名中台 401）。在容器内经 Platform.publish 将 videoUnderstanding.promptVersion 从 watch-v1 改为 watch-v2（版本化，可在中台回滚）。用同一样片真实复测：理解72秒重新计算（非缓存），全部中文、confidence 0.95；拆解对话第二轮“换成我在办公室拍”成功，简报 output=video、保留比心/剪刀手等动作与直视镜头、改为办公室场景。未确认简报、未生成作品。遗留：同账号同素材重做理解后，旧对话轮次仍计入4轮上限（显示3/4），可考虑按 promptVersion 或理解版本重置对话。

### 第143次 · 1:1 复刻（用户自备 Key）

新增 scripts/replica.py、服务路由与 /replica-media 签名访问、Dockerfile 模块、小程序 pages/replica 页与视频页入口（utils/watch-page.js openReplica），说明见 docs/replica-byok.md。用户 Key 不落盘、不记录，查询需再次携带；平台与下载域名白名单；参考视频归属校验；照片重编码；并发/每日限额。

测试：Python test-replica.py 6/6（Key 不入任务文件、跨账号不可见、授权必填、输入校验、平台错误中文化且脱敏、限额、超 30 秒截取），在线上同版镜像（Python 3.12）内另跑 test-watch-flow / test-wechat-auth / test-content-understanding 全部通过；test-video-server.py 28 项中 18 通过，10 项为 render() 依赖本机中文字体（镜像内无该字体路径），与本次改动无关。Node 定向 `node --test tests/replica-page.test.js tests/page-require-static.test.js tests/video-watch-page.test.js tests/platform-config.test.js tests/video-session.test.js tests/video-generation.test.js` 56/56。真实模型未调用（之前第142次后的样片测试已验证 animate-move 接口与计费）。累计143；145五次范围，150完整测试。

第143次部署补记（不另计数）：发现 Claude 第141–143次提交把 7 个原为 LF 的文件提交成 CRLF（只改行尾，导致增量部署误判 Dockerfile 依赖变化），07036ac 恢复为 LF，无内容变化。随后增量部署 platform-07036ac（备份 platform-6041d3f；20 模块加载、healthy）。公网 health 200；匿名 /replica/jobs、/replica/check、/replica-media 均 401。开发者工具打开 pages/replica/index，用假 Key 检测返回“API Key 无效或已失效”（getPolicy 不扣费）。未用真实 Key 生成；小程序需重新上传开发版后真机验收。

### 第144次 · 创作板块开发方案文档

新增 docs/creation-board-plan.md、tests/creation-board-plan.test.js 与台账条目，无业务代码。定向 `node --test tests/creation-board-plan.test.js tests/agent-handoff-claude.test.js tests/test-policy.test.js`，结果见下行。累计144；下次145五次范围（141–145），150完整测试。
结果：# pass 7 # fail 0

### 第145次 · 创作板块 M1：使用说明框、上传原视频、平台识别

按 docs/creation-board-plan.md M1：新增 scripts/link-platform.py 与 utils/link-platform.js（抖音/快手/小红书/B站/视频号识别，非抖音提示上传原视频且不调用解析器）；解析结果新增 source（作者、#话题、发布时间、公开互动数、粉丝数、音乐、抓取时间；不含头像/签名）；新增 POST /references/upload（multipart 流式落盘、取首个文件段、ffmpeg 探测、按 sha256 去重入 REFERENCE_ROOT、账号归属）；utils/link-notice.js 与 utils/reference-intake.js（三按钮说明框[上传原视频][放弃查看][我知道了]、7 天内不再提示、上传进度、复用 applyReference）；视频页接入（上传原视频按钮、说明框置于页尾不影响导航检查）；video-brief 支持上传素材作为来源。顺带修复第143次遗漏：pages/replica 加 app-navigation 与 frontend-inventory 条目；把测试产物 replica-tests/ 移出项目目录（曾使主包体积检查超 2MB）。

范围测试（141–145）与全量：Node `node --test tests/*.test.js` 374 项 370 通过；4 项为本环境缺依赖（docker×2、smol-toml、powershell 归档），与改动无关，需在用户本机复测。Python（线上同版镜像 3.12）：test-link-platform 2/2、test-replica 6/6、test-watch-flow、test-wechat-auth 通过；test-video-server 30 项 20 通过（含新增上传与非抖音拦截 2 项），10 项为 render() 依赖本机字体的既有环境问题。累计145；下次146定向，150完整测试。

### 第146次 · 创作板块 M2：快看、细看扩展与屏幕文字 OCR

按 docs/creation-board-plan.md M2：新增 scripts/screen-text.py（RapidOCR 本地 OCR：一次 ffmpeg 抽样、540 高、关闭方向分类、25 秒预算、最多 24 帧；跨帧合并为带时间与位置的文字段，标记常驻水印/账号文字，过滤低分与短数字噪声）；watch-flow 预处理期间并行 OCR，结果进入模型上下文（不含常驻文字）并随理解卡保存（analyzerVersion content-watch-5，缓存键加入 schema 与 OCR 开关）；理解卡新增自由描述的 type、tags、valueSources 与 valueShares（百分比）；新增快看场景 video_glance（2–6 张 360 短边帧，≤60 字，全站缓存）与 POST /references/glance；中台配置 videoUnderstanding 新增 glanceRatio（5–20，默认 10）与 ocr 开关，旧配置读取时自动补默认。前端：完整理解进行中显示“大致是：…（完整理解中）”，理解卡显示类型标签、吸引力来源占比与屏幕文字；版本判断兼容 content-watch-4/5。Dockerfile 新增 OCR 依赖 RUN 层；deploy-delta.sh/remote-release.sh 支持“仅新增 RUN 行”时在线上镜像上叠加依赖层。

实测（服务器 2 核）：17 秒对口型视频 OCR 22.6 秒，四句字幕文字与时间全部正确；舞蹈视频无字幕返回空。测试：Python（OCR 测试镜像，3.12）test-screen-text 3、test-content-understanding 8、test-watch-flow 7、test-platform-config、test-inspiration-ai、test-link-platform、test-replica 全通过；test-video-server 30 项 20 通过、10 项为既有字体环境问题。Node 全量 375 项中 371 通过，4 项为本环境缺 docker/smol-toml/powershell。累计146；150完整测试。

第146次部署补记（不另计数）：首次部署本机部署进程在服务器构建 OCR 依赖层期间被终止，镜像 platform-61111c6 已建成；手动执行模块检查（21 模块、OCR 可导入）与 remote-release.sh switch 完成切换。真实样片（对口型 17 秒，授权测试）：快看 5.4 秒但 type 照抄了提示词示例，OCR 在线上与转写争用 2 核 CPU 只覆盖到 4 秒。修正（c7a1464）：快看提示要求写具体类型、WATCH_SCHEMA 5.1、OCR 预算 45 秒/等待 55 秒；复测：快看 5.6 秒“情感语录真人出镜演绎”，细看 73.9 秒，type“真人翻唱/对口型视频”，吸引力 表演44/画面33/文字22，OCR 识别 3/4 句字幕（仍为 partial）。已知：模型把歌名写成未经证实的曲名，后续在 M3 纠错中由用户纠正；OCR 速度受服务器 2 核限制，后续可考虑只识别画面下半区或错峰执行。线上 platform-c7a1464。

### 第147次 · 创作板块 M3–M13：确认卡、纠错、分层问询、拆解方案、自动匹配、拆解卡、产出、套版成片、回传复盘、全站汇总、中台

按 docs/creation-board-plan.md 一次实现 M3–M12 与 M13 的代码部分（用户要求连续开发）：
- 后端 scripts/creation-board.py（Board）：会话（同账号同视频 7 天内计次 → 试探问询 / 第 2 次追问 / 第 3 次起对话式问答）；方案匹配（作者/类型/话题/确认次数 → strong/medium/weak 与默认依据，强匹配且理解把握≥阈值才给 8 秒倒计时）；确认与四类纠错（逐条改写、用户说法生成新类型草稿方案并实名上报、指定时间段重看≤2 次、我来描述），纠正只作用于本账号，≥3 个账号纠正同一视频触发共享缓存复核（watch-flow review_hook 重看一次）；拆解方案（7 个内置方案由旧维度迁移、对话生成/修改、复制、编辑、版本回退、删除、样片归纳 3–5 条后台任务）；按方案拆解（固定三字段+自定义≤12，宽松校验，“本视频没有”，按 视频+方案版本+上下文 缓存）；仅本次/存到方案调整；文字作品（原文对比、逐句相似度与≥8 字连续照搬提示、3 标题、封面、话题）；创作包（分镜、口播稿→提词器、节奏卡回退到音频估计、准备清单）；套版成片（ffmpeg 拼接 1–8 段、drawtext 字幕时间轴与淡入、Noto CJK 字体、/board-media 签名访问）；作品发布包、链接自动抓取第 1/3 天公开数据（仅解析不下载）、订阅提醒（openid 仅登录时记录，模板 ID 中台配置）、后台截图视觉识别（仅内存，不落盘）、回传奖励（额度用尽时自动抵扣一次分析）、复盘卡（与本人近 10 条中位数比较、要素映射、可信度、免责声明）、个性化画像信号、发布前预估（解锁且全站≥20 条时）；会话与新类型实名上报、中台看板/聚类/升级内置/会话列表/全站表现、creationBoard 配置。
- 网关新增场景 board_breakdown/board_plan/board_interview/board_output/data_screenshot；platform-config 新增 creationBoard（版本化、可回滚、旧配置补默认）；usage-ledger 支持额度用尽时消耗回传奖励；wechat-auth 新增 openids/notify/token；admin-console 新增 /admin-api/creation/* 与“创作板块”页。
- 小程序：utils/board-page.js + pages/video/board.wxml（等待期问询、确认卡、纠错、拆解卡逐项出现、调整、三条路线、文字对比、套版预览覆盖层与一键成片、创作包、发布）；新页 pages/board-work（回传与复盘）、pages/board-plans（方案管理）；提词器接收创作包口播稿；首次使用隐私告知；docs/privacy-creation-board.md 列出需在公众平台补充的隐私条目。
- Dockerfile：新增 fonts-noto-cjk 与 YOUAI_VIDEO_FONT（deploy-delta 支持新增 RUN/ENV 叠加层）。

测试：Python（本地 3.10）test-creation-board 14、platform-config、inspiration-ai、watch-flow 8、usage-ledger、screen-text、content-understanding、link-platform、replica 全通过；Node 全量 379 项 375 通过（4 项为本环境缺 docker/smol-toml/powershell）。新增 tests/creation-board.test.js 4 项（会话/倒计时自动确认/纠错载荷/产出与发布/页面事件全部有实现）。video-generation 测试桩补充 board-page 与 setInterval。累计147；150 完整测试。

第147次部署补记（同一里程碑，不另计数）：platform-f3064bd 在服务器叠加字体依赖层后本机部署进程中断，手动完成 22 模块检查、字体存在检查与切换；公网 health 200，匿名 /board/*、/board-media、/admin-api/creation/* 均 401。真实样片（对口型，测试账号 claude-test，flash 几次调用）：会话 attempt 1/试探问询/通用方案 weak；理解卡类型“真人翻唱/对口型视频”；按通用方案拆解 9.4 秒，7 个字段均有内容（结尾引导如实写“本视频没有明显的行动号召”）；文字作品 4.8 秒，三句改写与原文相似度 0.36/0/0.18 无照搬，3 标题+封面+话题。发现套版成片失败：imageio-ffmpeg 自带的 ffmpeg 不含 drawtext 滤镜 → 改为 PIL 用 Noto CJK 渲染透明文字条、ffmpeg overlay+fade 叠加（服务器实测合成成功、文字清晰）。

### 第148次 · 交接文档

新增 docs/agent-handoff-2026-10-18-claude.md（线上状态、完成项、待办、约束）。定向 `node --test tests/creation-board-plan.test.js tests/agent-handoff-claude.test.js tests/creation-board.test.js`，结果见下行。累计148；150 完整测试。
结果：# pass 7 # fail 0

### 第149次 · 体验版测试账号

体验版/开发版登录页新增“生成体验账号（随机手机号）”：服务端为当前微信生成独立账号，手机号为虚构 100 号段，直接视为已绑定；登录时携带账号ID切换，仅限请求来源为体验版/开发版（Referer 版本 0 或 devtools）且归属当前微信。数据照常写入，创作板块上报带 `account: 体验版`，中台“创作板块”可按 全部/正式/体验版 统计，并可一键关闭体验账号（会话立即失效，数据保留）。每个微信最多 20 个。
Python：test-wechat-auth（6）、test-creation-board（15）、test-admin-console（12）、test-phone-account（3）通过；Node：379 通过，3 个为环境项（无 .git / tools 目录）。累计149；150 完整测试。
部署：platform-1220551（代码层叠加，22 模块检查通过）；公网 health 200，匿名 /auth/trial 与 /admin-api/trial-accounts 均 401。小程序端需从 E:\data\codexYOUAI 上传新体验版后生效。

### 第150次 · 开发者工具全流程走查（创作板块）

用体验版测试账号在开发者工具走完：生成体验账号 → 链接使用说明框（7天不再提示生效）→ 试探问询 → 大致内容 → 确认卡 → 拆解卡（仅本次调整）→ 文字作品（原文对照）→ 上传自己的画面套版成片（720×1280，字幕按时间轴切换）→ 创作包 → 发布包/作品页（关联链接、手填数据、回传奖励）→ 拆解方案页（对话生成并保存）→ 部分不对（逐段纠正 + 告诉AI类型，生成“卡点手势舞拆解方案”）。中台数据均标注体验版。
修复：①Nginx 对 /youai/ 统一 64KB 上限，上传原视频/套版画面（最高200MB）、BYOK复刻任务（9MB）、数据截图（6MB）在网关即被拒绝 → 为这三个入口单独放宽（服务端仍各自校验）；/youai/board/works 前缀不带斜杠，避免 301 后变 GET 导致“生成发布包”404。②确认卡 catchtouchstart 吞掉按钮点击 → 改 bindtouchstart。③一次提交会重复创建两次拆解会话（提交次数虚增、过早进入追问/对话模式）→ 同一视频同一来源版本共享一次请求。④创作板块按钮无样式、画面上传成功后旧错误不清除。⑤已登录用户在体验版也能从“我的”生成体验账号。
Node：382 通过，3 个为环境项（无 .git / tools 目录）。Nginx 已在线更新（nginx -t 通过并 reload，备份于 /opt/youai/backups）。累计150。

### 第151次 · 灵感碎片箱与 TA 选题

新增碎片箱（docs/idea-box-plan.md）：文字/链接/截图（本地 OCR）/语音（本地转写，音频不留）；idea_note 轻反馈；TA 开场引用未用旧碎片、选题卡显示来源、和 TA 聊这个。Python：test-idea-box（4）、test-wechat-auth（含 /ideas HTTP 与签名图片）、test-topic-chat、test-inspiration-ai、test-admin-console 通过；Node：385 通过，3 个为环境项。部署 platform-52e5a71 → a134d9e → 452ff53；Nginx 增加 /youai/ideas/media 8m。走查发现并修复：轻反馈用 json_mode 被网关按选题格式拒绝；碎片截图相对地址在小程序内加载失败；长 OCR 文本折叠。累计151。

### 第152次 · 拆解质量（五条样片复盘）

见 docs/breakdown-quality-2026-10-18.md。复测：两条图文从“分析失败”变为可拆（幻灯片）；Codex 录屏屏幕字从 40 余条界面乱码降到 3 条作者字幕，“47 分钟”纠正；相亲角识别为商家引流、全程大标题单独改写；李醒醒识别为评论驱动低粉爆款、创作包用改写稿并附原句参考；无商品不再计商品占比。修正：截断回复修复一次、breakdown/output 上限 3500、图文临时文件显式 mp4、低粉爆款按全部互动。Python 新增 test-breakdown-quality（8）。部署 44a4338 → 9102bf2 → cf31257 → 本次（WATCH_SCHEMA 5.3）。累计152。

### 第153次 · A 字幕区域原分辨率二次识别

合并后只选 title/caption 的低置信或数字/英文候选，中点原分辨率取帧，横向15%/纵向40%外扩，字高不足48px放大2倍；只接受更高置信的单行结果并标 refined。最多12次、子预算15秒且受45秒总截止时间约束；ffmpeg超时取剩余预算。WATCH_SCHEMA 5.4。同步OCR调用不能抢占，截止后丢弃结果；真实CPU耗时上限仍待服务器验证。

验证：容器 Python scripts/test-screen-text.py（5）、test-watch-flow.py（8）、test-content-understanding.py（8）、test-breakdown-quality.py（7）全部通过；node --test tests/video-watch-page.test.js tests/creation-board.test.js（8/8）。服务器样片准确率及额外耗时待A–D完成后统一复测。累计153。

### 第154次 · B 作品元数据纠错词典

文案、话题、昵称、音乐名提取2–12字候选；作者字幕与ASR全文/时间段在观看前校正，逐词相似度≥0.75、差1–2字、长度≥3，歧义保留原文；数字不参与。记录corrected来源，保留时间戳。post透传预处理，WATCH_SCHEMA 5.5。
验证：容器Python test-screen-text（6）、test-watch-flow（8，含真实ffmpeg预处理和词典透传）、test-content-understanding（8）、test-breakdown-quality（7）通过；node --test tests/video-watch-page.test.js tests/creation-board.test.js 8/8通过。累计154。

### 第155次 · C 视频small与语音tiny分流（五次范围检查）

视频分析读取中台 videoUnderstanding.asrModel（tiny/base/small，默认small）；碎片和TA语音默认tiny。模型按名称缓存、CPU int8双线程并沿用串行锁，兼容现有tiny离线挂载；Dockerfile预下载三个可选模型，运行时local_files_only。观看缓存包含ASR模型，WATCH_SCHEMA 5.6。中台提供模型选择。
最近五次151–155：碎片箱/TA及语音HTTP；拆解质量/图文/作者文字；字幕裁剪；词典纠错；ASR配置、路由、缓存和镜像。合并范围：容器Python test-asr-routing、test-screen-text、test-watch-flow、test-content-understanding、test-breakdown-quality、test-platform-config、test-idea-box、test-wechat-auth、test-topic-chat、test-inspiration-ai、test-admin-console、test-creation-board 共106项通过；node --test tests/video-watch-page.test.js tests/creation-board.test.js tests/platform-config.test.js tests/admin-console.test.js tests/idea-box.test.js tests/topic-chat.test.js tests/inspiration-ai-config.test.js tests/video-generation.test.js tests/cloud-speech.test.js 共72项通过。
阶段状态：自动测试通过；模型镜像构建、离线加载、中台界面和服务器60秒tiny/small耗时/五条样片仍待验证，不关闭阶段检查。累计155，160完整测试。

### 第156次 · D 抖音公开评论证据

验证DTK已有 GET /api/v1/douyin/video/comments（aweme_id/count=20/include_raw=false/wait=8）；无需改解析服务。取得李醒醒真实评论并确认响应结构。YOUAI仅缓存脱敏文本≤80字、点赞/回复数、是否作者回复，按作品ID 24小时，失败降级空列表。reference.comments进入post_context.topComments最多10条，拆解卡展示3条；拆解提示要求根据真实评论规律，文字作品/创作包新增置顶评论和回复建议。隐私说明更新；样片脚本记录评论与ASR以便对比。
验证：容器Python test-top-comments（2）、test-breakdown-quality（8）、test-creation-board（16）、test-link-platform（2）、test-wechat-auth（6）共34项通过；node --test tests/creation-board.test.js tests/platform-config.test.js tests/video-generation.test.js 共53项通过。已测联系方式/身份字段不落盘、24小时缓存失效、失败不阻断及三条生成链路。界面和服务器五样片复测待完成；未部署。累计156。

第153/154次补充验证与修复（不重复计数）：服务器原OCR把“跑了4分钟”给到0.995434；用户于2026-10-19明确同意两个独立裁剪一致时纠正数字。新增仅数字差异、不同取帧时间、两次≥0.9且文本一致的例外，记录refinement.from/to/originalConfidence/confidences/frameTimes，禁止非数字变化或不一致读数。保留置信度6位；原框直接识别而不重复检测（避免检测器截掉7）；整帧阶段预留10秒。服务器Codex样片旧45.47s→新45.01s，两个作者字幕段都读出“跑了47分钟”，预算下覆盖9/10秒为partial。补充长文案分词。最新Python screen-text 8、watch-flow 9、content-understanding 8、breakdown-quality 8，Node watch-page/creation-board 8全部通过。UI：微信模拟器三条评论和文字置顶建议实际渲染；390px中台ASR选择可切换无横向溢出，截图目视通过。实际真机尚未验证。

第156次补充（不另计数）：文字作品/创作包JSON示例显式列出pinnedComment和replySuggestions，测试校验两条提示均包含字段，避免仅在文字说明中要求而模型遗漏。原D范围Python34、Node53重新通过。

第153/155次服务器复测修复（不另计数）：platform-bcc32c2 全流程中small与OCR并行抢占CPU，舒恩OCR仅覆盖3/10秒且未完成数字双裁剪；因此改为抽帧后OCR→ASR串行，数字候选优先大字幕，WATCH_SCHEMA升5.7使旧结果失效。新增串行执行/大数字字幕优先回归测试。容器Python screen-text9、watch-flow9、content-understanding8、breakdown-quality8、asr-routing2，共36通过；Node watch-page/creation-board8通过。修复版服务器复测待完成。

第156次真实样片补充（不另计数）：五条完成后人工发现commentPlay泛化、网友经历被写成创作者“亲测”。收紧拆解为真实具体话题+规律+动作；两种输出禁止借用评论者亲历、未经核实背书或承诺服务，≤70字完整成句，减少80字落盘截断。Python原D范围34、Node53通过；继续复测五条下游输出，复用已验证5.7观看缓存。

第156次缓存补充（不另计数）：真实复测发现拆解缓存未含提示版本，旧commentPlay继续命中。增加BREAKDOWN_SCHEMA参与缓存key，测试同版本复用、版本变化重新调用且后续复用；原D范围Python34、Node53再次通过。

第153–156次最终验收（2026-10-19，不增加计数）：完整备份 `/opt/youai/backups/20261018T165623Z-platform-8915c8a` 校验通过，通知用户后发布，最终 `platform-4e85b84` / WATCH_SCHEMA5.7 / BREAKDOWN_SCHEMA comments-grounded-2。串行修复后14个Python关联测试文件通过、151–155合并Node72通过；D后续提示/缓存修复均重跑Python34/Node53通过；node --test tests/test-policy.test.js 4/4通过。三个离线模型加载、中台390px模型选择、微信模拟器评论及两类建议显示均完成；25模块检查通过，公网health200/匿名管理401，容器healthy、重启0。未上传体验版，未做真机验证。

服务器60秒同音轨：新tiny50.43s/348.3MB，small267.88s/1348.9MB；原tiny61.93s/347.8MB（共享负载，非独占基准）。使用scripts/sample-breakdown-run.py以claude-test完成五条重新分析及修复后复测；最终五条无HTTP错误、每条3代表评论及两类建议，99条评论白名单通过。舒恩OCR9/10秒partial，两段4→47双裁剪证据保留；李醒醒仍有“行情内幕”错字。最终commentPlay明确引用真实餐饮窍门/深夜焦虑等话题。四轮结果和费用记录留服务器卷，实际模型75次均ok，估算¥0.35721021。生成建议仍需事实/服务承诺校对。

第155次阶段检查的必要环境验证已补齐并关闭；累计156，下一次157，160完整测试，十次周期不重置。详情见 docs/breakdown-quality-2026-10-19-codex.md 与 docs/agent-return-2026-10-19-codex.md。

### 第157次 · 首页页面配置缺失导致白屏

用户截图报pages/main/index缺少JSON、页面未注册。仓库首页仅有js/wxml/wxss，补充pages/main/index.json为空配置，继承app.json全局导航；新增主包及全部分包注册路由必须存在且可解析JSON的回归检查。node --test tests/navigation.test.js tests/demo.test.js：12/12通过。开发者工具重新编译并reLaunch首页，路径正确、125个view及textarea存在；截图目视首页正常显示，不再白屏。截图留本机Temp/youai-main-json-fixed.png；TA卡片仍有独立的“模型或请求参数不受支持”提示，本次没有验证或修复该后端模型问题。累计157，下一次158，160完整测试；仅本地小程序修复，未部署服务器或上传体验版。

### 第158次 · TA聊天自动热榜审核失败降级

真实HTTP复现上游400 data_inspection_failed，原因是自动附带的实时热榜触发内容审核，旧错误分类误报模型参数不支持。Gateway只识别明确审核错误码并保留脱敏事件，不向用户泄露上游原文；TA仅对有自动热榜的该错误移除currentHotspots后重试一次，用户输入、偏好、历史、碎片均保持，仍拒绝则报审核失败。两次请求共享原timeoutSeconds总预算，成功回复明确标为创作建议、hasHotspots=false。

测试：容器Python test-topic-chat7、test-inspiration-ai11、test-idea-box4、test-hotspot-summary3、test-content-understanding8、test-watch-flow9、test-creation-board16、test-admin-console12、test-wechat-auth6，共76项通过；node --test tests/topic-chat.test.js tests/inspiration-ai-config.test.js tests/idea-box.test.js 共12项通过。覆盖仅指定错误重试、无热榜不重试、二次拒绝不持久化、参数完整保留、总超时不增加及错误信息脱敏。完整备份 /opt/youai/backups/20261019T080712Z-platform-4e85b84（约2.1GB）服务归档、数据库、镜像、Nginx SHA256及恢复清单验证通过；通知用户后发布platform-0026265，25模块检查通过。常驻服务真实HTTP新聊天返回3主题；首页实际重试成功且出现热榜暂不可用的创作建议提示，红色错误消失，截图目视通过。公网health200，容器healthy/重启0，无近期Traceback。临时账号请求文件已清理；未上传体验版。累计158，下一次159，160完整测试。

### 第159次 · Claude 2026-10-19～21 轮次汇总（补登记）

本轮 Claude 在 0026265 之后共 72 个提交（4f2915b…1954057），当时未逐条登记，按交接要求合并补记为一次，不追溯拆分计数。内容见 docs/agent-handoff-2026-10-21-claude.md：爆款拆解页动线/粘贴/流光进度/深度解析进度/创作小提示/确认卡自动拆解/超级拆解结果卡/热评加权/接下来做什么/我的创作与作品切换/返回兜底；悬浮球与后台任务（当前任务同步、任务面板）；首页品牌改「有AI」、标题前缀轮换、爆款拆解首屏卡、/creative-assets 增 breakdowns/replicas；每用户每日新视频数与日预算、额度申请（调试期自动通过）；POST /references/peek 快速大致内容、热评与下载并行；飞书多维表格长期资产台账（scripts/asset-ledger.py、发件箱投递、方案表、仅本次调整表）、完整手机号表、采集声明 v2。影响：pages/video、pages/main、pages/board-work、components/app-navigation、utils（board-page/reference-intake/analysis-eta/creation-tips/analysis-records/back-fallback/collect-statement）、video-server.py、creation-board.py、wechat-auth.py、scripts/asset-ledger.py、Dockerfile.video。

测试：按交接要求执行完整测试 node --test tests/*.test.js（设备 Linux 环境分 6 组运行，90 个文件）：444 项，440 通过，4 项失败均为环境项——云端 Compose 实际解析、视频 Worker 持久目录（spawnSync docker ENOENT）、tests/codex-http-repair.test.js、源码归档校验（需 Windows 进程，返回 null），与本轮之前相同，不记为通过。video-server.py 相关 Python 测试需在服务器容器（Python 3.12）验证，本次未执行；体验版未上传，真机未验证。线上 video 服务为 HEAD 增量部署。累计159，下一次160完整测试（本次全量为补登记时的临时全量验证，不关闭160）。

### 第160次 · 隐私说明与采集声明 v2 同步（十次完整测试）

docs/privacy-creation-board.md 改为隐私文案唯一说明：公开评论段更新为最多20条热评按热度加权进入拆解；采集声明逐字同步 v2（VERSION=2，完整手机号/飞书/截图与低清副本）；新增「服务器与飞书上实际保存了什么」表（phones、board.sqlite、ledger 发件箱、media、飞书各表、停用方式、分享权限提醒）；链接使用说明与首次使用告知逐字同步；微信隐私指引补剪切板、手机号、第三方存储（飞书）三行。新增 tests/privacy-doc.test.js 校验文档与 collect-statement/link-notice/board.wxml 文案逐字一致、指引条目齐全。影响：仅文档与测试，无界面和服务端行为变化。

最近十次（151–160）汇总：151碎片箱/TA语音HTTP；152拆解质量/图文/作者文字；153字幕裁剪与数字双裁剪；154词典纠错；155 ASR small/tiny 分流；156抖音公开评论证据；157首页 index.json 白屏修复；158 TA 热榜审核失败降级；159 Claude 10-19～21 轮次汇总（拆解页/悬浮球/首页品牌/额度/peek/飞书台账/采集声明v2）；160隐私说明同步。最近五次（156–160）：评论证据、首页配置、TA降级、Claude轮次、隐私文档。

完整测试 node --test tests/*.test.js（设备 Linux 分6组，91个文件）：446项，442通过；4项失败为环境项：tests/cloud-deployment.test.js 两项（spawnSync docker ENOENT）、tests/codex-http-repair.test.js、tests/project-package.test.js 源码归档（需Windows进程）。环境不可用，未记为通过：需在装有 Docker Desktop 的 Windows 本机补跑 `node --test tests/cloud-deployment.test.js tests/codex-http-repair.test.js tests/project-package.test.js` 后才能关闭本批。node --test tests/privacy-doc.test.js tests/collect-statement.test.js：4/4通过。未部署（无服务端改动），未上传体验版。累计160；本批完整测试已执行，待上述环境项补测后关闭，下一批从161（1/10）开始。

### 第161次 · 方法卡复用（新批次 1/10）

creation-board.py 新增方法库：board.sqlite 表 methods(cat,name,how,level,assets,count,used,last) 与 method_results(work,cat,name,ratio,at)。每次拆解把「能不能学」里可学程度高/中的方法按理解卡类型（去分隔符归一，≤12字）记录，按素材去重计数；生成文字作品/创作包时 payload 增 methods（同类目、至少出现在1条其它爆款、不含本片已拆出的方法；同类目不足2条时跨类目补位需≥3条其它爆款；≥2条作品数据回流且播放中位数<0.8倍作者平时的方法停推），提示词要求挑1–2条自然融入并回填 usedMethods，只记录确实提供过的方法并累计 used；create_work 记下用上的方法，save_metrics 后按 review.ratio 写 method_results 打分；admin_dashboard 增 methods（前20）。小程序文字作品卡与创作包卡显示「借鉴同类爆款方法：名称（N 条同类爆款在用，用过的作品播放约平时 x 倍）」（utils/board-page.js methodNote）。不依赖飞书台账（台账停用时照常工作）。影响：creation-board 拆解/两类输出/作品/数据回流/中台概览，pages/video 两张输出卡。

测试：Python（设备 3.10）test-creation-board 22/22 通过（新增按类目复用、分隔符归一、低可学不入库、本片方法不重复、usedMethods 过滤编造名、播放倍数打分、差数据停推、跨类目补位门槛）；test-asset-ledger、test-top-comments 通过；test-breakdown-quality 8/9，1项为环境项（导入 video-server.py 需 tomllib，Python 3.10 无），需在服务器容器补测。node --test tests/creation-board.test.js tests/video-generation.test.js tests/reference-intake.test.js tests/replica-page.test.js tests/navigation.test.js：104/104 通过（新增 methodNote 文案与 wxml 绑定）。真机/模拟器界面待验证。累计161，下一次162，165五次范围，170完整测试。

第161次补充（不另计数）：新增 Board.backfill_methods()，video-server 启动时后台线程一次性把已有拆解记录补进方法库（cache 表 methods-backfill-v1 标记，只跑一次）。test-creation-board 23/23 通过（新增回填与只跑一次）；video-server.py 语法检查通过，导入测试仍需服务器容器。

### 第162次 · 项目地图与接手文档整理（2/10）

新增 docs/PROJECT-MAP.md（产品一句话、接手顺序、目录与模块、线上与数据卷、测试方法与已知环境失败、发布与回滚、文档现行/交接/历史分类、常见坑，含 TLS 证书 2027-01-13 到期提醒）与 tests/project-map.test.js（地图列出路径必须存在、AGENTS/CLAUDE 必须指向地图）。AGENTS.md 增接手入口、交接文档随做随写、结构变化同步地图；CLAUDE.md 更正过时的交接格式/启动清单引用，补设备 shell 测试分组、tomllib 与 SSH 网络限制；README 顶部指向地图；creation-board-plan 进度表补 M14–M19；task-ledger 登记 RUN-20261021-CLAUDE-CONTINUE；agent-handoff-2026-10-21-claude.md 增「续」节（首次纳入版本库）。项目扫描：未发现已跟踪的密钥（base64 命中为学习分包视频），无误跟踪的日志/数据库。影响：仅文档与文档测试。

测试：node --test tests/agent-handoff-claude.test.js tests/agent-handoff.test.js tests/task-ledger.test.js tests/creation-board-plan.test.js tests/project-map.test.js tests/test-policy.test.js tests/privacy-doc.test.js tests/development-master-plan.test.js tests/product-plan.test.js tests/cloud-creation-roadmap.test.js：33/33 通过。累计162，下一次163，165五次范围，170完整测试。

### 第163次 · 三组 Python 测试补跑与测试隔离修复（3/10）

服务器 SSH 仍不可达（Network is unreachable），第161次方法卡复用未能部署，容器补测改为本机 Python 3.10 + tomllib 垫片（方法见 PROJECT-MAP 第5节）。test-video-server 首跑 1 项失败：`test_reference_download_uses_video_candidates_referer_and_falls_back_after_403` 单独跑通过、整组失败，原因是前一测试把同一链接的解析结果留在 `_PARSE_CACHE`（3 分钟缓存）。修复：`RendererTests.setUp` 清空 `server._PARSE_CACHE`（只改测试）。

测试：`python3 -m unittest test-video-server test-breakdown-quality test-creation-board` 62/62 通过（30+9+23）。部署后需在容器再跑一次确认。

第163次补充：03:44 用 claude-deploy 增量发布 platform-3bb8bbf（含第161次方法卡复用），健康检查 200，备份 platform-1954057。

### 第164次 · 文字作品补「发布正文」，标题沿用原作口吻（4/10）

用户反馈（图文「各位，自建一个抖店动销群…」285赞/803评）：文字作品只有图片文字改写和三个口号式标题，没有正文，标题丢了原作直接邀请的口吻。原因：`text_work` 提示词按视频写，没有要求作品描述，标题无风格约束。修改：`scripts/creation-board.py` 输出新增 `caption`（按原描述改写，保留人称/口吻/句式/长度与互动号召）、`captionOrig`、`captionTooClose`、`kind`；标题须沿用原作开头的口吻与钩子类型，禁止套营销模板；图文不出时间轴；作品与 `publishText` 用正文。小程序 `pages/video/board.wxml` 增「发布正文」可编辑区，图文显示「图片文字」、隐藏原片语音；`utils/board-page.js` 复制与发布带正文。

测试：test-creation-board 24/24（新增图文正文用例）；Node 相关 109/109；容器 Python 3.12 三组 63/63（需置空 YOUAI_PUBLIC_ASSET_BASE_URL）。

### 第165次 · 生成结果顶部附压缩原视频（5/10，五次范围 161–165）

用户要求在文字作品/创作包生成位置上方附上压缩后的原视频，方便对照。新增 `POST /board/preview {id}`（`scripts/video-server.py` `reference_preview`）：按参考素材生成一次 360p（crf32、≤600k、单声道 48k、faststart）副本，存为 `references/<digest>.mp4` 并用 `<sha>.preview` 记录复用；压缩后不更小则直接用原文件；为用户 claim 后返回 `/reference-assets/<digest>.mp4`，由 reply 自动签名。小程序 `pages/video/board.wxml` 文字作品卡与创作包卡顶部加 `<video class="board-ref-video">`（「原视频（压缩版，仅供对照）」，加载中提示），`utils/board-page.js` `boardRefLoad` 每个拆解只请求一次、拼接 baseUrl；`pages/video/index.wxss` 样式。

测试：容器 Python 3.12 三组 64/64（新增预览复用用例）；五次范围 Node 132/132（creation-board、creation-board-plan、navigation、privacy-doc、reference-intake、replica-page、video-generation、interface-copy、project-map、task-ledger、agent-handoff×2、test-policy）。

第165次补充：04:34 部署 platform-c79e8ef（含第164、165次），健康 200，备份 platform-3bb8bbf。预览转码实测 19s 视频 8.6 秒、81s 视频 65 秒。

### 第166次 · 「接下来做什么」上方也放原视频（6/10）

用户要求拆解结果底部、「接下来做什么」上方也放压缩原视频。`pages/video/board.wxml` 在该处加同一播放器（`board-ref-route`），`utils/board-page.js` 改为拆解结果出来即加载预览（不必等生成文字作品）；仍每个拆解只请求一次 `/board/preview`。只改小程序，无需部署后端。

测试：node --test tests/creation-board.test.js tests/interface-copy.test.js tests/navigation.test.js 45/45（新增「仅有拆解即加载预览」用例，播放器数量 3）。

### 第167次 · 裂变：同一段画面出 3 条不同文案（7/10）

用户要求最终页增加裂变功能（已确认：变文案/字幕、入口在文字作品卡下方、一次 3 条）。服务端 `scripts/creation-board.py`：抽出 `_timed_lines` 与 `_render`（套版成片共用），新增 `variants`/`_variants`——调一次模型，基于已生成文字作品写 3 版开头钩子不同、口吻不变、时间轴沿用的文案（附 title/caption），无可用句的版本跳过、最多 3 条；后台线程**依次**合成，单条失败不影响其余，结果存 `outputs.variants`。`scripts/video-server.py` 新增 `POST /board/variants {id,clips,position}`，为每条预先 claim `board:<id>`，进度用已有 `GET /board/jobs/<id>`。小程序：文字作品卡「裂变 3 条」按钮，复用套版成片选画面面板（mode=variants），逐条显示钩子/视频/标题/正文，可复制文案、保存相册；`pages/video/index.js` 卸载时清 `variantTimer`。

测试：test-creation-board 25/25（新增裂变用例：前置条件、跳过坏版本、最多 3 条、依次合成、单条失败、保存结果）；Node 88/88（creation-board、interface-copy、navigation、video-generation）；容器 Python 3.12 三组 65/65，另用真实 ffmpeg 合成 5 秒样片成功。

### 第168次 · 原视频只留在最新完成的板块（8/10）

用户反馈页面出现两个原视频。`pages/video/board.wxml`：「接下来做什么」上方的原视频（及加载提示）在当前路线的结果卡（文字作品/创作包）出来后隐藏，只保留结果卡顶部那个；未生成或切到尚未生成的路线时仍显示在「接下来做什么」上方。仅小程序。

测试：node --test tests/creation-board.test.js tests/interface-copy.test.js 30/30（断言两处条件）。

### 第169次 · 远程 MCP：抖音解析（9/10）

用户要求把解析下载做成 MCP，并用独立的一套资源优先保证 MCP（已确认：服务器远程 MCP、独立解析密钥/额度、直接开放 dtk 自带 MCP、每天 50 次）。新增 `scripts/mcp-gateway.py`：校验客户端访问令牌（服务器只存 sha256）、北京时间每日上限（pool_status/get_task_result 不计，超限返回可读工具错误）、以 MCP 专用 dtk 密钥转发 Streamable HTTP（含 SSE 流式透传，只回传必要响应头）。`scripts/video-server.py` 在 GET/POST/DELETE `/mcp` 于登录鉴权之前交给网关。服务器上已在 dtk 新建 `youai-mcp` 密钥（douyin:read，10 次/分钟），配置写入数据卷 `assets/mcp/config.json`（600）；访问令牌原文写入用户本机 claude-deploy 目录。说明见 `docs/mcp-remote.md`。

测试：test-mcp-gateway 5/5（令牌、每日上限与跨日、拒绝格式、转发头与流、上游错误）；容器 Python 3.12 四组 70/70。dtk 专用密钥实测 initialize/tools/list 正常（8 个工具）。

### 第170次 · MCP 增加服务器托管下载工具 download_video（10/10，十次完整测试）

用户要求再加一个由服务器下载好后提供链接的工具。`scripts/mcp-gateway.py` 增加本地工具机制（register / local_call / augment_list：把本地工具追加进 dtk 的 tools/list，JSON 与 SSE 两种格式都处理）与签名文件链接（file_link / file_allowed，30 分钟，签名密钥由 dtkKey 派生）。`scripts/video-server.py`：`download_video` 用 MCP 专用 dtk 密钥调用 `acquire_reference(..., comments=False)`（新增参数，MCP 不抓评论以省配额），返回作品信息与 `https://youai888.top/youai/mcp/files/<sha>.mp4?e=&s=`；`GET /mcp/files/` 验签后支持断点续传下载。完整测试发现 `scripts/Dockerfile.video` 未包含 `mcp-gateway.py`（整包部署会启动失败），已补入 COPY（仅 COPY 行，增量部署不受影响）。

测试：test-mcp-gateway 7/7；容器 Python 3.12 四组 73/73（新增 download_video 用例：专用密钥、不抓评论、签名链接、错误转可读提示）；完整 Node 450 项 446 通过，4 项为已知环境项（云端 Compose×2、codex-http-repair、源码归档）。

第170次补充：2026-10-22 00:00 部署 platform-3936e72（含第167、169、170次），健康 200，modules ok 27，备份 platform-c79e8ef。公网验证：无令牌/错令牌 401；initialize 200（dtk 5.1.3，SSE）；tools/list 9 个工具（含 download_video）；download_video 真实链接 4.2 秒返回（作品 7693845706146340337，1080×1920，6.76 秒，2,206,939 字节），签名链接下载 200 video/mp4 字节一致，篡改签名 403；pool_status 正常；网关当日计数 1，dtk request_log 记在 youai-mcp 名下。
