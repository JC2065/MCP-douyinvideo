const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

test('视频解析守护程序按就绪状态恢复依赖并可撤销',()=>{
 const ensure=fs.readFileSync('scripts/ensure-video-stack.ps1','utf8');
 const install=fs.readFileSync('scripts/install-video-stack-watchdog.ps1','utf8');
 const uninstall=fs.readFileSync('scripts/uninstall-video-stack-watchdog.ps1','utf8');
 for(const marker of ['/readyz','/health','docker compose','--wait','start-video-server.ps1','ensure-reference-relay.ps1','VideoStackWatchdog'])assert.ok(ensure.includes(marker),marker);
 assert.match(ensure,/RedirectStandardError/);
 assert.doesNotMatch(ensure,/DTK_API_KEY\s*=/);
 assert.match(install,/AtLogOn/);
 assert.match(install,/Minutes 5/);
 assert.match(install,/MultipleInstances IgnoreNew/);
 assert.match(uninstall,/Unregister-ScheduledTask/);
});

test('高度参考中继只公开签名素材并由 Cloudflare Tunnel 提供 HTTPS',()=>{
 const relay=fs.readFileSync('scripts/reference-relay.py','utf8');
 const ensure=fs.readFileSync('scripts/ensure-reference-relay.ps1','utf8');
 assert.match(relay,/verified_reference_video/);
 assert.doesNotMatch(relay,/asset-runs|\/jobs\//);
 for(const marker of ['trycloudflare','127.0.0.1:8766','RandomNumberGenerator','reference-relay.json'])assert.ok(ensure.includes(marker),marker);
 assert.doesNotMatch(ensure,/YOUAI_REFERENCE_MEDIA_SECRET=[A-Za-z0-9_-]{16,}/);
});
