const test=require('node:test'),assert=require('node:assert/strict'),a=require('../utils/creative-assets');
test('方案、文字、视频、灵感、AI交流和拆解统一汇总，视频本机与云端去重',()=>{const rows=a.merge({works:[{id:1,title:'方案',text:'脚本'}],ideas:[{id:2,text:'灵感'}]},[{id:'v',url:'old',title:'视频'}],{videos:[{id:'v',url:'signed',title:'视频'}],texts:[{id:'t',text:'正文',createdAt:2}],chats:[{id:'c',text:'我与AI对话',time:3000}]},[{id:'r',title:'拆解'}]);assert.equal(rows.length,6);assert.equal(new Set(rows.map(r=>r.key)).size,6);assert.equal(rows.find(r=>r.kind==='video').url,'signed');assert.equal(rows[0].kind,'chat');assert.ok(a.route(rows.find(r=>r.kind==='text')).includes('textId=t'));assert.ok(a.route(rows.find(r=>r.kind==='analysis')).includes('analysis-records'));});
test('我的创作覆盖独立产物，账号表单邮箱不伪装已绑定',()=>{const fs=require('node:fs'),xml=fs.readFileSync('pages/main/index.wxml','utf8'),js=fs.readFileSync('pages/main/index.js','utf8');assert.ok(xml.includes('wx:for="{{creativeWorks}}"'));assert.ok(js.includes("['draft','video','text','image','analysis','replica']"),'爆款拆解和复刻也进我的创作');for(const t of ['保存资料','邮箱仅保存，暂未验证绑定。','拆解记录','优秀作品'])assert.ok(xml.includes(t));assert.ok(!xml.includes('src="/assets/icons/learn-selected.png" mode="aspectFit"/></view>'));});
const vm=require('node:vm'),fs=require('node:fs');
test('资料保存成功刷新头像昵称邮箱，失败保留输入且可重试',async()=>{let page,fail=false,submitted;const toasts=[];vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:n=>n.endsWith('/account')?{save:async(api,data)=>{submitted=data;if(fail)throw Error('邮箱无效');return {phoneBound:true,nickname:data.nickname,avatar:data.avatar,email:data.email,emailVerified:false};}}:n.endsWith('creator-preferences')?{profile:()=>({})}:n.endsWith('store')?{initial:()=>({})}:n.endsWith('learning')?{cases:[],hotspots:[],hotspotDiscovery:{platforms:[]}}:{},Page:p=>page=p,wx:{}});page.setData=v=>Object.assign(page.data,v);page.toast=t=>toasts.push(t);page.setData({accountProfile:{phoneBound:true},editNickname:'新昵称',editEmail:'creator@example.com',editAvatar:2});await page.saveAccountProfile();assert.equal(submitted.email,'creator@example.com');assert.equal(page.data.accountProfile.nickname,'新昵称');assert.equal(page.data.accountProfile.emailVerified,false);assert.equal(toasts.at(-1),'资料已保存');fail=true;await page.saveAccountProfile();assert.equal(page.data.profileError,'邮箱无效');assert.equal(page.data.editEmail,'creator@example.com');assert.equal(page.data.profileSaving,false);});

test('本机方案毫秒时间不会被当作秒放大，最新生成作品正常置顶',()=>{const now=Date.now();const rows=a.merge({works:[{id:1,createdAt:now-10000}]},[],{texts:[{id:'new',createdAt:now/1000}]});assert.equal(rows[0].id,'new');assert.equal(rows[1].time,now-10000);});

test('仅保存编辑过的发布标题和封面也在资产列表复用',()=>{const data={},api={getStorageSync:k=>data[k],setStorageSync:(k,v)=>data[k]=v};require('../utils/publication-draft').save(api,'work',{title:'保存的新标题',coverPath:'/local/cover',platforms:[]});const rows=a.decorate(api,a.merge({},[],{texts:[{id:'work',title:'原始标题'}]}));assert.equal(rows[0].title,'保存的新标题');assert.equal(rows[0].coverPath,'/local/cover');});

test('云端视频通过账号授权资产入口重开，不写入旧的共享本机视频索引',()=>{const row=a.merge({},[],{videos:[{id:'owned',url:'/assets/owned/final.mp4'}]})[0];assert.equal(row.cloud,true);assert.ok(a.route(row).includes('runId=owned'));});

test('图片作品归入创作资产并保留时间、状态和重新打开路由',()=>{const rows=a.merge({},[],{images:[{id:'image-one',title:'猫',status:'done',createdAt:1700000000,url:'/image-assets/x.png'}]});assert.equal(rows[0].kind,'image');assert.equal(rows[0].label,'图片作品');assert.equal(rows[0].time,1700000000000);assert.ok(a.route(rows[0]).includes('imageId=image-one'));});
test('内容创作页底部「最近生成」换成「我的创作」：同一份列表，默认展开、可收起，点开各自作品',()=>{
 const fs=require('node:fs'),xml=fs.readFileSync('pages/video/index.wxml','utf8'),js=fs.readFileSync('pages/video/index.js','utf8');
 assert.ok(!xml.includes('最近生成'));assert.match(xml,/data-tab="drafts" catchtap="creativeTabPick">我的创作<\/text><text class="creative-sep">\/<\/text><text[^>]*data-tab="works" catchtap="creativeTabPick">我的作品<\/text>/);assert.match(xml,/bindtap="toggleCreative"/);assert.match(xml,/<block wx:if="\{\{!creativeClosed\}\}">/,'默认展开（creativeClosed 未设置）');
 assert.match(js,/onShow\(\)\{this\.refreshCreative\(\);/);assert.match(js,/CREATIVE_KINDS=\['draft','video','text','image','analysis','replica'\]/);
 assert.match(js,/if\(row\.kind==='draft'\)return wx\.reLaunch\(\{url:'\/pages\/main\/index\?workId='/);
});
test('内容创作页去掉「1/3·内容拆解」和两个记录链接；我的创作/我的作品切换：过程 vs 成品',()=>{
 const fs=require('node:fs'),vm=require('node:vm'),xml=fs.readFileSync('pages/video/index.wxml','utf8'),js=fs.readFileSync('pages/video/index.js','utf8');
 assert.ok(!xml.includes('1/3·内容拆解'));assert.ok(!xml.includes('bindtap="analysisRecords"')&&!xml.includes('bindtap="textHistory">我的文字作品'),'删掉两个记录链接');
 const m=js.match(/const isFinished=(r=>[^\n]*)/);const isFinished=vm.runInNewContext(m[1]);
 assert.equal(isFinished({kind:'video'}),true);assert.equal(isFinished({kind:'text'}),true);assert.equal(isFinished({kind:'replica',status:'done'}),true);
 assert.equal(isFinished({kind:'analysis'}),false);assert.equal(isFinished({kind:'draft'}),false);assert.equal(isFinished({kind:'replica',status:'running'}),false);
});
test('我的创作卡片：状态和「打开拆解」在同一行，卡片更矮',()=>{
 const fs=require('node:fs'),xml=fs.readFileSync('pages/video/index.wxml','utf8');assert.match(xml,/<view class="creative-foot"><text class="muted">\{\{item\.kind==='draft'\?item\.status:item\.stage\|\|'已保存'\}\}<\/text><text class="link">/);
 assert.match(fs.readFileSync('pages/video/index.wxss','utf8'),/\.creative-foot\{display:flex;justify-content:space-between/);
});
