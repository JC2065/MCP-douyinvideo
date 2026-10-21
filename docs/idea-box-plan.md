# 灵感碎片箱 + TA 选题（“我想记”优化）

> 2026-10-18 与用户确认：TA 定位为**选题助手**；“我想记”是日常灵感碎片箱，碎片包括**文字、链接、截图、语音**；**TA 可以主动拿旧碎片开场**。

## 1. 决策
- 我想记负责“存”，TA 负责“用”。记录要比打开备忘录更快：文字直接记、粘链接自动识别平台、截图（相册/拍照/从微信聊天选）、按住说话。
- 截图在服务器本地 OCR（RapidOCR）、语音本地转写（faster-whisper），不调用付费模型；语音转写后**删除音频**，只留文字；截图原图保留在用户自己的碎片里，可删除。
- 保存后由便宜模型（灵感 AI 场景 `idea_note`，默认 qwen3.8-flash，中台可关）补一句“适合做成什么”的轻反馈和最多 3 个标签；失败不影响保存。
- TA 开场：上下文加入该账号未使用、最少被提起的碎片（最多 8 条）。有碎片时至少 1 个选题要建立在一条旧碎片上，并尽量与当前热点结合；选题卡显示“源自你的碎片”。被提起的碎片计数，避免反复拿同一条。
- 在碎片箱点“和 TA 聊这个”：带着该碎片发起对话（focus fragment）。
- “把点子做成视频”从首页按钮移到碎片条目操作里；链接碎片可“拆这个链接”（进入创作板块）。
- 未登录：文字碎片仍记在本机；截图/语音需登录。登录后本机未同步的文字碎片自动上传（clientId 去重）。
- 每账号最多 500 条碎片、每天 100 条；截图 ≤6MB；语音 ≤60 秒。

## 2. 数据与接口
- `scripts/idea-box.py` `IdeaBox`：表 fragments(id, user, kind text|link|image|voice, text, url, platform, media, extracted, note, tags, status new|used|archived, surfaced, last_surfaced, client_id, created)。
- 接口：`POST /ideas`（文字/链接）、`POST /ideas/media?kind=image|voice&clientId=`（multipart）、`GET /ideas`、`POST /ideas/<id>/status`、`POST /ideas/<id>/delete`；截图预览 `/idea-media/<id>.jpg`（归属校验 + 签名链接）。
- Nginx：`= /youai/ideas/media` 放宽到 8m。
- `/topics/chat` 支持可选 `fragmentId`；服务端注入碎片上下文，回复的 topics 可带 `fragmentId`（仅限给出的碎片）。

## 3. 客户端
- 首页“我想记”：输入框 + 工具行（按住说话 / 截图 / 聊天里选）+ [记下来] [碎片箱 N ›]。
- `pages/idea-box`：全部/未用/已用筛选；条目显示类型、内容、AI 轻反馈、标签、时间；操作：和 TA 聊这个、拆这个链接（链接）、做成视频、标记已用、删除。
- TA 选题卡：带 fragmentId 时显示“源自你的碎片：…”。
- 顺手修：“登录后聊天”按钮被挤成三行；未登录时 TA 区域显示示例选题而不是空灰框。

## 4. 隐私
- 隐私指引需新增：麦克风（录音，用于语音碎片转文字，音频转写后删除）、相册/拍照与聊天文件（用于截图碎片）。见 docs/privacy-creation-board.md。

## 5. 进度
- [x] 服务端模块与接口（scripts/idea-box.py，/ideas*，/idea-media，Nginx 8m）
- [x] TA 接入（topic-chat.py ideaFragments/focusFragmentId，选题带 fragmentId，提起计数）
- [x] 客户端（首页工具行与碎片箱入口、pages/idea-box、TA 卡片来源、未登录示例）
- [x] 部署（platform-452ff53，Nginx 已更新）与开发者工具走查：文字/链接/截图（OCR+轻反馈）、碎片箱页、TA 开场引用旧碎片、和 TA 聊这个；语音需真机测试

## 6. 已知事项
- 本机旧笔记不区分账号：首次登录的账号会同步这台设备上未同步的笔记（之后标记已同步，不会再传）。
- 轻反馈只在新建碎片时生成；同步上来的旧笔记没有轻反馈。
