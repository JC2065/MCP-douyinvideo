const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root, name), 'utf8');

test('开发规则与说明统一五次范围和十次完整验证周期及优先级', () => {
  const rules = read('AGENTS.md');
  const readme = read('README.md');
  for (const content of [rules, readme]) {
    assert.match(content, /每累计 5 次/);
    assert.match(content, /每累计 10 次/);
    assert.match(content, /汇总最近五次改动/);
    assert.match(content, /改动部位的测试与完整测试同时出现时，只执行完整测试/);
    assert.doesNotMatch(content, /完整测试按下述每 5 次/);
    assert.ok(content.includes('node --test tests/<相关文件>.test.js'));
    assert.ok(content.includes('docs/test-batches.md'));
  }
  assert.match(rules, /同一改动中的修复、重试和补充提交不重复计数/);
  assert.match(rules, /不得将失败批次标记完成或清零/);
  assert.match(rules, /临时全量验证不重置计数/);
  assert.match(rules, /第 5 次通过仅完成阶段检查，不重置十次周期/);
  assert.match(rules, /该范围包含本次改动，不再重复执行本次定向测试/);
});

test('批次记录入口存在且完整测试仍覆盖全部测试文件', () => {
  const batches = read('docs/test-batches.md');
  assert.ok(batches.includes('../AGENTS.md'));
  assert.ok(batches.includes('改动内容及影响范围'));
  assert.ok(batches.includes('定向测试与结果'));
  assert.ok(batches.includes('整批汇总'));
  assert.ok(batches.includes('第 5 次阶段检查'));
  assert.ok(batches.includes('第 10 次完整检查'));
  assert.ok(batches.includes('不额外执行改动部位测试'));
  assert.equal(JSON.parse(read('package.json')).scripts.test, 'node --test tests/*.test.js');
});

test('长任务每三分钟主动汇报可核验状态', () => {
  const rules = read('AGENTS.md');
  const guide = read('docs/progress-reporting.md');
  for (const content of [rules, guide]) {
    assert.match(content, /3 分钟/);
    assert.match(content, /已完成/);
    assert.match(content, /正在执行/);
    assert.match(content, /卡点/);
    assert.match(content, /下一步/);
  }
  assert.match(rules, /不得超过 3 分钟无反馈/);
  assert.match(guide, /没有真实证据时不得写“已完成”/);
});

test('Claude 说明文件指向 AGENTS.md 统一规则', () => {
  const claude = read('CLAUDE.md');
  assert.ok(claude.includes('AGENTS.md'));
  assert.match(claude, /以 `AGENTS.md` 为准/);
  assert.ok(claude.includes('docs/task-ledger.md'));
  assert.ok(claude.includes('docs/test-batches.md'));
});
