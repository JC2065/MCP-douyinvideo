const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const dp = require('../utils/daily-pick');

const cases = [
  { id: 1, form: '图文型', title: 'a' },
  { id: 2, form: '图文型', title: 'b' },
  { id: 3, form: '动图视频', title: 'c' },
];

test('同一天同一形式推荐稳定，跨天轮换', () => {
  const d1 = '2026-10-09T10:00:00+08:00';
  const d1b = '2026-10-09T22:00:00+08:00';
  const d2 = '2026-10-10T08:00:00+08:00';
  assert.equal(dp.pick(cases, '图文型', d1).id, dp.pick(cases, '图文型', d1b).id, 'same day same pick');
  assert.notEqual(dp.pick(cases, '图文型', d1).id, dp.pick(cases, '图文型', d2).id, 'rotates next day');
  assert.equal(dp.pick(cases, '动图视频', d1).id, 3, 'single-case form always returns it');
});

test('空形式返回 null，默认形式跳过空分类', () => {
  assert.equal(dp.pick(cases, '空镜头视频'), null, 'empty form returns null');
  assert.equal(dp.defaultForm(cases), '图文型', 'first non-empty form');
  assert.equal(dp.defaultForm([]), '纯文字型', 'fallback to first form');
});

test('拆学首屏以工作台替代每日一拆，保留视频与模板入口',()=>{
 const xml=fs.readFileSync('pages/main/index.wxml','utf8');const js=fs.readFileSync('pages/main/index.js','utf8');
 assert.ok(!xml.includes('每日一拆')&&!xml.includes('dailyForms'));
 const study=xml.slice(xml.indexOf("<block wx:if=\"{{tab==='拆学'}}\">"),xml.indexOf("<block wx:if=\"{{tab==='任务'}}\">"));
 assert.ok(study.includes('拆解工作台')&&study.includes('bindtap="settings"')&&study.includes('bindtap="videoStudio"'));
 assert.ok(study.indexOf('study-workbench')<study.indexOf('learning-filters'));
 assert.ok(js.includes("'灵感','创作','拆学','任务','我的'"));
});

test('全部案例都标注了视频形式', () => {
  const refs = [require('../utils/case87')].concat(require('../utils/local-cases'), require('../utils/video-cases'));
  assert.ok(refs.length >= 8, 'reference cases present');
  for (const c of refs) assert.ok(dp.FORMS.includes(c.form), `case ${c.id} has valid form`);
  assert.ok(new Set(refs.map(c => c.form)).size >= 2, 'multiple forms covered');
});
