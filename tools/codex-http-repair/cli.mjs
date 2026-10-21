import { createRepair } from './repair.mjs';
const tool = createRepair();
try {
  const [action = 'inspect', argument] = process.argv.slice(2);
  if (!['inspect', 'repair', 'restore'].includes(action)) throw new Error('用法: node cli.mjs inspect | repair <fingerprint> | restore <backupId>');
  console.log(JSON.stringify(tool[action](argument), null, 2));
} catch (error) { console.error(error.code ? `文件操作失败: ${error.code}` : error.message); process.exitCode = 1; }
