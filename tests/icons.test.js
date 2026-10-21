const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {variants,svg}=require('../scripts/generate-icons.cjs');
test('图标资产完整、可复建并使用透明三倍分辨率 PNG',()=>{
  for(const {name,state} of variants){
    const base=`assets/icons/${name}-${state}`;
    assert.equal(fs.readFileSync(base+'.svg','utf8').trim(),svg(name,state));
    const png=fs.readFileSync(base+'.png');
    assert.equal(png.subarray(1,4).toString(),'PNG');
    assert.equal(png.readUInt32BE(16),84);
    assert.equal(png.readUInt32BE(20),84);
    assert.equal(png[25],6,'RGBA transparency');
  }
});
test('五个导航有独立常态和选中态，文字和点击绑定保留',()=>{
  const wxml=fs.readFileSync('pages/main/index.wxml','utf8');
  const nav=wxml.slice(wxml.lastIndexOf('<view class="nav">'));
  for(const name of ['inspiration','create','learn','tasks','profile']){
    assert.ok(nav.includes(name));
    assert.notEqual(fs.readFileSync(`assets/icons/${name}-default.png`).compare(fs.readFileSync(`assets/icons/${name}-selected.png`)),0);
  }
  assert.ok(nav.includes("tab===item?'selected':'default'"));
  assert.ok(nav.includes('bindtap="tab"'));
  assert.ok(nav.includes('<text>{{item}}</text>'));
  assert.ok(!/[✧✎▤▣○]/.test(nav));
  for(const match of wxml.matchAll(/src="(\/assets\/icons\/[^{}"]+)"/g)) assert.ok(fs.existsSync('.'+match[1]),match[1]);
});
