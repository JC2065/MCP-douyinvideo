const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const dir = path.join(__dirname, '../docs/competition-2026');
test('authorization identifies the submitted work and leaves signing to the rights holder', () => {
  const body = fs.readFileSync(path.join(dir, '参赛授权书.md'), 'utf8');
  for (const value of ['作品名称：YOUAI', 'wx8ae5d4f3ea8d0d8b', '不涉及作品知识产权的转让', '授权人签字／单位盖章', '________年________月________日']) assert.ok(body.includes(value));
  assert.ok(!body.includes('永久') && !body.includes('不可撤销'));
  const file = fs.readFileSync(path.join(dir, 'YOUAI参赛授权书.docx'));
  assert.equal(file.subarray(0, 2).toString(), 'PK');
  assert.ok(file.length < 100 * 1024 * 1024);
});
test('competition submission preserves scope and real-client limitations', () => {
  const body = fs.readFileSync(path.join(dir, '作品说明.md'), 'utf8');
  for (const section of ['创作背景', '创作思路', '实践过程', '当前成果与验证范围', '后续完善计划']) assert.ok(body.includes(section));
  for (const limit of ['真实手机手机号授权尚未验收', '正式审核仍待验证', '不将规划能力作为已上线成果']) assert.ok(body.includes(limit));
  assert.equal(/sk-[A-Za-z0-9]{20,}|BEGIN .*PRIVATE KEY/.test(body), false);
  const file = fs.readFileSync(path.join(dir, 'YOUAI微信小程序参赛作品说明.docx'));
  assert.equal(file.subarray(0, 2).toString(), 'PK');
  assert.ok(file.length < 100 * 1024 * 1024);
});
