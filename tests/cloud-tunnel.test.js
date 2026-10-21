const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
test('跨服务器通路仅回环绑定并严格校验主机',()=>{
 const unit=fs.readFileSync(path.join(__dirname,'../deploy/youai-video-tunnel.service'),'utf8');
 assert.ok(unit.includes('StrictHostKeyChecking=yes'));
 assert.ok(unit.includes('ExitOnForwardFailure=yes'));
 assert.ok(unit.includes('127.0.0.1:18765:127.0.0.1:8765'));
 assert.ok(unit.includes('Restart=always'));
 const route=fs.readFileSync(path.join(__dirname,'../deploy/youai-health.nginx.conf'),'utf8');
 assert.ok(route.includes('location = /youai/health'));
 assert.ok(route.includes('proxy_pass http://127.0.0.1:18765/health'));
 assert.doesNotMatch(route,/location\s+\/\s*\{/);
 assert.ok(route.includes('location ^~ /youai/'));
 assert.ok(route.includes('access_log off'));
});
