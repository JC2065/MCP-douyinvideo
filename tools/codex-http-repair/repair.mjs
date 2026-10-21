import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { isDeepStrictEqual } from 'node:util';
import { parse, stringify } from 'smol-toml';

const alias = 'codex-http-repair';
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
export const defaultHome = () => path.resolve(process.env.CODEX_HOME || path.join(os.homedir(), '.codex'));
function read(file) {
  try {
    if (!fs.lstatSync(file).isFile()) throw new Error('配置或备份不是普通文件，停止修改。');
    return fs.readFileSync(file, 'utf8');
  } catch (e) { if (e.code === 'ENOENT') return null; throw e; }
}
function decode(text) {
  try { return parse(text || ''); } catch { throw new Error('配置 TOML 无效，未修改；请先修复语法。'); }
}
// Only simple textual edits are attempted. A complete semantic comparison below
// rejects quoted/dotted/multiline layouts that cannot be safely preserved.
function setRoot(text, key, value) {
  const firstTable = text.search(/^\s*\[/m);
  const end = firstTable < 0 ? text.length : firstTable;
  const root = text.slice(0, end);
  const re = new RegExp(`^${key}\\s*=.*$`, 'm');
  const line = `${key} = ${JSON.stringify(value)}`;
  return (re.test(root) ? root.replace(re, line) : `${line}\n${root}`) + text.slice(end);
}
export function plan(text) {
  const before = decode(text);
  const expected = decode(text);
  if (before.profile || Object.values(before.profiles || {}).some(p => p.model_provider || p.model_providers)) {
    throw new Error('检测到 profile 的连接覆盖，请先在用户配置中明确单一 provider；未修改。');
  }
  const provider = before.model_provider || 'openai';
  let next = text || '';
  if (provider === 'openai') {
    if (before.model_providers?.openai) throw new Error('存在内置 openai 覆盖，请先处理版本兼容问题。');
    if (before.model_providers?.[alias]) throw new Error('HTTP 配置名称已存在但未启用，停止以避免覆盖。');
    const info = {
      name: 'OpenAI', wire_api: 'responses', requires_openai_auth: true,
      supports_websockets: false, supports_standalone_web_search: true,
      env_http_headers: { 'OpenAI-Organization': 'OPENAI_ORGANIZATION', 'OpenAI-Project': 'OPENAI_PROJECT' }
    };
    if (before.openai_base_url) info.base_url = before.openai_base_url;
    expected.model_provider = alias;
    expected.model_providers ||= {};
    expected.model_providers[alias] = info;
    next = setRoot(next, 'model_provider', alias);
    next += '\n# Codex HTTP repair: keep existing authentication, disable model WebSocket.\n';
    next += stringify({ model_providers: { [alias]: info } });
  } else {
    const info = before.model_providers?.[provider];
    if (!info || info.aws || (info.wire_api && info.wire_api !== 'responses')) {
      throw new Error('仅支持 OpenAI 或已定义的 Responses 自定义 provider。');
    }
    if (info.supports_websockets === false) return { text: next, provider, changed: false };
    expected.model_providers[provider].supports_websockets = false;
    const lines = next.split('\n');
    const start = lines.findIndex(line => {
      const m = line.match(/^\s*\[model_providers\.(.+)\]\s*(?:#.*)?$/);
      if (!m) return false;
      try { return Object.hasOwn(parse(`[model_providers.${m[1]}]\nx=1`).model_providers, provider); } catch { return false; }
    });
    if (start < 0) throw new Error('无法保留此 TOML 布局，请使用独立的 provider 表。');
    let end = start + 1;
    while (end < lines.length && !/^\s*\[/.test(lines[end])) end++;
    const field = lines.findIndex((line, i) => i > start && i < end && /^\s*supports_websockets\s*=/.test(line));
    if (field >= 0) lines[field] = lines[field].replace(/=\s*(true|false)/, '= false');
    else lines.splice(start + 1, 0, 'supports_websockets = false');
    next = lines.join('\n');
  }
  if (!isDeepStrictEqual(decode(next), decode(stringify(expected)))) throw new Error('配置语义校验失败，未写入任何配置。');
  return { text: next, provider: expected.model_provider, changed: next !== text };
}
export function validateWithCodex(text, executable = process.env.CODEX_HTTP_REPAIR_CODEX || 'codex') {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'codex-http-check-'));
  try {
    fs.writeFileSync(path.join(dir, 'config.toml'), text, { mode: 0o600 });
    const result = spawnSync(executable, ['features', 'list'], {
      cwd: dir, env: { ...process.env, CODEX_HOME: dir }, encoding: 'utf8',
      timeout: 15000, windowsHide: true, maxBuffer: 1024 * 1024
    });
    if (result.error || result.status !== 0) throw new Error('本机 Codex 配置验证失败或找不到 codex；未应用修改。可在启动环境设置 CODEX_HTTP_REPAIR_CODEX 为可执行文件绝对路径。');
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
}
export function createRepair(home = defaultHome(), validate = validateWithCodex) {
  home = path.resolve(home);
  const config = path.join(home, 'config.toml');
  const backups = path.join(home, 'http-repair-backups');
  function inspect() {
    const text = read(config);
    const proposal = plan(text);
    return {
      configPath: config, fingerprint: hash(text === null ? '\0missing' : text),
      provider: proposal.provider, changed: proposal.changed,
      action: proposal.changed ? '关闭模型 WebSocket，使用 HTTP(S)/SSE；保留模型与凭据配置。' : '配置已关闭模型 WebSocket。',
      limitation: '不能证明重连根因。命令行、项目/托管配置或已运行会话可能覆盖设置；应用后完全退出并重启 Codex。'
    };
  }
  function locked(fn) {
    fs.mkdirSync(home, { recursive: true });
    const lock = path.join(home, '.http-repair.lock');
    try { fs.mkdirSync(lock); } catch { throw new Error('另一个修复正在执行，或存在遗留锁目录；未修改。'); }
    try { return fn(); } finally { fs.rmdirSync(lock); }
  }
  function replace(text, original) {
    if (read(config) !== original) throw new Error('配置已被其他程序修改，请重新检查。');
    const temp = path.join(home, `.http-repair-${crypto.randomUUID()}.tmp`);
    try {
      fs.writeFileSync(temp, text, { flag: 'wx', mode: original === null ? 0o600 : fs.statSync(config).mode & 0o777 });
      if (read(config) !== original) throw new Error('配置已被其他程序修改，请重新检查。');
      fs.renameSync(temp, config);
    } finally { if (fs.existsSync(temp)) fs.unlinkSync(temp); }
  }
  function repair(fingerprint) {
    return locked(() => {
      const original = read(config);
      const state = inspect();
      if (state.fingerprint !== fingerprint) throw new Error('配置指纹不匹配，请先重新检查。');
      if (!state.changed) return { ...state, applied: false };
      const proposal = plan(original);
      validate(proposal.text);
      fs.mkdirSync(backups, { recursive: true, mode: 0o700 });
      if (fs.lstatSync(backups).isSymbolicLink()) throw new Error('备份目录不能是符号链接。');
      const backupId = crypto.randomUUID();
      fs.writeFileSync(path.join(backups, `${backupId}.json`), JSON.stringify({
        original, originalHash: hash(original === null ? '\0missing' : original), appliedHash: hash(proposal.text)
      }), { flag: 'wx', mode: 0o600 });
      replace(proposal.text, original);
      return { applied: true, backupId, ...inspect(), restartRequired: true };
    });
  }
  function restore(backupId) {
    return locked(() => {
      if (!/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(backupId)) throw new Error('备份 ID 无效。');
      if (fs.lstatSync(backups).isSymbolicLink()) throw new Error('备份目录不能是符号链接。');
      const raw = read(path.join(backups, `${backupId}.json`));
      if (raw === null) throw new Error('备份不存在。');
      let b;
      try { b = JSON.parse(raw); } catch { throw new Error('备份损坏。'); }
      if ((b.original !== null && typeof b.original !== 'string') || hash(b.original === null ? '\0missing' : b.original) !== b.originalHash) throw new Error('备份校验失败。');
      const current = read(config);
      if (current === null || hash(current) !== b.appliedHash) throw new Error('修复后配置已更改，拒绝覆盖；请手动合并备份。');
      if (b.original === null) fs.unlinkSync(config);
      else { decode(b.original); replace(b.original, current); }
      return { restored: true, restartRequired: true };
    });
  }
  return { inspect, repair, restore };
}
