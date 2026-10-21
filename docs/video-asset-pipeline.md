# 视频资产与生成任务契约

本契约是参考视频分析到成片工作流的持久化基础。所有记录按用户隔离；媒体按 `user_id + sha256` 去重；任何派生产物都保留来源资产、分析、故事板、镜头、生成任务和模型参数版本的血缘。

## 资产图谱

`media_assets` 保存原片、音频、关键帧、字幕、候选镜头与最终成片的地址和媒体属性。`reference_analyses` 固定一次分析的版本、证据、置信度和转写；`video_shots` 是最小分析与重做单元。`storyboards` 保存三种参考模式下可审核的版本和费用预估。`generation_jobs` 保存经过脱敏的实际请求快照、Provider 任务号、阶段和预估/实际成本。`video_artifacts.lineage` 连接来源与结果。`creation_feedback` 只记录用户明确执行的接受、拒绝、编辑、重做和删除事件，并支持软删除。

## 状态与门禁

素材必须依次达到“链接已识别”“媒体已获取”“分析成功”。只有存在成功分析及已批准故事板时才能排队生成。生成任务使用 `draft → queued → running → succeeded|failed|cancelled`；失败任务可重新排队，成功和取消任务不可改写。故事板引用模式只能是 `reference-video`、`content-structure`、`visual-style` 或 `same-topic`。默认使用 `visual-style`，把最多 3 张代表帧作为 Base64 `reference_image` 真正提交给 Provider；`reference-video` 只在原片不超过 15 秒且已配置模型可访问的 HTTPS 素材地址与签名密钥时开放，通过 30 分钟有效的签名 URL 提交原片。15.00–15.50 秒的小幅容器时长误差会规范到 14.9 秒并以派生 SHA 提交，原片不覆盖且血缘可追溯；明显超长、配置缺失或素材超时均在付费调用前明确拦截，禁止静默退化成纯文本生成。

本机 Demo 的 HTTPS 素材地址由独立参考中继经 Cloudflare Tunnel 提供。中继与主视频 API 分端口，只接受健康检查和签名原片路径；签名绑定素材 SHA 与过期时间。Quick Tunnel 不作为生产依赖承诺，正式环境使用命名 Tunnel 或兼容 S3 的临时对象 URL，生成完成或超时后即可回收远端对象。

## 长期与临时资产

长期保留授权状态、源文件哈希、成功分析、镜头、获批故事板、被采用产物、脱敏提示词参数、成本和显式反馈。临时抽帧、未采用候选、失败低质产物和过期下载地址由后续生命周期任务清理；删除前不得破坏已发布成片的血缘。

API Key、Authorization、token、secret 和 password 不得进入请求快照。真实 Provider 调用生成前先写预估成本，完成后补实际成本；币种固定为 CNY。
