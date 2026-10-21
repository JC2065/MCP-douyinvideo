const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');

const xml = fs.readFileSync('pages/main/index.wxml', 'utf8');
const js = fs.readFileSync('pages/main/index.js', 'utf8');

test('创作工具板块位于入口行与我的创作之间', () => {
  const entry = xml.indexOf('class="entry-row"');
  const grid = xml.indexOf('创作工具');
  const works = xml.indexOf('我的创作');
  assert.ok(entry > 0 && grid > entry && works > grid, 'section order: entry-row -> 创作工具 -> 我的创作');
  assert.ok(xml.includes('wx:for="{{creationTools}}"'), 'tool grid loops creationTools');
  assert.ok(xml.includes('bindtap="toolEntry"'), 'tool item triggers toolEntry');
});

test('创作工具数据与可执行工作台入口', () => {
  assert.ok(js.includes('creationTools:['), 'creationTools defined in data');
  for (const name of ['全网视频下载', '视频文案提取', '视频音频提取', '图片去水印', '视频封面提取', '提词器']) {
    assert.ok(js.includes(`name:'${name}'`), `tool ${name} present`);
  }
  assert.ok(js.includes("'/pages/creation-tool/index?tool='+tool.icon"), 'toolEntry opens selected executable tool');
  assert.ok(xml.includes('data-tool="{{item.icon}}"'));
  assert.ok(!js.includes('演示版即将上线'));
});

test('六个创作工具工作台已注册并提供媒体处理和本地提词交互',()=>{
  const app=fs.readFileSync('app.json','utf8'),page=fs.readFileSync('pages/creation-tool/index.js','utf8'),view=fs.readFileSync('pages/creation-tool/index.wxml','utf8');
  assert.ok(app.includes('pages/creation-tool/index'));
  for(const id of ['download','transcript','audio','eraser','cover','teleprompter'])assert.ok(page.includes(`${id}:`),id);
  for(const behavior of ["'/tools/run'",'saveVideoToPhotosAlbum','saveImageToPhotosAlbum','exportFile','togglePlay','speed(e)','font(e)','mirror()'])assert.ok(page.includes(behavior),behavior);
  for(const binding of ['bindtap="run"','bindtap="copyText"','bindtap="saveAsset"','bindtap="togglePlay"','bindtap="mirror"'])assert.ok(view.includes(binding),binding);
  assert.ok(view.includes('当前输出平台解析获得的无水印原片'));
});

test('三个创作入口使用一主两辅布局并直达对应视频创作起点', () => {
  const block = xml.match(/<view class="entry-row">([\s\S]*?)<view class="section">创作工具/);
  assert.ok(block, 'entry block exists');
  assert.equal((block[1].match(/<button /g) || []).length, 3);
  assert.equal((block[1].match(/class="entry entry-primary"/g) || []).length, 1);
  assert.equal((block[1].match(/class="entry entry-compact"/g) || []).length, 2);
  assert.equal((block[1].match(/bindtap="videoStudio"/g) || []).length, 3);
  for (const source of ['idea', 'douyin', 'command']) assert.ok(block[1].includes(`data-source="${source}"`));
  for (const copy of ['一句话出作品', '爆款拆解复刻', '爆款口令']) assert.ok(block[1].includes(copy));
  for (const icon of ['inspiration-selected.png', 'create-selected.png', 'sparkle-selected.png']) assert.ok(block[1].includes(icon));
});

test('六个创作工具使用统一蓝色线性图标，保留名称和点击区域',()=>{assert.ok(xml.includes('src="/assets/icons/{{item.icon}}-selected.png"'));assert.ok(!xml.includes('<text class="tool-glyph">'));for(const name of ['download','transcript','audio','eraser','cover','teleprompter']){assert.ok(js.includes("icon:'"+name+"'"));const svg=fs.readFileSync('assets/icons/'+name+'-selected.svg','utf8');assert.ok(svg.includes('stroke="#075dcc"'));assert.ok(svg.includes('stroke-width="1.9"'));assert.ok(svg.includes('fill="none"'));}});

test('参考视频为主入口，工具隐藏解释且保持六种稳定工具ID',()=>{assert.match(xml,/entry entry-primary[^>]*data-source="douyin"/);assert.doesNotMatch(xml,/class="tool-desc"/);assert.match(fs.readFileSync('pages/main/index.wxss','utf8'),/height:98rpx/);});

test('创作和拆学去掉顶部说明，三个入口仅展示图标和名称',()=>{assert.ok(!xml.includes('从一个选题，开始你的短视频创作。'));assert.ok(!xml.includes('看懂案例，把好方法用进创作。'));const block=xml.slice(xml.indexOf('<view class="entry-row">'),xml.indexOf('<view class="section">创作工具'));assert.doesNotMatch(block,/entry-hint|entry-kicker/);assert.match(fs.readFileSync('pages/main/index.wxss','utf8'),/entry-row\{height:192rpx/);});

test('三个创作入口增高约30%，拆学页可切换优秀作品和优秀项目',()=>{const css=fs.readFileSync('pages/main/index.wxss','utf8');assert.match(css,/entry-row\{height:192rpx/);assert.ok(xml.includes('优秀作品')&&xml.includes('优秀项目'));assert.ok(xml.includes('短视频创作加速计划'));});
test('爆款拆解复刻是首屏第一视觉：整行蓝色大卡片 + 大标题 + 开始拆解按钮，另外两个入口并排在下方',()=>{
  assert.match(xml,/data-source="douyin" bindtap="videoStudio"><view class="hero-top">[\s\S]*?<text class="entry-title">爆款拆解复刻<\/text><text class="hero-sub">[\s\S]*?<view class="hero-go">开始拆解 ›<\/view><\/button>/);
  const css=fs.readFileSync('pages/main/index.wxss','utf8');assert.match(css,/\.entry-row \.entry-primary\{[^}]*width:100%;min-height:236rpx/);assert.match(css,/\.entry-primary \.entry-title\{[^}]*font-size:46rpx/);assert.match(css,/\.entry-row \.entry-secondary\{display:flex;flex-direction:row/);
});
