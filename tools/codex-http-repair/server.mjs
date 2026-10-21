import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { createRepair } from './repair.mjs';
const repair = createRepair();
const server = new McpServer({ name: 'codex-http-repair', version: '1.0.0' });
const result = fn => async args => {
  try { return { content: [{ type: 'text', text: JSON.stringify(fn(args)) }] }; }
  catch (error) { return { isError: true, content: [{ type: 'text', text: error.code ? `文件操作失败 (${error.code})，请检查权限与路径。` : error.message }] }; }
};
server.registerTool('codex_connection_inspect', {
  description: '预览本机 Codex 的 HTTP 修复并获取指纹。不输出配置内容或凭据。',
  inputSchema: {}, annotations: { readOnlyHint: true, openWorldHint: false }
}, result(() => repair.inspect()));
server.registerTool('codex_connection_repair', {
  description: '用户要求修复连接时使用。先检查，再用返回的 fingerprint 应用修复。自动备份，需重启 Codex。',
  inputSchema: { fingerprint: z.string().regex(/^[a-f0-9]{64}$/) },
  annotations: { readOnlyHint: false, destructiveHint: false, openWorldHint: false }
}, result(({ fingerprint }) => repair.repair(fingerprint)));
server.registerTool('codex_connection_restore', {
  description: '使用 repair 返回的 backupId 恢复；如果修复后用户又编辑了配置则拒绝覆盖。',
  inputSchema: { backupId: z.string().uuid() },
  annotations: { readOnlyHint: false, destructiveHint: true, openWorldHint: false }
}, result(({ backupId }) => repair.restore(backupId)));
server.connect(new StdioServerTransport()).catch(() => {
  console.error('MCP transport failed');
  process.exitCode = 1;
});
