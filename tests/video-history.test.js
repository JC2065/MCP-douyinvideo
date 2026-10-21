const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const history=require('../utils/video-history');
test('三类来源生成可辨识标题并保存标准来源',()=>{
 const idea=history.create({sourceType:'idea',idea:'下班后的治愈晚餐。',time:1});
 const douyin=history.create({sourceType:'douyin',idea:'参考这个抖音视频的内容结构',reference:{title:'大家都抽到了吗 #雾子 #守望先锋'},time:2});
 const command=history.create({sourceType:'command',idea:'模板内容',theme:'秋天的桂花拿铁',time:3});
 assert.equal(idea.title,'下班后的治愈晚餐');assert.equal(idea.sourceLabel,'点子创作');
 assert.equal(douyin.title,'大家都抽到了吗');assert.equal(douyin.sourceLabel,'抖音参考');
 assert.equal(command.title,'秋天的桂花拿铁');assert.equal(command.sourceLabel,'模板口令');
});
test('旧历史兼容为带时间的来源标题，资产状态明确',()=>{const old=history.normalize({id:'old',sourceType:'douyin',idea:'',time:new Date(2026,9,12,3,5).getTime(),url:'x'});assert.match(old.title,/抖音参考 · 10-12 03:05/);assert.equal(old.assetStatus,'仅保留成片记录');assert.equal(history.normalize({...old,assetUrl:'/asset-runs/old'}).assetStatus,'已保存资产包');});
test('创作资产展示作品、灵感、AI交流和拆解分类，保持云端同步与失败可重试',()=>{const xml=fs.readFileSync('pages/video-assets/index.wxml','utf8'),js=fs.readFileSync('pages/video-assets/index.js','utf8');for(const text of ['作品','灵感','AI交流','拆解','云端','点击重试'])assert.ok(xml.includes(text));assert.ok(js.includes('assets.cloud'));assert.ok(js.includes('account.cached(wx)?.userId!==user'));assert.ok(js.includes('assets.route(row)'));});
