# 贡献指南

感谢你愿意参与有AI（YOUAI）！无论是报告问题、改进文档还是提交代码，我们都非常欢迎。

## 开始之前

- 先读 [项目地图](docs/PROJECT-MAP.md)：现状、目录、测试与发布、常见坑都在这一页。
- 较大的改动（新功能、改接口、改数据结构）请先开一个 Issue 讨论方向，避免白做。
- 参与即表示你同意遵守 [行为准则](CODE_OF_CONDUCT.md)。

## 开发环境

| 部分 | 要求 |
| --- | --- |
| 小程序 | [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)，原生 WXML/WXSS/JS，无构建步骤 |
| Node 测试 | Node.js 20+，`node --test` |
| 后端 | Python 3.12 + ffmpeg，依赖见 `scripts/Dockerfile.video` |

```bash
git clone https://github.com/JC2065/MCP-douyinvideo.git
cd MCP-douyinvideo
node --test tests/*.test.js
cd scripts && python3 -m unittest test-creation-board test-mcp-gateway
```

本地启动后端与连接方式见 [README · 快速开始](README.md#-快速开始)，环境变量见 [`.env.example`](.env.example)。

## 提交流程

1. Fork 本仓库，从 `main` 拉出分支：`feat/xxx`、`fix/xxx`、`docs/xxx`。
2. 改动尽量小而聚焦，一个 PR 解决一件事。
3. **为改动补测试**：页面逻辑与文案放 `tests/*.test.js`，后端放 `scripts/test-*.py`。
4. 本地跑通受影响的测试，确认 CI 通过。
5. 提交信息写清「改了什么、为什么」，中英文均可，例如：`fix: 图文作品不再显示 0–3 秒时间轴`。
6. 发起 PR 并按模板填写；维护者会尽快审阅。

## 代码约定

- **页面**：`pages/*/index.js` 里的 `require` 写在文件顶层（写在对象展开里会被开发者工具的依赖分析剔除，导致白屏）；每个页面必须有 `index.json`。
- **后端**：`scripts/video-server.py` 按文件名加载同目录模块；新增模块要同时加进 `scripts/Dockerfile.video` 的 `COPY`（有测试守护）。
- **用户可见文案**统一写「有AI」；`YOUAI1:` 口令前缀、请求头等内部标识不改。
- **隐私**：改动隐私相关文案时，同时更新 `docs/privacy-creation-board.md`（有逐字一致性测试）。

## 安全红线

- 不要提交任何 API Key、令牌、密码、数据库或 `.env` 文件。
- 用户自带的模型 Key 不存储、不写日志；评论者身份不保存。
- 发现漏洞请按 [SECURITY.md](SECURITY.md) 私下报告，不要开公开 Issue。

## 许可

提交贡献即表示你同意你的贡献以 [MIT 许可证](LICENSE) 发布。
