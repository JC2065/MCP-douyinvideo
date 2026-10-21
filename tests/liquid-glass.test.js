const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const css = fs.readFileSync('styles/liquid-glass.wxss', 'utf8');
const rule = selector => {
  const start = css.indexOf(selector + ' {');
  assert.ok(start >= 0, `Missing ${selector}`);
  return css.slice(start, css.indexOf('}', start));
};

test('所有页面使用全局主题，浮动导航不会遮挡底部内容', () => {
  assert.match(fs.readFileSync('app.wxss', 'utf8'), /@import "styles\/liquid-glass.wxss";/);
  assert.match(rule('.shell'), /180rpx \+ env\(safe-area-inset-bottom\)/);
  assert.match(rule('.nav'), /18rpx \+ env\(safe-area-inset-bottom\)/);
  assert.match(rule('.nav-item'), /min-height: 96rpx/);
  assert.match(rule('button'), /min-height: 88rpx/);
  for (const dir of ['case-study', 'study-201', 'study-202', 'study-203', 'study-204']) {
    assert.match(fs.readFileSync(`${dir}/index.wxss`, 'utf8'), /templates\/study.wxss/);
  }
});

test('玻璃主题提供无模糊回退和减少动态透明度选项', () => {
  assert.match(rule('.nav'), /background: rgba\(243,248,255,\.94\)/);
  assert.match(css, /@supports.*backdrop-filter/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /@media \(prefers-reduced-transparency: reduce\)/);
  assert.match(css, /backdrop-filter: none/);
  assert.match(css, /transition: none/);
});

function luminance(hex) {
  const channels = hex.match(/[a-f\d]{2}/gi).map(value => {
    const n = parseInt(value, 16) / 255;
    return n <= .04045 ? n / 12.92 : ((n + .055) / 1.055) ** 2.4;
  });
  return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
}
test('正文、辅助文字与操作色在最深背景满足普通文字对比度', () => {
  const colors = Object.fromEntries([...css.matchAll(/--glass-(\w+): (#[a-f\d]{6})/g)].map(m => [m[1], m[2]]));
  for (const color of Object.values(colors)) {
    assert.ok((luminance('d5e9fb') + .05) / (luminance(color) + .05) >= 4.5, color);
  }
});

test('紧凑布局减少内容留白但保留主要按钮和导航触达尺寸',()=>{
  assert.match(rule('.card'),/padding: 20rpx; margin: 12rpx/);
  assert.match(rule('.capture textarea'),/height: 120rpx/);
  assert.match(rule('.case'),/padding: 0/);
  assert.match(css,/\.case \{ display: flex; align-items: stretch;/);
  assert.match(rule('.case .cover'),/width: 166rpx/);
  assert.match(rule('button'),/min-height: 88rpx/);
  assert.match(rule('.nav-icon'),/width: 48rpx; height: 48rpx/);
  assert.match(rule('.idea-actions'),/display: flex; flex-wrap: wrap/);
  assert.ok(fs.readFileSync('pages/main/index.wxml','utf8').includes('class="record-item-actions"'));
});

test('学习筛选横向滚动、收藏固定，案例显示标题和独立元数据',()=>{
 const xml=fs.readFileSync('pages/main/index.wxml','utf8');
 assert.match(xml,/<scroll-view class="category-scroll" scroll-x/);
 assert.match(xml,/<\/scroll-view><text class="chip favorite-filter/);
 assert.match(xml,/class="case-meta"/);
 assert.match(xml,/wx:if="{{item.duration}}"/);
 assert.match(rule('.learning-case .cover'),/height: 116rpx/);
 assert.match(rule('.category-scroll'),/min-width: 0/);
 assert.match(rule('.learning-case .case-title'),/overflow-wrap: break-word/);
});
