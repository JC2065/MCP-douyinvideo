# YOUAI 手机参考视频解析：案例复盘与部署交接方案

## 最新续作结果（2026-10-13，优先于下文历史快照）

用户要求原 agent 继续后，以下工作已经实际完成：

- 浏览器镜像导入，DTK 五组件及业务三组件均 healthy；两个 Compose 修正已同步，视频使用 `dtk-api-1:8000`，Redis 上限 512MB。
- 浏览器 `/rpc/health` 为 `status=ok`、backend cloak；受限 tmpfs 配置实际生效。已通过管理端队列创建一个新抖音身份，任务 `dd09aff5-c82e-4ab8-8b07-54980d9c237d` 为 done，可用抖音身份从 8 增至 9，`can_mint=true`、`auto=true`。此为手动触发维护任务验证，不等同于长期自动恢复观测。
- 第二条真实短链 `JPVrvc_frWo` 获得作品 `7691159511617134777`，3,357,579 字节，H.264 576×1024、14.57 秒、有音轨。未专门清除缓存，不宣称此请求必然未命中缓存。
- DTK 五组件及视频容器受控重启后均 healthy，新身份保留；公网临时鉴权会话再次取得原截图视频，大小、SHA 和归属一致。
- 新旧公网 health 均 200，未鉴权解析请求为 401。运行约 24 分钟后服务器可用内存约 960MB，Swap 使用约 181MB；现有资源仅适合低并发，不将一次验证描述为长期容量保证。
- 手机复测提示已经发出，但尚未获得用户结果。**服务器侧修复完成；E27 和第 65 次必要验收仅保留手机确认待办。** 本轮无新增付费视频调用。

下文“尚未部署/同步/重启”均为交接时历史快照，不应重复执行。后续首先取得手机原链接的解析/内容分析结果；若有新报错按阶段定位。

交接时间：2026-10-13，Asia/Shanghai。服务器状态实查时间：19:07。本文为本次云端解析故障的接手入口；旧的 2026-10-11 交接文档仅作历史参考。

## 1. 给接手 agent 的任务

在现有部署上继续完成广州云端抖音解析闭环，完成自动身份维护、重启验证和用户手机复测。**不要重新部署整个项目，也不要再次要求用户提供已配置的密钥。**

当前结论：截图中的“尚未配置素材解析服务”已在服务端修复；同一真实短链通过了广州下载和公网鉴权接口。自动维护身份的浏览器组件尚未部署，修复后的用户手机界面尚未复测。任务 E27 保持 active，第 65 次必要集成验证待完成。

用户最新要求是整理交接方案并把工作交给另一个 agent。本轮不自动创建新会话或向其他 agent 发送消息；请由用户把本文交给接手方。

## 2. 案例背景与根因

用户已完成手机纯文字视频生成、播放、保存到相册，随后要求验证千问付费视频及抖音真实链接。此前抖音验证发生在 Windows 本地解析服务，手机实际使用纽约 HTTPS 入口转发到广州视频服务。广州容器未设置解析服务 URL/key，因此手机仍报错。

这次截图的链接为 `https://v.douyin.com/pLJqnGLWy2g/`，平台作品为 `7693845706146340337`。不能用“本机 DTK 解析成功”代替“手机云端请求成功”。

修复路径：迁移本机 DTK 的已验证镜像、数据库和解析身份到广州，在独立 Docker 网络接入视频服务。解析凭据保留在服务器受限文件中，不下发小程序。

## 3. 实际架构与资产位置

| 组件 | 位置与职责 | 当前状态 |
| --- | --- | --- |
| 小程序 | `E:\data\codexYOUAI`；手机请求 `https://api.onesvips.top/youai` | 已有微信登录、归属门禁及签名下载 |
| 纽约 RackNerd | `198.23.196.191`；HTTPS 入口、已有旧业务 | 保留根路由，通过受限 SSH 通路转发 `/youai` |
| 广州百度云 | `182.61.14.185`；业务 API、Postgres、视频 Worker | 7 个容器健康，约 2.25GB 可用内存 |
| 云端视频 | `/opt/youai/internal-api`，Compose `compose.video-cloud.yml` | `youai-video-video-1`，镜像 `codexyouai-video:parser-65` |
| 云端解析 | `/opt/youai/reference-parser` | DTK API、Worker、Redis、TimescaleDB 健康；浏览器缺席 |
| 本机 DTK | `E:\data\codexYOUAI-services\Douyin_TikTok_Download_API-5.1.3` | 五容器曾受控恢复 healthy，后续自行复查 |
| 迁移包/证据 | `E:\data\codexYOUAI-data\cloud-parser` | 仓库外，包含敏感数据库/配置，不可上传 Git |
| 长期资产 | 飞书“YOUAI 管理台/资产”及专用云盘目录 | 本轮未重新修改；既有归档配置继续使用 |

广州 SSH 使用本机 `C:\Users\one\.ssh\youai_deploy`，用户名 root，必须保持 `BatchMode=yes`、`StrictHostKeyChecking=yes`。私钥留在本机。备案后的国内域名规划为 `api.youai888.top`，本次不要更改 DNS 或切换域名。

广州 4GB 规格实际系统内存 3387MB，已新增 `/swapfile` 4GB、权限 600、写入 `/etc/fstab`，当前 Swap 用量为 0。此变更已实际执行。

## 4. 已完成与证据

### 本次直接核验

- 云端解析四组件 `/readyz` 为 ok，Postgres/Redis 正常；视频 `/health` 为 ok。
- 广州视频容器真实获取截图短链，状态 `acquired`。文件 1,725,435 字节，H.264，576×1024，6.76 秒，有音轨。
- SHA-256：`feaafc9376ea98d150be4e7bdb59345cf95184a38fe5f84abc02820396bc06d9`。
- 文件在视频容器 `/data/render/references/<sha256>.mp4`，对应服务器持久目录 `/opt/youai/internal-api/video-data/render/references/`。
- 公网 `POST https://api.onesvips.top/youai/references/acquire` 已取得相同媒体，并验证资源归属。该验证使用临时部署测试会话，随后已撤销并清理归属记录，**不是新的真实 wx.login 或手机 UI 验收**。
- 验证脚本：仓库外 `E:\data\codexYOUAI-data\cloud-parser\verify-public-parser.py`，服务器同名文件在解析目录；脚本需要在视频容器执行，不打印 token。
- 交接收尾最近五次合并范围 Node 测试 **74/74**；视频 Python 25/25、微信认证 4/4、归档 5/5；`git diff --check` 通过。结果已记入 `docs/test-batches.md`，必要集成仍待接手方完成。

### 前序会话结果，本次未重新调用

- 用户已确认纯文字成片可以保存到手机本地。
- 千问真实付费任务 `1917de1c-a7a2-4653-8979-5ca127fd3cea` 成功；wan3.0-video、480P、2 秒、9:16，689,018 字节，H.264 480×854、2 秒。请求关闭声音但结果有音轨，仍需区分静音音轨与实际有声，不得报告静音选项完全通过。
- 此处不再创建付费任务。真实付费调用只在功能需要且已获用户授权时执行；本次解析修复无需追加模型消费。

## 5. 当前代码、服务器差异与未完成项

工作起点 HEAD 为 `e62d7e6`。本次变更在交接提交中保存；提交时仍保留 E27 active，不将阶段保存称为部署验收完成。

| 文件 | 变更 | 部署情况 |
| --- | --- | --- |
| `scripts/video-server.py` | 新增服务端 HTTP 主机精确允许名单，默认仍要求 HTTPS/回环地址 | 已包含在 `parser-65` 镜像 |
| `scripts/test-video-server.py` | 容器 HTTP 接入及拒绝其他主机/含账号密码 URL 的测试 | 本地通过 |
| `compose.video-cloud.yml` | 独立 parser 网络和可选凭据文件 | 初版已部署；最新版主机名修正未同步 |
| `deploy/reference-parser-cloud.override.yml` | 资源上限与浏览器镜像版本固定 | 初版已上传；最新版修正未同步 |
| `tests/cloud-deployment.test.js` | 实际 Compose 解析验证新网络及配置 | 本地通过 |
| 台账、测试批次与本文 | 记录证据、差异、剩余验收 | 交接提交保存 |

**接手时必须处理的差异：**

1. 服务器视频 Compose 仍为 `YOUAI_REFERENCE_PARSER_URL=http://api:8000`、允许名单 `api`。本地已改为 `http://dtk-api-1:8000` 和 `dtk-api-1`，避免两个 Docker 网络都存在 `api` 别名导致解析歧义。需同步本地文件并重建视频容器，镜像无需重建。
2. 服务器解析 override 初版将 Redis 内存上限设为 256MB，但原命令 maxmemory 为 320MB；本地已改回 512MB 并删除无效的环境覆盖。需同步。
3. 服务器尚无 browser-rpc 容器。交接收尾时 `browser.tar` 已完成上传，SCP 退出码 0，两端均为 **457,905,664 字节**，SHA-256 均为 `11c1d5c9e17bf7b39a640dfb9396c9bcb6e54888d08b128f9649f79af326f1de`。尚未导入镜像或启动浏览器，可直接从导入步骤接手。
4. 本地 override 已固定浏览器镜像 `dtk-browser-rpc:5.1.3`；API 仍为 `dtk-app:dev`。不要全局设 `DTK_IMAGE_TAG=5.1.3` 导致服务器 API 找不到镜像。
5. 浏览器上限为 2200MB，内存+Swap 上限 3GB，2 CPU；这是拟部署保护值，**尚未经过云端浏览器负载验证**。Swap 不是算力扩容。
6. 迁移身份在云端至少一次可用；这可能命中解析缓存，不能据此证明新身份创建、签名及过期恢复能力。

## 6. 接手执行顺序

### A. 先快照现状，不重复迁移

查看 Git 状态、本文、`AGENTS.md`、`docs/task-ledger.md` E27、`docs/test-batches.md` 第 65 次记录。读取密钥时只用于请求，禁止打印整个 `.env` 或容器环境。

通过严格 SSH 盘点 `docker ps`、两个健康端点、Swap 和 `browser.tar` 文件大小；检查旧公网根路由和 `/youai/health`。此前数据库已恢复完成，不再删除或重建 `dtk_postgres-data`。

### B. 收尾镜像上传并校验

原 SCP 会话 ID 为 46629，交接前已正常退出，无需重新上传。大小及哈希见上一节。接手后核对文件仍在，再执行 `docker load -i /opt/youai/reference-parser/browser.tar`。

如上传已中断，保留源文件并重新传输同名包；传完验证哈希，不凭会话存活推断成功。

### C. 同步修正、启动浏览器并验证

先备份服务器当前两个 YAML，再同步本地 `compose.video-cloud.yml` 至 `/opt/youai/internal-api/`，本地 `deploy/reference-parser-cloud.override.yml` 至 `/opt/youai/reference-parser/cloud.override.yml`。

在服务器执行（**未完成步骤，不是已执行记录**）：

```sh
cd /opt/youai/reference-parser
docker compose -p dtk -f docker/compose.yml -f cloud.override.yml --profile browser config -q
docker compose -p dtk -f docker/compose.yml -f cloud.override.yml --profile browser up -d --no-build --wait
cd /opt/youai/internal-api
VIDEO_TAG=parser-65 docker compose -f compose.video-cloud.yml config -q
VIDEO_TAG=parser-65 docker compose -f compose.video-cloud.yml up -d --no-build --wait
```

`--wait` 可耗时，不要一次阻塞超过可汇报窗口。确认浏览器 `/rpc/health` JSON 中 `status=ok`；HTTP 200 本身不代表浏览器 backend 可用。检查 `docker stats`、OOMKilled、重启次数及现有 API/视频延迟。

读取 DTK 自带文档和现有配置，核验 RPC 配置、自动维护任务及可用身份；用一个未缓存的公开抖音链接检验真实平台请求。必要时做受控身份刷新，不要删除有效身份或反复创建付费任务。

### D. 重启、公网及手机验收

1. 解析与视频容器受控重启后，所有组件恢复 healthy、身份数据保留，原短链依旧取得完整媒体。
2. 通过公网受保护接口再次验证返回 `acquired`、媒体探测成功和用户归属，未鉴权请求仍为 401。
3. 请用户在原小程序重新粘贴同一短链，确认错误消失、下载校验成功并进入内容分析。服务器验证不能代替用户手机确认。
4. 内容分析/AI 成片若出现新错误，独立定位，不把解析成功扩大为全功能通过。
5. 完成 E27 记录、测试证据与 commit；未完成的项目明确保留待验证。

## 7. 测试与提交规则

这是累计第 65 次逻辑改动，正好为五次范围检查；继续同一故障的修复、重试、交接补充提交不新增计数。完成范围为 61–65，下一次完整周期检查为累计 70。必要集成验证未完成时第 65 次保留待验证状态。

```powershell
node --test tests/cloud-tunnel.test.js tests/cloud-deployment.test.js tests/cloud-preflight.test.js tests/backend-runtime.test.js tests/task-ledger.test.js tests/test-policy.test.js tests/video-generation.test.js tests/asset-lifecycle.test.js tests/video-session.test.js tests/video-history.test.js tests/creation-tools.test.js tests/tool-interfaces.test.js tests/upload-quality.test.js tests/agent-handoff.test.js
& 'C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe' scripts/test-video-server.py
& 'C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe' scripts/test-wechat-auth.py
& 'C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe' scripts/test-asset-archive.py
git diff --check
```

正常代码改动后执行上述应有范围。纯环境验证不伪造新增改动；没有新增风险不重复跑相同测试。所有文件改动需更新批次并 Git commit，不把用户未完成工作覆盖掉。

## 8. 密钥、数据恢复和踩坑

- 密钥不得写入仓库、报告或聊天。服务器 DTK `.env`、`reference-parser.env`、数据库快照都敏感；本文只提供路径。
- 视频凭据：`/opt/youai/internal-api/credentials/reference-parser.env`；DTK 凭据：`/opt/youai/reference-parser/.env`。本机准备源文件在仓库外迁移目录。
- 初次逻辑 `pg_restore` 出现 TimescaleDB 超表分片错误；后来在停止本机 DB 的窗口制作了物理一致性卷快照 `postgres-volume.tgz`，恢复到全新云端 DTK 卷后成功。业务数据库未被删除或覆盖。
- 该云端 DTK 卷曾使用 `docker volume create` 创建，Compose 提示已有卷不是它创建的；这是已知提示，不能为消除提示直接删卷。
- 本机恢复时曾因全局镜像标签导致找不到镜像，后来给 `dtk-app:dev` 增加 `dtk-app:5.1.3` 标签恢复五容器健康。云端用显式浏览器镜像覆盖，避免同样问题。
- 普通 PowerShell 文本管道不应用来保存二进制 pg_dump；已有可用快照，不需要重复备份迁移。
- 原镜像 `codexyouai-video:protected-63` 仍可用于回滚，但回滚到它会重新失去本次云端解析接入。回滚前保留当前配置备份；不要停旧纽约业务。

## 9. 汇报方式与交付定义

用户反复要求进度透明：最长每 3 分钟汇报一次“已完成、正在执行、卡点、下一步”，不要长时间静默。已发现阻塞要给出真实证据；无输出并不代表任务健康。

完成标准是“云端能持续解析、重启恢复通过、公网鉴权和媒体校验通过、用户手机确认”，不是“容器启动”或“单次缓存命中”。最终回交需要：Git commit、通过测试、真实链接证据、容器/资源状态、手机结论和剩余限制。

## 10. 可直接粘贴给新 agent 的接手指令

> 请接手 `E:\data\codexYOUAI` 的 RUN-20261013-E27。先阅读 `docs/agent-handoff-2026-10-13-cloud-parser.md`、`AGENTS.md`、台账和第 65 次测试记录。广州云端已能解析并下载截图链接，但浏览器身份维护组件、配置修正同步、重启和手机复测未完成。按照本文执行顺序继续，不重新迁移已恢复数据库，不打印凭据，不追加付费模型调用；每 3 分钟汇报四项状态，测试、台账和 Git commit 随任务收尾。用户已授权此部署，无需重复询问常规操作许可。
