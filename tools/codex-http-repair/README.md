# Codex HTTP 连接修复工具包

此工具针对模型 WebSocket 连接在代理下失败、随后重试的情况，将模型连接配置为 HTTP(S)/SSE。它不是代理软件，不把 HTTPS 改为明文 HTTP，也不承诺修复所有“重连 5/5”：官方配置中 SSE 中断的默认重试次数同样是 5。

## 安装和使用

将 `dist/codex-http-repair-1.0.0.mcpb` 导入支持 MCPB 的桌面客户端。运行环境需要 Node.js 20+，且 `codex` 在 PATH 中。如果客户端找不到 Codex，可在 MCP 启动环境设置 `CODEX_HTTP_REPAIR_CODEX` 为 codex 可执行文件绝对路径。工具在本地通过 stdio 工作，不监听网络端口。

依次调用：

1. `codex_connection_inspect`：只读检查，返回修复预览及 `fingerprint`。
2. `codex_connection_repair`：传入上一步 `fingerprint`，验证本机 Codex 能加载候选配置后再备份和应用。保存返回的 `backupId`。
3. 完全退出并重启 Codex，新建会话验证连接。当前已运行会话不会即时改变。
4. 如需撤回，调用 `codex_connection_restore` 并传入 `backupId`。若修复后配置又有改动，工具拒绝覆盖，应手动合并备份。

不支持 MCPB 的客户端可解压包，将 MCP 命令配置为 `node /绝对路径/server.cjs`。安装本身不会修改配置，必须调用修复工具。YOUAI 小程序中的工具包列表目前只保存元数据，不能执行本地修复工具。

## 修改范围与兼容性

目标仅为 `CODEX_HOME/config.toml`，未设置时为用户目录下 `.codex/config.toml`。不会读取 `auth.json`、上传配置、修改模型/推理强度/权限、降低重试次数或自动重启客户端。

本机 `codex-cli 0.162.0-alpha.17.2` 禁止覆盖内置 `openai`，且 `responses_websockets` / `responses_websockets_v2` 已移除，不能靠这些旧功能开关修复。默认 OpenAI 使用名为 `codex-http-repair` 的自定义 provider，`name = "OpenAI"`、`requires_openai_auth = true`，沿用登录及认证方式，设置 `supports_websockets = false`。保留显式 `openai_base_url` 及组织/项目环境变量映射。自定义 Responses provider 则只更新它的 WebSocket 标记，保持地址、认证与其他字段。

存在 profile 连接覆盖、冲突名称、无效 TOML、不支持的 provider 或无法安全保留的特殊 TOML 布局时，返回原因并不修改。工具保留其他配置及注释，修改后对完整 TOML 语义进行比对；写入采用临时文件替换、指纹检查与工具间互斥。外部编辑器不遵守工具锁，因此仍应避免同时编辑配置。运行中的客户端、命令行或托管设置可能覆盖用户配置；模型请求之外的 MCP/应用通信不受此设置控制。

备份保存在 `.codex/http-repair-backups/<backupId>.json`，包含原始配置（可能含原有敏感字段），请与用户配置同等保护，勿上传或提交。Windows 权限继承自用户目录；POSIX 备份使用 0600。配置被后续修改时拒绝自动恢复。

## 开发、测试及打包

在此目录运行 `pnpm install --frozen-lockfile --ignore-scripts`，然后 `node build.mjs`。构建将运行时依赖打入单个 `server.cjs`，用官方 MCPB CLI 验证清单并生成包，安装时不需要联网下载依赖。源码命令行入口：`node cli.mjs inspect`、`node cli.mjs repair <fingerprint>`、`node cli.mjs restore <backupId>`。

仓库根目录执行 `node --test tests/codex-http-repair.test.js`。测试只用临时配置，不会修改真实用户配置；含备份恢复、冲突保护、凭据不泄露、MCP stdio 集成。实际模型重连改善需重启后的真实会话验证，配置加载成功不等于网络验证通过。

依据：

- https://learn.chatgpt.com/docs/config-file/config-reference （supports_websockets、SSE 重试次数）
- https://github.com/openai/codex/blob/main/codex-rs/model-provider-info/src/lib.rs （provider 默认认证和地址选择；上游 main 可能变化）
- https://github.com/openai/codex/blob/main/codex-rs/core/src/client.rs （模型 WebSocket 能力检查）
- https://github.com/anthropics/mcpb/blob/main/MANIFEST.md （MCPB 0.3 清单）
