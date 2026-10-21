# 基线恢复说明

基线业务提交026fb30，最终源码提交以manifest.json为准。对外源码为source.zip；Git历史和生产材料位于private目录，包含数据库、用户资产、身份和凭据，不对外分享。

1. 阅读manifest.json/verification.json，对照SHA256确认文件完整。source.zip每个文件均与冻结Git提交比对；解压后导入微信开发者工具，不包含node_modules。
2. 恢复Git：`git clone <private/project.bundle> <新目录>`，再checkout清单中的commit。使用新目录，不覆盖正在迭代的工作区。安装锁文件声明的依赖，再执行相关测试。
3. 恢复云端：先准备与runtime.txt一致的大版本PostgreSQL/TimescaleDB和外部Docker网络；private/cloud-private.tar.gz包含video-data、models、credentials、tls、Compose与采集源码/配置。提取到隔离目录，按tar路径分别放入internal-api、reference-parser、hotspots；不要直接解压覆盖生产。
4. YOUAI数据库：在新空库以pg_restore恢复youai.dump。解析器库使用对应TimescaleDB版本，先CREATE EXTENSION并调用timescaledb_pre_restore，再恢复parser.dump，完成后timescaledb_post_restore。实际备份已在同版本临时库恢复通过；globals.sql用于检查角色，不能直接覆盖其他项目角色。
5. ny-proxy.tar.gz保存YOUAI nginx片段，youai-video-tunnel.service保存广州隧道单元。纽约现有主站、证书与SSH授权需另外保留并按源部署说明接入，本包不是纽约整机备份。
6. 新建视频/API镜像时使用源码Dockerfile与对应依赖版本；DTK原始源码包和DailyHotApi源码包位于third-party。Docker镜像、Node/Python运行时、node_modules、Redis运行中队列未打包，恢复需要下载依赖或使用现有镜像。不是完全离线整机恢复包。
7. 恢复后验证两个health、数据库迁移状态、管理员/微信会话隔离、免费生成、媒体下载、解析、热点内容与归档。检查凭据挂载和文件权限，未完成验证前不得切换正式域名。

数据库分别为事务一致导出，媒体为在线文件备份，未停止线上服务；不同数据库与文件之间不声明同一时刻的全局事务快照。中台新迭代使用独立分支，以本包回滚当前业务；不会以改后台配置替代新客户端能力的发布。
