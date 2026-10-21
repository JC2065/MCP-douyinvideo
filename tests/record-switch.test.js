const fs = require('fs');
const test = require('node:test');
const assert = require('node:assert');

const xml = fs.readFileSync('pages/main/index.wxml', 'utf8');

test('记录开关提供 收藏/作品/点子/日历 四种视图', () => {
  const sw = xml.match(/<view class="record-switch">([\s\S]*?)<\/view><\/view>/);
  assert.ok(sw, 'record-switch exists');
  const btns = sw[1].match(/<button /g) || [];
  assert.equal(btns.length, 4, 'four switch buttons');
  for (const mode of ['favorites', 'works', 'list', 'calendar']) {
    assert.ok(sw[1].includes(`data-mode="${mode}"`), `mode ${mode} present`);
  }
  assert.ok(sw[1].includes('>收藏<') && sw[1].includes('>作品<') && sw[1].includes('>点子<') && sw[1].includes('>日历<'), 'four labels');
  assert.ok(sw[1].indexOf('data-mode="favorites"') < sw[1].indexOf('data-mode="works"'), 'favorites sits left of works');
});

test('收藏视图展示已收藏的学习案例并支持查看拆解', () => {
  assert.ok(xml.includes(`recordMode==='favorites'`) && xml.includes(`wx:for="{{cases}}"`), 'favorites loops cases');
  assert.ok(xml.includes(`wx:if="{{item.favorited}}"`), 'only favorited cases shown');
  const favorites=xml.slice(xml.indexOf(`<block wx:elif="{{recordMode==='favorites'}}">`),xml.indexOf(`<block wx:elif="{{recordMode==='works'}}">`));
  assert.ok(favorites.includes('class="record-item record-favorite"'), 'favorites use shared card');
  assert.ok(favorites.includes('class="record-item-actions single"'), 'favorite action stays at card bottom');
  assert.ok(xml.includes('还没有收藏，去「拆学」里打开一个案例试试。'), 'favorites empty state');
});

test('作品视图在固定滚动区内展示并支持打开编辑', () => {
  assert.ok(xml.includes(`wx:for="{{state.works}}"`), 'works loop in record panel');
  assert.ok(xml.includes(`bindtap="editor">打开编辑`), 'works open editor link');
  const works=xml.slice(xml.indexOf(`<block wx:elif="{{recordMode==='works'}}">`),xml.indexOf('<block wx:else>',xml.indexOf(`<block wx:elif="{{recordMode==='works'}}">`)));
  assert.ok(works.includes('class="record-item record-work"'), 'works use shared card');
  assert.ok(works.includes('已保存 {{item.versions.length}} 个版本'), 'works retain version information');
  assert.ok(xml.includes('还没有作品，去「创作」开始你的第一份方案。'), 'works empty state');
});

test('四个视图共用同一个展示框', () => {
  const start = xml.indexOf('class="card record-frame"');
  const end = xml.indexOf("view==='command'", start);
  assert.ok(start > 0 && end > start, 'record frame bounds found');
  const frame = xml.slice(start, end);
  assert.ok(frame.includes('class="record-switch"'), 'switch lives inside the frame');
  assert.ok(frame.includes('class="record-panel"'), 'content viewport lives inside the frame');
  assert.ok(frame.includes('class="idea-calendar"'), 'calendar view lives inside the frame');
  assert.ok(xml.includes(`wx:if="{{recordCount}}"`), 'one count drives the scroll viewport');
});

test('日历视图向下滑动展示当天的点子、作品与收藏', () => {
  assert.ok(xml.includes('点子 {{calendar.records.length}}'), 'day feed groups ideas');
  assert.ok(xml.includes('作品 {{dayFeed.works.length}}'), 'day feed groups works');
  assert.ok(xml.includes('收藏 {{dayFeed.favorites.length}}'), 'day feed groups favorites');
  assert.ok(xml.includes('创作资产 {{dayFeed.assets.length}}'), 'day feed groups creative assets');
  const scroll = xml.indexOf('class="record-scroll"');
  assert.ok(scroll > 0 && xml.indexOf('class="idea-calendar"') > scroll, 'calendar scrolls inside the shared viewport');
  assert.ok(xml.includes('向下滑动查看'), 'day feed hints at scrolling');
});

test('当天内容使用统一卡片层级和明确操作区', () => {
  for (const type of ['record-idea', 'record-work', 'record-favorite']) assert.ok(xml.includes(type), type + ' card exists');
  for (const label of ['灵感记录', '创作方案', '收藏案例']) assert.ok(xml.includes(label), label + ' label exists');
  assert.ok(xml.includes('class="record-item-head"'), 'card header exists');
  assert.ok(xml.includes('class="record-item-actions"'), 'card actions exist');
  assert.ok(xml.includes('>生成视频</button>') && xml.includes('>开始创作</button>'), 'idea actions are concise');
  assert.ok(!xml.includes('把想法变成作品 →'), 'old link copy removed');
});

test('日历使用贡献热力图强度，月份统计和今天合并为单行', () => {
  assert.ok(xml.includes('class="calendar-toolbar"'), 'calendar toolbar exists');
  assert.ok(xml.includes('class="calendar-stats"'), 'monthly stats are in toolbar');
  assert.ok(!xml.includes('class="calendar-summary"') && !xml.includes('class="calendar-legend"'), 'summary row and legend removed');
  assert.ok(xml.includes("item.key?'day-valid':'day-empty'"), 'blank month cells are identified');
  assert.ok(xml.includes('class="today-dot"'), 'today has an independent marker');
  assert.ok(xml.includes("item.selected?'day-selected':''"), 'selected day is independent from intensity');
});

test('记录位于我的快捷入口和偏好设置之后，灵感仅保留输入和热点',()=>{const mine=xml.indexOf("tab==='我的'");const records=xml.indexOf('class="card record-frame"');assert.ok(records>mine);assert.ok(records>xml.indexOf('class="account-shortcuts"'));assert.ok(records>xml.indexOf('class="account-row admin-entry'));const inspiration=xml.slice(xml.indexOf("tab==='灵感'"),xml.indexOf("tab==='创作'",xml.indexOf("tab==='灵感'")));assert.ok(!inspiration.includes('record-frame'));});
