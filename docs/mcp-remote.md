# 远程 MCP：抖音解析（2026-10-21）

外部 AI 客户端（Claude、Codex、Cursor 等）通过 `https://youai888.top/youai/mcp` 使用服务器上的抖音解析能力。

## 架构

客户端 →（访问令牌）→ 有AI视频服务 `/mcp`（`scripts/mcp-gateway.py`）→（MCP 专用 dtk 密钥）→ dtk 自带 MCP `http://dtk-api-1:8000/mcp/`

- **鉴权**：客户端带 `Authorization: Bearer <访问令牌>`。服务器只保存令牌的 sha256，原文在用户本机 `E:\data\codexYOUAI-data\claude-deploy\youai-mcp-token.txt`（不进 Git）。
- **独立密钥与额度**：dtk 里单独一把 `youai-mcp` 密钥（前缀 93e7e240a97b，仅 douyin:read，每分钟 10 次），与小程序的 `youai-reference-parser`（每分钟 120 次）分开限流、分开记日志，互不占用。
- **每日上限**：网关按北京时间每天最多 50 次（`pool_status`、`get_task_result` 不计）。超出时返回可读的工具错误，不转发。
- **配置**：服务器 `/opt/youai/internal-api/video-data/assets/mcp/config.json`（容器内 `/data/assets/mcp/config.json`，权限 600）：`tokenSha256`、`dtkKey`、`dailyLimit`。改文件即时生效，无需重启。用量在同目录 `usage.sqlite`。
- dtk 的地址、密钥都不出服务器；网关只回传 `Content-Type`、`Mcp-Session-Id` 等必要响应头。

## 工具（共 9 个）

**`download_video`（有AI自建，在网关本地处理）**：参数 `url`（分享链接或整段分享文案）。用 MCP 专用 dtk 密钥解析，复用小程序的下载流程（`acquire_reference`，不抓评论）把无水印视频下载到服务器（图文合成为每张 3 秒的幻灯片视频，与小程序素材同一存储、按 sha256 去重），返回作品信息（文案、话题、作者昵称与粉丝数、点赞/评论/收藏/分享、时长、分辨率、大小）和 `downloadUrl`：`https://youai888.top/youai/mcp/files/<sha256>.mp4?e=<过期时间>&s=<签名>`，30 分钟有效，无需登录或 Referer，支持断点续传。签名密钥由 dtkKey 派生，删除 config.json 后所有链接立即失效。计入每日额度。网关把它追加到 dtk 的 tools/list 结果里。

**dtk 提供的 8 个**：

`parse_url`（解析分享链接）、`get_video`（作品详情，含无水印地址）、`get_user`、`list_user_posts`、`list_comments`、`get_content_history`（需 archive 权限，本密钥无）、`pool_status`、`get_task_result`。返回的媒体地址是抖音 CDN 原始地址，会过期，下载时可能需要 `Referer: https://www.douyin.com/`。

## 客户端配置示例

把 `<TOKEN>` 换成 `youai-mcp-token.txt` 里的内容。

- Claude Code：`claude mcp add --transport http youai https://youai888.top/youai/mcp --header "Authorization: Bearer <TOKEN>"`
- 通用 JSON（Cursor 等）：`{"mcpServers":{"youai":{"url":"https://youai888.top/youai/mcp","headers":{"Authorization":"Bearer <TOKEN>"}}}}`

## 运维

- 换令牌：本机生成新令牌，把 sha256 写进 config.json 的 `tokenSha256`。
- 停用：删掉 config.json（网关对所有请求返回 401），或在 dtk 控制台吊销 `youai-mcp` 密钥。
- 调额度：改 `dailyLimit`；分钟级限流在 dtk 控制台改该密钥的 rate_limit。
