# Claude → Codex 交接 · 2026-10-19

## 交接基线
- 分支 `codex/admin-console`，提交 `8915c8a` 之后加本交接文档；线上 **platform-8915c8a**（增量部署）。健康 200。
- 测试批次累计 **152**，下一次 **第153次**（`docs/test-batches.md`）。
- 小程序：本轮改动**尚未上传体验版**。只能从 `E:\data\codexYOUAI` 上传（开发者工具里另有 `E:\data\codexYOUAI-services\creation-*-preview` 等本地预览副本，它们连 127.0.0.1，传上去手机会报 “url not in domain list:127.0.0.1”）。版本号接 1.0.135 之后（建议 1.0.136）。

## 本次 Claude 完成内容（2026-10-18，按提交顺序）
1. **体验版测试账号**（1220551）：体验版/开发版可生成独立账号（虚构 100 号段手机号），数据照常上传，中台标注“体验版”，可一键关闭。
2. **创作板块走查修复**（df1d80c）：Nginx 对 `/youai/` 统一 64KB，上传原视频/套版画面/BYOK/数据截图被网关拒绝 → 单独放宽；确认卡 catchtouchstart 吞点击；一次提交创建两次会话。
3. **灵感碎片箱**（52e5a71…6940567）：`scripts/idea-box.py`、`pages/idea-box`；文字/链接/截图（本地 OCR）/语音（本地转写，音频不留）；`idea_note` 轻反馈；TA 开场引用未用旧碎片。设计见 `docs/idea-box-plan.md`。
4. **首页**（1b9eb59…3a8b955）：我想记为第一视觉主体，语音/图片图标与“记下来”收进输入框，碎片箱入口在标题右侧；TA 输入框发送不撑高、超两行可展开、发送左侧语音输入（`/voice/transcribe` 只转文字不存）。
5. **拆解质量**（44a4338…8915c8a）：图文作品转幻灯片；作品数据 + 账号画像 → `insight`（为什么火、驱动、账号角色、复刻难度、评论区打法、摆拍提醒）；OCR 分层（title/caption/watermark/ui，相对字号）与相似误识投票；观看模型输出校对后的 `keyText` 并优先使用；全程大标题单独改写；创作包用改写稿并附原句参考。详见 `docs/breakdown-quality-2026-10-18.md`。

## 接口与数据变化
- 新接口：`POST /auth/trial`；`/ideas`、`/ideas/media`、`/ideas/sync`、`/ideas/<id>/status|delete`、`GET /idea-media/<id>.jpg`；`POST /voice/transcribe`。
- Nginx（`deploy/youai888.nginx.conf`，已上线）：`/youai/references/upload` 210m、`/youai/replica/jobs` 10m、`/youai/ideas/media` 8m、`/youai/voice/transcribe` 4m、`^~ /youai/board/works`（**不带尾斜杠**，否则 301 变 GET）7m。
- `source_meta` 新增：`kind`(video|gallery)、`imageCount`、`description`、`author.totalLikes/verified/signature(联系方式已替换)/hasContact`。
- 观看结果 `understanding.keyText`；`screenText.items[].layer`；`WATCH_SCHEMA` 5.3（改提示词或输出结构要同步升版本，否则读旧缓存）。
- 拆解 `breakdown.insight`；文字作品 `screenTitles`；创作包 `shots[].orig/tooClose`。
- 灵感 AI 场景新增 `idea_note`；`board_breakdown`/`board_output` 默认输出上限 3500。

## 测试证据
- Python（容器 Python 3.13）：test-breakdown-quality（8）、test-idea-box（4）、test-wechat-auth（含 /ideas、/voice/transcribe HTTP）、test-creation-board、test-screen-text、test-link-platform 等全部通过；test-video-server 的 RendererTests（字体）与 test-video-image（ASR）为本地环境项。
- Node：386 通过，3 个环境项（codex-http-repair、产品方案 Demo 基线需 .git、源码归档）。
- 真实样片：`scripts/sample-breakdown-run.py` 以 `claude-test` 跑五条抖音链接，结果在服务器 `/data/assets/claude-runs/run7.json`（图文）、`run8.json`（三条视频）、`run9.json`。
- 注意：用户机器的 Python 是 3.10（无 tomllib），video-server 相关测试需在 3.11+ 跑。

## 运行状态
- 创作板块、碎片箱、TA、体验账号均在线；体验账号开关在中台“创作板块”页底部，**提交微信审核前请关闭**（审核版与体验版请求来源相同）。
- 语音相关（碎片语音、TA 语音输入）只在开发者工具外真机可测，尚未真机验证。

## 密钥与费用
- 部署用 `claude-deploy` 目录下的 key（Codex 不要使用或移动它，Codex 用自己的部署方式）。
- 2026-10-18 排查图文时，服务器解析服务（dtk）的访问密钥在 Claude 的命令输出里显示过一次，未写入任何文件；建议用户在中台/服务器轮换一次。
- 本轮真实模型调用：五条样片 ×3 次全流程 + 碎片轻反馈若干，均为 qwen3.8-flash 级别，费用很低。

## 未完成事项（交给 Codex，按建议顺序）

### A. 字幕区域放大后二次识别（低成本、优先）
- 现状：`scripts/screen-text.py` `extract()` 以短边 540px 抽帧整图 OCR；小字号字幕易错字（如“47”读成“4”）。现在靠观看模型 `keyText` 兜底。
- 做法：`merge()` 之后，对 `layer in ('title','caption')` 且（置信度 < 0.9 或含数字/专有名词）的 span，在其中点时间用 ffmpeg 取**原分辨率**单帧，按 box 外扩（横向 15%、纵向 40%）裁剪，字高 < 48px 时放大 2 倍，再 OCR；新结果置信度更高才替换，记录 `refined: true`。上限 12 个裁剪、总时长 ≤ 15 秒，计入现有 45 秒预算（watch-flow 里 OCR 线程 join 55 秒）。
- 验收：Codex 录屏样片（https://v.douyin.com/_rhgl9IFmKM/）OCR 本身读出“跑了47分钟”；两核服务器总 OCR 时间增加 ≤ 10 秒。
- 测试：fake recognise 验证只重识别 title/caption、预算用尽即停、低置信不覆盖高置信。改完升 `WATCH_SCHEMA`。

### B. 用作品文案、话题、昵称、音乐名做纠错词典
- 做法：从 `reference.source`（description、hashtags、author.nickname、music.title）切出 2–12 字的候选词；对作者字幕（OCR span）和语音转写逐句做模糊匹配（difflib ≥ 0.75、差 1–2 字、长度 ≥ 3），命中则替换并记录 `corrected:{from,to,by:'lexicon'}`。**数字不参与替换**（避免把 47 改成别的）。
- 位置：`screen-text.py` 新增 `correct(items, lexicon)`；`watch-flow.py` 的 `preprocess` 需要拿到 post（`watch()` 已有 `post` 参数，透传即可）；语音转写在送观看模型前同样校正。
- 验收：“似水汽年”在文案含“似水流年”时被纠正；与文案无关的文字不变；数字不变。
- 测试 + 升 `WATCH_SCHEMA`。

### C. 语音转写模型 tiny → small
- 现状：`video-server.py` `_transcribe_reference` 用 faster-whisper，`YOUAI_WHISPER_MODEL` 默认 `tiny`，int8、2 线程，`ASR_LOCK` 串行。李醒醒样片 tiny 转写成“特术议加点什么行情内目”（字幕是对的）。同一函数也服务碎片语音和 TA 语音输入（要求快）。
- 做法建议：
  1. 视频分析用 small，语音输入（`/ideas/media` voice、`/voice/transcribe`）继续 tiny：两个模型实例或按调用方传 `model`。
  2. small 模型文件打进镜像（服务器访问 HuggingFace 可能受限，用国内镜像或预先下载后 COPY；`deploy-delta.sh` 支持 Dockerfile 新增 `RUN`/`ENV` 行叠加）。确认内存（两核服务器，small int8 约 0.5GB 内存）。
  3. 配置进中台“作品拆解 → 观看配置”（`platform-config.py` videoUnderstanding 新增 `asrModel: tiny|base|small`），默认 small。
- 验收：李醒醒样片转写与字幕基本一致；记录 60 秒音频 tiny/small 耗时对比；语音输入延迟不变。
- 风险：small 转写约为 tiny 的 3 倍时间，长视频分析时间会变长；观看缓存 key 需包含 asr 模型。

### D. 接入抖音热门评论
- 目的：评论驱动型作品（李醒醒评论/赞 0.35、零＄落 8.12、避雷帖 0.29）的爆点在评论区，拆解要基于真实评论给“评论区打法”，文字作品/创作包给置顶评论建议。
- 先确认数据来源：解析服务 dtk（`YOUAI_REFERENCE_PARSER_URL=http://dtk-api-1:8000`，见 `docs/agent-handoff-2026-10-13-cloud-parser.md`）是否已有评论接口；没有则在 dtk 侧增加“按 content_id 取热门评论前 20 条”的接口。
- 只保留：评论文本（替换联系方式，≤ 80 字）、点赞数、回复数、是否作者回复；**不保存评论者昵称、头像、ID**。按 content_id 缓存 24 小时；超时 10 秒；失败不影响拆解。
- 使用：`reference['comments']` → `post_context` 增加 `topComments`（≤ 10 条）；`board_breakdown` 提示词要求 `insight.commentPlay` 引用评论规律（大家在评论里干什么：接龙、爆料、站队、求资源）；文字作品/创作包给“置顶评论/回复话术”。拆解卡 insight 区展示 2–3 条代表评论。
- 隐私：更新 `docs/privacy-creation-board.md`（公开评论仅取文本用于分析，不保存评论者身份）。
- 验收：李醒醒、零＄落两条样片的 commentPlay 明显基于真实评论内容。

### 用户侧待办（非代码）
1. 从 `E:\data\codexYOUAI` 上传体验版 1.0.136 并真机走查（语音两处、截图碎片、创作板块图文样片）。
2. 微信公众平台隐私指引补充：麦克风、选中的照片、微信聊天文件（见 `docs/privacy-creation-board.md`）。
3. 订阅消息模板申请后在中台填写模板 ID。
4. 提交审核前在中台关闭体验版测试账号。

## 回滚点
- 后端：`bash /opt/youai/releases/remote-release.sh switch platform-<上一个>`（本轮依次 1220551 → 52e5a71 → a134d9e → 452ff53 → 1b9eb59 → 44a4338 → 9102bf2 → cf31257 → 8915c8a）。
- Nginx：服务器 `/opt/youai/backups/nginx-youai888-<时间>` 为每次修改前备份；仓库版本 `deploy/youai888.nginx.conf`。改后务必 `nginx -t` 再 reload。

## 回交格式（Codex → Claude）
按 `docs/agent-return-YYYY-MM-DD-codex.md`，包含：回交基线、完成内容、接口与数据变化、测试证据、运行状态、密钥与费用、未完成事项、回滚点。

## 可直接发给 Codex 的提示词
> 读 `docs/agent-handoff-2026-10-19-claude.md` 和 `docs/breakdown-quality-2026-10-18.md`，按“未完成事项”A→B→C→D 顺序实现：A 字幕区域放大二次识别，B 用作品文案/话题/昵称/音乐名做纠错词典，C 语音转写视频分析用 small、语音输入保留 tiny，D 接入抖音热门评论（只存文本与计数，不存评论者身份）。每项都要有测试、升级 WATCH_SCHEMA（A、B、C）、在第153次起记录测试批次；用 `scripts/sample-breakdown-run.py` 在服务器以 claude-test 复测五条样片（链接见 breakdown-quality 文档开头的样片名，对应链接在 run7/run8 结果里），对比改动前后。部署前告诉用户。仓库存 LF、工作区 CRLF，提交时按 LF 暂存。完成后写 `docs/agent-return-YYYY-MM-DD-codex.md`。
