# Claude → Codex 交接 · 2026-10-18

## 线上状态
- 后端：`platform-67a81d8`（增量部署，镜像含 OCR 依赖层与 Noto CJK 字体层）。健康 200；匿名 /board/*、/board-media、/admin-api/creation/*、/replica/* 均 401。
- 小程序：本轮新增页面与改动**尚未上传开发版**（需在微信开发者工具上传，版本号接 1.0.135 之后）。开发者工具在新增目录后可能报 “WXML file not found”，用“项目 → 重新打开此项目”解决。

## 本轮完成（按 docs/creation-board-plan.md）
- 1:1 复刻（用户自备 Key）：`scripts/replica.py`、`pages/replica`，见 `docs/replica-byok.md`。
- M1 使用说明框/上传原视频/平台识别；M2 快看/理解卡 type·tags·valueSources/本地 OCR；M3–M13 创作板块全部代码（`scripts/creation-board.py`、`utils/board-page.js`、`pages/video/board.wxml`、`pages/board-work`、`pages/board-plans`、中台“创作板块”页）。进度表第 11 节已勾选；测试批次第 145–147 次。
- 部署脚本：`deploy-delta.sh` 支持新增 RUN/ENV 行在线上镜像叠加；若本机部署进程在服务器构建依赖层时中断，按批次记录手动执行模块检查与 `remote-release.sh switch`。

## 待办（需要用户或下一位代理）
1. **P0 用户操作**：微信公众平台“用户隐私保护指引”按 `docs/privacy-creation-board.md` 补充；申请订阅消息模板后在中台“创作板块参数”填写模板 ID。
2. **P0** 上传小程序开发版并真机走查：粘贴链接说明框 → 快看 → 等待期问询 → 确认卡/倒计时/纠错 → 拆解卡 → 文字作品/创作包/套版成片 → 发布包 → 回传与复盘；`pages/board-plans` 新建/归纳/编辑。
3. **P1** OCR 在 2 核服务器上与转写争 CPU，长视频时为 partial；可考虑只识别画面下半区、或转写完成后再 OCR。
4. **P1** 测试账号 `claude-test` 在 board.sqlite / watch 缓存中有少量真实走查数据，可保留作样例或删除。
5. **P2** 第 150 次完整测试（`npm test`，需在装有 docker 的用户本机）；`test-video-server.py` 中 10 个 render 测试依赖字体，现镜像已有 Noto CJK（`YOUAI_VIDEO_FONT`），可在镜像内复测确认。

## 约束
- 不使用 claude-deploy 钥匙；部署前备份并征得用户同意（用户已授权 Claude 本轮连续开发与部署）。
- 提交前检查行尾（仓库 LF）；`project.config.json` 与 Claude 旧交接文档的格式改动不提交。
