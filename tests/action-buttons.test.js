const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const css=fs.readFileSync('styles/liquid-glass.wxss','utf8');

test('主要和次要动作按钮统一为截图中的 72rpx 胶囊尺寸',()=>{
  assert.match(css,/--action-button-h:\s*72rpx/);
  assert.match(css,/\.primary, \.secondary \{[^}]*min-height: var\(--action-button-h\)[^}]*border-radius: 999rpx[^}]*font-size: 25rpx/s);
  assert.match(css,/\.actions button \{[^}]*min-height: var\(--action-button-h\)/s);
  assert.match(css,/\.capture-actions button \{[^}]*min-height: var\(--action-button-h\)/s);
});

test('小型操作按钮保持独立紧凑尺寸',()=>{
  assert.match(css,/\.small \{[^}]*min-height: 56rpx[^}]*font-size: 23rpx/s);
});
