# 前端页面、事件与状态索引

自动从当前 WXML 提取；共享 include 模板同样展开。事件含义请结合 JS 与主交接文档，不把存在绑定等同于业务上线。

2026-10-15拆解迭代补充：pages/settings/index新增素材选择、多目标、模板预览、DIY编辑/排序/删除/保存/设默认；共享study页新增analysisGoal/analysisMaterial并将快照带入草稿；pages/video/index新增templateChange/materialChange/analysisGoal/analysisSettings与分镜失效门禁。完整新流程见analysis-template-workflow.md，下面冻结交接索引中的旧设置说明以该文档为准。

## pages/admin/index

管理员独立登录 → 总览/工具/热点/版本/审计。工具开关先显示差异，再确认发布；回滚需确认。热点详情显示pending/ready/empty/error/expired，并可手动刷新/重试。网络失败和会话过期显示反馈；返回页面清除内存管理会话，不沿用微信身份。入口位于“我的 → 管理中台”。本页为新迭代新增，冻结设计交接基线仍保持原样。

## pages/main/index

源码：`pages/main/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`back → close`；`change → field`；`confirm → hotspotSend`；`input → commandField`；`input → field`；`input → hotspotInput`；`tap → action`；`tap → aiConfig`；`tap → applyCase`；`tap → calendarMove`；`tap → calendarSelect`；`tap → calendarToday`；`tap → caseDetail`；`tap → commandExample`；`tap → copyCommand`；`tap → copyVideoSource`；`tap → createDiscoveredHotspot`；`tap → dailyFormSwitch`；`tap → discoverHotspots`；`tap → editor`；`tap → favorite`；`tap → favs`；`tap → filter`；`tap → generate`；`tap → hotspotPlatform`；`tap → hotspotReset`；`tap → hotspotSend`；`tap → hotspotSuggest`；`tap → idea`；`tap → inspire`；`tap → learnForDraft`；`tap → newTask`；`tap → open`；`tap → parseCommand`；`tap → preferences`；`tap → publish`；`tap → recordMode`；`tap → reset`；`tap → reviewWork`；`tap → saveDiscoveredHotspot`；`tap → saveProfile`；`tap → saveReview`；`tap → saveWork`；`tap → settings`；`tap → switchRole`；`tap → tab`；`tap → taskDetail`；`tap → toggleAccountMore`；`tap → tool`；`tap → toolEntry`；`tap → toolInterfaces`；`tap → useCommand`；`tap → videoAssets`；`tap → videoStudio`

条件状态：

- `{{!hotspotMessages.length}}`
- `{{!hotspotVisible.length}}`
- `{{!recordCount}}`
- `{{!state.earnings.length}}`
- `{{!state.works.length}}`
- `{{!view&&tab!=='我的'&&tab!=='灵感'}}`
- `{{!view}}`
- `{{(filter==='全部'||filter===item.tag)&&(!onlyFav||item.favorited)}}`
- `{{accountMore}}`
- `{{calendar.records.length}}`
- `{{caseTitle}}`
- `{{commandPreview}}`
- `{{daily.duration}}`
- `{{daily.poster}}`
- `{{daily}}`
- `{{dayFeed.favorites.length}}`
- `{{dayFeed.works.length}}`
- `{{hotspotError}}`
- `{{hotspotMessages.length}}`
- `{{hotspotMode==='chat'}}`
- `{{hotspotMode==='rank'}}`
- `{{item.caseTitle}}`
- `{{item.duration}}`
- `{{item.favorited}}`
- `{{item.poster}}`
- `{{item.source}}`
- `{{item.status==='已完成'}}`
- `{{item.today}}`
- `{{onlyFav&&!state.favorites.length}}`
- `{{recordCount||recordMode==='calendar'}}`
- `{{recordCount}}`
- `{{recordMode==='calendar'}}`
- `{{recordMode==='favorites'}}`
- `{{recordMode==='works'}}`
- `{{selected.source}}`
- `{{selected.status==='已完成'}}`
- `{{selected.url}}`
- `{{source}}`
- `{{state.role==='个人'&&(selected.status==='制作中'||selected.status==='待修改')}}`
- `{{state.role==='个人'&&selected.status==='招募中'}}`
- `{{state.role==='商家'&&selected.status==='待选人'}}`
- `{{state.role==='商家'&&selected.status==='待验收'}}`
- `{{state.role==='商家'}}`
- `{{tab!=='我的'||view}}`
- `{{tab==='任务'}}`
- `{{tab==='创作'}}`
- `{{tab==='学习'}}`
- `{{tab==='我的'}}`
- `{{tab==='灵感'}}`
- `{{tab===item}}`
- `{{view==='about'}}`
- `{{view==='case'}}`
- `{{view==='casePicker'}}`
- `{{view==='command'}}`
- `{{view==='earnings'}}`
- `{{view==='editor'}}`
- `{{view==='profile'}}`
- `{{view==='publish'}}`
- `{{view==='review'}}`
- `{{view==='task'}}`

## pages/video/index

源码：`pages/video/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`blur → input`；`change → durationChange`；`change → generationToggle`；`change → togglePreferences`；`error → playbackError`；`input → constraintInput`；`input → input`；`input → shotInput`；`input → themeInput`；`submit → interview`；`tap → adjustDirection`；`tap → answer`；`tap → approveStoryboard`；`tap → assetFeedback`；`tap → backToDirection`；`tap → edit`；`tap → generationOption`；`tap → permissions`；`tap → refreshArchive`；`tap → reopen`；`tap → restoreArchive`；`tap → retryAnalysis`；`tap → retryArchive`；`tap → retryReference`；`tap → reviewStoryboard`；`tap → save`；`tap → selectFrameSampling`；`tap → selectSource`；`tap → smartDuration`；`tap → toggleAssetSection`；`tap → toggleAssets`

条件状态：

- `{{!archiveState||archiveState.status==='failed'||archiveState.status==='not_queued'}}`
- `{{analysisStatus==='done'}}`
- `{{answers.visualStyle==='AI 生成画面'}}`
- `{{archiveState.status==='archived'}}`
- `{{assetManifest.analysis.previewFrames.length}}`
- `{{assetManifest.analysis.summary}}`
- `{{assetManifest.generation.provider==='qianwen'&&assetManifest.generation.settings.resolution}}`
- `{{assetManifest.source.previewUrl}}`
- `{{assetSection==='analysis'}}`
- `{{assetSection==='generation'}}`
- `{{assetSection==='lineage'}}`
- `{{assetSection==='source'}}`
- `{{assetSection==='storyboard'}}`
- `{{error}}`
- `{{history.length}}`
- `{{item.key==='referenceMode'}}`
- `{{referenceDetail}}`
- `{{referenceElapsed}}`
- `{{referenceStatus==='checking'}}`
- `{{referenceStep}}`
- `{{showAssets&&assetManifest}}`
- `{{showAssets}}`
- `{{sourceType==='command'}}`
- `{{sourceType==='douyin'&&analysisStatus!=='idle'}}`
- `{{sourceType==='douyin'&&referenceStatus!=='idle'}}`
- `{{sourceType==='douyin'&&reference}}`
- `{{sourceType==='douyin'}}`
- `{{sourceType==='idea'}}`
- `{{stage==='generating'}}`
- `{{stage==='idea'}}`
- `{{stage==='interview'}}`
- `{{stage==='result'}}`
- `{{stage==='storyboard'}}`

## pages/video-assets/index

源码：`pages/video-assets/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`tap → open`；`tap → remove`

条件状态：

- `{{empty}}`

## pages/hotspots/index

源码：`pages/hotspots/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`confirm → send`；`input → input`；`tap → close`；`tap → create`；`tap → detail`；`tap → mode`；`tap → noop`；`tap → platform`；`tap → reset`；`tap → save`；`tap → send`；`tap → suggest`

条件状态：

- `{{!messages.length}}`
- `{{!visible.length}}`
- `{{context.topic}}`
- `{{error}}`
- `{{messages.length}}`
- `{{mode==='chat'}}`
- `{{mode==='rank'}}`
- `{{reply}}`
- `{{selected}}`

## pages/settings/index

源码：`pages/settings/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`tap → clearOverrides`；`tap → mode`；`tap → select`

条件状态：

- `{{prefs.mode==='manual'&&prefs.preset===item.id}}`

## pages/preferences/index

源码：`pages/preferences/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`change → enabled`；`input → field`；`input → keywords`；`tap → add`；`tap → choose`；`tap → clearMemory`；`tap → reset`；`tap → save`；`tap → section`；`tap → switchProfile`

条件状态：

- `{{error}}`
- `{{profile}}`
- `{{section==='agent'}}`
- `{{section==='direction'}}`
- `{{section==='rhythm'}}`
- `{{section==='topics'}}`
- `{{section==='video'}}`

## pages/ai/index

源码：`pages/ai/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`change → bundleToggle`；`change → sceneToggle`；`input → bundleLinkInput`；`input → customField`；`input → keyInput`；`input → scenePrompt`；`tap → addBundleLink`；`tap → addCustom`；`tap → chooseDefault`；`tap → removeBundle`；`tap → removeCustom`；`tap → reset`；`tap → save`；`tap → sceneBundle`；`tap → sceneModel`；`tap → uploadBundle`

条件状态：

- `{{!state.bundles.length}}`
- `{{error}}`
- `{{item.baseUrl!==undefined&&item.id[0]==='c'}}`
- `{{item.cfg.enabled}}`
- `{{state.bundles.length}}`
- `{{state.defaultModel===item.id}}`

## pages/tool-interfaces/index

源码：`pages/tool-interfaces/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`input → field`；`submit → save`；`tap → auth`；`tap → check`；`tap → clear`；`tap → method`；`tap → select`；`tap → source`

条件状态：

- `{{allowCustom}}`
- `{{error}}`
- `{{form.auth==='bearer'}}`
- `{{selected==='download'}}`
- `{{source==='public'}}`

## pages/replica/index

源码：`pages/replica/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。用户自备 Key 的 1:1 复刻，见 `docs/replica-byok.md`。

事件：`change → consentChange`；`change → providerChange`；`change → rememberChange`；`input → keyInput`；`tap → checkKey`；`tap → choosePhoto`；`tap → forgetKey`；`tap → modeChange`；`tap → openGuide`；`tap → openJob`；`tap → save`；`tap → submit`

条件状态：

- `{{!sha}}`
- `{{keyStatus}}`
- `{{photoPath}}`
- `{{error}}`
- `{{job}}`
- `{{job.estimateYuan}}`
- `{{videoUrl}}`
- `{{jobs.length}}`

## pages/board-work/index

源码：`pages/board-work/index.js` / `.wxml` / `.wxss`。作品发布包、链接/截图回传、奖励与复盘卡（创作板块 M10–M11）。

事件：`input → linkInput`；`input → valueInput`；`tap → chooseScreenshot`；`tap → copyPublish`；`tap → dayPick`；`tap → openWork`；`tap → saveLink`；`tap → saveMetrics`；`tap → subscribe`

条件状态：

- `{{!id}}`
- `{{!works.length}}`
- `{{work}}`
- `{{work.cover}}`
- `{{work.review}}`
- `{{work.review.interactionPercent!==null}}`
- `{{work.review.originalInteractionPerFollower!==null}}`
- `{{notice}}`
- `{{error}}`

## pages/board-plans/index

源码：`pages/board-plans/index.js` / `.wxml` / `.wxss`。拆解方案：内置/我的、对话生成、样片归纳、复制编辑与版本回退（创作板块 M5–M6）。

事件：`change → editPick`；`input → chatInput`；`input → editField`；`input → editName`；`input → linksInput`；`tap → addField`；`tap → cancelEdit`；`tap → chatDraft`；`tap → edit`；`tap → fork`；`tap → induce`；`tap → remove`；`tap → removeField`；`tap → rollback`；`tap → saveDraft`；`tap → saveEdit`；`tap → tab`

条件状态：

- `{{editing}}`
- `{{tab==='new'}}`
- `{{draft}}`
- `{{job}}`
- `{{field.evidence}}`
- `{{tab==='mine'}}`
- `{{tab==='mine'&&!mine.length}}`
- `{{error}}`

## pages/creation-tool/index

源码：`pages/creation-tool/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`change → font`；`change → speed`；`input → input`；`input → scriptInput`；`tap → copyText`；`tap → mirror`；`tap → resetPrompt`；`tap → run`；`tap → saveAsset`；`tap → toggleAudio`；`tap → togglePlay`

条件状态：

- `{{error}}`
- `{{result.kind==='audio'}}`
- `{{result.kind==='image'}}`
- `{{result.kind==='text'}}`
- `{{result.kind==='video'}}`
- `{{result}}`
- `{{running}}`
- `{{tool!=='teleprompter'}}`
- `{{tool==='eraser'}}`

## case-study/index

源码：`case-study/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`change → chooseAnalysis`；`error → failed`；`input → theme`；`tap → check`；`tap → create`；`tap → favorite`；`tap → note`；`tap → retry`；`tap → section`；`tap → seek`；`tap → settings`；`tap → source`；`tap → toggleDetails`；`tap → toggleSupplements`；`timeupdate → time`

条件状态：

- `{{analysis.supplements.length}}`
- `{{analysis}}`
- `{{detailsOpen}}`
- `{{error}}`
- `{{item.status==='未观察到'}}`
- `{{loading}}`
- `{{section==='看懂作品'}}`
- `{{section==='跟着练习'}}`
- `{{section==='逐段拆解'}}`
- `{{supplementsOpen}}`
- `{{videoSrc}}`

## study-201/index

源码：`study-201/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`change → chooseAnalysis`；`error → failed`；`input → theme`；`tap → check`；`tap → create`；`tap → favorite`；`tap → note`；`tap → retry`；`tap → section`；`tap → seek`；`tap → settings`；`tap → source`；`tap → toggleDetails`；`tap → toggleSupplements`；`timeupdate → time`

条件状态：

- `{{analysis.supplements.length}}`
- `{{analysis}}`
- `{{detailsOpen}}`
- `{{error}}`
- `{{item.status==='未观察到'}}`
- `{{loading}}`
- `{{section==='看懂作品'}}`
- `{{section==='跟着练习'}}`
- `{{section==='逐段拆解'}}`
- `{{supplementsOpen}}`
- `{{videoSrc}}`

## study-202/index

源码：`study-202/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`change → chooseAnalysis`；`error → failed`；`input → theme`；`tap → check`；`tap → create`；`tap → favorite`；`tap → note`；`tap → retry`；`tap → section`；`tap → seek`；`tap → settings`；`tap → source`；`tap → toggleDetails`；`tap → toggleSupplements`；`timeupdate → time`

条件状态：

- `{{analysis.supplements.length}}`
- `{{analysis}}`
- `{{detailsOpen}}`
- `{{error}}`
- `{{item.status==='未观察到'}}`
- `{{loading}}`
- `{{section==='看懂作品'}}`
- `{{section==='跟着练习'}}`
- `{{section==='逐段拆解'}}`
- `{{supplementsOpen}}`
- `{{videoSrc}}`

## study-203/index

源码：`study-203/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`change → chooseAnalysis`；`error → failed`；`input → theme`；`tap → check`；`tap → create`；`tap → favorite`；`tap → note`；`tap → retry`；`tap → section`；`tap → seek`；`tap → settings`；`tap → source`；`tap → toggleDetails`；`tap → toggleSupplements`；`timeupdate → time`

条件状态：

- `{{analysis.supplements.length}}`
- `{{analysis}}`
- `{{detailsOpen}}`
- `{{error}}`
- `{{item.status==='未观察到'}}`
- `{{loading}}`
- `{{section==='看懂作品'}}`
- `{{section==='跟着练习'}}`
- `{{section==='逐段拆解'}}`
- `{{supplementsOpen}}`
- `{{videoSrc}}`

## study-204/index

源码：`study-204/index.js` / `.wxml` / `.wxss`（部分样式由全局提供）。

事件：`change → chooseAnalysis`；`error → failed`；`input → theme`；`tap → check`；`tap → create`；`tap → favorite`；`tap → note`；`tap → retry`；`tap → section`；`tap → seek`；`tap → settings`；`tap → source`；`tap → toggleDetails`；`tap → toggleSupplements`；`timeupdate → time`

条件状态：

- `{{analysis.supplements.length}}`
- `{{analysis}}`
- `{{detailsOpen}}`
- `{{error}}`
- `{{item.status==='未观察到'}}`
- `{{loading}}`
- `{{section==='看懂作品'}}`
- `{{section==='跟着练习'}}`
- `{{section==='逐段拆解'}}`
- `{{supplementsOpen}}`
- `{{videoSrc}}`


### 账号模板同步状态（累计78）

拆解工作台、案例详情和参考视频入口确认微信身份后加载模板；工作台展示同步中、已同步、网络失败、本机修改、版本冲突及恢复备份入口。失败不丢修改，换账号独立缓存；未保存草稿不上传。身份确认期间暂停模板编辑与参考方案提交，防止使用前一账号数据。
## pages/analysis-records/index

2026-10-16补充：我的拆解记录，按账号读取本机最近30条；查看已保存拆解的可复用方法与原始分享内容。尚未跨设备同步。入口位于拆学工作台与视频拆解页；onShow刷新，open展开详情、close收起。覆盖无记录、读取失败、记录详情与账号切换后清空旧详情；使用app-navigation返回上一页。

## pages/idea-box/index

源码：`pages/idea-box/index.js` / `.wxml` / `.wxss`。灵感碎片箱：未用/已用/全部筛选；文字、链接、截图、语音碎片；AI 轻反馈与标签；和 TA 聊这个、拆这个链接、做成视频、标为已用、删除（docs/idea-box-plan.md）。

事件：`tap → pick`；`tap → chat`；`tap → breakdown`；`tap → video`；`tap → mark`；`tap → remove`；`tap → preview`；`tap → toggle`；`tap → login`

条件状态：
- `{{!loggedIn}}`
- `{{error}}`
- `{{!loading&&!rows.length&&!error}}`
- `{{item.image}}`
- `{{item.note}}`
- `{{item.kind==='link'&&item.platform==='douyin'}}`
