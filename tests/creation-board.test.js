const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function board(responses={}){const calls=[];const store={};const timers=[];
 const wx={showToast(){},setClipboardData(o){o.success&&o.success();},navigateTo(o){calls.push({nav:o.url});},getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;},chooseMedia(){},uploadFile(){},saveVideoToPhotosAlbum(){},downloadFile(){}};
 const ctx={wx,module:{exports:{}},require:n=>n.includes('video-service')?{baseUrl:'https://api.example.com'}:{session:()=>Promise.resolve({token:'t'})},setInterval:(f)=>{timers.push(f);return timers.length;},clearInterval(){},setTimeout:(f)=>{timers.push(f);return timers.length;},clearTimeout(){},JSON,Number,Object,Math,Promise,String};
 vm.runInNewContext(fs.readFileSync('utils/board-page.js','utf8'),ctx);
 const page={...ctx.module.exports,data:{reference:{asset:{sha256:'a'.repeat(64)},analysis:{analyzerVersion:'content-watch-5'}}},_sourceVersion:1,setData(v){for(const [k,val] of Object.entries(v)){if(k.includes('.')||k.includes('[')){const parts=k.replace(/\[(\d+)\]/g,'.$1').split('.');let o=this.data;for(const p of parts.slice(0,-1)){o[p]=o[p]??{};o=o[p];}o[parts.at(-1)]=val;}else this.data[k]=val;}},
  request(path,method,data){calls.push({path,method,data});const v=responses[path];return Promise.resolve(typeof v==='function'?v(data):v||{});}};
 return {page,calls,timers,store};}
const tick=()=>new Promise(r=>setImmediate(r));
const SESSION={id:'b'.repeat(32),attempt:1,card:{overview:'女生跳手势舞',valueShares:[{key:'text',label:'文字',percent:60}],confidence:0.9,timeline:[{start:0,end:3,what:'握拳'}]},plan:{name:'通用拆解'},suggestion:{basis:['同一博主'],strength:'strong'},questions:{mode:'probe',items:[]},countdownSeconds:8,answers:{}};
test('board session starts with the analysis, refreshes when ready and counts down to an automatic confirm',async()=>{
 const {page,calls,timers}=board({'/board/session':SESSION,'/board/refresh':SESSION,'/board/confirm':{...SESSION,confirmed:true},'/board/breakdown':{...SESSION,breakdown:{fields:[{key:'positioning',label:'一句话定位',format:'text',value:'x'}]}}});
 await page.startBoard(page.data.reference);assert.equal(calls[0].path,'/board/session');assert.equal(calls[0].data.reference.asset.sha256,'a'.repeat(64));
 await page.boardReady();assert.equal(page.data.boardCountdown,5,'自动开始最多等 5 秒');assert.equal(page.data.boardRecommend,'text');
 for(let i=0;i<5;i++)timers[0]();await tick();await tick();
 const confirm=calls.find(c=>c.path==='/board/confirm');assert.equal(confirm.data.auto,true);assert.equal(confirm.data.verdict,'ok');
 assert.ok(calls.some(c=>c.path==='/board/breakdown'));
});
test('touching the card pauses the countdown; partial verdict sends corrections, statement and chosen plan',async()=>{
 const {page,calls}=board({'/board/session':SESSION,'/board/refresh':SESSION,'/board/confirm':SESSION,'/board/breakdown':SESSION});
 await page.startBoard(page.data.reference);await page.boardReady();page.boardPause();assert.equal(page.data.boardCountdown,0);
 page.boardVerdict({currentTarget:{dataset:{verdict:'partial'}}});page.boardFixInput({currentTarget:{dataset:{index:0}},detail:{value:'双手比心'}});
 page.boardStatementInput({detail:{value:'这其实是反差萌剧情'}});page.setData({boardPlans:[{id:'p1',name:'我的'}]});page.boardPlanPick({detail:{value:'0'}});
 await page.boardConfirm({currentTarget:{dataset:{verdict:'partial'}}});
 const confirm=calls.find(c=>c.path==='/board/confirm').data;assert.deepEqual(JSON.parse(JSON.stringify(confirm.corrections)),[{index:0,text:'双手比心'}]);assert.equal(confirm.statement,'这其实是反差萌剧情');assert.equal(confirm.planId,'p1');assert.equal(confirm.auto,false);
});
test('outputs, adjustments, teleprompter and publishing call the board API',async()=>{
 const {page,calls,store}=board({'/board/output/text':{...SESSION,outputs:{text:{lines:[{text:'新一句'}],titles:['标题'],hashtags:['话题']}}},'/board/output/package':{...SESSION,outputs:{package:{shots:[{line:'台词'}],script:''}}},'/board/adjust':SESSION,'/board/works':{id:'c'.repeat(32)}});
 page.boardSet({...SESSION});
 await page.boardOutput({currentTarget:{dataset:{route:'text'}}});assert.equal(page.data.boardRoute,'text');
 page.boardCopyText();
 page.setData({boardAdjust:'多看台词'});await page.boardAdjustSend({currentTarget:{dataset:{save:'1'}}});assert.equal(calls.find(c=>c.path==='/board/adjust').data.save,true);
 await page.boardOutput({currentTarget:{dataset:{route:'package'}}});page.boardTeleprompter();assert.equal(store['youai-teleprompter-script'],'台词');
 await page.boardPublish();assert.ok(calls.some(c=>c.nav==='/pages/board-work/index?id='+'c'.repeat(32)));
});
test('pages, include and server wiring are registered',()=>{
 const app=JSON.parse(fs.readFileSync('app.json','utf8'));for(const p of ['pages/board-work/index','pages/board-plans/index'])assert.ok(app.pages.includes(p),p);
 const index=fs.readFileSync('pages/video/index.wxml','utf8');assert.ok(index.includes('<include src="board.wxml"/>'));
 const wxml=fs.readFileSync('pages/video/board.wxml','utf8');const methods=require('../utils/board-page');
 for(const m of wxml.matchAll(/(?:bind|catch)\w+="(\w+)"/g))assert.equal(typeof methods[m[1]],'function',m[1]);
 assert.match(fs.readFileSync('pages/video/index.js','utf8'),/^const boardPage=require\('\.\.\/\.\.\/utils\/board-page'\);/m);
 const server=fs.readFileSync('scripts/video-server.py','utf8');for(const t of ["'/board/confirm'","'/board/output/text'","board-media","BOARD.tick()"])assert.ok(server.includes(t),t);
 for(const page of ['pages/board-work/index','pages/board-plans/index']){const js=fs.readFileSync(page+'.js','utf8');let def;vm.runInNewContext(js,{require:()=>({}),Page:p=>def=p,wx:{}});for(const m of fs.readFileSync(page+'.wxml','utf8').matchAll(/(?:bind|catch)\w+="(\w+)"/g))assert.equal(typeof def[m[1]],'function',page+':'+m[1]);}
 assert.match(fs.readFileSync('pages/creation-tool/index.js','utf8'),/youai-teleprompter-script/);
});
test('one submission starts one board session even when analysis finishes before the first start returns',async()=>{
 const {page,calls}=board({'/board/session':SESSION,'/board/refresh':SESSION});
 const first=page.startBoard(page.data.reference);await page.boardReady();await first;
 assert.equal(calls.filter(c=>c.path==='/board/session').length,1);
 page._sourceVersion=2;page.setData({board:null});await page.startBoard(page.data.reference);
 assert.equal(calls.filter(c=>c.path==='/board/session').length,2);
});
test('confirm card buttons stay tappable: the card must not catch touchstart',()=>{
 const wxml=fs.readFileSync('pages/video/board.wxml','utf8');
 assert.doesNotMatch(wxml,/board-confirm"[^>]*catchtouchstart/);assert.match(wxml,/board-confirm"[^>]*bindtouchstart="boardPause"/);
});
test('拆解页按时间顺序往下长：先输入、再进度、再结果，旧内容折叠，新内容出现后滚过去',async()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');const idea=xml.slice(xml.indexOf("<block wx:if=\"{{stage==='idea'}}\">"),xml.indexOf("<block wx:if=\"{{stage==='interview'}}\">"));
 const order=['class="card capture ','bindtap="parseTap"','id="analysis-progress"','class="card analysis-state','id="analysis-result"','class="card watch-card"','<include src="board.wxml"/>','class="section creative-head"'];
 for(let i=1;i<order.length;i++)assert.ok(idea.indexOf(order[i-1])<idea.indexOf(order[i]),order[i]);
 assert.ok(idea.includes('data-key="inputOpen"')&&idea.includes('data-key="progressOpen"'));
 assert.ok(!idea.slice(idea.indexOf('</form>')).includes('form-type="submit"'),'表单外的按钮不用 submit');
 const b=fs.readFileSync('pages/video/board.wxml','utf8');for(const id of ['board-confirm','board-breakdown','board-output'])assert.ok(b.includes('id="'+id+'"'),id);assert.ok(b.includes('data-key="boardDetailOpen"'));
 const {page}=board({'/board/output/text':{...SESSION,breakdown:{fields:[]},outputs:{text:{lines:[]}}}});const scrolled=[];page.scrollToBlock=id=>scrolled.push(id);
 page.data.analysisStatus='done';page.boardSet({...SESSION,sha:'a'});assert.deepEqual(scrolled,['board-confirm']);
 page.boardSet({...SESSION,sha:'a',breakdown:{fields:[]}});assert.equal(scrolled.at(-1),'board-breakdown');
 page.data.boardDetailOpen=true;await page.boardOutput({currentTarget:{dataset:{route:'text'}}});assert.equal(scrolled.at(-1),'board-output');assert.equal(page.data.boardDetailOpen,false);
 page.toggleFold({currentTarget:{dataset:{key:'boardDetailOpen'}}});assert.equal(page.data.boardDetailOpen,true);page.toggleFold({currentTarget:{dataset:{key:'board'}}});assert.ok(page.data.board);
 assert.match(fs.readFileSync('pages/video/index.js','utf8'),/input\(e\)\{[^\n]*inputOpen:false,progressOpen:false,boardDetailOpen:false/);
});
test('长按「我看到的是」及之后的卡片：复制全部或选择部分复制',()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');for(const p of ['confirm','breakdown','text','package'])assert.match(xml,new RegExp('bindlongpress="copyMenu" data-part="'+p+'"|data-part="'+p+'"[^>]*bindlongpress="copyMenu"|bindlongpress="copyMenu"[^>]*data-part="'+p+'"'),p);
 assert.match(xml,/<text user-select="\{\{true\}\}" class="copy-text">/);
 const {page}=board();const copied=[];let sheet;page.data.board={card:{overview:'女生跳手势舞',type:'舞蹈',tags:['手势舞'],timeline:[{start:0,end:3,what:'握拳'}]},breakdown:{planName:'通用拆解',insight:{why:'评论驱动'},fields:[{label:'一句话定位',value:'x'},{label:'能不能学',value:[{item:'极简',how:'固定机位'}]}]},outputs:{text:{lines:[{start:0,end:3,text:'第一句'}],titles:['标题一'],hashtags:['日常']}}};
 assert.equal(page.cardText('confirm'),'我看到的是：女生跳手势舞\n类型：舞蹈  #手势舞\n0–3秒  握拳');
 assert.equal(page.cardText('breakdown'),'拆解卡 · 通用拆解\n为什么火：评论驱动\n【一句话定位】\nx\n【能不能学】\n· 极简（学法：固定机位）');
 assert.equal(page.cardText('text'),'0–3秒  第一句\n标题1：标题一\n#日常');
});
test('长按复制的方法名不与内容创作页已有方法重名',()=>{const js=fs.readFileSync('pages/video/index.js','utf8');for(const n of ['cardText','copyMenu','copyNow','copyAllNow','copyClose','copyNoop'])assert.ok(!new RegExp('[,{\\s]'+n+'\\(').test(js),n);});
test('「我看到的是」右侧超级拆解 / 1:1 复刻：默认超级拆解，选复刻弹出选择，可继续拆解、进入复刻或关闭',()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8'),index=fs.readFileSync('pages/video/index.wxml','utf8');
 assert.match(xml,/我看到的是：<\/view><view class="mode-switch">/);assert.ok(!xml.includes('自备 Key')&&!index.includes('用自己的 Key'));assert.ok(index.includes('title="做私域，有AI"'));
 const {page}=board();let opened=0,modal;page.openReplica=()=>opened++;page.wx=undefined;
 page.boardModePick({currentTarget:{dataset:{mode:'replica'}}});assert.equal(page.data.replicaChoice,true);assert.equal(page.data.boardMode,'replica');
 page.replicaChoiceClose();assert.equal(page.data.replicaChoice,false);assert.equal(page.data.boardMode,'super',"关闭后回到超级拆解");
 page.boardModePick({currentTarget:{dataset:{mode:'replica'}}});page.replicaGo();assert.equal(opened,1);assert.equal(page.data.replicaChoice,false);
});
test('拆解卡阅读顺序：数据依据在顶部收起 → 结论 → 怎么学（展开）→ 结构 → 评论区；能学的按可学程度排',()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');const card=xml.slice(xml.indexOf('id="board-breakdown"'),xml.indexOf('接下来做什么'));
 const order=['数据依据','id="bd-conclusion"','wx:for="{{bdGroups}}"'];for(let k=1;k<order.length;k++)assert.ok(card.indexOf(order[k-1])<card.indexOf(order[k]),order[k]);
 const {bdSections}=require('../utils/board-page');
 const bd=bdSections({fields:[{key:'positioning',format:'text',value:'深夜情绪树洞'},{key:'timeline',format:'timeline',value:[{start:0,end:3,text:'a'},{start:3,end:12,text:'b'}]},{key:'learnable',format:'list',value:[{item:'颜值',level:'低'},{item:'极简画面',level:'高',how:'固定机位'},{item:'文案',level:'中'}]},{key:'hook',format:'text',label:'开头钩子',value:'h'},{key:'screen_text',format:'text',label:'屏幕文字',value:'s'},{key:'cta',format:'text',label:'结尾引导',value:'c'}],
  insight:{why:'评论驱动',commentPlay:'抛问题',topComments:[{text:'x'}],numbers:{ratios:{commentPerLike:0.36,collectPerLike:0.03}}}});
 assert.equal(bd.positioning,'深夜情绪树洞');assert.equal(bd.best.item,'极简画面');assert.equal(bd.data.summary,'评论/赞 0.36 · 收藏/赞 0.03');
 assert.deepEqual(bd.groups.map(g=>g.id),['learn','structure','comments']);assert.deepEqual(bd.groups[0].fields[0].value.map(r=>r.level),['高','中','低']);
 assert.equal(bd.groups[0].summary,'可学高 1 条 · 开头钩子 · 结尾引导');assert.equal(bd.groups[1].summary,'2 段 · 12 秒');assert.equal(bd.groups[2].summary,'打法 + 1 条真实热评');
 const {page}=board();page.boardSet({id:'x',breakdown:{fields:[{key:'learnable',format:'list',value:[{item:'a',level:'高'}]}],insight:{}}});
 assert.equal(JSON.stringify(page.data.bdOpen),JSON.stringify({data:false,conclusion:true,learn:true,structure:true,comments:true,commentsMore:false}),'拆解成功后结论/怎么学/结构/评论区都展开');assert.equal(JSON.stringify(page.data.bdNav.map(n=>n.label)),JSON.stringify(['结论','怎么学']));
 page.bdToggle({currentTarget:{dataset:{key:'data'}}});assert.equal(page.data.bdOpen.data,true);
});
test('数据依据分两类：我读到的信息（原始输入）+ 据此算出的指标',()=>{
 const {bdEvidence}=require('../utils/board-page');
 const ev=bdEvidence({source:{kind:'gallery',imageCount:1,description:'这么晚 还不睡 #深夜',hashtags:['深夜'],createdAt:1760000000,stats:{digg_count:680,comment_count:5522,share_count:27,collect_count:19,play_count:null},author:{nickname:'零ⅹ',followerCount:16,totalLikes:690,verified:false,signature:'永远的神'},music:{title:'原声'}},analysis:{summary:{durationSeconds:3},screenText:{items:[{text:'OCR 原文'}]},understanding:{keyText:[{start:0,end:3,text:'睡了吗',layer:'caption'},{start:0,end:3,text:'没睡就乱 评论吧'}]},audio:{transcript:{text:''}}}},
  {topComments:[{text:'a'},{text:'b'}],numbers:{ratios:{commentPerLike:8.12,collectPerLike:0.03,sharePerLike:0.04,likePerFollower:42.5},tier:'素人/小号（<1万粉）',drivers:['评论驱动'],lowFollowerHit:true,business:false}});
 const read=Object.fromEntries(ev.read.map(r=>[r.k,r.v]));
 assert.match(read['作品'],/^图文 1 张 · 发布于 2025-/);assert.equal(read['文案'],'这么晚 还不睡');assert.equal(read['话题'],'#深夜');assert.equal(read['公开数据'],'点赞 680 · 评论 5522 · 转发 27 · 收藏 19（平台未公开播放量）');
 assert.equal(read['账号'],'零ⅹ · 粉丝 16 · 总获赞 690');assert.equal(read['音乐'],'原声');assert.equal(read['屏幕文字'],'睡了吗 / 没睡就乱 评论吧','优先用校对后的作者文字');assert.equal(read['声音'],'没有识别到人声');assert.equal(read['评论'],'读到 2 条热评（只取文字和点赞、回复数）');
 const calc=Object.fromEntries(ev.calc.map(r=>[r.k,r.v]));assert.match(calc['互动比率'],/评论\/赞 8\.12.*赞\/粉 42\.5/);assert.match(calc['低粉爆款'],/^是/);assert.equal(calc['商家引流'],'否');assert.equal(ev.summary,'读到 10 项信息 · 评论/赞 8.12');
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');assert.ok(xml.indexOf('我读到的信息')<xml.indexOf('据此算出的指标'));
});

test('评论按赞和回复算权重，卡片先看前3条可展开其余',()=>{
 const {commentNote,bdEvidence}=require('../utils/board-page');
 assert.equal(commentNote({read:20,likes:1500,replies:200,top1Share:0.62,top3Share:0.8,shape:'单条主导',consensus:2,discussion:1}),'单条主导：最热一条占 62% 热度 · 共识 2 条 · 讨论 1 条（热度 = 赞 + 3×回复）');
 assert.match(commentNote({read:3,shape:'互动太少'}),/^评论互动太少，判断仅供参考/);
 const ev=bdEvidence({source:{},analysis:{}},{topComments:new Array(20).fill({text:'x'}),commentStats:{read:20,likes:900,replies:80,top3Share:0.5,shape:'分散',consensus:3,discussion:2},numbers:{}});
 const read=Object.fromEntries(ev.read.map(r=>[r.k,r.v])),calc=Object.fromEntries(ev.calc.map(r=>[r.k,r.v]));
 assert.equal(read['评论'],'读到 20 条热评（赞合计 900 · 回复合计 80，只取文字和点赞、回复数）');assert.match(calc['评论权重'],/^观点分散：前 3 条占 50% 热度/);
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');assert.match(xml,/index<3\|\|bdOpen\.commentsMore/);assert.match(xml,/展开其余/);
});
test('爆款拆解和 1:1 复刻都记进「我的创作」：同一条视频只出一张，进度取最新',()=>{
 const assets=require('../utils/creative-assets');
 const local=[{id:'a'.repeat(64)+':smart:{}',time:1000,updatedAt:1000,stage:'已识别内容',text:'女生唱歌',title:'女生唱歌',sourceValue:'https://v.douyin.com/x/',reference:{asset:{sha256:'a'.repeat(64)}}}];
 const remote={breakdowns:[{id:'s1',sha:'a'.repeat(64),time:5000,stage:'已完成拆解',text:'评论驱动',title:'女生唱歌',url:'https://www.douyin.com/video/1'},{id:'s2',sha:'b'.repeat(64),time:3000,stage:'已识别内容',title:'另一条',url:'https://www.douyin.com/video/2'}],replicas:[{id:'r1',status:'done',seconds:8,createdAt:2}]};
 const rows=assets.merge({},[],remote,local),an=rows.filter(r=>r.kind==='analysis');
 assert.equal(an.length,2);assert.equal(an[0].stage,'已完成拆解');assert.equal(an[0].text,'评论驱动');assert.equal(an[0].label,'爆款拆解');
 assert.equal(assets.route(an[0]),'/pages/video/index?source=douyin&idea='+encodeURIComponent('https://v.douyin.com/x/'),'优先用用户粘贴的原链接重新打开');
 const rp=rows.find(r=>r.kind==='replica');assert.equal(rp.label,'1:1复刻');assert.equal(rp.stage,'已生成');assert.equal(assets.route(rp),'/pages/replica/index');
 const js=fs.readFileSync('pages/main/index.js','utf8');assert.ok(js.includes("['draft','video','text','image','analysis','replica'].includes(r.kind)"));
 const records=require('../utils/analysis-records');const store={};const api={getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;}};
 records.save(api,{reference:{status:'analyzed',asset:{sha256:'c'.repeat(64)},analysis:{understanding:{status:'ready',overview:'一只猫在跳舞'}}},sourceValue:'https://v.douyin.com/y/'});
 assert.equal(records.load(api)[0].stage,'已识别内容');assert.equal(records.load(api)[0].title,'一只猫在跳舞');
 assert.ok(records.note(api,'c'.repeat(64),{stage:'已完成拆解',text:undefined}));assert.equal(records.load(api)[0].stage,'已完成拆解');assert.equal(records.load(api)[0].text,'一只猫在跳舞','没有结论时保留原文');
});
test('文字作品整卡可复制：顶部复制全部/选择复制，新文案可改可选中，原文和标题可选中',()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8'),i=xml.indexOf('board-text-work'),block=xml.slice(i,xml.indexOf('board-compose',i));
 for(const t of ['bindtap="copyAllPart"','bindtap="copySelectPart"','<textarea class="board-line-edit"','auto-height','catchlongpress="copyKeep"'])assert.ok(block.includes(t),t);
 assert.ok(!/<input value="\{\{item\.text\}\}"/.test(block),'单行 input 会截断长句，改成自动换行的 textarea');
 assert.ok((block.match(/<text user-select>/g)||[]).length>=5,'原文、标题、封面话题都能长按选中');
 const board=require('../utils/board-page');const copied=[];global.wx={setClipboardData:o=>{copied.push(o.data);},showToast(){}};
 const page={data:{board:{outputs:{text:{lines:[{start:0,end:3,text:'新的一句'}],titles:['标题A'],cover:'封面',hashtags:['老歌']}}}},cardText:board.cardText,copyNow:board.copyNow,setData(x){Object.assign(this.data,x);}};
 board.copyAllPart.call(page,{currentTarget:{dataset:{part:'text'}}});assert.match(copied[0],/0–3秒  新的一句[\s\S]*标题1：标题A[\s\S]*#老歌/);
 board.copySelectPart.call(page,{currentTarget:{dataset:{part:'text'}}});assert.equal(page.data.copySheet.title,'文字作品');
});
test('AI 额度用完 / 没看成：卡片说明原因并可「再试一次」，不显示确认按钮、不自动倒计时',()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8'),i=xml.indexOf('id="board-confirm"'),card=xml.slice(i,xml.indexOf('id="board-breakdown"'));
 assert.ok(card.includes('bindtap="retryWatch"'));assert.ok(card.indexOf("board.card.status!=='local_only'&&board.card.status!=='unavailable'")<card.indexOf('✓ 对，开始拆解'),'没看成时不让确认');
 const board=require('../utils/board-page');const calls=[];const page={data:{reference:{asset:{sha256:'a'.repeat(64)}},analysisStatus:'done',board:{id:'x'}},setData(x){Object.assign(this.data,x);},analyzeReference(r){calls.push(r);}};
 board.retryWatch.call(page);assert.equal(calls.length,1);assert.equal(page.data.board,null);assert.equal(page.data.analysisStatus,'idle');
 page.data.analysisStatus='running';board.retryWatch.call(page);assert.equal(calls.length,1,'正在识别时不重复');
 assert.match(fs.readFileSync('utils/board-page.js','utf8'),/cardStatus!=='local_only'&&cardStatus!=='unavailable'&&!session\.confirmed/);
});
test('额度用完：购买（占位，后期接支付）+ 申请增加额度（选次数、填用途、一天一次）',async()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');for(const t of ['bindtap="quotaBuy"','bindtap="quotaApplyOpen"','catchtap="quotaApplySend"','已申请 +'])assert.ok(xml.includes(t),t);
 const board=require('../utils/board-page');const sent=[],toasts=[],modals=[];global.wx={showToast:o=>toasts.push(o.title),showModal:o=>{modals.push(o);o.success({confirm:true});}};
 const page={data:{},setData(x){for(const [k,v] of Object.entries(x)){if(k.startsWith('quotaSheet.'))this.data.quotaSheet[k.slice(11)]=v;else this.data[k]=v;}},boardRequest:async(p,d)=>{sent.push([p,d]);return {id:'q',status:'pending',amount:d.amount};}};
 Object.assign(page,{quotaApplyOpen:board.quotaApplyOpen});
 board.quotaBuy.call(page);assert.match(modals[0].content,/即将开通/);assert.equal(page.data.quotaSheet.amount,5,'购买暂未开通时引导去申请');
 board.quotaAmount.call(page,{currentTarget:{dataset:{amount:'10'}}});board.quotaReason.call(page,{detail:{value:'批量拆对标'}});
 await board.quotaApplySend.call(page);assert.deepEqual(sent[0],['/board/quota/request',{amount:10,reason:'批量拆对标'}]);assert.equal(page.data.quotaSheet,null);assert.equal(page.data.quota.request.status,'pending');
 board.quotaApplyOpen.call(page);assert.equal(page.data.quotaSheet,null,'等待审核时不再重复申请');
});
test('调试阶段申请即到账：弹出暂时免费提示，确认后直接重新解析',async()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');assert.ok(xml.includes('wx:for="{{[1,5,10]}}"'));assert.ok(xml.includes('调试阶段暂时免费'));
 const board=require('../utils/board-page');const modals=[];let retried=0;global.wx={showToast(){},showModal:o=>{modals.push(o);o.success({confirm:true});}};
 const page={data:{quotaSheet:{amount:5,reason:'',busy:false}},setData(x){for(const [k,v] of Object.entries(x)){if(k.startsWith('quotaSheet.'))this.data.quotaSheet[k.slice(11)]=v;else this.data[k]=v;}},boardRequest:async(p,d)=>({id:'q',status:'approved',amount:d.amount,granted:d.amount,auto:true,balance:5}),retryWatch(){retried++;}};
 await board.quotaApplySend.call(page);assert.match(modals[0].title,/暂时免费/);assert.match(modals[0].content,/已发放 5 次/);assert.equal(retried,1);assert.equal(page.data.quota.balance,5);
});
test('「对，开始拆解」也是胶囊进度：按本机最近耗时估算，完成记下耗时，失败归零',()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');assert.equal((xml.match(/class="primary prog-btn/g)||[]).length,3,'三个拆解按钮都有进度');assert.match(xml,/'正在深度拆解 '\+boardPct\+'%'/);
 const board=require('../utils/board-page');const store={};global.wx={getStorageSync:k=>store[k],setStorageSync:(k,v)=>{store[k]=v;}};
 const page={data:{},setData(x){Object.assign(this.data,x);}};board.boardProgressStart.call(page);assert.equal(page.data.boardPct,2);
 page.boardPctStarted=Date.now()-12000;board.boardProgressEnd.call(page,true);assert.equal(page.data.boardPct,100);assert.deepEqual(store['youai-breakdown-pace-v1'],[12]);
 board.boardProgressStart.call(page);board.boardProgressEnd.call(page,false);assert.equal(page.data.boardPct,0);assert.equal(store['youai-breakdown-pace-v1'].length,1,'失败不记耗时');
});
test('内容出来后自动倒计时开始拆解（可点内容暂停）；方案行写清「正在使用…方案深度拆解」，换一个/管理方案在右侧',async()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');assert.match(xml,/正在使用『\{\{boardPlanChoice\?boardPlanChoice\.name:board\.plan\.name\}\}』方案深度拆解/);assert.ok(xml.indexOf('board-plan-name')<xml.indexOf('board-plan-links'));assert.ok(xml.includes('秒后自动开始拆解'));
 const board=require('../utils/board-page');const counts=[];
 const run=async(session,data={})=>{const page={data:{reference:{analysis:{analyzerVersion:'content-watch-5'}},board:{id:'b',sha:'s'},...data},setData(x){Object.assign(this.data,x);},boardSet(v){this.data.board=v;},boardRequest:async()=>session,boardCountdown(n){counts.push(n);},boardFail(e){throw e;}};await board.boardReady.call(page);};
 await run({card:{status:'ready'},countdownSeconds:0});assert.deepEqual(counts,[3],'弱匹配也自动开始');
 await run({card:{status:'ready'},countdownSeconds:8});assert.deepEqual(counts,[3,5],'最多等 5 秒');
 await run({card:{status:'local_only'},countdownSeconds:8});await run({card:{status:'ready'},confirmed:true});await run({card:{status:'ready'}},{boardPaused:true});assert.equal(counts.length,2,'没看成/已确认/用户暂停时不自动');
});
test('超级拆解结果：标题右侧「方案」+ 折叠胶囊；没有跳转目录；结论和其它三部分一样可折叠、带编号',()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8'),i=xml.indexOf('id="board-breakdown"'),card=xml.slice(i,i+6000);
 assert.ok(card.includes('超级拆解结果'));assert.ok(!card.includes('拆解卡 ·'));assert.ok(card.indexOf('catchtap="boardOpenPlans">方案')<card.indexOf('class="bd-fold-pill"'),'方案在折叠按钮左侧');
 assert.ok(!card.includes('bdJump')&&!card.includes('bd-toc'),'删掉了 4 个跳转');
 assert.match(card,/data-key="conclusion" catchtap="bdToggle"><text class="bd-num">1<\/text><text class="bd-sec-title">结论<\/text>/);assert.match(card,/<text class="bd-num">\{\{index\+2\}\}<\/text>/);
 assert.match(fs.readFileSync('pages/video/index.wxss','utf8'),/\.fold-label\.done\{background:transparent;color:#0868df/);
});
test('接下来做什么：推荐项单独一行，其余三个（另一种作品 / 1:1 复刻 / AI 生成）矮一半排成一排',()=>{
 const xml=fs.readFileSync('pages/video/board.wxml','utf8'),i=xml.indexOf('class="board-routes"'),block=xml.slice(i,xml.indexOf('</view></view>',i));
 assert.equal((block.match(/class="route-main"/g)||[]).length,1);assert.equal((block.match(/class="route-alt"/g)||[]).length,3);
 const css=fs.readFileSync('pages/video/index.wxss','utf8');assert.match(css,/\.route-main\{[^}]*height:84rpx/);assert.match(css,/\.route-alt\{[^}]*height:56rpx/);
});
test('拆解完成后「我看到的」不消失：和识别完成合成一个卡片，可收起，逐段画面可展开',()=>{
 const xml=fs.readFileSync('pages/video/index.wxml','utf8');
 assert.match(xml,/board\.breakdown&&board\.card\}\}" class="card seen-card"/);assert.match(xml,/<text class="fold-label done">✓ 我看到的<\/text>/);assert.match(xml,/\{\{board\.card\.overview\}\}/);
 assert.match(xml,/!progressOpen&&!\(board\.breakdown&&board\.card\)\}\}" class="card fold-bar"/,'有「我看到的」时不再单独显示识别完成条');
 const board=require('../utils/board-page');const page={data:{},setData(x){Object.assign(this.data,x);}};board.toggleFold.call(page,{currentTarget:{dataset:{key:'seenClosed'}}});assert.equal(page.data.seenClosed,true);board.toggleFold.call(page,{currentTarget:{dataset:{key:'seenTimeline'}}});assert.equal(page.data.seenTimeline,true);
});
test('方法卡复用：文字作品与创作包只显示模型确实用上的同类爆款方法及依据',()=>{
 const {methodNote}=require('../utils/board-page');
 const out={methods:[{name:'评论区接龙',seen:3,lift:1.8,scope:'同类目'},{name:'先上价格',seen:4,lift:null,scope:'跨类目'},{name:'没用上',seen:9,scope:'同类目'}],usedMethods:['评论区接龙','先上价格']};
 assert.equal(methodNote(out),'评论区接龙（3 条同类爆款在用，用过的作品播放约平时 1.8 倍）；先上价格（4 条其它类目爆款在用）');
 assert.equal(methodNote({methods:out.methods,usedMethods:[]}),'');assert.equal(methodNote(null),'');
 const xml=require('fs').readFileSync('pages/video/board.wxml','utf8');
 assert.match(xml,/wx:if="\{\{boardMethodText\}\}"[^>]*>借鉴同类爆款方法：\{\{boardMethodText\}\}/);assert.match(xml,/wx:if="\{\{boardMethodPkg\}\}"[^>]*>借鉴同类爆款方法：\{\{boardMethodPkg\}\}/);
 const py=require('fs').readFileSync('scripts/creation-board.py','utf8');assert.match(py,/'methods': method_prompt/);assert.match(py,/"usedMethods":\["用上的方法名"\]/);
});
test('breakdown alone loads the reference preview for the next-step area',async()=>{
 const {page,calls}=board({'/board/preview':{url:'/reference-assets/'+'d'.repeat(64)+'.mp4'}});
 page.boardSet({...SESSION,breakdown:{fields:[]}});await tick();await tick();
 assert.equal(calls.filter(c=>c.path==='/board/preview').length,1);assert.match(page.data.boardRefVideo,/^https:\/\/api\.example\.com\/reference-assets\//);
});
test('generated text and package cards show a compressed reference video loaded once per session',async()=>{
 const withText={...SESSION,outputs:{text:{lines:[],titles:[],caption:'新正文'}}};
 const {page,calls}=board({'/board/preview':{url:'/reference-assets/'+'c'.repeat(64)+'.mp4?__u=u&__e=1&__s=x'}});
 page.boardSet(withText);await tick();await tick();
 assert.equal(page.data.boardRefVideo,'https://api.example.com/reference-assets/'+'c'.repeat(64)+'.mp4?__u=u&__e=1&__s=x');
 page.boardSet({...withText,outputs:{...withText.outputs,package:{shots:[]}}});await tick();
 assert.equal(calls.filter(c=>c.path==='/board/preview').length,1,'同一拆解只取一次预览');
 assert.equal(calls.find(c=>c.path==='/board/preview').data.id,SESSION.id);
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');
 assert.equal((xml.match(/class="board-ref-video" src="\{\{boardRefVideo\}\}"/g)||[]).length,3,'接下来做什么上方、文字作品卡与创作包卡顶部都有原视频');
 assert.ok(xml.lastIndexOf('board-ref-route')<xml.indexOf('接下来做什么'));
 const hide="!((board.outputs.text&&boardRoute==='text')||(board.outputs.package&&boardRoute==='package'))";
 assert.equal(xml.split('board-ref-route').length-1,2);assert.ok(xml.includes('{{boardRefVideo&&'+hide+'}}')&&xml.includes('{{boardRefLoading&&'+hide+'}}'),'生成结果出来后，接下来做什么上方的原视频隐藏，只留在结果卡里');
 assert.ok(xml.indexOf('board-ref-video')<xml.indexOf('<text class="strong">文字作品</text>'));
 assert.match(fs.readFileSync('scripts/video-server.py','utf8'),/path=='\/board\/preview'/);
});
test('variants: entry under the text work, three scripts on the same clips, results polled with copy and save',async()=>{
 const items=[{id:'1'.repeat(32),angle:'直接邀请',title:'标题一',caption:'正文一',status:'done',video:'/board-media/'+'1'.repeat(32)+'.mp4?__s=x'},{id:'2'.repeat(32),angle:'讲经过',status:'running'}];
 const {page,calls}=board({'/board/variants':{id:'j'.repeat(32),status:'running',message:'正在合成第 1/3 条',items}});
 page.boardSet({...SESSION,outputs:{text:{lines:[{start:0,end:2,text:'一'}],titles:[],hashtags:['抖店']}}});
 page.boardVariantOpen();assert.equal(page.data.boardCompose.mode,'variants');
 await page.boardVariantRun();assert.ok(!calls.some(c=>c.path==='/board/variants'),'没选画面不请求');
 page.setData({'boardCompose.clips':[{sha:'e'.repeat(64)}],'boardCompose.position':'top'});
 await page.boardVariantRun();const req=calls.find(c=>c.path==='/board/variants');
 assert.deepEqual(req.data.clips,['e'.repeat(64)]);assert.equal(req.data.position,'top');assert.equal(req.data.id,SESSION.id);
 assert.equal(page.data.boardVariants.items[0].videoUrl,'https://api.example.com/board-media/'+'1'.repeat(32)+'.mp4?__s=x');assert.equal(page.data.boardVariants.items[1].videoUrl,'');
 const xml=fs.readFileSync('pages/video/board.wxml','utf8');
 assert.match(xml,/bindtap="boardComposeOpen">套版成片（可选）<\/button><button size="mini" bindtap="boardVariantOpen">裂变 3 条<\/button>/);
 assert.match(xml,/bindtap="boardVariantRun"[^>]*>生成 3 条变体/);assert.match(xml,/boardVariantCopy/);assert.match(xml,/boardVariantSave/);
 assert.match(fs.readFileSync('scripts/video-server.py','utf8'),/path=='\/board\/variants'[\s\S]{0,400}AUTH\.claim\(user,'board:'\+item\['id'\]\)/);
 assert.match(fs.readFileSync('pages/video/index.js','utf8'),/clearTimeout\(this\.variantTimer\)/);
});
