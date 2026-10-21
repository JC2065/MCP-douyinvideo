# Claude → Codex 交接说明 · 2026-10-17

接手者先读本文，再读 `AGENTS.md`、`docs/task-ledger.md` 末尾、`docs/test-batches.md` 末尾。Codex 交回时按文末“回交格式”新增 `docs/agent-return-YYYY-MM-DD-codex.md`；Claude 下次接手会先读最新一份回交文档。

## 交接基线

- 仓库：`E:\data\codexYOUAI`，分支 `codex/admin-console`，HEAD 为本文所在提交（上一业务提交 `d214e58`）。
- 起点：Claude 从 `2ce8489`（Codex 的“游客先浏览”）接手，首个提交 `ccfc312`。
- 工作区：仅 `project.config.json` 有用户自己的未提交改动（换行符差异），Claude 未触碰，接手后也不要提交它，除非用户要求。
- 远端：本分支**未推送**到 `origin`（GitHub OnesProu/codexYOUAI），Claude 没有执行 push。是否推送由用户决定。
- 测试批次：累计 **129**（本文为第129次）。**下一次第130次必须执行完整 `npm test`**（等价 `node --test tests/*.test.js`）。
- 线上：广州 `/opt/youai/internal-api` 的 `VIDEO_TAG=platform-d214e58`，健康。上一版备份在 `/opt/youai/releases/platform-d214e58/`。

## 本次 Claude 完成内容（按用户可见行为）

| 内容 | 提交 | 文档 |
| --- | --- | --- |
| Claude 协作规则入口（统一遵循 AGENTS.md） | `ccfc312` `d800f41` | `CLAUDE.md` |
| 配置中心 + 六板块管理中台：模型连接（含自定义 OpenAI 兼容连接）、只写不读密钥、文字作品 AI 场景、视频生成参数、三阶段流程草案/校验/发布/回滚、服务配置状态 | `d1e5a88` `36aed9f` | `docs/platform-config-center.md` |
| 图文（图片生成）只写密钥位与模型配置（默认百炼 wan2.6-t2i，生成接口**尚未实现**）；中台导航换行 | `f521b82` | 同上 |
| 部署：增量发布（只传代码，服务器上叠加构建）、整包发布、自动回滚、只读诊断、上传前镜像内加载检查；修复 Dockerfile 漏列模块与 `utils/platform-boundaries.json` | `0ab93a3`…`66396df` `27bf6d8` | `docs/platform-config-center.md`“部署” |
| Claude 专用部署钥匙（独立于用户钥匙，可吊销） | `3defe9c` `04f5bc9` `4faf0e2` | 本文“密钥与费用” |
| 首页：切换底部标签回顶部；选题对话字段契约测试 | `09f1656` | 任务台账 RUN-20261017-HOME-FIXES |
| 审核整改：案例页 `<video poster>` 本地图片报错；审核就绪测试 | `bb006d3` | 任务台账 RUN-20261017-REVIEW-FIX |
| 个性化记忆：选题“喜欢/不想要”、采纳与作品信号 → 规则化画像（门槛/衰减/上限），与模型无关，换模型/换 key 保留；偏好页“TA 的了解”可查看/删除/关闭/清空；中台可调参数 | `d214e58` | `docs/personalization-memory.md` |

## 接口与数据变化

- 管理接口（独立管理员会话）：`GET/POST /admin-api/platform`、`POST /admin-api/platform/secret|probe`、`GET /admin-api/workflows`、`POST /admin-api/workflows/:stage/(draft|validate|publish|rollback)`。
- 用户接口（需登录）：`GET /profile`、`POST /profile/signal|remove|settings|clear`。
- 灵感 AI 场景新增 `text_works`；旧三场景配置自动补齐。`/topics/chat` 现接受 `preference` 字段（旧线上镜像不接受，是 10-17 审核被拒的“请求无效”根因之一）。
- 持久数据（服务器 `video-data`）：`admin/platform/`（config、versions、secrets.json 权限600、workflows）、`assets/auth/user-profile.sqlite`。均无数据库迁移；回滚镜像不会删除这些文件。
- 配置优先级：中台写入的密钥 > 环境变量 > 凭据文件；中台发布的视频模型/等待上限优先于 `YOUAI_QIANWEN_MODEL/TIMEOUT`。

## 测试证据

- 各次定向测试、Python 测试与真实浏览器/开发者工具走查记录在 `docs/test-batches.md` 第123–129次。
- 已知环境限制：用户机器 Linux 环境 Python 为 3.10，`test-admin-console.py`、`test-video-server.py` 需 3.11+（tomllib）；`test-video-server.py` 在无 FFmpeg 音轨支持的沙箱有 1 项既有失败（改动前同样失败）。
- 未验证：手机真机、真实模型连接检测（中台按钮会产生少量费用）、小程序新界面在真机与审核环境的表现。

## 运行状态

- 线上 video 服务镜像 `codexyouai-video:platform-d214e58`，`127.0.0.1:8765`，经 `https://youai888.top/youai/` 反代。`/health` 200；未登录访问 `/profile`、`/admin-api/platform` 均为 401。
- 进程内任务字典（生成/分析任务）重启即丢失，这是既有行为，未改。

## 密钥与费用

- Claude 专用钥匙：`E:\data\codexYOUAI-data\claude-deploy\`（`id_ed25519`、`known_hosts`）。已加入服务器 `/root/.ssh/authorized_keys`，行尾标记 `claude-deploy`；删除该行即吊销。Codex 继续使用用户原有的 `C:\Users\one\.ssh\youai_deploy`，**不要使用或移动 claude-deploy 钥匙**。
- 用户账户已在 Claude 设置中允许所有域名（Claude 才能 SSH）。
- 付费调用：Claude 在开发者工具走查时误触发 1 个真实视频任务（job `8ae3b0ea26fc4b23b79d1082570ad4af`，720P 智能时长），原因是开发者工具以开发者本人微信静默登录、账号已绑手机。**注意：开发者工具里“确认分镜并生成”会对开发者本人账号真实计费。**

## 未完成事项

- **P0 小程序重新提交审核**：用户已在公众平台补充手机号隐私声明；建议把“相册（仅写入）”用途改为“保存生成的作品和封面到相册”（核对表见用户手中的 `有AI隐私指引核对表.xlsx`）。新版本需包含 `09f1656`、`bb006d3`、`d214e58` 的界面改动。审核备注建议见任务台账 RUN-20261017-REVIEW-FIX。
- **P1 个性化第二步**：浏览行为（记下的点子、关注热词、拆解案例）与对话内容提取（需用户确认后才写入）；考虑把画像也注入热点总结与文字作品场景。
- **P1 图片作品生成**：中台已有 `image-gen` 密钥与模型配置（`Platform.image_settings()`），尚缺服务端生成接口与小程序启用。
- **P2 原生管理页**：新增自定义连接、视频/图片参数、流程步骤编辑目前仅网页中台支持。
- **P2 六板块第3–5批**：小程序固定组件渲染、Skill 执行、Outbox/飞书表（见 `docs/workflow-platform-design.md`）。
- 清理：服务器 `/opt/youai/releases/` 下有一个名称末尾带回车的空目录（`platform-4df4161`），可删除。

## 回滚点

- 后端：把 `/opt/youai/releases/<要回到的标签>/env.previous` 复制回 `/opt/youai/internal-api/.env`，执行 `docker compose -f compose.video-cloud.yml up -d --no-build --wait video`。可回到 `platform-f521b82`、`platform-3aa5fb3` 或原始 `assets-111-final`（旧版不认识 `preference` 字段，选题对话会再次 400）。
- 代码：`2ce8489` 为 Claude 接手前；`d1e5a88` 起为配置中心；`d214e58` 为个性化记忆。

## Codex 接手须知

- 发布：Windows 上双击 `deploy-platform.cmd`（默认增量；依赖变化或 `-Full` 时整包，需 Docker Desktop）。Linux/macOS：`DEPLOY_KEY=... bash scripts/deploy-delta.sh`。服务器步骤统一在 `scripts/remote-release.sh`。
- 新增服务端 Python 模块时，同步加入 `scripts/Dockerfile.video` 的 COPY（有测试守护）；启动时读取的数据文件也要 COPY。
- 改选题对话请求字段时，同步改 `scripts/topic-chat.py` 白名单（`tests/main-tab-scroll.test.js` 守护）。
- `templates/study.wxml` 被五个案例分包共用；`<video poster>` 只能用 https（`tests/review-readiness.test.js`）。
- 与 Claude 不要同时修改同一批文件；交替工作时以 Git 提交和任务台账为准。

## 回交格式（Codex → Claude）

交回前新增 `docs/agent-return-YYYY-MM-DD-codex.md`，至少包含：

1. **回交基线**：分支、HEAD、工作区是否干净、是否已推送。
2. **完成内容**：按用户可见行为描述，并列出对应 commit。
3. **接口与数据变化**：请求/响应、数据文件、配置项与兼容策略。
4. **测试证据**：命令、通过数量、真实环境验证与未完成验证；当前累计次数与下一次应执行的范围。
5. **运行状态**：线上 `VIDEO_TAG`、是否部署、备份位置。
6. **密钥与费用**：只写位置，不写密钥；列出实际触发的付费调用。
7. **未完成事项**：按 P0/P1/P2，含复现条件与建议下一步。
8. **回滚点**。

并在 `docs/task-ledger.md` 记录对应任务。交回前运行 `git status --short`、`git log -10 --oneline`、`git diff --check`。

## 可直接发给 Codex 的提示词

> 接手 `E:\data\codexYOUAI`（分支 `codex/admin-console`）。先阅读 `docs/agent-handoff-2026-10-17-claude.md`、`AGENTS.md`、`docs/task-ledger.md` 与 `docs/test-batches.md` 末尾。当前累计第129次，下一次改动是第130次，必须执行完整 `npm test`。不要提交 `project.config.json` 的现有改动，不要使用 `claude-deploy` 钥匙。开发者工具里点击生成会对开发者本人账号真实计费，验证用 mock。每个逻辑改动更新任务台账、测试、批次记录并提交。工作结束时按交接文档“回交格式”新增 `docs/agent-return-YYYY-MM-DD-codex.md`。
