# Claude 工作说明

本项目的全部协作规则以 `AGENTS.md` 为准，Claude 与 Codex 遵循同一套规则，不另立标准：

- 开始工作前先阅读 `AGENTS.md`，并在 `docs/task-ledger.md` 登记任务。
- 每次改动后创建对应 Git commit，编写或更新相关测试，并在 `docs/test-batches.md` 记录；按 `AGENTS.md` 的五次范围测试、十次完整测试规则执行。
- 跨 Agent 接手或回交按最新 `docs/agent-handoff-*-claude.md` 末尾的“回交格式”；避免与 Codex 同时修改同一批文件。项目全貌见 `docs/PROJECT-MAP.md`。

如本文件与 `AGENTS.md` 有冲突，以 `AGENTS.md` 为准。

## 新对话启动清单（Claude 接手时先做）

1. 请用户授权两个文件夹：`E:\data\codexYOUAI`（项目）与 `E:\data\codexYOUAI-data\claude-deploy`（Claude 专用部署钥匙，仅此子目录，不要请求整个 codexYOUAI-data）。
2. 读本文件、`AGENTS.md`、`docs/PROJECT-MAP.md`、`docs/test-batches.md` 末尾（累计次数与下一次测试档位）；再读 `docs/agent-handoff-*-claude.md` 与 `docs/agent-return-*-codex.md` 中日期最新的一份，了解上一轮改动、部署状态、费用与待办。
3. Git：用户机器无 Git 身份配置，提交沿用上一条提交的作者（`-c user.name=… -c user.email=…`）；命令加 `-c core.autocrlf=true`（工作区有 CRLF，否则整文件显示改动）。开工先用 `device_request_delete_permission` 请求项目文件夹删除权限，否则 Git 会遗留 `.lock` 文件；没有权限时把锁 `mv` 成 `.git/stale-*`。
4. 测试：Node 测试可在用户机器的 Linux 环境直接跑，但单次调用最长 180 秒且后台进程会被结束，完整测试分 6 组跑（见 `docs/PROJECT-MAP.md` 第 5 节）。该环境 Python 为 3.10 且无 PyPI 网络，凡导入 `video-server.py`/`admin-console.py`（依赖 `tomllib`）的测试需在服务器容器运行。
5. 微信开发者工具：可用计算机控制查看模拟器与控制台；批量写文件后若模拟器空白，先点工具栏“编译”重编译再判断。
6. 当前主线是创作板块：先读 `docs/creation-board-plan.md` 第 0、1、11 节（已定决策与 M1–M13 进度表），按进度表继续，不要重新讨论已定决策。
7. 提交前检查行尾：仓库内文件以 LF 存储，工作区为 CRLF；用 `git diff --cached --numstat` 确认没有整文件改动（第141–143次曾误提交 CRLF，见 07036ac）。

## 部署（Claude 可自行执行）

- 线上：广州 `182.61.14.185`，目录 `/opt/youai/internal-api`，`.env` 中 `VIDEO_TAG` 为当前版本，备份在 `/opt/youai/releases/<tag>/`。
- 钥匙：把 `claude-deploy/id_ed25519` 复制到 Linux 环境 `~/.cd/key`（chmod 600），`known_hosts` 同步复制；保持 `StrictHostKeyChecking=yes`。
- 增量发布：`DEPLOY_KEY=~/.cd/key DEPLOY_KNOWN_HOSTS=~/.cd/known_hosts bash scripts/deploy-delta.sh [--dry-run]`。只传 `scripts/` 与 `utils/platform-boundaries.json`，服务器上叠加构建；健康检查失败自动回滚。
- `Dockerfile.video` 的 FROM/RUN 有变化时不能增量：请用户双击 `deploy-platform.cmd`（需本机 Docker Desktop 运行）。
- 部署前先告知用户要发布的内容并取得同意；服务器偶尔断开短时间内的连续 SSH 连接，等待约20秒重试。
- 设备 shell 的网络受账号设置限制：SSH 报 `Network is unreachable` 时不要反复重试，请用户双击 `deploy-platform.cmd`（默认增量）或放开网络后再发布。
- 吊销 Claude 权限：删除服务器 `/root/.ssh/authorized_keys` 中以 `claude-deploy` 结尾的行。

## 需要用户本人完成

- 管理中台登录（`https://youai888.top/youai/admin/`）与输入任何密码、密钥。
- 微信公众平台操作：隐私保护指引、合法域名、提交审核与发布；小程序原生页面改动需随版本审核才生效。
- 手机真机测试。
