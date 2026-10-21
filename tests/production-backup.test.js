const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const script=fs.readFileSync('scripts/backup-production.sh','utf8');

test('production snapshot preserves old image, configuration, media and database privately',()=>{
 for(const part of ['set -euo pipefail','umask 077','docker image inspect','docker save','internal-api.tgz','pg_dump','backend.dump','nginx.tgz','sha256sum -c SHA256SUMS','gzip -t','pg_restore --list','chmod 600'])assert.ok(script.includes(part),part);
 assert.match(script,/\[\[ "\$TAG" =~/);
 assert.ok(!script.includes('claude-deploy'));
 assert.ok(!script.includes('rm -rf'));
});

test('production snapshot stops SQLite writer and restores service even on failure',()=>{
 const stop=script.indexOf('stop -t 60 video'),archive=script.indexOf('tar -czf "$DEST/internal-api.tgz"'),restart=script.indexOf('\nresume\n'),image=script.indexOf('docker save');
 assert.ok(script.indexOf('trap resume EXIT')<stop);
 assert.ok(stop<archive&&archive<restart&&restart<image);
 assert.ok(script.indexOf('trap - EXIT')>restart);
 assert.match(script,/up -d --no-build --wait video/);
});
