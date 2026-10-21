const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { createRequire } = require('node:module');
const root = path.resolve(__dirname, '../tools/codex-http-repair');
const local = createRequire(path.join(root, 'package.json'));
const { parse } = local('smol-toml');
const api = import(pathToFileURL(path.join(root, 'repair.mjs')));
test('桌面工具及产物排除出小程序上传包', () => {
  const config = JSON.parse(fs.readFileSync(path.resolve(root, '../../project.config.json'), 'utf8'));
  for (const value of ['tools', 'dist']) assert.ok(config.packOptions.ignore.some(rule => rule.type === 'folder' && rule.value === value));
});
async function fixture(t, original, validator = () => {}) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'repair-test-'));
  t.after(() => fs.rmSync(home, { recursive: true, force: true }));
  const file = path.join(home, 'config.toml');
  if (original !== null) fs.writeFileSync(file, original);
  return { home, file, tool: (await api).createRepair(home, validator) };
}

test('默认 OpenAI 使用 HTTP 别名，保留模型、注释、端点与其他语义', async () => {
  const input = '# keep\nmodel = "test-model"\nopenai_base_url = "https://example.com/v1"\n[features]\nfoo = true\n';
  const { plan } = await api;
  const result = plan(input);
  const parsed = parse(result.text);
  assert.equal(parsed.model, 'test-model');
  assert.equal(parsed.model_provider, 'codex-http-repair');
  const provider = parsed.model_providers['codex-http-repair'];
  assert.equal(provider.name, 'OpenAI');
  assert.equal(provider.requires_openai_auth, true);
  assert.equal(provider.supports_websockets, false);
  assert.equal(provider.base_url, 'https://example.com/v1');
  assert.match(result.text, /# keep/);
  assert.deepEqual({ ...parsed.features }, { foo: true });
  assert.equal(plan(result.text).changed, false);
});

test('自定义 provider 仅关闭 WebSocket，保留密钥、嵌套表及 CRLF', async () => {
  const input = 'model_provider = "my.proxy"\r\n[model_providers."my.proxy"]\r\nname="proxy"\r\nsupports_websockets = true # keep\r\nexperimental_bearer_token="SECRET"\r\n[model_providers."my.proxy".http_headers]\r\nX="Y"\r\n';
  const { plan } = await api;
  const output = plan(input).text;
  assert.equal(output, input.replace('= true # keep', '= false # keep'));
  assert.equal(plan(output).changed, false);
});

test('缺省标记可插入，其他 provider 不受影响', async () => {
  const input = 'model_provider="a"\n[model_providers.a]\nname="A"\n[model_providers.b]\nname="B"\nsupports_websockets=true\n';
  const output = parse((await api).plan(input).text);
  assert.equal(output.model_providers.a.supports_websockets, false);
  assert.equal(output.model_providers.b.supports_websockets, true);
});

test('无效或复杂冲突配置不修改', async () => {
  const { plan } = await api;
  for (const input of ['x=[', 'profile="work"', '[profiles.work]\nmodel_provider="x"',
    '[model_providers.codex-http-repair]\nname="other"', '[model_providers.openai]\nsupports_websockets=false',
    'model_provider="ollama"', 'model_provider="x"\nmodel_providers.x={name="X", supports_websockets=true}',
    'model_provider="x"\n[model_providers.x]\nname="X"\nwire_api="chat"']) {
    assert.throws(() => plan(input));
  }
});

test('应用、备份、幂等、精确恢复；输出不含配置密钥', async t => {
  const input = '# original\nmodel="keep"\n[other]\nsecret="DO_NOT_LEAK"\n';
  const { tool, file, home } = await fixture(t, input);
  const state = tool.inspect();
  const applied = tool.repair(state.fingerprint);
  assert.equal(applied.applied, true);
  assert.equal(tool.repair(tool.inspect().fingerprint).applied, false);
  assert.doesNotMatch(JSON.stringify([state, applied]), /DO_NOT_LEAK/);
  assert.equal(fs.readdirSync(path.join(home, 'http-repair-backups')).length, 1);
  assert.equal(tool.restore(applied.backupId).restored, true);
  assert.equal(fs.readFileSync(file, 'utf8'), input);
});

test('新配置可创建并恢复为不存在', async t => {
  const { tool, file } = await fixture(t, null);
  const result = tool.repair(tool.inspect().fingerprint);
  assert.ok(fs.existsSync(file));
  tool.restore(result.backupId);
  assert.ok(!fs.existsSync(file));
});

test('陈旧指纹与后续编辑拒绝覆盖', async t => {
  const { tool, file } = await fixture(t, 'model="first"');
  const old = tool.inspect().fingerprint;
  fs.writeFileSync(file, 'model="second"');
  assert.throws(() => tool.repair(old), /指纹/);
  const result = tool.repair(tool.inspect().fingerprint);
  fs.appendFileSync(file, '\n# later');
  const edited = fs.readFileSync(file, 'utf8');
  assert.throws(() => tool.restore(result.backupId), /已更改/);
  assert.equal(fs.readFileSync(file, 'utf8'), edited);
  assert.throws(() => tool.restore('../config.toml'), /ID/);
});

test('验证失败及验证期间编辑不覆盖原配置', async t => {
  const { tool, file } = await fixture(t, 'model="keep"', () => { throw new Error('unsupported'); });
  assert.throws(() => tool.repair(tool.inspect().fingerprint), /unsupported/);
  assert.equal(fs.readFileSync(file, 'utf8'), 'model="keep"');
  const second = await fixture(t, 'model="old"', () => fs.writeFileSync(second.file, 'model="new"'));
  assert.throws(() => second.tool.repair(second.tool.inspect().fingerprint), /其他程序/);
  assert.equal(fs.readFileSync(second.file, 'utf8'), 'model="new"');
});

test('损坏备份和锁阻止写入', async t => {
  const { tool, home } = await fixture(t, '');
  fs.mkdirSync(path.join(home, '.http-repair.lock'));
  assert.throws(() => tool.repair(tool.inspect().fingerprint), /锁/);
  fs.rmdirSync(path.join(home, '.http-repair.lock'));
  const applied = tool.repair(tool.inspect().fingerprint);
  const backup = path.join(home, 'http-repair-backups', applied.backupId + '.json');
  const record = JSON.parse(fs.readFileSync(backup));
  record.original = 'changed';
  fs.writeFileSync(backup, JSON.stringify(record));
  assert.throws(() => tool.restore(applied.backupId), /校验/);
});

test('本机 Codex 可加载候选配置；找不到可执行文件时失败', async () => {
  const { plan, validateWithCodex } = await api;
  validateWithCodex(plan('model="test-model"').text);
  assert.throws(() => validateWithCodex('', 'not-a-codex-executable-123'), /验证失败/);
});

test('打包后的 MCP 服务可初始化、列出工具、检查、应用并恢复', async t => {
  const { home, file } = await fixture(t, 'model="keep"');
  const mcpbRequire = createRequire(local.resolve('@anthropic-ai/mcpb'));
  const archive = mcpbRequire('fflate').unzipSync(fs.readFileSync(path.resolve(root, '../../dist/codex-http-repair-1.0.0.mcpb')));
  assert.deepEqual(Object.keys(archive).sort(), ['README.md', 'manifest.json', 'server.cjs']);
  const extracted = path.join(home, 'installed');
  fs.mkdirSync(extracted);
  for (const [name, bytes] of Object.entries(archive)) fs.writeFileSync(path.join(extracted, name), bytes);
  assert.deepEqual(Buffer.from(archive['server.cjs']), fs.readFileSync(path.join(root, 'bundle/server.cjs')));
  const { Client } = await import(pathToFileURL(local.resolve('@modelcontextprotocol/sdk/client/index.js')));
  const { StdioClientTransport } = await import(pathToFileURL(local.resolve('@modelcontextprotocol/sdk/client/stdio.js')));
  const client = new Client({ name: 'repair-test', version: '1.0.0' });
  const transport = new StdioClientTransport({ command: process.execPath,
    args: [path.join(extracted, 'server.cjs')], env: { ...process.env, CODEX_HOME: home }, stderr: 'pipe' });
  t.after(() => client.close());
  await client.connect(transport);
  assert.equal((await client.listTools()).tools.length, 3);
  const inspect = await client.callTool({ name: 'codex_connection_inspect', arguments: {} });
  assert.ok(!inspect.isError);
  const fingerprint = JSON.parse(inspect.content[0].text).fingerprint;
  const repaired = await client.callTool({ name: 'codex_connection_repair', arguments: { fingerprint } });
  assert.ok(!repaired.isError, JSON.stringify(repaired));
  const backupId = JSON.parse(repaired.content[0].text).backupId;
  assert.equal(parse(fs.readFileSync(file, 'utf8')).model_provider, 'codex-http-repair');
  const stale = await client.callTool({ name: 'codex_connection_repair', arguments: { fingerprint } });
  assert.equal(stale.isError, true);
  const restored = await client.callTool({ name: 'codex_connection_restore', arguments: { backupId } });
  assert.ok(!restored.isError);
  assert.equal(fs.readFileSync(file, 'utf8'), 'model="keep"');
});

test('真实 Codex 对本地模拟 Responses 服务直接发 HTTP POST，无 WebSocket Upgrade', { timeout: 25000 }, async t => {
  const http = require('node:http');
  const { spawn } = require('node:child_process');
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'repair-http-test-'));
  const file = path.join(home, 'config.toml');
  let accept;
  const request = new Promise(resolve => { accept = resolve; });
  const server = http.createServer((req, res) => {
    if (req.url.includes('/responses')) accept({ method: req.method, upgrade: req.headers.upgrade });
    res.writeHead(200, { 'Content-Type': 'text/event-stream' });
    res.end('event: response.completed\ndata: {"type":"response.completed","response":{"id":"resp_test","status":"completed","output":[]}}\n\n');
  });
  server.on('upgrade', (req, socket) => { accept({ upgrade: true }); socket.destroy(); });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const input = `model="gpt-5"\nmodel_provider="test"\n[model_providers.test]\nname="Local test"\nbase_url="http://127.0.0.1:${server.address().port}/v1"\nenv_key="REPAIR_TEST_KEY"\nsupports_websockets=true\n`;
  fs.writeFileSync(file, (await api).plan(input).text);
  const child = spawn(process.env.CODEX_HTTP_REPAIR_CODEX || 'codex', ['exec', '--ephemeral', '--skip-git-repo-check', '--json', 'Reply OK'], {
    cwd: home, env: { ...process.env, CODEX_HOME: home, REPAIR_TEST_KEY: 'local-dummy-key', HTTP_PROXY: '', HTTPS_PROXY: '', ALL_PROXY: '', NO_PROXY: '127.0.0.1,localhost' },
    windowsHide: true, stdio: ['ignore', 'ignore', 'pipe']
  });
  let stderr = '';
  child.stderr.on('data', chunk => { stderr += chunk.toString(); });
  t.after(async () => {
    if (child.exitCode === null && child.signalCode === null && child.pid) {
      const closed = new Promise(resolve => child.once('close', resolve));
      child.kill();
      await closed;
    }
    server.closeAllConnections();
    server.close();
    fs.rmSync(home, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
  });
  const timer = setTimeout(() => accept({ timeout: true }), 18000);
  t.after(() => clearTimeout(timer));
  const result = await Promise.race([request, new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', () => resolve({ exited: true }));
  })]);
  assert.deepEqual(result, { method: 'POST', upgrade: undefined }, stderr.slice(-1200));
});
