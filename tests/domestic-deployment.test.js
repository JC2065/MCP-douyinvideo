const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const endpoints=require('../utils/service-endpoints');
test('all native cloud entry points share the domestic origin; local mode is simulator-only',async()=>{
 assert.equal(endpoints.BASE,'https://youai888.top/youai');
 for(const platform of ['ios','android','devtools']){
  const api={getSystemInfoSync:()=>({platform}),getStorageSync:()=>true};
  assert.equal(endpoints.videoBase(api),platform==='devtools'?'http://127.0.0.1:8765':endpoints.BASE);
  api.getStorageSync=()=>false;assert.equal(endpoints.videoBase(api),endpoints.BASE);
 }
 assert.equal(endpoints.videoBase(null),endpoints.BASE);
 assert.equal(require('../utils/admin-client').BASE,endpoints.BASE);
 assert.equal(require('../utils/analysis-sync').BASE,endpoints.BASE);
 let url;await require('../utils/hotspot-discovery').load({request:o=>{url=o.url;o.fail();}});
 assert.equal(url,endpoints.BASE+'/hotspots');
});
test('domestic hosting serves only the browsing bundle and keeps admin and internal services separate',()=>{
 const config=fs.readFileSync('deploy/youai888.nginx.conf','utf8');
 assert.match(config,/root \/opt\/youai\/web-current;/);
 assert.match(config,/location = \/admin \{ return 302 \/youai\/admin\/; \}/);
 assert.match(config,/index\\\.html\|app\\\.js\|model\\\.js\|style\\\.css/);
 assert.match(config,/location \/ \{ return 404; \}/);
 assert.ok(config.includes('^/assets/(icons/[a-z0-9-]+\\.svg|[a-zA-Z0-9_-]+\\.jpg)$'));
 const compose=fs.readFileSync('compose.video-cloud.yml','utf8');
 assert.match(compose,/YOUAI_ADMIN_ORIGIN: https:\/\/youai888.top/);
 assert.match(compose,/YOUAI_PUBLIC_ASSET_BASE_URL: https:\/\/youai888.top\/youai/);
 assert.match(compose,/YOUAI_FEISHU_CONFIG: \/credentials\/feishu-matrix.json/);
 const project=JSON.parse(fs.readFileSync('project.config.json','utf8'));
 assert.equal(project.setting.urlCheck,true);
 for(const folder of ['web','backend','scripts','deploy'])assert.ok(project.packOptions.ignore.some(x=>x.type==='folder'&&x.value===folder));
});
