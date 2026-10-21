# YOUAI Liquid Glass 设计

来源：安装并使用 https://github.com/anthropics/skills/tree/main/skills/frontend-design 。安装目录为用户技能目录中的 frontend-design。
设计参考：https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/ 。这是 WXSS 视觉近似，不是原生 iOS 实时折射。

## 设计方案

- 冰蓝底色 #edf3fa、阅读白 #ffffff、正文墨色 #182438、辅助灰 #56657a、操作蓝 #075dcc。
- 使用系统字体，中文优先苹方；正文左对齐，标题 44rpx，段落 28rpx，辅助信息 22rpx。
- 保留紧凑首页，直接呈现灵感记录；玻璃导航悬浮于内容之上。正文卡片高不透明，避免长文难读。
- 圆角按层次区分：输入 26rpx、正文 34rpx、捕捉灵感 40rpx、控制项胶囊形。

```text
YOUAI                   品牌说明
当前页面提示              演示版
我的记录                 辅助信息
╭ 输入想法                    ╮
╰ 私人笔记           记下来    ╯
记录 / 热点 / 内容卡片
     ( 灵感 创作 学习 任务 我的 )
                 安全区域
```

审查：不添加大幅宣传区，不让每张正文卡片模糊；视觉重点集中于灵感输入区与悬浮导航。覆盖五个主页面、编辑表单、设置、案例拆解。未新增字体、图片或运行时依赖。

兼容：无 backdrop-filter 支持时保留 94% 不透明的导航底色；支持时启用模糊。尊重减少动态与减少透明度偏好。底部内容间距包含安全区域，按钮触达高度至少 88rpx。

验证：`node --test tests/*.test.js`。微信工具可用时运行 `node scripts/devtools-smoke.cjs`；真机需另查不同基础库对 backdrop-filter 的支持及视频原生层叠表现。

## 图标

使用原创圆角线性图标：灯泡（灵感）、方框铅笔（创作）、翻开的书（学习）、公文包（任务）、人物（我的）。统一 28×28 画布和圆头圆角笔画，常态灰蓝，选中态蓝色并略加粗。新增、生成、返回及个人菜单箭头同属一套图标，保留文字标签。

源文件与透明 PNG 放在 `assets/icons`；小程序使用 3 倍分辨率 PNG，避免依赖系统字形或 SVG 渲染支持。`scripts/generate-icons.cjs` 可通过 Playwright 和本机 Edge 重建，外部安装可由 `YOUAI_PLAYWRIGHT_MODULE` 指定；小程序运行无需新依赖。

## 紧凑工作台排版

配色和图标资产保持不变，布局改为适合手机的紧凑工作台。页面边距 22rpx，卡片内边距 20rpx、间距 12rpx；标题 34rpx，正文 25–26rpx。学习案例使用左侧缩略图、右侧信息的列表；表单、创作入口、设置及拆解页统一缩减段落间距。主要按钮仍至少 88rpx，导航图标仍为 48rpx，安全区域保留。

视频采访页缩减说明区与问题卡间距，方案摘要和生成操作优先出现在手机首屏。不是将桌面后台多列表格直接塞入小屏。

验证：`node --test tests/*.test.js`；开发者工具自动化连接后运行 `node scripts/compact-layout-smoke.cjs`，检查五个页面、案例列表和采访页操作位置，并保存截图。
