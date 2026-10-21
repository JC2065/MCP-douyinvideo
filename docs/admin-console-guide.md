# 中台操作与发布

网页入口：https://api.onesvips.top/youai/admin/ 。新版小程序入口：我的 → 管理中台。两端使用同一云端数据与管理权限；手机原生入口无需web-view业务域名。

2026-10-17（第123次）：新增配置中心与六板块导航，模型连接、只写密钥、视频参数、文字作品模型和三阶段流程见[配置中心与六板块中台](platform-config-center.md)；部署使用 `scripts/deploy-platform.ps1`。

## 首次登录

本机私有凭据：`E:/data/codexYOUAI-data/credentials/admin-console/admin-login.txt`。此目录仅当前用户和SYSTEM可访问，不随源码包分享。云端只有密码哈希，微信登录不能进入管理接口。管理会话1小时失效；网页刷新、小程序退出页面后需重新登录。服务器重启撤销所有管理会话。

## 可管理内容

- 总览：四个平台更新情况、当前进程生成与内容分析任务。详细失败日志未暴露给客户端，历史任务和同步工具任务暂未接入。
- 工具：勾选暂停，取消恢复；先查看差异，再确认发布。服务端立即拒绝已暂停工具的新请求；客户端配置缓存最长1小时，提示可能稍后更新。
- 热点：选择话题查看pending/ready/empty/error/expired状态与来源摘录；可刷新或重试。保留2并发与缓存，重试不能保证公开索引覆盖每个话题。
- 版本：最近50个配置版本，恢复所选版本会创建新版本。发布冲突时刷新，重新核对差异；不要强制覆盖他人更新。
- 审计：最近100条登录、退出、发布、回滚与话题重试记录，不包含密码、会话令牌或模型密钥。

## 小程序与中台迭代边界

本次新增管理页面需正常更新小程序并提交审核。之后已有工具维护状态、热点检索数据和配置回滚在云端调整；新增页面、客户端交互或超出既有功能范围的能力仍需客户端发布。首版没有AI参数、提示词编辑和归档补偿，不能把所有后续迭代都视为无需审核。

## 服务部署与恢复

广州：`/opt/youai/internal-api`，专用配置目录`video-data/admin`；凭据目录继续只读挂载。纽约仅承接现有HTTPS入口并转发，后台没有直接开放额外公网端口。当前镜像`codexyouai-video:analysis-78`，包含拆解模板校验；管理员登录支持8–256位密码，云端只保存哈希。

代码回退：保留原镜像`codexyouai-video:content-74`；部署前compose和.env保存于`/opt/youai/releases/admin-75/compose.previous.yml`与`env.previous`。恢复这两个文件后在internal-api运行`docker compose -f compose.video-cloud.yml up -d video`，检查health与client-config。原版本恢复旧credentials配置位置；本轮配置历史保留在video-data/admin。回退前保存该目录，避免将配置回退误当数据迁移。

密码轮换：在仓库外备份并移开两份本机凭据，再运行admin-bootstrap生成新凭据，将新admin-auth.json以600权限上传credentials并重启video容器；重启撤销全部旧会话。不要把明文密码上传服务器或聊天。

验收：源码测试、生产鉴权/冲突/回滚、公网网页、小程序开发者工具与受控重启分别记录在test-batches。手机真机和正式审核状态单独列明。


账号拆解模板：持久化于video-data/assets/analysis/preferences.sqlite，通过微信会话隔离，写入采用版本比较。已执行SQLite在线备份至同目录preferences.backup.sqlite并验证完整性，权限600；不要直接复制运行中的WAL数据库作为唯一备份。回退镜像前保存该数据目录，旧镜像不提供账号模板接口，但不得删除数据库。analysis-78部署前.env备份位于/opt/youai/releases/analysis-78/env.previous。
