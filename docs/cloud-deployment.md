# 百度云部署准备

## 当前入口（2026-10-15，第82次）

国内中台、业务入口、媒体地址与网站已部署，详见 [国内部署与后续迭代](domestic-deployment.md)。小程序代码已切换国内地址；微信合法域名校验报 url not in domain list，配置与真机复验待完成。以下章节为分阶段历史记录，以本段及国内部署文档为准。

## 2026-10-15 国内域名 HTTPS 实际部署（第81次）

`youai888.top` 实际 A 解析为 `182.61.14.185`。Ubuntu Nginx 已安装并配置开机启动，配置源为 `deploy/youai888.nginx.conf`，服务器安装到 `/etc/nginx/sites-available/youai888` 并链接到 sites-enabled。80 重定向到 HTTPS；根路径仅提供入口就绪文本，`/youai/` 去掉前缀转发现有回环视频服务 8765，保留 Authorization 和原有鉴权。数据库和内部 8080 未开放。此步骤不代表产品首页上线或小程序域名切换完成。

用户提供的 TrustAsia 证书包仅存仓库外；服务器 `/opt/youai/tls-youai888/` 受限保存原包、fullchain.pem、privkey.pem，私钥权限600。证书和私钥公钥摘要一致，SAN 覆盖 youai888.top、www.youai888.top，有效期 UTC 2026-10-15 07:00 至 2027-01-13 06:59:59（北京时间到期为2027-01-13 14:59:59）。当前手动证书部署，没有自动续期，需要到期前续签并替换文件，执行 nginx -t 后 reload。

公网不跳过证书校验：HTTP 301、HTTPS 根路径200、/youai/health 200，匿名 POST /youai/references/acquire 401。nginx -t 通过。www 当前 NXDOMAIN；如需使用，DNS 增加 www A 到182.61.14.185。证书未覆盖 api.youai888.top，不能直接将此证书用于该子域名。

小程序地址、媒体签名地址和管理员 Origin 仍为现有 api.onesvips.top；本次没有切换这些配置或完成新域名真机验收。回滚本次入口可删除 `/etc/nginx/sites-enabled/youai888` 链接，nginx -t 后 reload；原 Nginx 配置备份位于 `/opt/youai/backups/https-20261015/nginx-before`，内部容器无需调整。后续变更前须先核对在线配置，避免覆盖新的修改。

当前完成本机视频服务、真实飞书归档和广州服务器内部 PostgreSQL/API。视频 Worker、公网 HTTPS 和正式手机尚未接通。服务器为广州 Ubuntu 24.04、2 核 4 GB、6 Mbps。

## 2026-10-12 服务器实际进展

用户在 SmartTerm 添加本机部署公钥后，SSH 主机密钥严格校验登录成功。root 只读盘点：根盘 79 GB、可用 70 GB，可用内存约 2.8 GB；80/443 无监听，428/781 等已有监听保留。尚未识别这些已有服务用途，不修改它们。

通过服务器已配置的 Ubuntu 百度镜像源安装 `docker.io` 与 `docker-compose-v2`：Docker 29.1.3、Compose 2.40.3，服务 active。ECR 公共镜像拉取因 TLS 握手超时失败；改为本机 `python:3.12.8-slim-bookworm` 镜像通过 SCP 传输并 docker load。隔离网络容器实际运行成功，受控重启 Docker 后再次运行成功。镜像 tar 保留在仓库外和服务器 root 目录。

这些证据只确认基础容器环境可用，后台 API、数据库、解析器和视频 Worker 尚未在服务器部署。域名 `onesvips.xx.kg` 当前 DNS 返回 Cloudflare 代理地址，无法据此确认源站；用户表示备案状态不确定。公网开放前继续核验域名和生产用户鉴权。

## 内部后台部署验收

后续已部署在 `/opt/youai/internal-api`：`compose.cloud.yml`，API 镜像 `codexyouai-api:941905d`，PostgreSQL 16。数据库无公网端口；API 仅绑定 `127.0.0.1:8080`。凭据由 `scripts/bootstrap-cloud.sh` 在服务器首次生成：随机 32 字节密码、独立 CA、postgres SAN 证书，`.env` 和私钥受限。已有凭据脚本拒绝覆盖；不要运行带 `-v` 的 down 删除数据库卷。

生产 `DATABASE_SSL_MODE=verify-full`，CA 通过 Compose 传入，数据库运行连接实测 TLS。三项迁移 001/002/003 全部 applied；`/health/live` 与 `/health/ready` 通过。两容器受控重启、健康等待后，双端点再次通过，迁移状态保留。数据库初始备份 `backups/initial-20261012.dump` 已生成，`pg_restore --list` 可读；未做覆盖性恢复，不宣称恢复演练通过。

运维命令在该目录执行：`docker compose -f compose.cloud.yml ps`、`docker compose -f compose.cloud.yml up -d --wait --pull never`。首次迁移：`docker compose -f compose.cloud.yml run --rm --no-deps api node backend/migrate.js up`；状态使用 `status`。数据库卷随服务停止保留。未来升级前备份数据、保存旧 API_TAG 和镜像，回滚仅切换 API_TAG 后重建 API；数据库回滚须审查迁移兼容性，不自动 down 迁移。

内部 API 使用现有开发账号传参契约，尚未提供生产微信登录鉴权，因此维持本机监听。小程序后台截图实际 request 域名为 `api.onesvips.top`，当前 DNS 指向 `198.23.196.191`，与广州实例不同；上传下载白名单为空，旧域名解析保留。

## 内部视频 Worker 验收（第 59 次）

`compose.video-cloud.yml` 已部署在同一目录，镜像 `codexyouai-video:f24044f`，`127.0.0.1:8765` 仅内部访问。Python/Pillow/FFmpeg、Noto 中文字体、render/assets/tools 持久目录和飞书只读凭据挂载已配置。服务监听与 render 根路径可通过环境变量设置，默认本机行为保留。云端已完成合成样片生成、原片/代表帧分析、飞书归档和 9 文件恢复，样片 ID `0b12a0991c70442e8aebec4e3836cfd0`；重启后健康及 archived/verified 状态保留，付费调用为零。

首次验收脚本与后台队列并行处理同一样片，发现重复稳定 ID；添加创建记录的确定性 client_token 并用停服务、独立验收容器、恢复服务的方法重新验证。失败样片 `c12eb838c9cb46b684651d1801cb2c82` 记录保留待核对，不删除任何表记录。未来维护运行验收脚本前应停止自动 Worker；真实工作只用队列统一调度。

当前镜像尚未安装语音转写模型，未配置付费模型密钥和抖音解析器，纯文字及抽帧归档通过不能代替 AI 生成/语音/真实抖音验证。生产用户隔离和公网接口仍待接入，客户端地址尚未切换。

用户决定先沿用境外 `api.onesvips.top`：RackNerd 1 GB VPS `198.23.196.191` 用于 HTTPS 入口，广州承担重处理。NameSilo 域名管理入口已确认；旧服务器 Console/SSH 授权待用户完成，未更改 DNS 或现有境外服务。面板用户名不是已确认的 Linux SSH 用户名。手机可用性待完成入口鉴权、两服务器受保护连接、模型/解析配置、微信上传下载域名及正式手机实测。

## 第一步：只读盘点

用户提供 SSH 用户名及本机密钥路径后，用 SSH 将 `scripts/cloud-preflight.sh` 作为标准输入执行 `sh -s`。首次连接先核对百度云控制台所示 SSH 主机指纹，保留主机密钥校验。无需上传密钥到服务器或发送密码到聊天。

工具只输出系统、CPU、内存、磁盘、监听端口、Docker 与容器摘要，不打印环境变量、容器配置或密钥，不安装软件、重启服务或删除文件。输出用于确定端口冲突、可用容量和安装需求。禁止将现有本机 `compose.backend.yml` 的开发数据库密码直接用于生产。

## 后续部署顺序

1. 盘点现有服务和备份，建立 `/opt/youai` 版本目录与独立持久数据目录，保存上一版本回滚指针。
2. 配置生产数据库随机密码、微信登录鉴权与用户资产隔离；媒体恢复和反馈接口也必须检查用户权限。
3. 将视频服务改为可配置监听地址，配置 Linux 字体、FFmpeg、转写依赖和解析器；串行重任务，并验证容器重启后资产及队列保留。
4. 在服务器外提供备案域名、DNS、HTTPS；通过反向代理暴露受保护 API，数据库和内部服务不直接开放公网。
5. 将仓库外飞书凭据与六表映射放入服务器受限文件，仅挂载到视频服务；首次使用合成样片验证归档恢复。
6. 配置微信 request、uploadFile、downloadFile 合法域名，更新客户端生产地址；手机移动网络实测分析、生成、播放、保存和两个账户隔离。

当前缺口：SSH 登录方式、备案域名、服务器磁盘/已有服务、生产鉴权、视频服务 Linux 容器及对象存储。Docker 安装在这台云服务器内，不需要另外购买 Docker 服务。飞书用于归档；模型取材和手机播放仍需要可访问的 HTTPS 媒体地址。

验收必须包括容器健康、数据库迁移、受控重启、正式手机及恢复实测。准备文件或本地测试成功不能标记云端已上线。
