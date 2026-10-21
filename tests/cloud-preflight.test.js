const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
test('部署盘点只读且避免泄露凭据', () => {
  const script = fs.readFileSync(path.join(__dirname, '../scripts/cloud-preflight.sh'), 'utf8');
  for (const part of ['free -m', 'df -h', 'ss -ltn', 'docker ps --format', 'docker compose version']) assert.ok(script.includes(part));
  assert.doesNotMatch(script, /docker inspect|printenv|sudo|apt install|docker compose up|systemctl|rm -|cat .*\.env/);
  assert.ok(script.includes('current account lacks access'));
});
test('上线步骤包含真实手机与账户隔离门禁', () => {
  const doc = fs.readFileSync(path.join(__dirname, '../docs/cloud-deployment.md'), 'utf8');
  for (const part of ['主机指纹', '用户资产隔离', 'Linux 字体', '受控重启', '合法域名', '正式手机尚未接通']) assert.ok(doc.includes(part));
});
