const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const dayFeed = require(path.resolve('utils', 'day-feed'));
const ideaCalendar = require(path.resolve('utils', 'idea-calendar'));

const at = day => new Date(day + 'T10:00:00+08:00').getTime();
const today = day => (day === ideaCalendar.dayKey() ? Date.now() - 600000 : at(day));
const cases = [{ id: 201, title: '洗发水案例', tag: '情绪种草', goal: '表达香气体验' }, { id: 202, title: '沐浴露案例', tag: '情绪种草', goal: '用情境引起兴趣' }];

test('当天汇总只取当天完成的点子、作品与收藏', () => {
  const state = {
    ideas: [{ id: 1, createdAt: today('2026-10-09'), text: '今天的点子' }, { id: 2, createdAt: at('2026-10-08'), text: '昨天的点子' }],
    works: [{ id: 11, createdAt: today('2026-10-09'), title: '今天改的作品' }, { id: 12, updatedAt: at('2026-10-07'), title: '前天的作品' }],
    favorites: [201, 202],
    favoriteAt: { 201: '2026-10-09', 202: '2026-10-05' }
  };
  const feed = dayFeed.build(state, cases, '2026-10-09');
  assert.equal(feed.ideas.length, 1);
  assert.equal(feed.works.length, 1);
  assert.deepEqual(feed.favorites.map(c => c.id), [201]);
  assert.equal(feed.total, 3);
});

test('未标日期数据归入 unknown，不伪造日期', () => {
  const state = {
    ideas: [{ id: 1, text: '没有日期的旧点子' }],
    works: [{ id: 'old-work', title: '没有时间戳的旧作品' }],
    favorites: [202],
    favoriteAt: { 201: '2026-10-09' }
  };
  const unknown = dayFeed.build(state, cases, 'unknown');
  assert.equal(unknown.ideas.length, 0, '点子由日历自己的未标日期列表处理，避免重复');
  assert.equal(unknown.works.length, 1);
  assert.deepEqual(unknown.favorites.map(c => c.id), [202]);
  assert.equal(unknown.total, 2);
  assert.equal(dayFeed.build(state, cases, '2026-10-09').total, 0);
});

test('缺少收藏时间表时容错为空，不报错', () => {
  const feed = dayFeed.build({ ideas: [], works: [], favorites: [201] }, cases, '2026-10-09');
  assert.equal(feed.favorites.length, 0);
  assert.equal(feed.total, 0);
});

test('作品优先用更新时间，其次创建时间，最后回退到 id 时间戳', () => {
  assert.equal(dayFeed.workDay({ id: at('2026-10-01'), createdAt: at('2026-10-03'), updatedAt: at('2026-10-05') }), '2026-10-05');
  assert.equal(dayFeed.workDay({ id: at('2026-10-01'), createdAt: at('2026-10-03') }), '2026-10-03');
  assert.equal(dayFeed.workDay({ id: at('2026-10-01') }), ideaCalendar.dayKey(at('2026-10-01')));
  assert.equal(dayFeed.workDay({ id: 'no-timestamp' }), '');
});

test('当天及未标日期的创作资产纳入日历记录',()=>{
  const feed=dayFeed.build({ideas:[],works:[],favorites:[]},cases,'2026-10-09',[{key:'video:v',kind:'video',time:today('2026-10-09')},{key:'text:t',kind:'text',time:at('2026-10-09')},{key:'chat:c',kind:'chat' }]);
  assert.equal(feed.assets.length,2);assert.equal(feed.total,2);assert.equal(dayFeed.assetDay({time:at('2026-10-09')}),'2026-10-09');
  assert.equal(dayFeed.build({},cases,'unknown',[{kind:'analysis'}]).assets.length,1);
});

test('图片作品与其他作品一起按实际时间进入当天日历明细',()=>{const assets=require('../utils/creative-assets').merge({},[],{images:[{id:'image',createdAt:at('2026-10-09')/1000,status:'done'}]});const feed=dayFeed.build({},[], '2026-10-09',assets);assert.equal(feed.total,1);assert.equal(feed.assets[0].kind,'image');assert.equal(feed.assets[0].label,'图片作品');});
