# Agent 双向交接说明 · 2026-10-11

当前任务主线与资源矩阵请先阅读[云端创作推进规划](cloud-creation-roadmap.md)。P0 云端准备 → P1 正式手机闭环是最高优先。2026-10-12 商业版六表及本机资产同步、归档、校验恢复和反馈已实测接通，详见[资产闭环](asset-lifecycle.md)；百度云部署与正式手机验证仍未完成。

本文是本轮交给其他 Agent 的入口，也是未来交回本项目时的验收契约。接手者先按顺序阅读 [AGENTS.md](../AGENTS.md)、[README.md](../README.md)、[测试批次记录](test-batches.md)，再阅读本文。若说明冲突，以用户最新指令、`AGENTS.md` 和当前代码为准。

## 一句话目标

把 YOUAI 的内容创作板块做成持续学习用户偏好的短视频创作工具：用户从点子、抖音链接或模板口令开始，经过少量确认，得到可直接播放和保存的 AI 画面或纯文字视频。

## 交接基线

- 仓库：`E:\data\codexYOUAI`
- 远端：`https://github.com/OnesProu/codexYOUAI.git`
- 分支：`master`
- 本文生成前的功能基线：`988f2af feat: route AI video creation to qianwen`
- 接手时必须以 `git status --short` 和 `git log -5 --oneline` 看到的实际 HEAD 为准，不要重置、覆盖或丢弃未提交改动。
- 测试计数：累计第 20 次完整测试已通过；视频资产契约是累计第 21 次，下一项逻辑改动从累计第 22 次继续。
- 当前活动任务：`docs/task-ledger.md` 的 `TASK-20261011-01`，目标是升级参考视频分析到生成成片的完整工作流。

## 当前已实现

1. 创作首页三个入口分别进入点子、抖音参考视频、模板口令。
2. 视频创作是四阶段：选择起点、对齐创作意图、审核分镜、生成成片。方向沟通包含结果、受众、开场、语气、画面、结尾、2–30 秒时长和内容边界；参考视频额外选择高度参考原片、画面风格、内容结构或同题新作。默认“画面风格”会把最多 3 张代表帧作为 `reference_image` 提交；高度参考只在原片不超过 15 秒且配置 `YOUAI_PUBLIC_ASSET_BASE_URL` 与 `YOUAI_REFERENCE_MEDIA_SECRET` 时提交 30 分钟签名 `reference_video`。缺配置时在付费调用前阻止，不能退化成纯文字生成。系统形成可编辑三段故事板，只有明确批准后才提交生成。
3. 抖音短链直接交给自托管 DTK 解析，再获取媒体；只从视频主地址和视频流选择下载候选，携带抖音来源页请求头并支持 CDN 备用地址回退。只有完成下载、大小、SHA-256 和 FFmpeg 解码验证才进入内容分析。失效短链会返回 `short_link_expired`，媒体地址全部受限会返回 `media_download_failed`，解析器凭据失效会引导到“我的”接口管理。不得仅凭分享文案匹配或替换视频。`scripts/video-server.py` 会异步抽帧、检测变化、转写音轨并缓存 `ReferenceAnalysis v1`，页面成功后标记为 `analyzed` 才允许进入方向确认。代表帧采样分智能、精简、标准、细致四档，并按素材 SHA 与档位分别缓存；采样点避开文件边缘，单点失败执行精确解码重试，至少 3 张有效帧即可降级继续，不足时返回成功数与最少门槛。自动转写需校对，字幕 OCR、多模态画面语义、原视频上传和数据库持久化仍待实现。
   本机已安装 `YOUAI Video Stack Watchdog` 计划任务：登录时及每 5 分钟运行 `scripts/ensure-video-stack.ps1`，以 DTK `/readyz` 和 YOUAI `/health` 为准恢复 Docker Desktop、DTK Compose 栈和视频网关。日志在 `E:\data\codexYOUAI-data\logs`；`scripts/uninstall-video-stack-watchdog.ps1` 可撤销。
   高度参考原片由 `scripts/reference-relay.py` 和 `scripts/ensure-reference-relay.ps1` 提供：独立中继只服务限时 HMAC 原片，TryCloudflare 提供动态 HTTPS，状态写在仓库外 `E:\data\codexYOUAI-data\reference-relay.json`。精确时长位于 15.00–15.50 秒的容器尾帧误差会自动转码成 14.9 秒派生素材，以新 SHA 文件提交并写入 `<原 SHA>.reference-video.json` 血缘；超过 15.50 秒仍阻止。当前适合本机 Demo；上线时替换为命名 Tunnel 或 S3/OSS，不要把 Quick Tunnel 描述为生产 SLA。
4. 视频历史由 `utils/video-history.js` 统一管理。新记录按点子正文、抖音原视频标题或模板主题生成标题并标注来源；旧记录会补来源与时间。用户从“我的 → 视频资产”进入 `pages/video-assets/`，可重新打开成片和资产详情或移除本机索引。成片页五类资产可逐项展开，原片与代表帧经 `/asset-runs/<runId>/source.mp4` 和 `/asset-runs/<runId>/keyframes/<index>.jpg` 受控读取；公开清单不会返回绝对路径。长期文件仍在 `E:\data\codexYOUAI-data\video-assets`，元数据在 PostgreSQL；移除索引不删除长期资产，后续长期删除必须先做引用检查和可恢复机制。
5. 生成任务允许最多 64 KB 请求，足以容纳当前 `ReferenceAnalysis v1`；小程序提交前会裁剪参考对象，只保留分析证据、状态和素材 SHA-256。其他 POST 接口仍使用 8–32 KB 的较小上限，超限会返回明确错误。
6. 服务端会校验故事板 `approved` 状态和三段内容，并把沟通答案、必须出现、不要出现及分镜文案/画面写入实际模型提示词；纯文字 Provider 使用三段分镜文案。
7. 每次成功生成都会写入 `E:\data\codexYOUAI-data\video-assets` 的长期资产包，并通过后端 `/api/v1/video-runs` 事务写入媒体、分析、镜头、故事板、生成任务、最终产物和血缘。成片 URL 改为持久 `/assets/<runId>/final.mp4`，重启视频服务仍可播放；页面“查看本次资产”读取 `/asset-runs/<runId>`。本机资产用户 ID 由 `YOUAI_ASSET_USER_ID` 指定，默认仅用于本机开发环境。
8. `AI 生成画面` 调用千问 `wan3.0-video`，服务端会按参考模式构造 `input.media` 后提交异步任务、轮询并下载 MP4；`纯文字画面` 使用本机 Pillow + FFmpeg 合成。
9. 真实千问验证任务 `3f826597-e33e-4c90-87a0-3c0713317c56` 已成功，结果为 720×1280、H.264、2.02 秒。任务会产生第三方费用，不要为了冒烟测试反复提交真实生成。
10. PostgreSQL 与 YOUAI API 已用 `compose.backend.yml` 运行；`001_identity_and_ideas` 与 `002_video_asset_pipeline` 已应用，后者提供媒体、分析、分镜、故事板、任务、产物、反馈和成本表。小程序业务数据目前仍主要保存在微信本地，尚未切换到后端同步。
11. 首页六个创作工具已进入 `pages/creation-tool/` 可执行工作台。下载、文案、音频、去水印原片和封面复用 `scripts/video-server.py` 的 DTK、FFmpeg 与 faster-whisper 链路，并通过链接索引和 SHA 原片缓存避免重复下载；工具资产只从 `/tool-assets/<sha>/<允许文件>` 读取。去水印仅代表取得平台无水印源，不提供通用涂抹修复。提词器完全本地运行，文案不上传。
12. AI 画面生成前可调整 Wan3.0 模式、清晰度、宽高比、手动/智能时长、声音、提示词优化和水印。默认 720P、9:16、有声、优化提示词、无水印；智能时长提交 `-1`。首尾帧只从已验证原片抽取 `first_frame`/`last_frame`，与 reference 系列素材互斥；高度参考显式时长必须满足输入加输出不超过 30 秒。参数写入资产清单，禁止只改 UI 不改 Provider 请求。

## 关键文件地图

| 范围 | 文件 | 作用 |
| --- | --- | --- |
| 视频页面 | `pages/video/index.js`、`index.wxml`、`index.wxss` | 三阶段交互、来源读取、时长、提交、轮询、播放和保存 |
| 创作入口 | `pages/main/index.js`、`index.wxml` | 三张入口卡及来源参数路由 |
| 创作载荷 | `utils/video-brief.js` | 来源归一化、智能时长和统一任务载荷 |
| 用户偏好 | `utils/creator-preferences.js` | 默认 2 秒、感觉和助手方式；当前只做显式档案存储，不自动推测用户偏好 |
| 服务地址 | `utils/video-service.js` | 开发环境指向 `http://127.0.0.1:8765` |
| 视频服务 | `scripts/video-server.py` | 抖音页面读取、千问任务、本机文字合成、MP4 Range 响应 |
| 视频服务启动 | `scripts/start-video-server.ps1` | 从仓库外凭据文件注入本机 DTK v5.1.3 地址和只读 API Key |
| 视频服务测试 | `scripts/test-video-server.py` | 协议 mock、本机真实 MP4 生成与解码 |
| 前端测试 | `tests/video-generation.test.js`、`tests/creator-preferences.test.js` | 视频流程、载荷、默认值和偏好行为 |
| 后端基座 | `backend/`、`compose.backend.yml` | API、PostgreSQL、迁移和容器运行 |
| 视频资产契约 | `backend/video-pipeline.js`、`backend/migrations/002_video_asset_pipeline.*.sql`、`docs/video-asset-pipeline.md` | 资产去重、状态、成本、血缘、反馈和持久化表 |
| 解析配置 | `utils/tool-interfaces.js`、`pages/tool-interfaces/` | “我的”中的解析器地址、凭据、连接检测和 7 天过期提醒；令牌仅本机保存 |
| 六个创作工具 | `pages/creation-tool/`、`scripts/video-server.py` | 下载、转写、音频、无水印原片、封面和本地提词器；媒体工具共享原片缓存 |
| 进度与规则 | `README.md`、`docs/test-batches.md`、`AGENTS.md` | 能力边界、批次计数与强制交付规则 |

## 本机运行与密钥边界

视频服务启动命令：

```powershell
C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe scripts/video-server.py
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health

需要参考视频解析时，改用 `powershell -ExecutionPolicy Bypass -File scripts/start-video-server.ps1`。本机 DTK 服务目录为 `E:\data\codexYOUAI-services\Douyin_TikTok_Download_API-5.1.3`，凭据在该目录的 `.youai-parser.env`，不得复制到仓库或交接文档。Docker 项目名为 `dtk`，API 仅监听 `127.0.0.1:8000`；当前已铸造抖音访客身份并用作品 `7406616768753503538` 完成真实媒体获取。
```

当前应返回 `qianwen-video` 与 `local-text-renderer`。千问配置从环境变量 `YOUAI_QIANWEN_*` 或 `C:\Users\one\MoneyPrinterTurbo\config.toml` 的 `[app]` 分组读取。密钥不得写入仓库、README、测试输出、提交信息或交接文档。不要在日志中打印完整请求头。

后端状态检查：

```powershell
docker compose -f compose.backend.yml ps
Invoke-RestMethod http://127.0.0.1:8080/health/live
Invoke-RestMethod http://127.0.0.1:8080/health/ready
```

真机不能访问电脑的 `127.0.0.1`。真机或上线前必须部署 HTTPS 服务，修改 `utils/video-service.js`，并配置微信合法域名。

## 已知风险和下一步优先级

### 已解决：生成反馈和任务超时

累计第 19 次已让页面显示提交、排队、生成和下载阶段、已等待时间与任务号缩写，每 2 秒查询一次，并把前端等待上限从 180 秒改为 1800 秒。第三方没有返回可靠百分比，界面不会伪造完成百分比。

### P0：任务持久化与恢复

`scripts/video-server.py` 的 `JOBS` 只存在内存，服务重启后任务状态丢失。需要把本地任务 ID、第三方任务 ID、状态、输出和错误写入数据库，并让小程序重新进入页面后恢复轮询。

### P1：参考视频理解深度

参考视频已完成下载、抽帧、ASR、镜头变化与媒体提交。当前代表帧可约束构图、色彩和场景，但不能保证同一人物身份或逐镜头动作复刻；下一步应增加字幕 OCR、关键帧多模态语义、角色一致性控制和逐镜头生成/审核，并保留“读取成功”“完整分析成功”和“参考媒体已提交”的状态区别。

### P1：用户偏好学习闭环

当前创作档案由用户手动设置，尚未根据生成、重做、保存或发布反馈更新偏好。建议先定义显式反馈事件和可撤销的偏好摘要，再用于下一次生成；不得暗示系统已经学习未记录的数据。

### P2：成片完整度

目前第三方结果是无配音、无音乐的 AI 视频。下一阶段可增加脚本拆分、多镜头、配音、字幕、音乐、拼接和发布前预览，但每一步都要保留素材来源和失败恢复。

## 接手检查清单

1. 运行 `git status --short`，确认并保护已有工作区改动。
2. 阅读 `AGENTS.md` 和 `docs/task-ledger.md`，按活动任务与 `docs/test-batches.md` 的最新累计次数继续。
3. 运行 `node --test tests/agent-handoff.test.js tests/test-policy.test.js` 检查交接资料。
4. 检查视频服务 `/health`，不要用真实付费生成作为普通健康检查。
5. 检查 `docker compose -f compose.backend.yml ps`，确认 API 和 PostgreSQL 状态。
6. 开始任何改动前，先说明目标和受影响文件；完成后更新测试与批次记录，并创建对应 Git commit。

## 开发期间必须持续记录

- 每个逻辑改动对应一个 commit，并在 `docs/test-batches.md` 追加一行。
- 每次新任务开始前先在 `docs/task-ledger.md` 登记起始提交、目标、阶段和继续入口；过程中持续更新，结束时补齐结果。
- 记录用户决策、范围变化、接口契约、数据迁移和未完成验证，避免只存在于聊天。
- 变更第三方模型时记录模型 ID、参数范围、计费触发点和失败语义，不记录密钥。
- 真实付费调用只在功能需要且已获用户授权时执行；优先用 mock 验证协议。
- README 描述当前用户可用能力；设计文档描述未来方案；不能把计划写成已实现。

## 未来交回时的强制格式

接手 Agent 在交回前必须新增 `docs/agent-return-YYYY-MM-DD.md`，至少包含：

1. **回交基线**：分支、HEAD、工作区是否干净、远端同步状态。
2. **完成内容**：按用户可见行为描述，并列出对应 commit。
3. **接口与数据变化**：请求/响应、数据库迁移、配置项及兼容策略。
4. **测试证据**：执行命令、通过数量、真实环境验证和未完成验证；遵守 5/10 次批次规则。
5. **运行状态**：视频服务、容器、端口和后台任务；说明哪些状态会在重启后丢失。
6. **密钥与费用**：只说明密钥位置和付费任务 ID，不写密钥；列出实际触发的付费调用。
7. **未完成事项**：按 P0/P1/P2 排序，写明复现条件、影响和推荐下一步。
8. **回滚点**：可安全回滚的 commit，以及迁移或外部状态的回滚方法。

交回前运行：

```powershell
git status --short
git log -10 --oneline
git diff --check
```

若累计次数到 20，只运行 `npm test`，并完成相应必要集成验证。不得用“代码已写”代替环境验证，也不得把环境不可用记成通过。

## 可直接发给接手 Agent 的提示词

> 接手 `E:\data\codexYOUAI`。先阅读 `AGENTS.md`、`README.md`、`docs/task-ledger.md`、`docs/test-batches.md` 和 `docs/agent-handoff-2026-10-11.md`，保护现有工作区与提交历史。先继续任务台账里的活动任务，并按测试批次最新累计次数执行验证。每个逻辑改动必须更新任务台账、测试、批次记录并创建 Git commit。不要把任何 API Key 写入仓库；真实视频生成会计费，普通验证使用 mock。未来回交时按本文“未来交回时的强制格式”新增回交文档。

## 上传质量优化交接

累计第 50 次已实现分包专用模块迁移、组件按需注入、详情图片迁移；完整测试 193/193 和微信开发者工具 preview/六页面模拟器联调通过。`study-page.js` 与 `offline-video.js` 为五个分包内副本，修改时同步。最终代码质量面板三项状态仍待核验，桌面捕获连续超时，官方模拟器工具不提供该面板结果；第 50 次批次不关闭，后续确认属于同一逻辑改动，不重复计数。

第 50 次补充：媒体门槛现约束所有上传分包合计，187,799 字节，193/193 完整测试重跑通过。JPEG 有损压缩，仓库外 `E:\data\codexYOUAI-data\backups\upload-media-20261012` 保留原图；不要直接恢复原图导致超限。面板绿灯仍待重新扫描，计数不增加。

## 飞书建表工具继续入口

用户确认两个应用尚未创建，先交付建表工具与说明。入口 `docs/feishu-matrix-setup.md`，契约 `backend/feishu-matrix.js`，CLI `scripts/setup-feishu-matrix.js`；企业四表、商业版两表，同 Base 关联、跨组织稳定 ID。仓库外 `E:\data\codexYOUAI-data\credentials\feishu-matrix.json` 仅有占位配置，不能当已取得凭据。24/24 契约测试通过，尚未真实建表，不存在自动业务同步或文件归档。接手后先陪用户完成两个自建应用和 Base 授权，再运行 apply 并核验六表；P0/P1 手机云端闭环优先级保留。

企业管理四表已真实创建并回读：作品总表 8 字段、创作方案 10、存储资源池 11、成本与反馈 10，关系指向作品总表。真实映射保存在仓库外 `feishu-matrix-state.json`。归档组织应用与两表尚未配置；无业务记录同步。接下来陪用户建立商业版组织归档应用。

最新用户决策：单商业标准版组织统一六表，新应用鉴权成功，凭据当前放 management；运行 `--role management --layout unified`，使用新 Base 和独立 unified 状态文件。旧企业表及状态保留；截图已添加可编辑应用，等待表格链接。

统一六表已真实创建（2026-10-12）：商业标准版 Base 六张命名表、61 字段、三处关联均回读通过；再次 bootstrap 无重复。配置与 unified 状态文件仍在仓库外；未写业务记录、未接自动同步或文件归档。下一步接业务同步前保持用户归属、脱敏、持久队列与失败隔离，不把飞书表格作为业务事实来源。
