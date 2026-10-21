
## 2026-10-13 云端音频与转写修复（累计 66）

- 手机解析、视频下载已获用户确认，第 65 次所欠手机验证完成。
- 当前视频镜像：`codexyouai-video:tools-66-final`，广州 `/opt/youai/internal-api/.env` 的 VIDEO_TAG 已同步，避免下次 Compose 启动回退旧镜像。
- ASR：faster-whisper 1.1.0、PyAV 17.0.0、requests 2.32.3；离线 tiny 模型挂载 `/models/faster-whisper-tiny`，CPU 两线程、单模型串行。模型文件由已缓存副本部署到服务器 `models/faster-whisper-tiny`，不包含凭据。重建时须保留此目录。
- 修复不可用转写缓存永久复用；参考分析遇到不可用转写也会重试。音频端下载带鉴权，再用本地 MP3 播放，支持暂停、时间、错误和退出清理；导出用微信文件分享。没有把沙盒保存冒充系统文件保存。
- 真实样片：`ZCgX-yI6HNo`，SHA `c4aaed62d5cff1d1b0233ce3ae948ab202d9ecbb6eb5c454820233f38b7bf706`，21.2 秒。公网 MP3 509276 字节、Range 206、完整解码成功；转写约 6 秒，返回中文和时间戳，但错字明显，只能作为待校对初稿。没有调用付费模型或将分享标题当转写。
- 前端 57 项、Python 视频 25 项、微信鉴权 4 项通过；云端镜像音频解码/VAD/静音转写检查通过。微信 preview 打包通过；自动化端口未建立，未声称模拟器视觉及手机播放/导出验收通过。
- 新版二维码及原始测试日志位于仓库外 `E:/data/codexYOUAI-data/cloud-tools/`。手机复测：音频提取→播放→暂停→导出 MP3 到聊天；文案提取→看到真实文案并校对。
- 回滚命令（广州部署目录）：`VIDEO_TAG=parser-65 docker compose -f compose.video-cloud.yml up -d --wait`；同时把 `.env` 的 VIDEO_TAG 改回 parser-65。保留模型和视频资产，不删除数据。
