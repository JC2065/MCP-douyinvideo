# 视频拆解低成本方案：先看懂 → 再聊 → 再生成（交给 Codex 实施）

> 作者：Claude，2026-10-17。用户已确认：优先低成本，后期用户量大时消耗不能失控；拆解要少束缚模型，先真正看懂视频，再和用户沟通生成什么。
> 本文是实施规格，Codex 按此实现；规则仍以 `AGENTS.md` 为准（提交、测试批次、台账、回交文档）。

## 1. 现状评估（content-evidence-3，线上 platform-cbe5b1f）

| 项 | 现状 | 问题 |
| --- | --- | --- |
| 输入 | 均匀 ≤12 帧、768px、JPEG q75 + faster-whisper 转写 | 768px 每帧约 190 Token；12 帧对 60 秒舞蹈/剧情太稀，动作看不连贯；没有任何音乐/节奏信息 |
| 模型 | `reference_understanding` → qwen3-vl-plus（$0.20/M 入，$1.60/M 出），maxTokens 3500 | 输出是贵的部分；一次就生成三类共 18 条推荐 |
| 校验 | `normalize()` 严格：facts 必须引用输入帧时间、speechEvidence 必须出现在转写、推荐必须带 factIndexes | 付费结果整体被丢弃 → 用户重试 → 重复付费；也是“对模型限制太多”的根源 |
| 缓存 | 按素材 SHA + `understandingRevision`，中台任一场景改动即全部失效 | 改个提示词全站重算 |
| 单次成本 | 约 ¥0.03 / 60 秒视频（不含重试） | 重试与 18 条推荐放大成本 |

## 2. 目标流程

```
上传/解析参考视频
  └─ ① 本地预处理（服务器 CPU，零模型费用）
       抽帧(≈1fps + 镜头切换帧, 360px) · 转写 · 音频特征(文本)
  └─ ② 一次“看懂”调用（便宜多模态模型，宽松提示词）→ 理解卡 understanding
       └─ 低置信 / 用户点“再仔细看一遍” → ③ 升级 omni 模型（真实听音频）
  └─ ④ 拆解对话（最便宜文本模型，≤4 轮）→ 用户确认的 brief
  └─ ⑤ 只为用户选定的产物（文字/图片/视频）生成推荐与作品（复用现有生成链路）
```

### ① 本地预处理（不新增 pip 依赖，可增量部署）

- 只分析前 `maxAnalyzeSeconds`（默认 90，中台可配 30–300）。
- 抽帧：约 1 fps 的均匀帧 + 现有帧差检测到的镜头切换帧，去重后上限 `maxFrames`（默认 32，范围 8–48）；短边缩到 `frameShortSide`（默认 360，范围 240–768），JPEG q70。
  - Token 估算：tokens ≈ ceil(h/28)·ceil(w/28)/4 + 2；360×640 竖屏 ≈ 80 Token/帧，32 帧 ≈ 2.6k Token。
- 转写：沿用 faster-whisper；额外输出 `speechRatio`（有语音时长/总时长），无口播时明确标记“无口播/主要是音乐”。
- 音频特征（用已有的 imageio-ffmpeg 解码 PCM + numpy 能量包络，**不装 librosa**）：响度曲线概要、能量峰值时间点（onset 近似）、粗略 BPM 估计（自相关），一律写成文本给模型，例如 `音乐约 118 BPM（估计）；明显重拍 0.5s,1.0s,…；第 12–14 秒静音`。
- 估计值都标“估计”，模型和界面不得把它们当事实（第134次已删除帧差推断节奏，这里是独立的音频信号，可保留但需标注）。

### ② “看懂”调用

- 新 AI 场景 `video_watch`（中文名“视频观看理解”），默认 connection `qwen-domestic`、model `qwen3.8-flash`（$0.16/M 入、$0.47/M 出），maxTokens 1500，timeout 60。
  - 实施第一步先用 1 次真实调用确认 qwen3.8-flash 在兼容模式下接受多图输入；不接受则默认改为 `qwen3-vl-plus`，其余设计不变。真实调用前须征得用户同意（会产生少量费用）。
- 提示词（宽松，系统部分保持固定以命中百炼隐式前缀缓存）：
  “你是资深短视频导演。按时间顺序描述这段视频发生了什么：人物与动作、镜头与机位变化、声音与画面文字、情绪与节奏；说明它为什么吸引人、作者可能想表达什么、用户提交它可能想做什么；看不清或不确定的地方直接写在 uncertainties。转写和音频特征只作上下文，不要照抄成文案。”
- 输出轻量 JSON（字段缺失不报错）：
  ```json
  {"overview":"一句话", "timeline":[{"start":0,"end":3.5,"what":"…","camera":"…","sound":"…","text":"…"}],
   "audio":{"kind":"music|speech|mixed|none","note":"…"}, "style":{"mood":"…","pacing":"…","visual":"…"},
   "hooks":["…"], "likelyIntents":["想复刻这支舞","想做同款口播"], "uncertainties":["…"], "confidence":0.0}
  ```
  `timeline` 字段借鉴 video-to-prompt 的逐镜头结构（shot_size_estimate/composition/camera_motion/pacing_note），只借结构不复制代码。
- 宽松校验 `normalize_watch()`：只检查类型、长度上限、时间在 [0, 分析时长] 内且 start≤end；**单个坏字段丢弃，不整体判失败**；只有完全无法解析 JSON 才算失败（失败时允许一次自动修复重试，即把原输出交给同模型“只修 JSON”，maxTokens 1500）。
- 不再在这一步生成推荐。

### ③ 升级观看（按需）

- 新场景 `video_watch_deep`（“深度观看”），默认 `qwen3.8-omni-flash`，直接给视频（≤10MB 用 base64，否则用 5 分钟有效的签名 URL，复用现有签名资源机制），真正听音频。
- 只在以下情况触发：`confidence < deepWatchThreshold`（默认 0.4）且中台开启自动升级；或用户在理解卡上点“再仔细看一遍”（每用户每视频 1 次）。默认自动升级 **关闭**，只保留用户手动。
- 结果覆盖同一视频的理解卡并标记 `depth:"deep"`。

### ④ 拆解对话

- 新场景 `video_chat`（“拆解对话”），默认最便宜的文本模型（当前千问文本连接的 flash 档），maxTokens 600。
- 上下文：理解卡压缩为 ≤800 字摘要 + 个性化画像 `learnedProfile`（复用 `user-profile.py`）+ 最近对话。
- 第一轮由模型开口：用 2–3 句复述“我看到的是……”，并给 2–4 个可点选的方向（来自 likelyIntents），用户也可自由输入或纠正理解（纠正写回理解卡的 `userCorrections`）。
- 最多 `chatMaxTurns`（默认 4）轮，最后输出确认 brief：`{"output":"video|text|image","goal":"…","keep":["…"],"change":["…"],"notes":"…"}`，用户点“就这样做”后进入现有文字/图片/视频生成（替代原来的 18 条预生成推荐；推荐只为选定产物按需生成）。

## 3. 成本控制（必须实现）

1. **全站共享缓存**：键 = 素材 SHA-256 + 分析时长/帧参数 + 场景模型 + `promptVersion`。不同用户提交同一视频直接复用；中台改动无关场景不再让缓存失效（不再用全局 revision）。
2. **用量记录**：每次模型调用记录返回的 `usage`（prompt/completion tokens、模型、场景、是否命中缓存），新表或 JSONL，中台“总览”显示今日/近7日调用数、Token、估算费用（单价表放配置，可在中台改）。
3. **限额**：每用户每日新视频理解数 `perUserDailyVideos`（默认 10）；全站每日预算 `dailyBudgetYuan`（默认 20）。超额时降级为“仅本地分析”（转写+音频特征+帧时间轴），界面如实说明“今日 AI 观看额度已用完”，不伪装成功。
4. 视频只取前 90 秒、帧 360px、输出 Token 上限，均可在中台调。
5. 第二期：非即时任务走百炼 Batch（半价）；PySceneDetect 镜头检测（需改 Dockerfile 的 RUN 行 → 整包部署）。

### 成本估算（60 秒视频，按公开单价，需以真实 usage 校准）

| 方案 | 估算 |
| --- | --- |
| 现方案 content-evidence-3（不含重试） | ≈ ¥0.03 |
| 全程 omni 看视频 | ≈ ¥0.06–0.10 |
| 本方案：本地预处理 + qwen3.8-flash 看懂 | ≈ ¥0.01 |
| 拆解对话 4 轮（flash 文本） | ≈ ¥0.002–0.005 |
| 缓存命中 | ¥0 |

自建 GPU 推理（约 ¥3000/月）在每月新视频少于约 30 万条前不划算，暂不做。

## 4. 中台

“作品拆解”板块新增卡片（写入 `platform-config.py` 新 section `videoUnderstanding`，版本化、expectedRevision、可回滚，校验范围同上）：

`maxAnalyzeSeconds, maxFrames, frameShortSide, deepWatchThreshold, autoDeepWatch(false), chatMaxTurns, perUserDailyVideos, dailyBudgetYuan, prices{model: {in, out}}`

AI 场景列表新增 `video_watch / video_watch_deep / video_chat`，沿用连接选择、模型、超时、maxTokens、补充提示词。保留 `reference_understanding` 场景只为兼容旧缓存读取，不再调用。

## 5. 代码落点

| 文件 | 改动 |
| --- | --- |
| `scripts/content-understanding.py` | 新增 `watch()`、`deep_watch()`、`normalize_watch()`、`audio_features()`；旧 `understand()/normalize()` 保留供旧记录展示 |
| `scripts/video-server.py` `analyze_reference` | 帧采样参数改读中台；`analyzerVersion` → `content-watch-4`；旧 `content-evidence-3` 记录照常可读；新增路由 `POST /reference/deep-watch`、`POST /reference/chat`、`POST /reference/brief` |
| `scripts/inspiration-ai.py` | SCENES/DEFAULTS 增加三个场景；`complete()` 返回并记录 usage |
| `scripts/platform-config.py` / `admin-console.*` / `pages/admin` | `videoUnderstanding` 配置与用量概览 |
| 新 `scripts/usage-ledger.py` | 用量记录、每日额度/预算判断（Dockerfile.video 的 COPY 列表要加上，测试 `platform-config.test.js` 会检查） |
| 小程序视频页 | 理解卡（概述/时间轴/声音/不确定）+ “再仔细看一遍” + 对话区 + brief 确认；替换原推荐卡 |

## 6. 测试（全部 mock，禁止真实付费调用）

- Python：`test-content-understanding.py` 增加：宽松校验保留好字段丢坏字段；音频特征在纯音乐/纯口播/静音三种合成音频上的输出；帧数/尺寸上限；缓存跨用户命中且与无关场景修订无关；超额降级；深度观看仅在条件满足时触发；usage 记录。
- `test-video-server.py`：新路由鉴权（匿名 401、跨账号 403）、每用户额度、brief 进入生成。
- Node：视频页理解卡/对话/brief 渲染与旧 `content-evidence-3` 记录兼容；中台新卡片字段。
- 真实验收（需用户同意费用）：2–3 次真实调用核对 usage 与估算；用户提供 3–5 个样例（跳舞/口播/剧情/带货），人工判断“看懂了没有”。

## 7. 发布与回滚

- 第一期不改 Dockerfile 的 FROM/RUN，只增加 COPY 的模块 → 可用增量部署；部署前按第133次做完整备份，并征得用户同意。
- 回滚：`remote-release.sh switch <旧标签>`；新旧记录版本并存，回滚后旧版本忽略 `content-watch-4` 记录（重新分析）。
- Codex 使用 `youai_deploy` 钥匙，不使用 claude-deploy。

## 8. 验收标准

1. 跳舞无口播视频：理解卡说清动作/机位/音乐氛围，不出现编造的口播文案。
2. 单个 60 秒视频首次理解的真实费用 ≤ ¥0.015（以 usage 为准），同视频第二次 ¥0。
3. 模型返回部分字段错误时页面仍显示其余内容，不要求用户重试。
4. 对话 ≤4 轮得到 brief，生成结果符合 brief。
5. 超额时如实提示并给出本地分析结果。
