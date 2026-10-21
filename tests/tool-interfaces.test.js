const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const config=require('../utils/tool-interfaces');
function api(){const cache={};return {cache,getStorageSync:key=>cache[key],setStorageSync:(key,value)=>cache[key]=JSON.parse(JSON.stringify(value)),showToast(){},showModal:options=>options.success({confirm:true})};}
const custom={source:'personal',url:'https://api.example.com/extract',method:'POST',auth:'bearer',token:'private-token'};
function page(wx){let p;vm.runInNewContext(fs.readFileSync('pages/tool-interfaces/index.js','utf8'),{require:n=>n.endsWith('tool-interfaces')?config:{baseUrl:'http://localhost'},Page:value=>p=value,wx});p.setData=function(value){Object.assign(this.data,value);};return p;}
const event=data=>({currentTarget:{dataset:data}});

test('六工具默认公共只读，缓存不能伪造公共服务或管理员权限',()=>{
 const wx=api();wx.cache[config.KEY]={role:'admin',download:{source:'public',publicServiceId:'forged',allowCustom:false,url:custom.url,token:'public-key'}};
 const state=config.load(wx);
 assert.equal(config.tools.length,6);
 for(const tool of config.tools){assert.ok(tool.allowCustom);const resolved=config.resolve(state,tool.id);assert.equal(resolved.ready,tool.id==='download');assert.equal(resolved.serviceId,tool.id==='download'?'youai-reference-parser-v1':'');assert.ok(Object.isFrozen(tool));}
 assert.equal(state.role,undefined);assert.equal(state.download.publicServiceId,undefined);assert.equal(state.download.token,'');
 assert.throws(()=>config.save(wx,'unknown',custom),/工具不存在/);
 assert.throws(()=>config.save(wx,'download',{...custom,source:'admin'}),/接口来源/);
});

test('个人配置分工具保存与重开，切换公共不覆盖个人草稿，清除不影响其他工具',()=>{
 const wx=api();config.save(wx,'download',custom);config.save(wx,'audio',{...custom,url:'https://audio.example.com'});
 let state=config.load(wx);assert.equal(state.download.token,custom.token);assert.equal(config.resolve(state,'download').ready,false);assert.match(config.resolve(state,'download').status,/等待连接检测/);assert.equal(config.resolve(state,'download').token,undefined);
 config.markCheck(wx,'download',true,Date.now());state=config.load(wx);assert.equal(config.resolve(state,'download').ready,true);assert.deepEqual(config.connection(state,'download'),{baseUrl:custom.url,token:custom.token});
 config.save(wx,'download',{source:'public',url:'https://unsaved.example.com',token:'unsaved'});
 state=config.load(wx);assert.equal(state.download.url,custom.url);assert.equal(state.download.token,custom.token);assert.equal(config.resolve(state,'download').source,'public');
 config.clear(wx,'download');state=config.load(wx);assert.equal(state.download.token,'');assert.equal(state.download.url,'');assert.equal(state.audio.token,custom.token);
 const otherDevice=api();assert.equal(config.load(otherDevice).audio.token,'');
});

test('非法接口和认证在保存前拒绝，不发送请求或污染已有配置',()=>{
 const wx=api();config.save(wx,'download',custom);const before=JSON.stringify(wx.cache);
 for(const url of ['http://example.com','https://name:password@example.com','javascript:alert(1)','https://example.com/#hash','https://a b.com'])assert.throws(()=>config.save(wx,'download',{...custom,url}),/HTTPS/);
 for(const token of ['', 'bad\r\nheader', 'a'.repeat(2001)])assert.throws(()=>config.save(wx,'download',{...custom,token}),/令牌/);
 assert.throws(()=>config.save(wx,'download',{...custom,method:'DELETE'}),/GET 或 POST/);
 assert.throws(()=>config.save(wx,'download',{...custom,auth:'invalid'}),/认证方式/);
 assert.equal(JSON.stringify(wx.cache),before);
 config.save(wx,'download',{...custom,auth:'none'});assert.equal(config.load(wx).download.token,'');
});

test('损坏缓存降级，个人配置不完整时不会显示可用或回退公共服务',()=>{
 const wx=api();wx.cache[config.KEY]={download:{source:'personal',url:'broken',auth:'bearer',token:42}};
 const resolved=config.resolve(config.load(wx),'download');assert.equal(resolved.ready,false);assert.equal(resolved.source,'personal');
 wx.getStorageSync=()=>{throw Error('storage unavailable');};assert.equal(config.load(wx).download.source,'public');
});

test('管理页保存最终表单值、校验、取消丢弃和清除确认',()=>{
 const wx=api(),p=page(wx);p.onLoad({tool:'transcript'});assert.equal(p.data.selected,'transcript');
 p.source(event({source:'personal'}));p.auth(event({value:'bearer'}));p.save({detail:{value:{url:custom.url,token:custom.token}}});assert.equal(p.data.error,'');assert.equal(p.data.dirty,false);assert.equal(config.load(wx).transcript.token,custom.token);
 p.field({...event({field:'url'}),detail:{value:custom.url}});assert.equal(p.data.dirty,false,'late duplicate input events must not dirty a saved form');
 p.field({...event({field:'url'}),detail:{value:'http://invalid'}});p.save({});assert.match(p.data.error,/HTTPS/);
 wx.showModal=o=>o.success({confirm:false});p.select(event({id:'audio'}));assert.equal(p.data.selected,'transcript');p.clear();assert.equal(config.load(wx).transcript.token,custom.token);
 wx.showModal=o=>o.success({confirm:true});p.select(event({id:'audio'}));assert.equal(p.data.selected,'audio');p.select(event({id:'transcript'}));p.clear();assert.equal(p.data.source,'public');assert.equal(config.load(wx).transcript.token,'');
 p.onLoad({tool:'invalid'});assert.equal(p.data.selected,'download');
});

test('管理页存储失败显示错误，不提示保存成功',()=>{
 const wx=api(),p=page(wx);p.onLoad();wx.setStorageSync=()=>{throw Error('存储空间不足');};wx.showToast=()=>assert.fail('must not report success');p.save({});assert.equal(p.data.error,'存储空间不足');
});

test('参考解析配置可检测并在失败或过期时阻止使用',()=>{
 const wx=api();wx.request=options=>options.success({statusCode:200,data:{status:'ready'}});const p=page(wx);p.onLoad({tool:'download'});p.source(event({source:'personal'}));p.save({detail:{value:{url:custom.url,token:custom.token}}});assert.equal(p.data.status,'配置已保存，等待连接检测');p.check();assert.equal(config.resolve(config.load(wx),'download').ready,true);assert.equal(p.data.status,'个人配置已检测');
 config.markCheck(wx,'download',false);assert.equal(config.resolve(config.load(wx),'download').ready,false);
 config.markCheck(wx,'download',true,Date.now()-8*24*60*60*1000);assert.match(config.resolve(config.load(wx),'download').status,/已过期/);
});

test('头像身份切换与接口入口分层，角色切换不提升接口权限',()=>{
 const xml=fs.readFileSync('pages/main/index.wxml','utf8');assert.equal((xml.match(/bindtap="merchantEntry"/g)||[]).length,1);assert.equal((xml.match(/bindtap="switchRole"/g)||[]).length,0);assert.ok(!xml.includes('class="account-week"'));assert.ok(xml.indexOf('bindtap="toolInterfaces"')>xml.indexOf('wx:if="{{accountMore}}"'));
 let main;const wx=api();let route='';wx.navigateTo=o=>route=o.url;
 vm.runInNewContext(fs.readFileSync('pages/main/index.js','utf8'),{require:n=>require(path.resolve('pages/main',n)),Page:p=>main=p,wx});main.persist=()=>{};main.toast=()=>{};
 config.save(wx,'audio',custom);const before=JSON.stringify(config.load(wx));main.switchRole();assert.equal(main.data.state.role,'商家');main.switchRole();assert.equal(main.data.state.role,'个人');assert.equal(JSON.stringify(config.load(wx)),before);
 main.toolInterfaces();assert.equal(route,'/pages/tool-interfaces/index');for(const tool of config.tools){main.toolEntry(event({tool:tool.id}));assert.equal(route,'/pages/creation-tool/index?tool='+tool.id);}
 const p=page(wx);for(const [,handler] of fs.readFileSync('pages/tool-interfaces/index.wxml','utf8').matchAll(/bind\w+="(\w+)"/g))assert.equal(typeof p[handler],'function',handler);
});
