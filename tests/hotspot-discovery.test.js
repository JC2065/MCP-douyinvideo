const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');
const discovery=require('../utils/hotspot-discovery');const store=require('../utils/store');
const rows=[{id:'weibo-1',title:'今天咖啡热榜',platform:'微博',rank:1,url:'https://s.weibo.com/a',fetchedAt:1000},{id:'douyin-1',title:'咖啡新品',platform:'抖音',rank:1},{id:'weibo-2',title:'旅行记录',platform:'微博',rank:2}];
const event=data=>({currentTarget:{dataset:data}});
function harness(file='pages/hotspots/index.js'){let page;let state=store.initial();let route='';const wx={showToast(){},getStorageSync(){},setStorageSync(){},navigateTo(o){route=o.url;}};vm.runInNewContext(fs.readFileSync(file,'utf8'),{require:n=>n.endsWith('/store')?{...store,load:()=>state,save:s=>state=s}:require(path.resolve(path.dirname(file),n)),Page:p=>page=p,wx,Date,setTimeout,clearTimeout});page.data=JSON.parse(JSON.stringify(page.data));page.setData=function(x){Object.assign(this.data,x);};return {page,state,wx,get route(){return route;}};}
test('空榜不回退样例，搜索仅匹配已同步内容且保留名次',()=>{assert.equal(discovery.rows.length,0);assert.equal(discovery.search('咖啡').results.length,0);assert.equal(discovery.search('咖啡',{},rows).results.length,2);assert.equal(discovery.filter(rows,'微博')[1].rank,2);assert.throws(()=>discovery.search(' '));assert.equal(discovery.search('火星',{},rows).results.length,0);});
test('详情保存去重、来源和创作链接使用真实快照',()=>{const h=harness(),p=h.page;p.onLoad({mode:'rank'});p.setData({rows});p.refresh();assert.equal(p.data.visible.length,3);p.data.query='咖啡';p.send();p.mode(event({mode:'chat'}));assert.equal(p.data.visible.length,2);p.platform(event({platform:'微博'}));assert.equal(p.data.visible.length,1);p.detail(event({id:'weibo-1'}));p.save(event({id:'weibo-1'}));p.save(event({id:'weibo-1'}));assert.equal(h.state.ideas.filter(x=>x.hotspotId==='weibo-1').length,1);assert.equal(h.state.ideas[0].source.url,rows[0].url);p.create(event({id:'weibo-1'}));assert.ok(decodeURIComponent(h.route).includes(rows[0].title));});
test('首页平台筛选与保存使用同一真实快照',()=>{const h=harness('pages/main/index.js'),p=h.page;p.onLoad();p.setData({hotspotRows:rows,hotspotMode:'rank'});p.refreshInlineHotspots();assert.equal(p.data.hotspotVisible.length,3);p.hotspotPlatform(event({platform:'微博'}));assert.equal(p.data.hotspotVisible.length,2);p.saveDiscoveredHotspot(event({id:'weibo-1'}));p.saveDiscoveredHotspot(event({id:'weibo-1'}));assert.equal(p.data.state.ideas.filter(x=>x.hotspotId==='weibo-1').length,1);p.createDiscoveredHotspot(event({id:'weibo-1'}));assert.ok(decodeURIComponent(h.route).includes(rows[0].title));});
test('请求失败和旧协议不伪装成功，来源过期状态可见',async()=>{const bad=await discovery.load({request:o=>o.fail()});assert.ok(bad.error);const old=await discovery.load({request:o=>o.success({statusCode:200,data:{schemaVersion:2,rows}})});assert.ok(old.error);const good=await discovery.load({request:o=>o.success({statusCode:200,data:{schemaVersion:1,rows,sources:{}}})});assert.equal(good.rows.length,3);assert.match(discovery.status({sources:{w:{platform:'微博',fetchedAt:1000,status:'stale'}}},'微博'),/更新延迟/);});
test('离开页面后不再应用延迟响应',async()=>{let finish;let count=0;const page={};discovery.start(page,{request:o=>finish=o.success},()=>count++);discovery.stop(page);finish({statusCode:200,data:{schemaVersion:1,rows,sources:{}}});await Promise.resolve();assert.equal(count,0);});
test('所有热点页面事件都有处理函数，路由与入口完整',()=>{for(const file of ['hotspots','main']){const h=harness(`pages/${file}/index.js`);const xml=fs.readFileSync(`pages/${file}/index.wxml`,'utf8');for(const [,name] of xml.matchAll(/(?:bind|catch)\w+="(\w+)"/g))assert.equal(typeof h.page[name],'function',name);}assert.ok(JSON.parse(fs.readFileSync('app.json')).pages.includes('pages/hotspots/index'));});

test('升温与新入榜隔离缓存，按上升幅度排序且保留证据',()=>{
 const list=discovery.decorate([
  {...rows[0],trend:'rising',rankChange:3,previousRank:4,comparisonSeconds:600,comparedAt:1000,rankTrail:[{at:1000,rank:4},{at:1600,rank:1}]},
  {...rows[1],trend:'rising',rankChange:8},
  {...rows[2],trend:'rising',rankChange:20,stale:true},
  {id:'new',platform:'微博',rank:8,trend:'new'},
  {id:'baseline',platform:'微博',rank:9,trend:'baseline'}]);
 assert.deepEqual(discovery.select(list,'综合','rising').map(r=>r.id),['douyin-1','weibo-1']);
 assert.deepEqual(discovery.select(list,'微博','new').map(r=>r.id),['new']);
 assert.match(list[0].trendLabel,/上升3位/);assert.match(list[0].evidence,/4.*1/);assert.equal(list[0].trail.length,2);
 assert.match(list[2].trendLabel,/趋势暂停/);assert.equal(discovery.select(list,'综合','rank').length,5);
});

test('搜索词留在推荐区，可重搜且去重保留最近六项',()=>{const p=harness('pages/main/index.js').page;p.onLoad();p.setData({hotspotRows:rows,hotspotQuery:'咖啡'});p.hotspotSend();assert.deepEqual(Array.from(p.data.hotspotKeywords),['咖啡']);p.hotspotSuggest(event({query:'咖啡'}));assert.equal(p.data.hotspotKeywords.length,1);assert.equal(p.data.hotspotMode,'chat');for(let i=0;i<8;i++){p.setData({hotspotQuery:'词'+i});p.hotspotSend();}assert.equal(p.data.hotspotKeywords.length,6);assert.equal(p.data.hotspotKeywords[0],'词7');const xml=fs.readFileSync('pages/main/index.wxml','utf8');assert.ok(xml.includes('AI帮我总结最近热点'));for(const label of ['正在升温','新上榜','完整榜'])assert.ok(xml.includes(label));});

test('AI总结传递平台和档案偏好并展示服务端失败，不伪造成功内容',async()=>{
 let options;const module={exports:{}};vm.runInNewContext(fs.readFileSync('utils/hotspot-discovery.js','utf8'),{module,require:n=>n.includes('service-endpoints')?{BASE:'https://youai888.top/youai'}:{send:(_,o)=>options=o}});
 const result=module.exports.summarize({},'微博','关注真实生活趋势');assert.equal(options.url,'https://youai888.top/youai/hotspots/summary');assert.equal(options.data.platform,'微博');assert.equal(options.data.preference,'关注真实生活趋势');options.success({statusCode:503,data:{error:'暂无可用热点'}});await assert.rejects(result,/暂无可用热点/);
 const good=module.exports.summarize({},'综合');assert.equal(options.data.preference,'');options.success({statusCode:200,data:{text:'摘要',sources:[]}});assert.equal((await good).text,'摘要');
});

test('搜索词排在平台词条前面，选择关注词可看到匹配榜单',()=>{const xml=fs.readFileSync('pages/main/index.wxml','utf8');assert.ok(xml.indexOf('wx:for="{{watchKeywords}}"')<xml.indexOf('wx:for="{{hotspotPlatforms}}"'));const p=harness('pages/main/index.js').page;p.onLoad();p.setData({hotspotRows:rows,hotspotQuery:'咖啡'});p.hotspotSend();assert.equal(p.data.watchKeywords[0],'咖啡');assert.equal(p.data.watchKeyword,'咖啡');p.setData({hotspotMode:'rank'});p.refreshInlineHotspots();assert.equal(p.data.hotspotVisible.length,2);p.hotspotPlatform(event({platform:'微博'}));assert.equal(p.data.watchKeyword,'');assert.equal(p.data.hotspotVisible.length,2);});
test('内容搜索和关注接口分开，查询编码且关注身份由服务端决定',async()=>{let request;const query=discovery.lookup({request:o=>{request=o;o.success({statusCode:200,data:{items:[{title:'来源内容'}],ranked:[]}});}},'向日葵 花');assert.ok(request.url.includes(encodeURIComponent('向日葵 花')));assert.equal((await query).items.length,1);const bad=discovery.lookup({request:o=>o.fail()},'关键词');await assert.rejects(bad,/连接失败/);});

test('关注达到20项时拒绝增加新词，不悄悄挤掉旧关注',()=>{const p=harness('pages/main/index.js').page;p.onLoad();const words=Array.from({length:20},(_,i)=>'词'+i);p.setData({watchKeywords:words,hotspotQuery:'新关键词'});p.hotspotSend();assert.match(p.data.hotspotError,/最多关注20/);assert.deepEqual(Array.from(p.data.watchKeywords),words);});
