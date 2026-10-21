# 三阶段中台与小程序映射设计

状态：第96次设计交付。本机中台提供可交互的三阶段演练与固定组件映射；尚未部署生产流程API、真实Skill执行器或小程序动态渲染器。演练中的简报、证据、生成结果均为明确示例，不调用AI、不扣费、不写飞书。

## 共用内容与边界

中台管理“问什么、按什么顺序、调用什么能力、输出什么、何时确认”；小程序负责素材选择、输入、编辑、确认、进度和结果。映射的是同一份流程定义与服务端运行状态，不把管理员网页作为普通用户界面。网页用户工作台将来也使用相同运行API，但管理端与用户端权限独立。

| 中台板块 | 小程序入口 | 共享结果 | 下一步 |
| --- | --- | --- | --- |
| 需求设计 | 我想记、和TA聊、看热点、创作的一句话入口 | 用户确认后的brief_snapshot | 直接产出；有参考视频时先拆解 |
| 作品拆解 | 拆学的拆一条视频、创作的参考一条视频 | 带来源证据的analysis_snapshot | 保存拆解资产；用于创作时检查是否已有简报 |
| 作品产出 | 已确认简报或拆解结果的用于创作 | work_version与各类asset_ref | 用户预览确认后保存资产，异步飞书归档 |

独立拆解不强迫先填写需求；进入作品产出必须有已确认简报，拆解可选。需求改版会让依赖旧简报的拆解/作品显示“基于旧需求”，保留历史，不能静默当作新方案。演练清空当前派生引用但保留历史快照，真实服务须保存完整依赖图。

## 一份流程定义，固定组件呈现

FlowDefinition包含schema_version、stage、flow_id、revision、scope、owner_id、min_client_capabilities、steps。每一步有稳定step_id、component_type、字段schema、input_refs、output_schema、capability_ref、skill_ref、必需确认标记。中台编辑标签、字段、已支持步骤顺序、模板和模型引用；不下发JS、HTML或可执行代码。

组件集合：信息/素材表单、AI协作及结果编辑、确认卡、视频证据卡、生成任务进度、作品预览编辑、资产回执。未识别组件或客户端能力不足时阻止新任务并提示更新，不能跳过确认或降级成空白页。旧客户端继续保留兼容流程。新增原生组件/能力需客户端更新，不承诺所有变化都能靠网页配置完成。

小程序常驻页面建议为pages/workflow/index，参数仅传project_id、run_id、stage。登录后后端校验归属，再返回可呈现步骤。业务密钥、模型原始调用地址、MCP凭据不发客户端。当前仓库尚无此动态页面，后续实现时接入稳定壳。

## 版本、个人流程与发布

管理员全局流程：草案 → schema与依赖校验 → 手机组件预览 → 测试账号验证 → 发布不可变版本 → 小范围用户验证 → 扩大范围；支持回滚。发布用expectedRevision防覆盖，管理员操作写审计。回滚只影响新任务，运行中任务固定flow_snapshot及skill/model/MCP版本，不强制迁移。

普通用户：选择默认流程或与Skill沟通 → Skill给出待确认问题、步骤差异、能力依赖和预计费用 → 用户编辑/确认 → 保存个人版本。个人流程只覆盖本人指定阶段，不更改全局默认；无个人版本时使用兼容默认。Skill只能提出草案，不能替用户确认或直接发布。不可删除素材归属校验、证据来源、生成前确认、费用上限、最终验收等必需节点。

## 运行记录与接口草案

Project串联source_refs、brief_version、analysis_version、work_versions。WorkflowRun记录user_id、project_id、stage、flow_snapshot、input_snapshot、current_step、status、revision、capability_versions与outputs。StepRun记录状态、重试次数、耗时、脱敏错误、产物引用和费用回执。

| 接口草案 | 用途 |
| --- | --- |
| GET /workflow-definitions/effective?stage=… | 按用户、客户端能力解析默认/个人流程 |
| POST /workflow-drafts/propose | Skill生成个人草案与差异，不执行付费步骤 |
| POST /workflow-drafts/{id}/confirm | 用户确认个人版本，expectedRevision |
| POST /projects | 从灵感、热点或参考资产建立项目 |
| POST /projects/{id}/runs | 选择阶段，服务端固定有效流程与输入快照 |
| GET /runs/{id} | 两端读取同一状态；长任务轮询，重入恢复 |
| POST /runs/{id}/steps/{step}/confirm | 提交编辑结果并确认，expectedRevision与Idempotency-Key |
| POST /runs/{id}/steps/{step}/retry | 仅重试失败步骤，查询已有供应商任务后决定是否重新提交 |
| POST /runs/{id}/cancel | 停止未开始步骤；正在计费任务按供应商取消能力处理 |
| /admin-api/workflows/* | 全局草案、发布、历史、回滚、执行状态与审计 |

这些接口是本次设计契约，尚未实现；不能拿现有视频生成接口当完整流程服务。

状态为ready → waiting_user / running → succeeded；失败保留failed与可重试标记，可取消为cancelled。状态转换在服务端事务里校验当前步骤、版本、账号和幂等键。超时不能直接重发付费任务；先按原任务ID核对，防止重复扣费。其他账号资源统一404。UI禁用按钮只是体验措施，不能代替服务端校验。

## AI、MCP与飞书

Skill负责理解需求与提出步骤；执行器按capability_ref选择已批准、健康且满足输入输出契约/权限/预算的MCP版本。视频读取失败停在证据步骤，无匹配时明确阻断，不让AI补造证据。生产执行器复用现有视频/工具服务，通过适配器接入，不重复建设媒体处理工程。场景模型配置与已上线的灵感AI配置采用相同管理模式，但阶段模型与热点模型独立。

业务结果先保存主数据库与对象存储索引。Outbox异步把经授权的简报、拆解、作品版本映射到飞书，幂等键为user_id+project_id+asset_version+event_type，失败显示队列状态和可重试操作。未确认的私密对话不写飞书；飞书不可用不导致已保存作品丢失。最终资产的权限、索引和版本归属仍由业务后端控制。

## 实现顺序

先做共享Flow/Project/Run持久化、发布权限与事务状态机；再实现小程序固定组件壳及网页用户工作台；随后逐阶段接入需求Skill、视频证据/MCP、作品生成；最后接异步飞书归档与运行监控。每阶段先用一个默认流程走通真实账号闭环，再开放个人流程编排。上线验收需包含跨端恢复、并发确认、重复任务回执、能力失败、额度拒绝、版本回滚、跨账号隔离和飞书失败补偿。
