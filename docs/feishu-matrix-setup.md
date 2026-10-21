# 飞书六表搭建说明

当前交付为建表工具与字段契约；尚未创建真实飞书表格，未接通同步与文件归档。用户已确认先准备工具，两个组织的自建应用尚未创建。

## 用户准备

1. 在海纳众赢组织创建自建应用“YOUAI 管理台”；在商业标准版组织创建“YOUAI 资产归档”。分别发布到对应组织。
2. 各组织创建一个空白多维表格，分别命名“YOUAI 管理台”和“YOUAI 归档索引”。创建新的专用表，避免改动现有业务。
3. 为应用开通多维表格读取、创建数据表和创建字段所需权限，并把应用添加为对应表格的可编辑协作者；仅授权这两个专用表。文件归档权限在实现归档时另行配置。
4. 取得各自 App ID、App Secret，以及多维表格 URL 中 `/base/` 后的 app_token（这里称 baseToken）。App ID 是应用标识，baseToken 是表格标识，不能混用；Wiki 链接需要先取得实际 Base 标识。
5. 将 [配置模板](feishu-matrix-config.example.json) 复制到仓库外 `E:\data\codexYOUAI-data\credentials\feishu-matrix.json`，只在该文件填入真实值。不在聊天、Git 或小程序内存放 Secret。Linux 部署后放入仅服务账号可读的配置目录。

## 执行

无凭据预演（零网络调用）：

```powershell
node scripts/setup-feishu-matrix.js
```

真实创建（先完成上方授权）：

```powershell
node scripts/setup-feishu-matrix.js --apply --config E:\data\codexYOUAI-data\credentials\feishu-matrix.json --state E:\data\codexYOUAI-data\feishu-matrix-state.json
```

工具按名称查找表和字段，已有项只核对、不删除；创建失败后运行同一命令继续。真实 API 写入超时可能已成功，工具不盲目重发，重新查询后再继续。字段重名、类型或关联目标冲突会中止，需人工核对。运行期间不要同时启动另一份建表命令。保留默认空白字段，不自动删除用户表格。

企业侧：作品总表、创作方案、存储资源池、成本与反馈。商业版侧：资产目录、归档与恢复任务。同 Base 的方案/反馈关联作品，归档任务关联资产；跨组织用作品ID、资产ID、资源池ID关联，后台数据库保持完整映射。

输出状态包含 Base、table_id 和 field_id，不含密钥或访问 token。鉴权 token 仅在进程内缓存，接口失败返回 HTTP/飞书 code，不打印远端错误正文；检查后台权限和接口频率再重跑。

## 验收与下一步

- 两个组织分别显示 4 张和 2 张命名表，字段类型与代码契约一致。
- 重跑不产生重复表/字段，同 Base 关联字段指向正确表。
- 填写一条非敏感测试作品和资产，验证关系；不要在未授权时传输真实用户记录。
- 额度台账记录截图核验日期、有效期与已用值，不把历史额度自动写成当前权益。
- 之后接后台持久同步队列、批量增量写入、去重、失败恢复和飞书文件归档；本工具不是同步 Worker，也不具备文件迁移能力。

官方契约：[建表](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/create)、[建字段](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/create)、[应用鉴权](https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal)。真实组织联调仍待凭据配置。

可分组织执行：在上述真实命令中加入 `--role management` 只创建企业四表，或 `--role archive` 只创建商业版两表。状态文件合并保留另一组织的映射。读取成功但创建返回 403/91403 时，检查应用是否为该 Base 的可编辑协作者、建表/字段权限是否发布生效；不能将读取权限当成写入授权。

## 当前确认布局（2026-10-12）

用户已改为商业标准版单组织六表。新应用凭据当前在 management，使用 `--role management --layout unified`，新表链接的 Base 标识必须替换旧企业 baseToken。统一布局状态文件使用仓库外 `feishu-matrix-unified-state.json`，旧企业状态文件保持保留。旧双组织说明仅作历史/可选部署，不是当前默认。
