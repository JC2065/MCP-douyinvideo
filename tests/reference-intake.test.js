const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const platform=require('../utils/link-platform');const notice=require('../utils/link-notice');
test('link platform routing matches the server rules',()=>{
 assert.equal(platform.detect('3.02 nDH:/ https://v.douyin.com/V2-jkijASP8/ 复制此链接').url,'https://v.douyin.com/V2-jkijASP8/');
 assert.equal(platform.detect('https://v.kuaishou.com/x').platform,'kuaishou');assert.match(platform.detect('https://v.kuaishou.com/x').message,/上传原视频/);
 assert.equal(platform.detect('文字').platform,'none');assert.equal(platform.detect('https://a.example.com/b').platform,'unknown');
 const py=fs.readFileSync('scripts/link-platform.py','utf8');for(const id of ['douyin','kuaishou','xiaohongshu','bilibili','weixin'])assert.ok(py.includes("'"+id+"'"),id);
});
test('usage notice (incl. content recognition) snoozes for one hour only when asked',()=>{
 const store={};const api={getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;}};
 assert.equal(notice.shouldShow(api,1000),true);notice.snooze(api,1000);assert.equal(notice.shouldShow(api,1000+59*60000),false);assert.equal(notice.shouldShow(api,1000+61*60000),true);assert.match(notice.RECOGNITION,/自动开始内容识别.*模型费用/);
});
function mixin(){const calls=[];let state={};const wx={getStorageSync:()=>undefined,setStorageSync(){},chooseMedia:o=>o.success({tempFiles:[{tempFilePath:'tmp/v.mp4',size:1024}]}),
  uploadFile:o=>{calls.push(o);o.success({statusCode:200,data:JSON.stringify({status:'acquired',platform:'upload',asset:{sha256:'a'.repeat(64),sizeBytes:2048,media:{width:1080,height:1920,durationSeconds:12}}})});return {onProgressUpdate(){}};},login:o=>o.success({code:'c'}),request:o=>o.success({statusCode:200,data:{token:'t',expiresAt:9e9}})};
 const ctx={wx,require:n=>require('../utils/'+n.replace('./','')),module:{exports:{}},Date,JSON,Promise,clearTimeout,setTimeout};
 vm.runInNewContext(fs.readFileSync('utils/reference-intake.js','utf8'),ctx);const m=ctx.module.exports;
 const page={...m,data:{},setData(v){Object.assign(this.data,v);},checked:0,checkReference(){this.checked++;},confirmAnalysis(r){this.confirmed=r;}};return {page,calls};}
test('pasting a supported link shows the three-button notice; each button does what it says',()=>{
 const {page}=mixin();page.intakeLink('https://v.douyin.com/abc/');assert.equal(page.data.linkNotice,true);assert.equal(page.checked,0);
 page.linkNoticeAccept();assert.equal(page.checked,1);assert.equal(page.data.linkNotice,false);assert.equal(page._analysisConsent,true,'确认使用说明即同意开始识别，取到视频后不再弹二次确认');
 page.intakeLink('https://v.douyin.com/abc/');page.setData({sourceValue:'https://v.douyin.com/abc/'});page.linkNoticeAbort();assert.equal(page._analysisConsent,false);assert.equal(page.data.sourceValue,'');assert.equal(page.checked,1);
 page.intakeLink('https://v.kuaishou.com/x');assert.equal(page.data.referenceStatus,'failed');assert.equal(page.data.linkNotice,false);
});
test('uploading the original video reuses the acquired-reference path',async()=>{
 const {page,calls}=mixin();page.chooseReferenceVideo();await new Promise(r=>setImmediate(r));await new Promise(r=>setImmediate(r));
 assert.ok(calls[0].url.endsWith('/references/upload'));assert.equal(calls[0].name,'file');
 assert.equal(page.data.referenceStatus,'acquired');assert.equal(page.data.reference.platform,'upload');assert.equal(page.confirmed.platform,'upload');
 const brief=require('../utils/video-brief');assert.equal(brief.normalizeSource({type:'douyin',value:'',reference:page.data.reference}).value,'upload:'+'a'.repeat(64));
});
test('video page wires the notice, upload button and intake mixin',()=>{
 const wxml=fs.readFileSync('pages/video/index.wxml','utf8');for(const t of ['linkNoticeUpload','linkNoticeAbort','linkNoticeAccept','chooseReferenceVideo','1 小时内不再提示','我知道了，开始识别','{{linkNoticeRecognition}}'])assert.ok(wxml.includes(t),t);
 assert.ok(wxml.indexOf('linkNoticeUpload')<wxml.indexOf('linkNoticeAbort')&&wxml.indexOf('linkNoticeAbort')<wxml.indexOf('linkNoticeAccept'));
 const js=fs.readFileSync('pages/video/index.js','utf8');assert.match(js,/^const referenceIntake=require\('\.\.\/\.\.\/utils\/reference-intake'\);/m);assert.match(js,/this\.intakeLink\(value\)/);assert.match(js,/this\.applyReference\(result\)/);
 assert.match(fs.readFileSync('scripts/Dockerfile.video','utf8'),/scripts\/link-platform\.py/);
});
test('quick look result shows while the full watch runs, and the card shows type, value shares and screen text',async()=>{
 const {page}=mixin();page._sourceVersion=3;let sent;page.request=(path,method,data)=>{sent={path,data};return Promise.resolve({status:'ready',overview:'一位女生在客厅跳手势舞'});};
 page.requestGlance({asset:{sha256:'a'.repeat(64)}});await new Promise(r=>setImmediate(r));
 assert.equal(sent.path,'/references/glance');assert.equal(page.data.glance.overview,'一位女生在客厅跳手势舞');
 page.request=()=>Promise.resolve({status:'ready',overview:'旧结果'});page.requestGlance({});page._sourceVersion=4;await new Promise(r=>setImmediate(r));assert.equal(page.data.glance,null);
 const wxml=fs.readFileSync('pages/video/index.wxml','utf8');for(const t of ['glance-line','大致是：','valueShares','screenText.items','屏幕文字（自动识别）',"content-watch-5"])assert.ok(wxml.includes(t),t);
 const js=fs.readFileSync('pages/video/index.js','utf8');assert.match(js,/setTimeout\(\(\)=>\{this\.quickGlance\(reference\);this\.startBoard\(reference\);\},0\)/,'分析任务创建后立刻先看一眼');
 page.request=()=>Promise.resolve({status:'ready',overview:'x'});page._sourceVersion=5;assert.equal(await page.requestGlance({}),'ready','返回结果给按钮收尾');
 page.request=()=>Promise.reject(Error('x'));assert.equal(await page.requestGlance({}),'none');
});
test('识别预计时长：按视频时长估，攒够两次记录后按本机实际速度估；超时显示慢一些',()=>{
 const eta=require('../utils/analysis-eta');const store={};const api={getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;}};const ref=d=>({asset:{media:{durationSeconds:d}}});
 assert.equal(eta.estimate(api,ref(20)),130);assert.equal(eta.estimate(api,{}),120);assert.equal(eta.estimate(api,ref(1)),35);
 eta.record(api,ref(10),80);assert.equal(eta.estimate(api,ref(20)),130,'只有一次记录时仍按时长估');eta.record(api,ref(20),120);eta.record(api,ref(10),70);assert.equal(eta.estimate(api,ref(30)),210,'中位数 7 秒/秒');
 assert.equal(eta.text(40,130),'已等待 40 秒 · 预计约 2 分 10 秒');assert.equal(eta.text(150,130),'已等待 150 秒 · 比预计慢一些，快好了');assert.equal(eta.text(5,0),'已等待 5 秒');
 const js=fs.readFileSync('pages/video/index.js','utf8');assert.match(js,/if\(this\._analysisConsent\)\{this\._analysisConsent=false;return this\.analyzeReference\(reference\);\}wx\.showModal/);
});
test('上传原视频右侧「开始解析」：粘贴后自动解析时显示「正在解析」和动效；删掉了旧提示',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');assert.ok(!xml.includes('只有视频文件获取并验证成功后'));assert.ok(xml.indexOf('chooseReferenceVideo')<xml.indexOf('bindtap="parseTap"'));
 for(const t of ["正在获取视频","正在看大致内容","完整理解中 · 见下方","开始识别","重新解析","开始解析",'parse-fill'])assert.ok(xml.includes(t),t);
 const css=fs.readFileSync('pages/video/index.wxss','utf8');assert.match(css,/@keyframes parse-flow/);assert.match(css,/@keyframes parse-sheen/);assert.match(css,/\.parse-fill::after\{/);
 const js=fs.readFileSync('pages/video/index.js','utf8');assert.match(js,/parsePct:0,parseFlash:'',quickBusy:false/,'每次解析从 0% 开始');assert.match(js,/parsePct:100,parseFlash:state==='ready'\?'大致内容已出 100%'/,'大致内容出来就满格');assert.ok(!/analysisPercent:100,analysisStep:3,parsePct/.test(js),'按钮不再跟完整理解走');
 assert.match(js,/parseTap\(\)\{/);assert.match(js,/this\.referenceTimer=setTimeout\(\(\)=>this\.intakeLink\(value\),400\)/,'粘贴后仍自动开始');
});
test('识别进度里先显示「大致内容」：等待时转圈提示，拿到后显示，拿不到就不占位',async()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');const card=xml.slice(xml.indexOf('class="card analysis-state'),xml.indexOf('id="analysis-result"'));
 assert.ok(card.indexOf('analysis-track')<card.indexOf('glance-box'));assert.ok(card.indexOf('glance-box')<card.indexOf('不想等？后台排队'));assert.ok(!card.includes('代表帧从各时间段中间取样'));
 const ctx={wx:{},require:n=>require('../utils/'+n.replace('./','')),module:{exports:{}},Date,JSON,Promise,clearTimeout,setTimeout};vm.runInNewContext(fs.readFileSync('utils/reference-intake.js','utf8'),ctx);const m=ctx.module.exports;
 for(const [reply,want] of [[{status:'ready',overview:'女生对口型'},'ready'],[{status:'pending'},'none']]){const page={...m,data:{},_sourceVersion:1,setData(v){Object.assign(this.data,v);},request:()=>Promise.resolve(reply)};page.requestGlance({});assert.equal(page.data.glanceState,'loading');await new Promise(r=>setImmediate(r));assert.equal(page.data.glanceState,want);}
});
test('胶囊进度条：预计时间内走到 90%，超时缓慢逼近 99%，不会倒退或满格',()=>{
 const eta=require('../utils/analysis-eta');assert.equal(eta.percent(0,100),2);assert.equal(eta.percent(50,100),45);assert.equal(eta.percent(100,100),90);
 const a=eta.percent(150,100),b=eta.percent(300,100);assert.ok(a>90&&b>a&&b<=99,a+' '+b);assert.equal(eta.percent(5000,100),99);assert.equal(eta.percent(10,0),0);
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');assert.ok(xml.indexOf("glance-box")<xml.indexOf("正在进行深度解析……")&&xml.indexOf("正在进行深度解析……")<xml.indexOf("class=\"eta-bar\"")&&xml.indexOf("class=\"eta-bar\"")<xml.indexOf("queue-inline"),"进度条在大致内容下方、排队按钮上方");assert.match(xml,/style="width:\{\{analysisPercent\}\}%"/,"进度卡走完整理解，按钮走大致内容");
});
test('识别等待时的创作小提示：进度卡下方，识别中 4–6 秒轮换，点击换下一条',()=>{
 const tips=require('../utils/creation-tips');assert.ok(tips.TIPS.length>=15);assert.ok(tips.TIPS.every(t=>t.length<=40),'提示要短');assert.equal(tips.pick(tips.TIPS.length),tips.TIPS[0]);
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');assert.ok(xml.indexOf('class="card analysis-state')<xml.indexOf('class="tip-card"'));assert.ok(xml.indexOf('class="tip-card"')<xml.indexOf('id="analysis-result"'));assert.match(xml,/class="tip-card" bindtap="nextTip"/);
 const js=fs.readFileSync('pages/video/index.js','utf8');assert.match(js,/4000\+Math\.floor\(Math\.random\(\)\*2000\)/);assert.match(js,/!this\.tipWaiting\(\)\)\{this\.tipTimer=null;return;\}/,'等待结束就停止轮换');
});
test('等「大致内容」出来再翻到下一屏：快速阶段输入区不收起、不滚动，进度卡/提示/问题都先不出现',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8')+fs.readFileSync('pages/video/board.wxml','utf8'),js=fs.readFileSync('pages/video/index.js','utf8');
 assert.equal((xml.match(/!inputOpen&&!quickBusy/g)||[]).length,2,'输入区折叠等快速阶段结束');
 assert.match(xml,/analysisStatus!=='idle'&&!quickBusy&&\(analysisStatus!=='done'\|\|progressOpen\)/);assert.match(xml,/class="tip-card"/);assert.match(xml,/analysisStatus==='running'&&!quickBusy\}\}" class="card board-questions"/);
 assert.ok(!/quickBusy:true,parsePct:Math\.max\(this\.data\.parsePct\|\|0,55\)\}\);this\.nextTip\(\);this\.scrollToBlock/.test(js),'开始识别时不再立刻滚动');
 assert.match(js,/this\.setData\(\{parseFlash:'',quickBusy:false\}\);if\(this\.data\.analysisStatus==='running'\)this\.scrollToBlock\('analysis-progress'\)/,'大致内容出来后才翻页');
});
test('识别进行中不再在标题右侧显示「已等待 · 预计」，下方深度解析已有百分比',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');assert.match(xml,/<text wx:if="\{\{analysisStatus!=='running'\}\}" class="reference-elapsed">\{\{analysisElapsed\}\}<\/text>/);
});
test('创作小提示精简：去掉标签和「换一条」，开头小灯泡，单行更矮；点一下仍换下一条',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8'),i=xml.indexOf('class="tip-card"'),card=xml.slice(i,xml.indexOf('</view></view>',i));
 assert.ok(card.includes('bindtap="nextTip"'));assert.ok(card.includes('<text class="tip-icon">💡</text>'));assert.ok(!card.includes('tip-tag')&&!card.includes('换一条 ›'));
 assert.match(fs.readFileSync('pages/video/index.wxss','utf8'),/\.tip-text\{margin-top:0;[^}]*min-height:0\}/);
});
test('等待阶段都有创作小提示：获取视频、看大致内容、深度拆解时出现在「下一步…」上方；一直轮换到等待结束',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8'),js=fs.readFileSync('pages/video/index.js','utf8');
 const i=xml.indexOf('tip-card tip-wait');assert.ok(i>0&&i<xml.indexOf('class="section creative-head"'),'小提示在我的创作上方');assert.match(xml,/referenceStatus==='checking'\|\|quickBusy\|\|\(boardPct>0&&boardPct<100\)\)&&!tipsOff\}\}" class="tip-card tip-wait"/);
 assert.match(js,/tipWaiting\(\)\{const d=this\.data;if\(d\.tipsOff\)return false;return d\.analysisStatus==='running'\|\|d\.referenceStatus==='checking'\|\|!!d\.quickBusy\|\|\(d\.boardPct>0&&d\.boardPct<100\);\}/);
 assert.match(js,/this\.startReferenceProgress\(\);this\.nextTip\(\);/);assert.match(fs.readFileSync('utils/board-page.js','utf8'),/this\.setData\(\{boardPct:2\}\);if\(this\.nextTip\)this\.nextTip\(\);/);
});
test('长按创作小提示可关闭：24 小时内不显示，同一账号累计第 3 次关闭后永久不显示',()=>{
 const tips=require('../utils/creation-tips');const store={'youai.account.profile.v1':{userId:'u1'}};const api={getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;}};
 const t0=1_000_000_000_000,DAY=86400000;assert.equal(tips.hidden(api,t0),false);
 let r=tips.close(api,t0);assert.equal(r.count,1);assert.equal(r.permanent,false);assert.equal(tips.hidden(api,t0+DAY-1),true);assert.equal(tips.hidden(api,t0+DAY+1),false,'24 小时后恢复');
 tips.close(api,t0+2*DAY);r=tips.close(api,t0+4*DAY);assert.equal(r.count,3);assert.equal(r.permanent,true);assert.equal(tips.hidden(api,t0+400*DAY),true,'第 3 次后永久');
 store['youai.account.profile.v1']={userId:'u2'};assert.equal(tips.hidden(api,t0+400*DAY),false,'按账号分开');
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');assert.equal((xml.match(/bindlongpress="tipMenu"/g)||[]).length,2,'两处小提示都能长按');assert.equal((xml.match(/&&!tipsOff\}\}" class="tip-card/g)||[]).length,2);
});
test('输入框为空时有「点这里粘贴」：读剪贴板直接填入并开始解析；部分不对/完全不对作为备选更矮',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');assert.match(xml,/class="paste-chip" bindtap="pasteClipboard"/);
 const js=fs.readFileSync('pages/video/index.js','utf8');assert.match(js,/pasteClipboard\(\)\{wx\.getClipboardData\(\{success:r=>\{const value=String\(r&&r\.data\|\|''\)\.trim\(\);/);assert.match(js,/this\.input\(\{detail:\{value:value\.slice/);
 assert.match(fs.readFileSync('pages/video/index.wxss','utf8'),/\.board-actions button\.board-alt\{height:40rpx/);
});
test('参考视频页第一视觉是粘贴框：加高加边框；首页入口文案不限定平台',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');assert.match(xml,/class="card capture \{\{sourceType==='douyin'\?'capture-hero':''\}\}"><textarea class="\{\{sourceType==='douyin'\?'capture-link':''\}\}"/);
 assert.match(fs.readFileSync('pages/video/index.wxss','utf8'),/\.capture-link\{width:100%;min-height:300rpx/);
 const main=fs.readFileSync('pages/main/index.wxml','utf8');assert.ok(main.includes('粘贴链接就能开始')&&!main.includes('粘贴抖音链接就能开始'));
});
test('小提示只占一行：超长时左右滚动（图标固定），停留时间按滚动时长延长',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8'),css=fs.readFileSync('pages/video/index.wxss','utf8');
 assert.equal((xml.match(/<text class="tip-icon">💡<\/text><view class="tip-viewport tip-anim-\{\{tipFlip\}\}"><view class="tip-track/g)||[]).length,2,'图标在滚动区外面，不跟着动');
 assert.match(css,/\.tip-viewport\{flex:1;min-width:0;overflow:hidden;white-space:nowrap\}/);assert.match(css,/@keyframes tipMarquee\{0%,18%\{transform:translateX\(0\)\}82%,100%\{transform:translateX\(var\(--tip-shift\)\)\}\}/);
 const vm=require('node:vm'),js=fs.readFileSync('pages/video/index.js','utf8'),src=js.match(/\nmeasureTip\(schedule\)\{[\s\S]*?\}\);\},\n/)[0].trim().replace(/,$/,'');const page=vm.runInNewContext('({'+src+'})',{Math});let scheduled=0;page.data={};page.setData=function(x){Object.assign(this.data,x);};page.stopped=false;
 page.createSelectorQuery=()=>{const q={selectAll(){return q;},boundingClientRect(){return q;},exec(cb){cb([[{width:0},{width:200}],[{width:0},{width:480}]]);}};return q;};
 page.measureTip(ms=>{scheduled=ms;});assert.equal(page.data.tipShift,288);assert.ok(page.data.tipDur>=4);assert.ok(scheduled>=page.data.tipDur*2000,'滚完一个来回再换下一条');
 page.data.tipShift=0;page.createSelectorQuery=()=>{const q={selectAll(){return q;},boundingClientRect(){return q;},exec(cb){cb([[{width:200}],[{width:150}]]);}};return q;};page.measureTip(()=>{throw Error('短提示不滚动');});assert.equal(page.data.tipShift,0);
});
