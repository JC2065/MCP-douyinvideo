# MCP 包管理与流程能力路由

日期：2026-10-16。状态：管理板块、能力匹配交互与接口设计；尚未开发真实MCP客户端、打包分发器或运行沙箱，没有安装或调用示例包。入口为[中台设计预览](../web/admin-workflows/index.html)的“MCP 包管理”，承接[共享流程方案](workflow-platform-design.md)。原六业务板块不变，新增一个公共能力管理板块。

## 设计目标与职责

用户表达“读取这个视频” → Skill解析需求为video.read → 能力路由器匹配已批准工具包 → 校验本人资产权限/输入/版本/预算 → MCP网关调用固定工具 → 验证结构化输出 → 结果作为流程步骤产物保存。适配复杂工程的参数、重试、格式校验和错误分类被收进包内，流程不重复拼装底层命令。

Skill负责理解和规划；MCP工具负责确定能力边界内的执行；中台负责目录、发布、路由、权限和审计。MCP协议是工具发现与调用协议，不能单独保证工程正确，也不提供通用的包安装格式。本项目的“包”是YOUAI管理的MCP Server及其版本、依赖、运行配置和能力契约的封装。manifest和capability_id是YOUAI扩展，不声称是MCP标准字段。

官方协议依据：[工具与输入输出Schema](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx)、[协议与JSON Schema](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/index.mdx)。按实际实现支持的版本协商；工具自述和annotations只是提示，不能代替网关的权限与可信审核。

## 中台板块

| 区域 | 内容 |
| --- | --- |
| 包目录 | 包ID、发布者、来源、版本、摘要、能力、支持媒体类型、输入输出Schema、依赖、实际安装状态 |
| 工具详情 | tools/list发现结果、命名空间、超时、资源限额、是否付费/写入/外发、credential_ref与权限范围 |
| 测试与准入 | 隔离测试数据、契约测试、异常/超时/重试验证、依赖锁与摘要、审核及启用范围 |
| 能力路由 | capability_id到批准包/固定工具的映射，平台与文件类型限制、优先级、预算、显式降级方案 |
| 版本发布 | 草案 → 测试 → 批准 → 小范围启用 → 生效 → 停用/回滚；更新不影响已有实例的锁定版本 |
| 调用观察 | 项目/步骤/调用ID、脱敏输入引用、耗时、费用、结果资产、错误分类与归档回执 |

普通用户不需要挑包或安装；他们选择流程与授权范围。管理员负责准入、部署和维护。个人MCP连接如后续开放，需单独的租户级授权流程，不能继承平台管理员凭据。

## 首批候选封装

| 规划包 | 工具与能力 | 输入 → 输出 | 复用基础与范围 |
| --- | --- | --- | --- |
| youai-video-reader | read_video / video.read | video_asset → video-evidence.v1 | 封装现有元信息、代表帧/音轨提取；不把采样当作完整视频理解 |
| youai-transcript | transcribe_video / video.transcribe | video_asset → transcript.v1 | 封装现有语音转写，输出时间戳、语言、置信度和失败项 |
| youai-feishu-archive | archive_assets / archive.feishu | archive_event → archive-receipt.v1 | 封装现有归档worker的字段映射/幂等/回执；只有Outbox提交后可执行 |

后续候选：素材采集、封面/关键帧、媒体编排、标题/脚本生成。按依赖与用途拆成稳定包；不要把每个提示词都包装成新MCP，也不引入未经测试的第三方包代替已有稳定能力。

“读取视频”进一步区分metadata、keyframes、audio、transcript、vision_analysis。用户只要时长时调用元信息即可；需要语音内容才调用转写，需要理解画面才调用视觉模型。Skill不能仅因为名字含video就认为工具覆盖全部需求。复合read_video工具可在一次调用中组织所需子能力，但回执必须逐项标明成功、不可用、证据范围和费用。

## 匹配与调用策略

1. 只从注册并批准的包匹配，基于capability_id、input_schema、output_contract及工具真实版本，不依赖模糊名称相似度。
2. 服务端验证owner_user_id和asset_id的归属，再签发短期、限定资产范围的调用凭证；不允许模型提供任意本机路径或内网URL。远程视频先进入已有受控采集链路，校验平台、大小、时长、重定向与网络目的地。
3. 先过滤未安装/未批准/停用/不健康/协议不兼容/权限不足/预算不足的包，再按管理员优先级、支持范围和成本选取。预览模型中的approved/healthy为明确的设计样例，不是生产检测结果。
4. 选定后锁定package_id + version + digest + tool_name + schema_hash；tools/list变化时重新校验，不能在用户确认后偷偷改变工具含义。MCP工具名使用包命名空间，处理不同Server同名工具。
5. 已批准、只读且在用户既有授权与预算内的调用可自动执行，避免反复弹窗。新增外发、付费、写入、删除等动作遵循流程内的明确确认；不把包自述readOnlyHint当成可靠授权依据。
6. 无匹配显示原因和补充素材/申请能力入口；可显式使用已批准且输出契约相同的备用包。切换执行语义、外发范围或费用时重新确认，不能把空文本或错误结果标为成功。
7. 使用tools/call等实现所协商协议支持的调用；协议错误与业务isError分开分类；结果必须通过outputSchema/本地契约验证。工具返回的文本属于不可信数据，不能改变系统权限或触发下一次越权调用。
8. 运行结果记录call_id、run_id、step_id、package_lock、input_asset_refs、output_asset_refs、coverage、warnings、usage和状态。参数只存必要脱敏信息，凭据不进入Skill对话、日志或飞书。

## 示例包清单（YOUAI扩展，待实现）

```json
{
  "package_id": "youai-video-reader",
  "version": "1.0.0",
  "integrity": {"sha256": "由构建产物计算，发布前必填"},
  "transport": "stdio",
  "runtime_ref": "受控镜像摘要，发布前必填",
  "tools": [{
    "name": "read_video",
    "capability_id": "video.read",
    "input_contract": "video-asset-ref.v1",
    "output_contract": "video-evidence.v1",
    "permissions": ["asset:read"],
    "timeout_seconds": 120,
    "max_input_bytes": 209715200,
    "max_duration_seconds": 600
  }]
}
```

实际inputSchema由工具发现和准入测试保存，至少包含asset_id和所需outputs枚举，禁止additionalProperties越界。输出video-evidence.v1包含asset_id、metadata、keyframe_asset_refs、audio_asset_ref、transcript_ref、coverage和warnings；每项可为partial/unavailable，失败不能伪造“看过整段”。素材本体尽量经受控存储读取，不反复作为大Base64塞入上下文。

## 部署与生命周期

国内服务器运行YOUAI MCP Gateway，部署侧运行本地stdio Server或调用经批准的远程HTTP Server。小程序只请求业务API，不直连MCP Server、不拿工具密钥，也不下载执行代码。网页中台与小程序仍共用已批准流程能力目录，新增原生能力按客户端发布规则处理。

本地包用隔离进程/容器、固定镜像摘要、只读基础文件系统、限定挂载及CPU/内存/时长上限。网络出口按包配置；远程Server使用受限凭据和协议授权，禁止直接把用户或管理员令牌透传给不匹配的服务。credentials_ref在调用侧解析，包清单不保存密钥。

全局停用阻止新的调用；在途任务可等待结束或按可取消能力停止，状态不能伪装完成。旧实例保留原版本锁和资产来源。回滚只影响后续解析；已产出数据不抹除。无法继续提供旧版本时明确标记blocked，用户可确认迁移或重试，不自动换新版本继续。

幂等使用run_id:step_id:attempt:tool_id。下载/只读调用在明确无副作用时可有限退避重试；付费生成、飞书写入等动作先查已有回执。超时可能已执行成功，状态unknown需核对，不能直接再次调用。包升级须通过同一套成功、错误、部分成功、超时、撤销、协议变更和跨账号隔离测试。

## 接口与数据设计

| 拟新增接口 | 用途 |
| --- | --- |
| GET /admin/mcp/packages | 目录、实际安装版本、准入及健康状态 |
| POST /admin/mcp/packages/drafts | 登记受控来源和manifest，expectedRevision冲突保护，不立即执行安装脚本 |
| POST /admin/mcp/packages/:id/test | 在隔离环境运行契约测试，不挂生产数据或凭据 |
| POST /admin/mcp/packages/:id/approve | 管理员确认依赖、外发、费用与验证结果后批准固定版本 |
| POST /admin/mcp/packages/:id/activate | 启用/停用指定版本及范围，记录审计 |
| POST /workflow-capabilities/resolve | 服务端解析本人流程步骤能力，返回候选或blocked原因 |
| POST /workflow-runs/:run/steps/:step/calls | 校验确认快照后排队调用，要求Idempotency-Key |
| GET /workflow-tool-calls/:id | 本人查询状态与结构化结果，不暴露凭据 |

建议实体：mcp_packages、mcp_package_versions、mcp_tools、capability_routes、mcp_connections、workflow_tool_calls。连接授权按租户/账号范围隔离；包版本和Schema不可变，运行表保存锁定快照、审批来源、幂等键、费用与输出资产。飞书只接归档事件与脱敏运行回执，不接密钥、完整对话和未经授权私有素材。

## 实施与验收顺序

第一步把现有视频元信息/代表帧读取封装为真实只读MCP Server，完成标准客户端握手、工具发现、调用和Schema测试。第二步接注册表、固定版本部署、网关和一条video.read路由，再把现有作品拆解的证据节点接上。第三步接转写和飞书包，最后开放更多供应商与个人流程自动匹配。

验收：授权资产成功读取、他人资产404、未知输出明确不可用、任意路径/内网地址拒绝、包停用阻断新调用、版本升级不改旧任务、工具Schema变化触发阻断、超时核对不重复付费、错误不进入下游生成、飞书断线恢复不重复写入。当前交互预览只能验证匹配规则与页面行为，不作为上述真实MCP执行验收。
