# 配置中心与六板块中台（第123次）

入口不变：网页 `https://youai888.top/youai/admin/`，小程序“我的 → 管理中台”。本轮落实[六板块设计](workflow-platform-design.md)的第1–2批：持久化流程注册/版本服务、网页与原生管理端读取同一接口，并把散落的模型与密钥配置收进中台。第3–5批（小程序固定组件渲染、Skill 执行、Outbox/飞书表）尚未实现。

## 配置盘点（实施前）

| 类别 | 原来的位置 | 现在 |
| --- | --- | --- |
| 灵感 AI（TA推荐/对话/热点总结） | `hotspot-ai.json` / `YOUAI_HOTSPOT_AI_*`；场景参数已在中台 | 不变，另可改选已注册连接 |
| 文字作品生成 | 复用千问连接，模型/超时/上限写死在 `text-works.py` | 新增 AI 场景 `text_works`（40秒、1800 Token 默认），可改连接、模型、超时、上限与补充提示词 |
| 视频生成 Wan | `~/MoneyPrinterTurbo/config.toml` 或 `YOUAI_QIANWEN_*`，等待上限 `YOUAI_QIANWEN_TIMEOUT` | 中台“创作工具”：模型、服务端默认分辨率/水印、等待上限（60–3600秒），版本化 |
| 语音转写 | `YOUAI_WHISPER_MODEL`（随镜像） | 只读状态 |
| 抖音解析服务密钥 | `credentials/reference-parser.env` | 可在中台写入新密钥（用户个人配置的 token 仍优先） |
| 微信、飞书、数据库、热点源、公网素材地址 | 环境变量与只读 credentials 挂载 | 总览“服务配置状态”只显示是否配置，不显示值或私有路径 |
| 小程序“模型与技能”页 | 演示数据，Key 存手机本地，不发起调用 | 未改动；真实模型配置以中台为准 |

## 密钥：只写不读

- `POST /admin-api/platform/secret {ref, value}` 写入，`{ref, clear:true}` 清除；值 8–512 位、无空白。保存在 `video-data/admin/platform/secrets.json`（权限 600，管理目录可写，credentials 目录保持只读）。
- 任何接口都不返回密钥，只返回“已配置 · 来源 · 末4位 · 更新时间”。审计只记录事件与连接ID。
- 优先级：中台写入 → 环境变量 → 凭据文件。清除中台密钥后自动回到服务器凭据。
- 移除自定义连接会同时删除它的中台密钥；仍被 AI 场景使用的连接不能移除。
- 平台配置回滚只恢复连接与视频参数，不恢复或回显密钥。

## 模型连接

第124次：新增内置连接“图片生成（图文作品）”（`image-gen`），密钥同样只写不读；“创作工具”板块可改接口根地址与模型，默认阿里云百炼 `https://dashscope.aliyuncs.com/api/v1` + `wan2.6-t2i`。也可用环境变量 `YOUAI_IMAGE_API_KEY/BASE_URL/MODEL`。小程序“图片”作品的实际生成接口尚未接入，当前只保存配置。

内置：国内千问（文本）、千问 Wan（视频）、抖音参考解析服务。自定义：最多 8 个兼容 OpenAI Chat Completions 的连接（DeepSeek、豆包、Kimi、智谱等），只接受公网 HTTPS 地址，拒绝 IP、本机与内网主机名。发布后在 AI 场景里选择该连接；“检测连接”发起一次 32 Token 的真实调用，可能产生费用，需确认。

## 六板块与流程

网页导航：总览 / 热点推荐 / 创作工具 / 数据积累 / 确认需求 / 作品拆解 / 作品产出 / 模型与密钥 / 版本 / 审计。

三阶段流程默认定义与 `web/admin-workflows/model.js` 一致。管理员可改名、调整顺序、移除或恢复可选步骤 → 保存草案 → 查看差异与校验 → 发布；必需确认点、能力白名单、最多 12 步、“确认分镜与费用 → 生成 → 验收 → 归档”的顺序由服务端校验，不合规草案可保存但不能发布。步骤只允许 `id/title/capability/required` 四个字段，不能携带代码或地址。回滚（含“系统默认 default-v1”）新建发布版本。所有写入使用 expectedRevision，冲突返回 409。

原生管理页可写入密钥、检测连接、为 AI 场景切换连接、审核发布/放弃流程草案、恢复默认流程；新增自定义连接、视频参数与流程步骤编辑在网页完成。原生页面变更需随小程序版本审核。

## 接口

| 接口 | 说明 |
| --- | --- |
| `GET/POST /admin-api/platform` | 连接、视频参数、服务状态、版本；发布或 `{rollback}` |
| `POST /admin-api/platform/secret` | 只写密钥 |
| `POST /admin-api/platform/probe` | 检测文本连接 |
| `GET /admin-api/workflows` | 六板块目录与三阶段流程（发布版、草案、差异、错误、版本） |
| `POST /admin-api/workflows/:stage/(draft|validate|publish|rollback)` | 草案、校验、发布、回滚 |

## 部署

在本机仓库根目录运行（需 Docker Desktop 与 `C:\Users\one\.ssh\youai_deploy`）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy-platform.ps1 -DryRun   # 先看将执行的步骤
powershell -ExecutionPolicy Bypass -File scripts\deploy-platform.ps1
```

脚本先跑后端测试，构建 `codexyouai-video:platform-<提交>`，检查镜像包含服务端加载的全部模块，SCP 传输并 `docker load`；备份 `.env`、compose 与 `video-data/admin` 到 `/opt/youai/releases/<标签>/`；切换 VIDEO_TAG 只重启 video 服务，健康检查与“未登录访问管理接口返回401”任一失败即自动恢复旧版本。`Dockerfile.video` 已补齐此前未列出的 `inspiration-ai`、`text-works`、`topic-chat`、`hotspot-summary`、`hotspot-watch`、`content-boundaries` 模块。

首次部署后，中台的视频模型与等待上限以首次读取时的服务器配置为初值；一旦在中台发布，中台值优先于 `YOUAI_QIANWEN_MODEL/TIMEOUT`。

### 只传改动（第125次）

默认增量发布：上传 `git archive` 的 `scripts/` 与 `utils/platform-boundaries.json`（约300KB），在服务器上以当前线上镜像为基础叠加代码层构建新镜像，本机无需 Docker。线上镜像不是 `platform-<提交>`、该提交不在本仓库，或 `Dockerfile.video` 的 FROM/RUN 行有变化时自动改为整包上传；`-Full` 可强制整包。服务器端步骤统一由 `scripts/remote-release.sh`（live / build-delta / switch）执行；Linux/macOS 可用 `scripts/deploy-delta.sh`。

## 验收与限制

本机：Python 后端测试（新增 `test-platform-config.py` 8 项，灵感AI、文字作品、话题、热点总结、管理端全部通过）；Node 定向测试；本地真实浏览器走查 9 个板块、写入密钥、新增 DeepSeek 连接、流程草案发布与非法顺序拦截、390 宽度无横向溢出。云端部署、真实模型检测与手机原生页面验收需在执行部署脚本后记录。
