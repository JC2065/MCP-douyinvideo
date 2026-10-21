# 更新日志

本项目的重要变更记录在此。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

## [0.1.0] - 2026-10-22

首次公开发布（代码快照，完整开发过程见 [docs/test-batches.md](docs/test-batches.md) 与 [docs/DEV-LOG.md](docs/DEV-LOG.md)）。

### 新增

- **爆款拆解链路**：秒级快看（`/references/peek`）、深度解析（关键帧、OCR、语音转写、热评）、「我看到的是」确认与纠错、按拆解方案的超级拆解。
- **创作产出**：文字作品（逐句改写、发布正文、标题、封面大字、话题，相似度提示）、创作包与提词器、套版成片、裂变 3 条、1:1 复刻（自带 Key）。
- **方法卡复用**：按类目沉淀可学方法，生成时优先参考同类高频方法，数据回流后打分。
- **对照原视频**：生成结果旁附 360p 压缩原片（`/board/preview`）。
- **远程 MCP**：`/mcp` 网关（访问令牌、每日额度、独立 dtk 密钥），转发 dtk 自带的 8 个工具，并新增服务器托管下载工具 `download_video`。
- **额度与中台**：每用户每日新视频数、全站日预算、额度申请；管理中台。
- **长期资产**：飞书多维表格台账（发件箱异步投递）。
- **开源配套**：MIT 许可证、贡献指南、行为准则、安全策略、Issue/PR 模板与 CI。

[Unreleased]: https://github.com/JC2065/MCP-douyinvideo/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/JC2065/MCP-douyinvideo/releases/tag/v0.1.0
