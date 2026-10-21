const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

test('圈出的辅助文案删除，标题、空状态和创作入口保留', () => {
  const xml = fs.readFileSync('pages/main/index.wxml', 'utf8');
  for (const title of ['创作工具', '我的创作']) {
    assert.ok(xml.includes(`<view class="section">${title}</view>`)||xml.includes(`bindtap="toggleCreative"><text>${title}</text>`),title);
  }
  assert.ok(!xml.includes('按视频形式 · 每天轮换'));
  assert.ok(!xml.includes('{{state.works.length}} 份作品'));
  for (const binding of ['bindtap="toolEntry"', 'bindtap="editor"', 'bindtap="settings"']) {
    assert.ok(xml.includes(binding), binding);
  }
  assert.ok(xml.includes('你的第一份作品，从上方工具开始。'));
});

function files(dir) {
  return fs.readdirSync(dir, {withFileTypes:true}).flatMap(entry => {
    const file = path.join(dir, entry.name);
    return entry.isDirectory() ? files(file) : [file];
  });
}

test('各页面和共享拆解入口不再展示测试或开发阶段提示', () => {
  const targets = [...files('pages'), ...files('templates'), 'case-study/study-page.js', 'utils/hotspot-discovery.js'];
  for (const file of targets.filter(file => /\.(wxml|js)$/.test(file))) {
    const text = fs.readFileSync(file, 'utf8').replaceAll('演示证据', '');
    assert.doesNotMatch(text, /测试|演示|模拟数据|模拟结算|\bdemo\b/i, file);
  }
});

test('热点无样例兜底，无匹配反馈明确当前同步范围', () => {
 const discovery=require('../utils/hotspot-discovery');
 assert.equal(discovery.rows.length,0);
 assert.match(discovery.search('火星基地').message,/没有匹配结果/);
 assert.match(discovery.search('火星基地').message,/已同步榜单/);
});
