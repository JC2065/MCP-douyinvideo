const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
test('我的快捷入口及偏好列表不展示冗余提示，保留箭头和展开状态',()=>{
 const xml=fs.readFileSync('pages/main/index.wxml','utf8');
 const shortcuts=xml.slice(xml.indexOf('<view class="account-shortcuts">'),xml.indexOf('<view wx:if="{{accountMore}}" class="account-group account-more">'));
 assert.equal((shortcuts.match(/<button /g)||[]).length,4);
 assert.doesNotMatch(shortcuts,/class="muted"|查看任务|state\.works\.length|state\.favorites\.length/);
 for(const label of ['创作资产','偏好设置',"{{state.role==='商家'?'切回用户':'切为商家'}}",'任务进度'])assert.ok(shortcuts.includes(label));
 const preferences=xml.slice(xml.indexOf('class="account-group account-more"'));
 assert.ok(!xml.includes('本周完成')&&!xml.includes('调整目标')&&!xml.includes('作品与草稿')&&!xml.includes('我的收藏'));
 const labels=[...shortcuts.matchAll(/<text>([^<]+)<\/text>/g)].map(m=>m[1]);assert.deepEqual(labels,['创作资产','偏好设置',"{{state.role==='商家'?'切回用户':'切为商家'}}",'任务进度']);
 assert.ok(preferences.indexOf('wx:if="{{accountMore}}"')<preferences.indexOf('data-section="direction"'));
 assert.ok(shortcuts.includes('aria-expanded="{{accountMore}}"'));

});
test('我的分组入口不重复，低频设置默认折叠且可以展开收起',()=>{const s=fs.readFileSync('pages/main/index.wxml','utf8');const mine=s.slice(s.indexOf('<block wx:if="{{tab===\'我的\'}}">'),s.indexOf("view==='command'"));assert.equal((mine.match(/data-view="profile"/g)||[]).length,1);assert.equal((mine.match(/data-tab="创作"/g)||[]).length,0);for(const key of ['direction','video','topics','agent','rhythm'])assert.ok(mine.includes('data-section="'+key+'"'));for(const action of ['videoAssets','settings','aiConfig','merchantEntry','reset'])assert.ok(mine.includes('bindtap="'+action+'"'));assert.ok(mine.indexOf('wx:if="{{accountMore}}"')<mine.indexOf('bindtap="reset"'));let page;const routes=[];vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:n=>n.endsWith('creator-preferences')?{profile:()=>({})}:n.endsWith('store')?{initial:()=>({})}:n.endsWith('learning')?{cases:[],hotspots:[],hotspotDiscovery:{platforms:[],rows:[]}}:{},Page:p=>page=p,wx:{navigateTo:o=>routes.push(o.url)}});page.setData=function(d){Object.assign(this.data,d)};page.videoAssets();assert.deepEqual(routes,['/pages/video-assets/index']);page.settings();assert.equal(routes[1],'/pages/settings/index');assert.equal(page.data.accountMore,false);page.toggleAccountMore();assert.equal(page.data.accountMore,true);page.toggleAccountMore();assert.equal(page.data.accountMore,false);});

test('商家入口明确未认证，取消不切换，确认才进入原商家功能',()=>{
 let page,modal,count=0;vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:n=>n.endsWith('creator-preferences')?{profile:()=>({})}:n.endsWith('store')?{initial:()=>({role:'个人'})}:n.endsWith('learning')?{cases:[],hotspots:[],hotspotDiscovery:{platforms:[]}}:{},Page:p=>page=p,wx:{showModal:o=>modal=o}});
 page.switchRole=()=>count++;page.merchantEntry();assert.match(modal.content,/不代表已认证/);modal.success({confirm:false});assert.equal(count,0);modal.success({confirm:true});assert.equal(count,1);page.data.state.role='商家';modal=null;page.merchantEntry();assert.equal(modal,null);assert.equal(count,2);
});

test('管理中台只在偏好设置的折叠分组里出现',()=>{const xml=fs.readFileSync('pages/main/index.wxml','utf8');const start=xml.indexOf('class="account-group account-more"'),end=xml.indexOf('class="card record-frame"');assert.equal((xml.match(/bindtap="adminConsole"/g)||[]).length,1);assert.ok(xml.indexOf('bindtap="adminConsole"')>start);assert.ok(xml.indexOf('bindtap="adminConsole"')<end);});

test('商家入口根据当前视角切换文案',()=>{const xml=fs.readFileSync('pages/main/index.wxml','utf8');assert.ok(xml.includes("state.role==='商家'?'切回用户':'切为商家'"));});
