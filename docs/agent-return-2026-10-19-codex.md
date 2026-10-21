# Codex → Claude 回交 · 2026-10-19

## 回交基线

- 分支：`codex/admin-console`；接手线上 `platform-8915c8a`。
- A/B/C/D 分别记为累计153/154/155/156；修复和验证补充不重复计数。后续首页修复记157、TA审核错误修复记158，下一次159，160完整测试。
- 保留接手时两份 Claude 交接文档的既有修改，未加入提交。仓库LF、工作区CRLF。

## 完成内容

- A：原分辨率中点裁剪，水平15%/垂直40%外扩，字高不足48px放大2倍；仅作者title/caption，最多12个裁剪、子预算15秒，整帧阶段预留10秒。直接识别已定位文字框，避免再次检测漏掉细数字。置信度保留6位。
- 数字例外经用户明确同意：两个不同时间点裁剪均读出同一数字、置信度均≥0.9且非数字文字完全一致时，可覆盖原来高置信误读；保存原文、原置信度、两个新置信度和时间。其他文字仍要求新置信度更高。
- B：作品文案/话题/昵称/音乐名生成2–12字词典，长句分词；模糊纠错仅长度≥3、差1–2字、相似度≥0.75且无歧义，数字不参与。作用于OCR和ASR全文/时间段，保存corrected来源。
- C：视频分析默认small，可在中台选tiny/base/small；碎片和TA语音仍tiny。三个模型预装镜像，离线加载、CPU int8/2线程、沿用串行锁。观看缓存加入ASR模型，WATCH_SCHEMA依次5.4→5.5→5.6；完整流程发现OCR/ASR争抢CPU后改为串行，升5.7。
- D：复用DTK已有评论接口；按作品ID缓存24小时，最多20条，只持久化脱敏80字文本、点赞数、回复数、是否作者回复。失败降级；模型最多10条，拆解卡最多3条。文字作品和创作包新增置顶评论/回复建议，隐私说明同步。

## 接口与数据变化

- 无新增公开HTTP路由。DTK调用：`GET /api/v1/douyin/video/comments?aweme_id=…&count=20&include_raw=false&wait=8`。
- `reference.comments[]`：`text/likes/replies/isAuthorReply`；不保存评论者昵称、头像、账号ID或评论ID。
- `post_context.topComments`、`breakdown.insight.topComments`、两种产物的`pinnedComment/replySuggestions`；拆解缓存新增`BREAKDOWN_SCHEMA=comments-grounded-2`，修改提示或归一化时须升级，防止旧打法继续命中。
- `screenText.items[].refined/refinement/corrected`；`screenText.seconds/refinementSeconds`。
- `videoUnderstanding.asrModel`；兼容原`YOUAI_WHISPER_MODEL` tiny挂载，额外支持`YOUAI_WHISPER_TINY_MODEL/BASE_MODEL/SMALL_MODEL`。

## 测试证据

- 各次范围详见`docs/test-batches.md`；155合并151–155：Python106项、Node72项通过，串行修复后重跑14个关联Python文件全部通过（含video-server），Node合并范围72项通过；D补充修复范围Python34/Node53通过；测试政策检查4项通过。第155次必要环境验证已完成，阶段检查关闭，十次周期不重置。
- 镜像25模块加载成功；断网加载tiny/base/small并识别静音通过；small真实样片断网转写通过。
- 微信开发者工具实测三条评论、文字作品和创作包的置顶/回复建议渲染；中台390px下拉框small/tiny切换及无横向溢出，截图目视通过。模拟器已回首页；未上传体验版，未做真机验证。
- 服务器Codex样片单独OCR对比：旧45.47秒、新45.01秒；“跑了4分钟”→“跑了47分钟”，新覆盖9/10秒为partial。总预算为调度截止时间，底层同步调用/收尾存在少量超时误差，不声称硬实时保证。
- 60秒音频（李醒醒短音轨循环至60秒，非原生60秒讲话）：旧tiny 61.93s/347.8MB峰值；新tiny 50.43s/348.3MB；small 267.88s/1348.9MB，均available。当前共享负载下small约为同轮tiny的5.31倍，不能当作独占CPU基准。small明显改善乱码，但仍有“行情内幕”错字和繁体输出。语音输入模型/配置保持tiny；并发视频任务仍可能占用共享锁，未宣称并发延迟保证。
- 五条样片重新分析全流程全部完成；评论提示和缓存修复后五条再跑均通过，99条评论白名单通过，拆解/文字/创作包无HTTP错误且都有建议。李醒醒commentPlay引用“两杯可乐”，零＄落引用焦虑/看剧/情感吐槽。完整前后对比见[质量报告](breakdown-quality-2026-10-19-codex.md)。

## 运行状态

- 已发布`platform-0026265`（A–D基线为platform-4e85b84，随后补充首页/TA修复），每次正式切换前已通知用户。最终镜像25模块检查通过；公网health 200、匿名admin-api/platform 401，容器healthy、重启0。
- 完整备份：`/opt/youai/backups/20261018T165623Z-platform-8915c8a`（UTC目录，对应用户时区2026-10-19），服务归档/数据库/镜像/Nginx校验通过，约1.5GB。

## 密钥与费用

- 使用Codex自己的`~/.ssh/youai_deploy`，未读取或移动Claude密钥。无凭据写入日志/提交。
- 复测使用`claude-test`，会产生真实观看、拆解、文字和创作包模型调用；不生成成片、不发布作品。账本累计75次实际模型调用均ok、10次video_watch缓存记录，228749 tokens，配置价格估算¥0.35721021（约¥0.36，非最终供应商账单），含各轮重跑。

## 未完成事项

- A–D实现、范围测试、服务器复测已完成；后续首页修复记157、TA审核错误修复记158，下一次159，160完整测试。用户侧体验版上传、真机语音走查、公众平台隐私指引及审核前关闭体验账号仍沿用交接待办。
- 质量限制：small仍有错字/繁体，音乐可能误转写；OCR可能部分覆盖/界面误分层。生成建议仍可能将网友说法肯定化或提出未确认服务承诺，必须编辑校对，未自动发布。
- YOUAI评论缓存严格为白名单；DTK既有上游服务自己的缓存策略未更改，不能将YOUAI白名单保证扩大到整个第三方/解析链路。

## 回滚点

- 代码提交：A `85e72a1`；B `896c47c`；C `b07767b`；D `4e40971`；数字双裁剪补充 `b8ec5d6`；输出字段补充 `bcc32c2`；CPU串行与大数字字幕优先 `fff60cf`；评论证据/亲历约束 `55f7308`；拆解缓存版本 `4e85b84`。
- 后端上一版：`bash /opt/youai/releases/remote-release.sh switch platform-8915c8a`。当前镜像`codexyouai-video:platform-0026265`，完整旧版备份见运行状态；中间修复镜像也保留在服务器。

## 后续第157次 · 首页白屏修复

补齐pages/main/index.json，增加所有注册页面JSON存在/可解析检查。navigation/demo测试12项通过；微信开发者工具首页实测恢复，截图目视通过。未上传体验版。TA卡片存在独立模型请求错误提示，未将其视为本次页面注册修复通过项。累计157，下一次158，160完整测试。

## 后续第158次 · TA聊天恢复

- 根因：常驻服务附带实时热榜，上游返回400 data_inspection_failed；旧Gateway统一误报参数不支持。相同模型的无热榜请求成功，精确加入真实热榜可复现审核错误。
- 修复提交0026265：分类为content_filter，仅当存在自动热榜时移除currentHotspots重试一次；不改用户输入、历史、偏好和碎片，仍被拒绝则明确提示审核失败。重试受原超时预算约束，成功降级时明确说明这些是创作建议。上游错误正文不写入对外响应和业务事件。
- Python受影响范围76项、Node关联12项通过。发布前已通知用户并完成 /opt/youai/backups/20261019T080712Z-platform-4e85b84 全量备份（2.1GB），四个归档SHA256、解压及数据库恢复清单通过。
- 已发布platform-0026265；25模块检查通过。全新常驻HTTP聊天返回3个主题；首页真实重试触发热榜降级，显示创作建议且不再出现红色错误，截图目视通过（本机Temp/youai-ta-retry.png）。health200、容器healthy、重启0，无近期Traceback。没有上传体验版。
- 定位时仅暂存账号与请求业务参数，不含令牌/请求头，临时请求文件已清理。累计158，下一次159，160完整测试。此修复属于158，补充文档提交不另计数。
- 如需回滚本次TA修复：bash /opt/youai/releases/remote-release.sh switch platform-4e85b84。
