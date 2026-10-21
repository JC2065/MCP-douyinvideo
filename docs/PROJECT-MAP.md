# 项目地图（新 agent 先读这一页）

最后核对：2026-10-21，提交 5e9029c 之后。本页只写**现在是什么样**；历史过程看 `docs/test-batches.md` 与各 handoff/return 文档。代码或部署变化时顺手改本页（`tests/project-map.test.js` 会检查本页列出的文件都还存在）。

## 1. 产品一句话

「有AI」（内部代号 YOUAI）微信小程序：用户粘贴抖音链接 → 看懂视频（大致内容 → 深度解析）→ 确认/纠正理解 → 按拆解方案做「超级拆解」→ 生成文字作品 / 创作包 / 套版成片 / 1:1 复刻 → 发布后回传数据 → 复盘。当前主线是**创作板块**（`docs/creation-board-plan.md` 第 0、1、11 节是已定决策与 M1–M13 进度）。用户可见名称一律写「有AI」；`YOUAI1:` 口令前缀、请求头、内部标识不改。

## 2. 接手顺序（约 10 分钟）

1. `AGENTS.md`（规则，必须遵守）→ `CLAUDE.md`（Claude 专用：授权、Git、部署）。
2. 本页。
3. 最新交接：`docs/agent-handoff-*-claude.md` 与 `docs/agent-return-*-codex.md` 中日期最新的一份（当前：`docs/agent-handoff-2026-10-21-claude.md`）。
4. `docs/test-batches.md` 末尾：累计次数、下一次是定向/五次范围/完整测试。
5. 做事前在 `docs/task-ledger.md` 末尾登记；每完成一步就更新交接文档（见 AGENTS.md「Agent 交接」）。

## 3. 目录

| 位置 | 是什么 |
| --- | --- |
| `app.js` `app.json` `app.wxss` `pages/` `components/` `utils/` `styles/` `assets/` | 微信小程序（原生 WXML/WXSS/JS，无 npm 构建）。主包页面见 `app.json`；学习类分包 `case-study/ study-201…204/` |
| `pages/main` | 首页（标题前缀轮换、「爆款拆解复刻」首屏卡、我的创作/作品、登录与采集声明） |
| `pages/video` | 爆款拆解页（最重）：`index.js` 组合 `utils/watch-page.js`、`utils/board-page.js`、`utils/reference-intake.js`；拆解卡模板 `board.wxml` |
| `pages/board-work` `pages/board-plans` `pages/replica` `pages/idea-box` | 作品数据面板 / 拆解方案 / 1:1 复刻（BYOK）/ 灵感碎片箱 |
| `components/app-navigation` | 顶部导航 + 悬浮球（后台任务面板、返回） |
| `scripts/video-server.py` | **线上主服务**（Python，单进程 ThreadingHTTPServer）。加载同目录模块：`creation-board.py`（创作板块、额度、方法卡复用）、`watch-flow.py` `content-understanding.py` `screen-text.py`（看懂视频/OCR/ASR）、`top-comments.py`（热评）、`link-platform.py`（链接识别）、`asset-ledger.py`（飞书长期资产台账）、`wechat-auth.py`（登录、手机号）、`replica.py`、`idea-box.py`、`text-works.py` `image-works.py`、`asset-archive.py`、`analysis-plan.py` `analysis-preferences.py`、`content-boundaries.py` |
| `scripts/mcp-gateway.py` | 远程 MCP 网关 `/mcp`：访问令牌、每日上限、转发到 dtk 自带 MCP（见 `docs/mcp-remote.md`） |
| `scripts/admin-console.py` `admin-console.html` `platform-config.py` | 管理中台（`https://youai888.top/youai/admin/`，登录需用户本人） |
| `scripts/inspiration-ai.py` `usage-ledger.py` | 模型网关（预算、用量台账） |
| `scripts/test-*.py` | Python 单测（unittest，在 `scripts/` 下 `python3 -m unittest test-xxx`） |
| `scripts/Dockerfile.video` `remote-release.sh` `deploy-delta.sh` `deploy-platform.ps1` | 镜像与发布（见第 6 节） |
| `tests/*.test.js` | Node 测试（`node --test`），含小程序页面逻辑、文案守护、文档一致性 |
| `backend/` `compose.cloud.yml` | Node 多端数据中台 + Postgres（早期设计，非当前创作板块主路径） |
| `web/` | 网页版原型、管理流程页 |
| `tools/codex-http-repair` | 独立桌面工具（不进小程序包） |
| `docs/` | 文档，分类见第 7 节 |

## 4. 线上与数据

- 服务器：百度云广州 `182.61.14.185`，域名 `youai888.top`（Nginx，配置 `deploy/youai888.nginx.conf`）。**TLS 证书 2027-01-13 到期**，需提前续期。
- 容器 `youai-video-video-1` 运行 `video-server.py`；版本标签 `platform-<短哈希>`，`bash /opt/youai/releases/remote-release.sh live` 查看。
- 数据卷 `/data/assets/`：`board/board.sqlite`（会话、方案、作品、数据回流、额度、方法库）、`auth.sqlite`（含 `phones` 完整手机号）、`ledger/`（飞书发件箱、表映射、媒体缓存）、`top-comments/`。
- 飞书多维表格（长期资产，含完整手机号）：见 `docs/privacy-creation-board.md`「服务器与飞书上实际保存了什么」。
- 本机（用户 Windows）：仓库 `E:\data\codexYOUAI`；仓库外数据与凭据 `E:\data\codexYOUAI-data`（不进 Git）；Claude 部署钥匙仅 `E:\data\codexYOUAI-data\claude-deploy`。

## 5. 测试怎么跑

- Node：`node --test tests/<相关文件>.test.js`；完整测试 `node --test tests/*.test.js`。在 Claude 的设备 Linux shell 里单次调用最长 180 秒、后台进程会被结束，完整测试要**分组**跑（`ls tests/*.test.js | split -n l/6`，每组 `timeout 55`）。
- 已知环境失败（4 项，不是代码问题）：`tests/cloud-deployment.test.js` 两项（需 docker）、`tests/codex-http-repair.test.js`、`tests/project-package.test.js` 源码归档（需 Windows 进程）。需在装 Docker Desktop 的 Windows 本机补跑。
- Python：设备 Linux 为 3.10，无 `tomllib`、无 PyPI 网络；凡是导入 `video-server.py` 或 `admin-console.py` 的测试（如 `test-video-server`、`test-admin-console`、`test-breakdown-quality` 中图文一项）要在服务器容器（Python 3.12）跑。其余 `test-creation-board` `test-asset-ledger` 等可本机跑。
  - 本机替代（2026-10-21 验证可行）：仓库外建垫片 `mkdir -p ~/shim && printf 'from pip._vendor.tomli import *\nfrom pip._vendor.tomli import load, loads, TOMLDecodeError\n' > ~/shim/tomllib.py`，再 `PYTHONPATH=~/shim`，并把 `video-server.py` 的 Windows 默认路径改到临时目录：`YOUAI_ASSET_ROOT` `YOUAI_TOOL_ASSET_ROOT` `YOUAI_FEISHU_CONFIG` `YOUAI_FEISHU_STATE` `YOUAI_REFERENCE_RELAY_STATE` `YOUAI_REFERENCE_RELAY_CREDENTIALS` 指向 `~/ytmp/...`，`YOUAI_VIDEO_FONT=/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc`。**不设这些变量会在 `scripts/` 下建出 `E:/` 目录**。部署后仍以容器结果为准。
  - 容器内测试（不影响线上）：把 `scripts/` 打包 `docker cp` 到容器 `/tmp/ytest`，同样把上述路径变量指向 `/tmp/ytest/...`，并加 `-e YOUAI_PUBLIC_ASSET_BASE_URL=`（容器自带线上值，会让 `test_reference_relay_*` 失败），再 `python3 -m unittest test-breakdown-quality test-video-server test-creation-board`。
- 界面：微信开发者工具 + 模拟器；ToDesk 远控时 computer-use 不能操作开发者工具，可用 Playwright 按同样式还原截图自检，再请用户真机看。

## 6. 发布

- 只改 `scripts/` 与 `utils/platform-boundaries.json`：增量发布 `bash scripts/deploy-delta.sh`（Claude 用 claude-deploy 钥匙，见 `CLAUDE.md`），或用户双击 `deploy-platform.cmd`（默认增量）。健康检查失败自动回滚。
- `Dockerfile.video` 的 FROM/RUN 变化需整包：`deploy-platform.cmd`（PowerShell `-Full`，需本机 Docker Desktop）。改该文件要按字节替换保留换行（sed 会改整文件换行，导致误判为依赖变化）。
- 回滚：`bash /opt/youai/releases/remote-release.sh switch platform-<上一个>`。
- 设备 shell 能否 SSH 取决于账号网络设置；报 `Network is unreachable` 时请用户双击 `deploy-platform.cmd` 或放开网络。
- 小程序：只能用户从 `E:\data\codexYOUAI` 上传体验版，版本号接上次递增；原生页面改动要随版本审核生效。

## 7. 文档索引

**现行（随代码保持最新）**
- 规则：`AGENTS.md`、`CLAUDE.md`、`docs/progress-reporting.md`、`docs/test-batches.md`、`docs/task-ledger.md`
- 创作板块：`docs/creation-board-plan.md`（主方案）、`docs/privacy-creation-board.md`（隐私唯一说明，和小程序文案逐字一致）、`docs/output-types.md`、`docs/replica-byok.md`、`docs/breakdown-quality-2026-10-19-codex.md`
- 平台与中台：`docs/platform-config-center.md`、`docs/admin-console-guide.md`、`docs/ai-config.md`、`docs/inspiration-ai-config.md`、`docs/domestic-deployment.md`、`docs/release-strategy.md`
- 其它功能：`docs/idea-box-plan.md`、`docs/hotspot-summary.md`、`docs/navigation.md`、`docs/feishu-matrix-setup.md`
- 功能登记：`docs/feature-registry.json`

**交接（只看最新一份）**：`docs/agent-handoff-*-claude.md`、`docs/agent-return-*-codex.md`

**历史 / 早期方案（只作背景，不要据此改代码）**：`docs/handoff-2026-10-08.md`、`docs/agent-handoff-2026-10-11.md`、`docs/agent-handoff-2026-10-13-cloud-parser.md`、`docs/product-plan.md`、`docs/development-master-plan.md`、`docs/backend-data-platform.md`、`docs/demo-backend-data-design.md`、`docs/web-app-design.md`、`docs/cloud-runtime-design.md`、`docs/cloud-deployment.md`、`docs/video-demo.md`、`docs/hotspot-demo.md`、`docs/release-2026-10-17-133.md`、`docs/release-2026-10-18-140.md`。`README.md` 后半部分也是早期实现记录。

## 8. 容易踩的坑

- 设备 shell 默认不能删除文件：git 会留下 `.git/*.lock`。先 `device_request_delete_permission` 申请项目文件夹删除权限；没有权限时把锁文件 `mv` 成 `.git/stale-*`（不要放进 refs）。
- 用户机器无 Git 身份：提交用 `-c user.name/-c user.email` 沿用上一条提交的作者，并加 `-c core.autocrlf=true`；提交前 `git diff --cached --numstat` 确认没有整文件改动（工作区可能是 CRLF）。
- 只 `git add` 自己改的文件：不提交用户的 `project.config.json`，不提交 Codex 未提交的文档改动。
- 不把任何 API Key 写进仓库；不替用户输入密码/密钥；BYOK 用户 Key 不存不记日志；后台截图识别后不保存；评论者身份不保存。
- 改隐私相关文案时同时改 `docs/privacy-creation-board.md`，采集声明 `VERSION` 加 1。
- 不要覆盖用户本机小程序 storage（测试数据另建）。
- `pages/*/index.js` 里 require 要写在顶层常量（内联在对象展开里会被开发者工具依赖分析剔除导致白屏）；每个页面必须有 `index.json`。
