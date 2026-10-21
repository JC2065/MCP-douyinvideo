# 资产同步、归档与恢复

## 当前实现

本机视频服务成功保存资产包后自动写入 SQLite 持久队列。单后台 Worker 每 5 秒检查到期任务，失败指数退避，用户可手动重试；服务重启会恢复未完成任务。飞书失败不改变已经生成的视频结果，在线原片和成片均保留。

六表使用作品/方案/资产/反馈/资源池/任务稳定 ID 查询后更新，重复处理不会有意创建重复记录。一个资产包归档记录和每个文件的资产目录记录同时保存；每个文件条目包含哈希、大小、包 ID 和包内位置。

归档包包含原片、代表帧、分析、分镜、实际提示词、成片及脱敏生成设置和血缘索引；不打包原始 `request.json` 或包含绝对路径的本机 manifest。未知费用保持未知，不填成 0；套餐额度需要定期核验，不自动把旧截图数据作为当前值。

文件包按 18 MiB 分片上传，避开单次全量上传限制。用整个包哈希及分片序号命名，重试先查目录；每片上传后立即下载并核对 SHA-256，全部成功才标记已归档。大文件支持已用 19 MiB 合成文件验证；单作品解压内容上限 512 MiB。

恢复先下载全部分片，核对每片和整个包，再验证路径白名单、解压大小及所有文件哈希；结果保存在 `restored/<runId>`。缺失成片、文案/分镜、原片或代表帧按受控资产根目录恢复，已有在线文件不覆盖。此版本没有自动清理或删除云端/本机原始资产，归档和独立备份仍需区分。

## 配置和使用

- 仓库外凭据：`E:\data\codexYOUAI-data\credentials\feishu-matrix.json` 的 management，增加 `folderToken`。
- 六表映射：`E:\data\codexYOUAI-data\feishu-matrix-unified-state.json`，必须与配置的 Base 一致。
- 服务环境可指定 `YOUAI_FEISHU_CONFIG`、`YOUAI_FEISHU_STATE`、`YOUAI_ASSET_ROOT`；Linux 部署必须设置服务器实际路径。
- 飞书应用需要多维表格记录查询/创建/更新、云盘列表读取/上传/下载权限，Base 和归档目录需授权该应用。权限开通后发布生效。
- 成片页展开资产后可刷新同步状态、重试归档、取回归档，并提交“满意/需要修改”反馈。反馈先本地持久化，队列同步后更新反馈表。
- 历史资产不会自动批量上传；用户在对应作品中点击“同步并归档”才补入队列。

接口：`GET /asset-runs/<id>/archive`、`POST .../archive`（入队/重试）、`POST .../restore`（取回校验）、`POST .../feedback`（反馈）。状态为 not_queued、pending、running、failed、archived；阶段为 queued、syncing、packing、uploading、verified。错误不输出密钥。

SQLite 在资产根的 `archive/queue.sqlite`，回执和分片映射在 `archive/<id>/receipt.json`。数据库、manifest 和回执应一起备份，丢失本机索引后的纯云端灾难恢复目录重建另行实施。当前服务仍是本机开发账号模型；这条本机与飞书闭环不等于生产用户鉴权、对象存储或云端部署完成，上线继续执行 P0/P1。

## 验证

`python scripts/test-asset-archive.py` 覆盖持久队列、重试、去重、大包分片、删除测试文件后恢复、损坏拒绝和越界拒绝；`scripts/test-video-server.py` 覆盖既有调用方。`scripts/verify-feishu-archive.py` 会创建非敏感本地文字样片、原片与代表帧，并真实写入六表/上传/下载/恢复/同步反馈，不调用付费模型。运行真实验证会留下测试记录和文件，不自动删除。

官方接口：[上传文件](https://open.feishu.cn/document/server-docs/docs/drive-v1/upload/upload_all)、[下载文件](https://open.feishu.cn/document/server-docs/docs/drive-v1/download/download)、[记录查询](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/search)。
