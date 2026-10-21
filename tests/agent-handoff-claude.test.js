const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
test('Claude→Codex 交接文档包含基线、回交格式与双向入口',()=>{
 const doc=fs.readFileSync('docs/agent-handoff-2026-10-17-claude.md','utf8');
 for(const h of ['交接基线','本次 Claude 完成内容','接口与数据变化','测试证据','运行状态','密钥与费用','未完成事项','回滚点','回交格式（Codex → Claude）','可直接发给 Codex 的提示词'])assert.ok(doc.includes('## '+h),h);
 for(const m of ['platform-d214e58','累计 **129**','第130次','docs/agent-return-YYYY-MM-DD-codex.md','claude-deploy','8ae3b0ea26fc4b23b79d1082570ad4af'])assert.ok(doc.includes(m),m);
 assert.match(fs.readFileSync('AGENTS.md','utf8'),/agent-return-YYYY-MM-DD-codex\.md/);
 assert.match(fs.readFileSync('CLAUDE.md','utf8'),/agent-return-\*-codex\.md/);
});

test('Codex回交包含验证边界、最新累计134及下一次测试范围',()=>{const s=fs.readFileSync('docs/agent-return-2026-10-17-codex.md','utf8');for(const h of ['回交基线','完成内容','接口与数据变化','测试证据','运行状态','密钥与费用','未完成事项','回滚点'])assert.ok(s.includes('## '+h),h);for(const t of ['累计134','下一次135','mock','真机','qwen3-vl-plus','project.config.json','GitHub','歌词'])assert.ok(s.includes(t),t);});
