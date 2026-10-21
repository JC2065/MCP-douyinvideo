import { build } from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
const root = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(root, 'bundle');
fs.mkdirSync(out, { recursive: true });
await build({ entryPoints: [path.join(root, 'server.mjs')], outfile: path.join(out, 'server.cjs'), bundle: true,
  platform: 'node', target: 'node20', format: 'cjs', banner: { js: '// Generated from server.mjs; see source package.' },
  legalComments: 'eof'
});
for (const file of ['manifest.json', 'README.md']) fs.copyFileSync(path.join(root, file), path.join(out, file));
const cli = path.join(root, 'node_modules/@anthropic-ai/mcpb/dist/cli/cli.js');
const dist = path.resolve(root, '../../dist');
fs.mkdirSync(dist, { recursive: true });
const artifact = path.join(dist, 'codex-http-repair-1.0.0.mcpb');
for (const args of [['validate', path.join(out, 'manifest.json')], ['pack', out, artifact]]) {
  const run = spawnSync(process.execPath, [cli, ...args], { stdio: 'inherit', windowsHide: true });
  if (run.status !== 0) process.exit(run.status || 1);
}
