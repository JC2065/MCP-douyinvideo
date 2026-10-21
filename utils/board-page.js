// Creation board flow on the 拆解 page (docs/creation-board-plan.md M3–M9):
// tiered questions while watching → confirmation card (plan + basis + countdown) → corrections →
// breakdown by plan (fields revealed one by one, adjustable) → outputs (text work / package / compose) → publish.
const TELEPROMPTER_KEY='youai-teleprompter-script',PRIVACY_KEY='youai-board-privacy-v1';
const config=require('./video-service'),videoSession=require('./video-session');
const PACE_KEY='youai-breakdown-pace-v1';
function clean(value,max){return String(value||'').trim().slice(0,max);}
// 数据依据分两类：「我读到的信息」（原始输入，用来核对 AI 读没读对）和「据此算出的指标」（比率、量级、低粉爆款等判断依据）。
function bdNum(n){if(typeof n!=='number'||!isFinite(n))return '';return n>=1e8?(n/1e8).toFixed(1).replace(/\.0$/,'')+'亿':n>=1e4?(n/1e4).toFixed(1).replace(/\.0$/,'')+'万':String(n);}
function bdEvidence(reference,insight){const s=(reference&&reference.source)||{},a=(reference&&reference.analysis)||{},i=insight||{},n=i.numbers||{},st=s.stats||{},au=s.author||{},rows=[],calc=[];const add=(list,k,v)=>{if(v!==undefined&&v!==null&&String(v).trim())list.push({k,v:String(v).trim()});};
 const dur=(a.summary||{}).durationSeconds||(((reference||{}).asset||{}).media||{}).durationSeconds;let when='';if(s.createdAt){const t=typeof s.createdAt==='number'?(s.createdAt<1e12?s.createdAt*1000:s.createdAt):Date.parse(s.createdAt);if(t>0){const d=new Date(t);when=' · 发布于 '+d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate();}}
 add(rows,'作品',(s.kind==='gallery'?'图文 '+(s.imageCount||'')+' 张':'视频'+(dur?' '+Math.round(dur)+' 秒':''))+when);
 add(rows,'文案',String(s.description||'').replace(/#\S+/g,'').trim().slice(0,120));add(rows,'话题',(s.hashtags||[]).length?'#'+s.hashtags.slice(0,8).join(' #'):'');
 const pub=[['点赞',st.digg_count],['评论',st.comment_count],['转发',st.share_count],['收藏',st.collect_count],['播放',st.play_count]].filter(x=>typeof x[1]==='number').map(x=>x[0]+' '+bdNum(x[1]));if(pub.length)add(rows,'公开数据',pub.join(' · ')+(typeof st.play_count==='number'?'':'（平台未公开播放量）'));
 add(rows,'账号',[au.nickname,typeof au.followerCount==='number'?'粉丝 '+bdNum(au.followerCount):'',typeof au.totalLikes==='number'?'总获赞 '+bdNum(au.totalLikes):'',au.verified?'已认证':''].filter(Boolean).join(' · '));add(rows,'简介',au.signature);
 const m=s.music;add(rows,'音乐',typeof m==='string'?m:m&&[m.title,m.author].filter(Boolean).join(' - '));
 const txt=x=>typeof x==='string'?x:(x&&(x.text||x.content))||'',items=((a.screenText||{}).items||[]).map(txt).filter(Boolean),keyRaw=(a.understanding||{}).keyText,key=(Array.isArray(keyRaw)?keyRaw:keyRaw?[keyRaw]:[]).map(txt).filter(Boolean),shown=key.length?key:items;
 add(rows,'屏幕文字',shown.length?shown.slice(0,6).join(' / ').slice(0,140)+(shown.length>6?' 等 '+shown.length+' 段':''):'没有识别到屏幕文字');
 const tr=(((a.audio||{}).transcript)||{}).text;add(rows,'声音',tr?String(tr).slice(0,100):'没有识别到人声');
 const cs=i.commentStats;add(rows,'评论',(i.topComments||[]).length?'读到 '+i.topComments.length+' 条热评'+(cs?'（赞合计 '+cs.likes+' · 回复合计 '+cs.replies+'，只取文字和点赞、回复数）':'（只取文字和点赞、回复数）'):'没有读到评论');
 if(cs&&cs.read)add(calc,'评论权重',commentNote(cs));
 const r=n.ratios||{};if(r.commentPerLike!==null&&r.commentPerLike!==undefined)add(calc,'互动比率','评论/赞 '+r.commentPerLike+' · 收藏/赞 '+r.collectPerLike+' · 转发/赞 '+r.sharePerLike+(r.likePerFollower!==null&&r.likePerFollower!==undefined?' · 赞/粉 '+r.likePerFollower:''));
 add(calc,'账号量级',n.tier);add(calc,'互动类型',(n.drivers||[]).join('、'));if(n.tier||n.lowFollowerHit!==undefined)add(calc,'低粉爆款',n.lowFollowerHit?'是（点赞+评论+收藏+转发合计 ≥ 粉丝数的 2 倍，且 ≥ 1000）':'否');if(n.business!==undefined)add(calc,'商家引流',n.business?'是（简介留了联系方式，或文案、简介里有商业关键词）':'否');add(calc,'提醒',i.staging);
 return {read:rows,calc,summary:'读到 '+rows.length+' 项信息'+(r.commentPerLike!==null&&r.commentPerLike!==undefined?' · 评论/赞 '+r.commentPerLike:'')};}
// 拆解卡阅读顺序：数据依据（顶部，默认收起）→ 结论 → 怎么学（默认展开）→ 结构 → 评论区。内容不变，只调顺序与收放。
const BD_GROUP={positioning:'conclusion',learnable:'learn',hook:'learn',cta:'learn',benefit:'learn',emotion:'learn',offer:'learn',proof:'learn',timeline:'structure',rhythm:'structure',screen_text:'structure',visual:'structure',scene:'structure',limits:'data'};
const BD_LEVEL={'高':0,'中':1,'低':2};
function bdSections(bd){if(!bd)return null;const fields=(bd.fields||[]).map(f=>f.key==='learnable'&&Array.isArray(f.value)?{...f,value:[...f.value].sort((a,b)=>(a.level in BD_LEVEL?BD_LEVEL[a.level]:3)-(b.level in BD_LEVEL?BD_LEVEL[b.level]:3))}:f);
 const pick=g=>fields.filter(f=>f.key!=='positioning'&&(BD_GROUP[f.key]||'learn')===g),pos=fields.find(f=>f.key==='positioning'),learn=fields.find(f=>f.key==='learnable'),rows=learn&&Array.isArray(learn.value)?learn.value:[];
 const i=bd.insight||{},r=(i.numbers||{}).ratios||{},tl=fields.find(f=>f.key==='timeline'),tlv=tl&&Array.isArray(tl.value)?tl.value:[],learnF=pick('learn'),structF=pick('structure'),dataF=pick('data'),hi=rows.filter(x=>x.level==='高').length,top=i.topComments||[];
 return {positioning:pos&&typeof pos.value==='string'?pos.value:'',best:rows[0]&&rows[0].level==='高'?rows[0]:null,
  data:{fields:dataF,has:r.commentPerLike!==null&&r.commentPerLike!==undefined||!!i.staging||dataF.length>0,summary:r.commentPerLike!==null&&r.commentPerLike!==undefined?'评论/赞 '+r.commentPerLike+' · 收藏/赞 '+r.collectPerLike:(i.staging?'有摆拍提醒':'')},
  groups:[{id:'learn',title:'怎么学',fields:learnF,summary:[hi?'可学高 '+hi+' 条':'',...learnF.filter(f=>f.key!=='learnable').map(f=>f.label)].filter(Boolean).join(' · ')},
   {id:'structure',title:'结构',fields:structF,summary:tlv.length?tlv.length+' 段 · '+tlv[tlv.length-1].end+' 秒':structF.map(f=>f.label).join(' · ')},
   {id:'comments',title:'评论区',fields:[],summary:[i.commentPlay?'打法':'',top.length?top.length+' 条真实热评':''].filter(Boolean).join(' + ')}].filter(g=>g.id==='comments'?!!(i.commentPlay||top.length):g.fields.length)};}
// 方法卡复用：只展示模型确实用上的同类爆款方法，附「出现在几条爆款 / 用过的作品数据」作为依据
function methodNote(out){if(!out||!Array.isArray(out.methods)||!Array.isArray(out.usedMethods)||!out.usedMethods.length)return '';return out.methods.filter(m=>out.usedMethods.indexOf(m.name)>=0).map(m=>m.name+'（'+m.seen+' 条'+(m.scope==='跨类目'?'其它类目':'同类')+'爆款在用'+(m.lift?'，用过的作品播放约平时 '+m.lift+' 倍':'')+'）').join('；');}
function commentNote(cs){if(!cs||!cs.read)return '';const pct=x=>Math.round((x||0)*100)+'%';const shape=cs.shape==='互动太少'?'评论互动太少，判断仅供参考':cs.shape==='单条主导'?'单条主导：最热一条占 '+pct(cs.top1Share)+' 热度':cs.shape==='头部集中'?'头部集中：前 3 条占 '+pct(cs.top3Share)+' 热度':'观点分散：前 3 条占 '+pct(cs.top3Share)+' 热度';return shape+' · 共识 '+(cs.consensus||0)+' 条 · 讨论 '+(cs.discussion||0)+' 条（热度 = 赞 + 3×回复）';}
module.exports={
 boardRequest(path,data,timeout=60000){return this.request(path,'POST',data,timeout);},
 toggleFold(e){const key=e.currentTarget.dataset.key;if(!['inputOpen','progressOpen','boardDetailOpen','seenClosed','seenTimeline'].includes(key))return;this.setData({[key]:!this.data[key]});},
 // 长按「我看到的是」及之后的卡片：复制全部，或打开可选择文字的面板复制一部分。
 cardText(part){const b=this.data.board||{},lines=[];const add=v=>{if(v!==undefined&&v!==null&&String(v).trim())lines.push(String(v).trim());};
  if(part==='confirm'&&b.card){add('我看到的是：'+(b.card.overview||''));if(b.card.type)add('类型：'+b.card.type+(b.card.tags&&b.card.tags.length?'  #'+b.card.tags.join(' #'):''));(b.card.timeline||[]).forEach(t=>add(t.start+'–'+t.end+'秒  '+t.what));}
  else if(part==='breakdown'&&b.breakdown){const k=b.breakdown,i=k.insight||{};add('拆解卡 · '+(k.planName||''));if(i.why)add('为什么火：'+i.why);if(i.difficulty&&i.difficulty.score)add('复刻难度 '+i.difficulty.score+'/5 '+(i.difficulty.reason||''));if(i.commentPlay)add('评论区打法：'+i.commentPlay);
   (k.fields||[]).forEach(f=>{add('【'+f.label+'】');const v=f.value;if(Array.isArray(v))v.forEach(r=>add(r.item?('· '+r.item+(r.how?'（学法：'+r.how+'）':'')):(r.start!==undefined?r.start+'–'+r.end+'秒  ':'')+(r.text||'')));else if(v&&typeof v==='object')add((v.score!==undefined?v.score+' / 10 ':'')+(v.reason||''));else add(v);});}
  else if(part==='text'&&b.outputs&&b.outputs.text){const t=b.outputs.text;(t.screenTitles||[]).forEach(x=>add('大标题：'+x.text));(t.lines||[]).forEach(l=>add((l.start!==null&&l.start!==undefined?l.start+'–'+l.end+'秒  ':'')+l.text));if(t.caption)add('发布正文：'+t.caption);(t.titles||[]).forEach((x,n)=>add('标题'+(n+1)+'：'+x));if(t.cover)add('封面大字：'+t.cover);if(t.hashtags&&t.hashtags.length)add('#'+t.hashtags.join(' #'));}
  else if(part==='package'&&b.outputs&&b.outputs.package){const p=b.outputs.package;(p.shots||[]).forEach(s=>{add((s.start!==null&&s.start!==undefined?s.start+'–'+s.end+'秒 · ':'')+(s.shot||''));add('手机：'+(s.phone||''));add('动作：'+(s.action||''));if(s.line)add('台词：'+s.line);if(s.subtitle)add('字幕：'+s.subtitle);});(p.checklist||[]).forEach(c=>add('☐ '+c));if(p.pinnedComment)add('置顶评论：'+p.pinnedComment);}
  return lines.join('\n');},
 copyMenu(e){const part=e.currentTarget.dataset.part,text=this.cardText(part);if(!text)return;const title={confirm:'我看到的是',breakdown:'拆解卡',text:'文字作品',package:'创作包'}[part]||'内容';
  wx.showActionSheet({itemList:['复制全部','选择部分复制'],success:r=>{if(r.tapIndex===0)this.copyNow(text);else this.setData({copySheet:{title,text}});}});},
 copyAllPart(e){const text=this.cardText(e.currentTarget.dataset.part);if(text)this.copyNow(text);},
 copySelectPart(e){const part=e.currentTarget.dataset.part,text=this.cardText(part);if(text)this.setData({copySheet:{title:{confirm:'我看到的是',breakdown:'拆解卡',text:'文字作品',package:'创作包'}[part]||'内容',text}});},
 copyKeep(){},
 copyNow(text){wx.setClipboardData({data:text,success:()=>wx.showToast({title:'已复制',icon:'none'})});},
 copyAllNow(){if(this.data.copySheet)this.copyNow(this.data.copySheet.text);},
 copyClose(){this.setData({copySheet:null});},
 copyNoop(){},
 bdToggle(e){const key=e.currentTarget.dataset.key;this.setData({['bdOpen.'+key]:!(this.data.bdOpen||{})[key]});},
 bdJump(e){const id=e.currentTarget.dataset.id;if(id!=='conclusion')this.setData({['bdOpen.'+id]:true});if(this.scrollToBlock)this.scrollToBlock('bd-'+id);},
 // 「我看到的是」右侧：超级拆解（默认，按顺序拆）/ 1:1 复刻（弹出选择，可继续拆解或进入复刻，点空白或 × 关闭）。
 boardModePick(e){const mode=e.currentTarget.dataset.mode;if(mode!=='replica'){this.setData({boardMode:'super',replicaChoice:false});return;}this.boardPause();this.setData({boardMode:'replica',replicaChoice:true});},
 replicaChoiceClose(){this.setData({boardMode:'super',replicaChoice:false});},
 replicaGo(){this.setData({boardMode:'super',replicaChoice:false});if(this.openReplica)this.openReplica();},
 replicaHint(){if(this.boardPause)this.boardPause();wx.showModal({title:'1:1 复刻',content:'1:1 复刻会按原视频逐镜头直接生成新视频，需要使用你自己的视频模型 Key，生成费用由你的账号承担。下一步进入配置页面。',confirmText:'去配置',success:r=>{if(r.confirm&&this.openReplica)this.openReplica();}});},
 boardSet(session,extra={}){const prev=this.data.board||{};const shares=(session&&session.card&&session.card.valueShares)||[];const text=(shares.find(s=>s.key==='text')||{}).percent||0;const ins=session&&session.breakdown&&session.breakdown.insight;if(ins&&Array.isArray(ins.topComments))ins.topComments.forEach(c=>{if(c&&typeof c.share==='number')c.sharePct=Math.round(c.share*1000)/10;});const bd=session&&session.breakdown?bdSections(session.breakdown):null;if(bd){bd.evidence=bdEvidence(this.data.reference,session.breakdown.insight);bd.data.has=true;bd.data.summary=bd.evidence.summary;}if(session&&session.card&&session.card.status==='local_only'&&!(prev.card&&prev.card.status==='local_only'))setTimeout(()=>this.quotaLoad(),0);this.setData({board:session,boardError:'',boardRecommend:text>=40?'text':'package',bd,bdGroups:bd?bd.groups:[],boardHashtagText:((session&&session.outputs&&session.outputs.text&&session.outputs.text.hashtags)||[]).map(h=>'#'+h).join(' '),bdCommentNote:ins?commentNote(ins.commentStats):'',boardMethodText:methodNote(session&&session.outputs&&session.outputs.text),...(session&&prev.id&&session.id!==prev.id?{boardRefVideo:'',boardRefLoading:false}:{}),boardMethodPkg:methodNote(session&&session.outputs&&session.outputs.package),bdNav:bd?[{id:'conclusion',label:'结论'},...bd.groups.map(g=>({id:g.id,label:g.title}))]:[],...(bd&&!prev.breakdown?{bdOpen:{data:false,conclusion:true,learn:true,structure:true,comments:true,commentsMore:false},boardDetailOpen:true}:{}),...extra});if(session&&(session.breakdown||session.outputs&&(session.outputs.text||session.outputs.package)))this.boardRefLoad();if(!session||!this.scrollToBlock)return;if(session.breakdown&&!prev.breakdown)this.scrollToBlock('board-breakdown');else if(session.card&&!prev.card&&!session.breakdown&&this.data.analysisStatus==='done')this.scrollToBlock('board-confirm');},
 boardFail(error){if(this.boardProgressEnd)this.boardProgressEnd(false);this.setData({boardBusy:false,boardError:error&&error.message||'创作板块暂时不可用，请稍后重试'});},
 startBoard(reference){
  // analyzeReference and boardReady can both start the board for the same video; share one request so a submission counts as one attempt.
  const sha=reference&&reference.asset&&reference.asset.sha256;if(!sha||this.data.board&&this.data.board.sha===sha)return Promise.resolve();
  const version=this._sourceVersion,key=sha+':'+version;
  if(this._boardStart&&this._boardStart.key===key)return this._boardStart.promise;
  const promise=this.startBoardOnce(sha,version).finally(()=>{if(this._boardStart&&this._boardStart.key===key)this._boardStart=null;});
  this._boardStart={key,promise};return promise;
 },
 async startBoardOnce(sha,version){
  try{const session=await this.boardRequest('/board/session',{reference:{asset:{sha256:sha}},glance:this.data.glance||null},20000);if(version!==this._sourceVersion||this.stopped)return;let acknowledged=false;try{acknowledged=!!wx.getStorageSync(PRIVACY_KEY);}catch(_){}this.boardSet({...session,sha},{boardReveal:0,boardVerdict:'',boardCorrections:{},boardPrivacy:!acknowledged,boardPaused:false});}
  catch(error){this.setData({boardError:''});}
 },
 async boardReady(){
  const reference=this.data.reference;if(!reference||!/^content-watch-/.test(reference.analysis&&reference.analysis.analyzerVersion||''))return;
  try{
   if(!this.data.board)await this.startBoard(reference);
   if(!this.data.board)return;
   const session=await this.boardRequest('/board/refresh',{id:this.data.board.id},20000);this.boardSet({...session,sha:this.data.board.sha});
   const cardStatus=session.card&&session.card.status;if(cardStatus!=='local_only'&&cardStatus!=='unavailable'&&!session.confirmed&&!session.breakdown&&!this.data.boardPaused&&!this.data.boardVerdict)this.boardCountdown(Math.min(5,session.countdownSeconds>0?session.countdownSeconds:3));
  }catch(error){this.boardFail(error);}
 },
 // AI 没看成（额度用完 / 模型不可用）：保留已取得的视频，重新跑一次识别；服务端不缓存失败结果，所以会真的重新观看。
 // 额度用完时：购买（支付后期接入）/ 申请增加额度（管理员审核后发放次数）。
 async quotaLoad(){try{const value=await this.request('/board/quota','GET',undefined,15000);if(!this.stopped)this.setData({quota:value||null});}catch(_){}},
 quotaBuy(){wx.showModal({title:'购买额度',content:'购买功能即将开通。现在可以先申请增加额度，审核通过后就能继续。',confirmText:'去申请',cancelText:'知道了',success:r=>{if(r.confirm)this.quotaApplyOpen();}});},
 quotaApplyOpen(){if(this.data.quota&&this.data.quota.request&&this.data.quota.request.status==='pending')return;this.setData({quotaSheet:{amount:5,reason:'',busy:false}});},
 quotaApplyClose(){this.setData({quotaSheet:null});},
 quotaAmount(e){this.setData({'quotaSheet.amount':Number(e.currentTarget.dataset.amount)});},
 quotaReason(e){this.setData({'quotaSheet.reason':clean(e.detail.value,120)});},
 async quotaApplySend(){const sheet=this.data.quotaSheet;if(!sheet||sheet.busy)return;this.setData({'quotaSheet.busy':true});try{const request=await this.boardRequest('/board/quota/request',{amount:sheet.amount,reason:sheet.reason},15000);this.setData({quotaSheet:null,quota:{...(this.data.quota||{}),request,...(request.balance!==undefined?{balance:request.balance}:{})}});if(request.auto){wx.showModal({title:'已到账（暂时免费）',content:'现在是调试阶段，申请暂时免费：已发放 '+request.granted+' 次，额外额度共 '+request.balance+' 次。点「立即解析」继续。',confirmText:'立即解析',cancelText:'稍后',success:r=>{if(r.confirm)this.retryWatch();}});}else wx.showToast({title:request.existing?'今天已经申请过了，等待审核':'已提交，审核后通知你',icon:'none'});}catch(error){this.setData({'quotaSheet.busy':false});wx.showToast({title:(error&&error.message)||'提交失败，请重试',icon:'none'});}},
 retryWatch(){const reference=this.data.reference;if(!reference||this.data.analysisStatus==='running')return;clearInterval(this.boardTimer);this.setData({board:null,boardVerdict:'',boardCountdown:0,analysisStatus:'idle',progressOpen:false});if(this.analyzeReference)this.analyzeReference(reference);},
 boardCountdown(seconds){clearInterval(this.boardTimer);this.setData({boardCountdown:seconds});this.boardTimer=setInterval(()=>{if(this.stopped)return clearInterval(this.boardTimer);const left=this.data.boardCountdown-1;if(left<=0){clearInterval(this.boardTimer);this.setData({boardCountdown:0});this.boardConfirm({auto:true});}else this.setData({boardCountdown:left});},1000);},
 boardPrivacyOk(){try{wx.setStorageSync(PRIVACY_KEY,Date.now());}catch(_){}this.setData({boardPrivacy:false});},
 boardPause(){if(this.data.boardCountdown){clearInterval(this.boardTimer);this.setData({boardCountdown:0,boardPaused:true});}},
 boardAnswer(e){this.boardPause();const {key,value}=e.currentTarget.dataset;this.saveBoardAnswer(key,value);},
 boardAnswerInput(e){const key=e.currentTarget.dataset.key;this.setData({['boardDraft.'+key]:e.detail.value});},
 boardAnswerSubmit(e){const key=e.currentTarget.dataset.key;this.saveBoardAnswer(key,(this.data.boardDraft||{})[key]);},
 async saveBoardAnswer(key,value){value=clean(value,300);if(!value||!this.data.board)return;try{if(key==='dissatisfied'){const r=await this.boardRequest('/board/followups',{id:this.data.board.id,stage:value},30000);this.setData({boardFollowups:r.items,'board.answers.dissatisfied':value});return;}const session=await this.boardRequest('/board/answer',{id:this.data.board.id,key,value});this.boardSet({...session,sha:this.data.board.sha});}catch(error){this.boardFail(error);}},
 async boardInterviewSend(){const message=clean(this.data.boardInterviewMessage,600);if(this.data.boardBusy)return;this.setData({boardBusy:true});try{const session=await this.boardRequest('/board/interview',{id:this.data.board.id,message},40000);this.boardSet({...session,sha:this.data.board.sha},{boardInterviewMessage:'',boardBusy:false});}catch(error){this.boardFail(error);}},
 boardInterviewInput(e){this.setData({boardInterviewMessage:e.detail.value});},
 // 返回键先退出页内的一层：在「部分不对 / 完全不对」纠正状态时，回到「对，开始拆解 / 部分不对 / 完全不对」的选择处，而不是离开页面。
 onBallBack(){if(this.data.boardVerdict&&!this.data.boardBusy){this.setData({boardVerdict:'',boardCorrections:{}});if(this.scrollToBlock)this.scrollToBlock('board-confirm');return true;}return false;},
 boardVerdict(e){this.boardPause();this.setData({boardVerdict:e.currentTarget.dataset.verdict});},
 boardFixInput(e){this.boardPause();this.setData({['boardCorrections.'+e.currentTarget.dataset.index]:e.detail.value});},
 boardStatementInput(e){this.boardPause();this.setData({boardStatement:e.detail.value});},
 boardDescribeInput(e){this.boardPause();this.setData({boardDescribe:e.detail.value});},
 boardRangeInput(e){this.setData({['boardRange.'+e.currentTarget.dataset.key]:e.detail.value});},
 async boardPlansLoad(){try{const plans=await this.request('/board/plans');const rows=[...plans.mine,...plans.builtin].map(p=>({id:p.id,name:p.name+(p.owner==='builtin'?'':'（我的）')}));this.setData({boardPlans:rows});}catch(error){this.boardFail(error);}},
 boardPlanPick(e){this.boardPause();const row=(this.data.boardPlans||[])[Number(e.detail.value)];if(row)this.setData({boardPlanChoice:row});},
 boardOpenPlans(){wx.navigateTo({url:'/pages/board-plans/index'});},
 // 「对，开始拆解」胶囊进度：按本机最近几次拆解耗时估算，预计时间内走到 90%，超时缓慢逼近 99%，完成 100%。
 boardProgressStart(){clearInterval(this.boardPctTimer);clearTimeout(this.boardPctDone);let past=[];try{past=(wx.getStorageSync(PACE_KEY)||[]).filter(n=>n>0);}catch(_){}const sorted=[...past].sort((a,b)=>a-b),eta=sorted.length?Math.min(120,Math.max(8,sorted[Math.floor(sorted.length/2)])):30;this.boardPctStarted=Date.now();this.setData({boardPct:2});if(this.nextTip)this.nextTip();
  this.boardPctTimer=setInterval(()=>{if(this.stopped)return clearInterval(this.boardPctTimer);const e=(Date.now()-this.boardPctStarted)/1000,p=e<=eta?e/eta*90:90+9*(1-Math.exp(-(e-eta)/eta));this.setData({boardPct:Math.max(2,Math.min(99,Math.round(p)))});},500);if(this.boardPctTimer&&this.boardPctTimer.unref)this.boardPctTimer.unref();},
 boardProgressEnd(ok){clearInterval(this.boardPctTimer);if(!this.boardPctStarted)return;const seconds=(Date.now()-this.boardPctStarted)/1000;this.boardPctStarted=0;if(!ok)return this.setData({boardPct:0});try{wx.setStorageSync(PACE_KEY,[...(wx.getStorageSync(PACE_KEY)||[]),Math.round(seconds)].slice(-5));}catch(_){}this.setData({boardPct:100});this.boardPctDone=setTimeout(()=>{if(!this.stopped)this.setData({boardPct:0});},900);if(this.boardPctDone&&this.boardPctDone.unref)this.boardPctDone.unref();},
 async boardConfirm(e){
  if(this.data.boardBusy||!this.data.board)return;const auto=!!(e&&e.auto);clearInterval(this.boardTimer);
  const verdict=auto?'ok':(e&&e.currentTarget&&e.currentTarget.dataset.verdict)||this.data.boardVerdict||'ok';
  const corrections=Object.entries(this.data.boardCorrections||{}).map(([index,text])=>({index:Number(index),text:clean(text,200)})).filter(c=>c.text);
  const payload={id:this.data.board.id,verdict,corrections,statement:clean(this.data.boardStatement,400),describe:clean(this.data.boardDescribe,400),auto,planId:this.data.boardPlanChoice&&this.data.boardPlanChoice.id||undefined};
  this.setData({boardBusy:true,boardCountdown:0});this.boardProgressStart();
  try{const session=await this.boardRequest('/board/confirm',payload,60000);this.boardSet({...session,sha:this.data.board.sha},{boardVerdict:'',boardBusy:false});await this.boardBreakdown();}catch(error){this.boardFail(error);}
 },
 async boardRewatch(){if(this.data.boardBusy)return;const range=this.data.boardRange||{};const start=range.start===''||range.start===undefined?undefined:Number(range.start),end=range.end===''||range.end===undefined?undefined:Number(range.end);this.setData({boardBusy:true});try{const session=await this.boardRequest('/board/rewatch',{id:this.data.board.id,start,end},120000);this.boardSet({...session,sha:this.data.board.sha},{boardBusy:false});}catch(error){this.boardFail(error);}},
 async boardBreakdown(){
  this.setData({boardBusy:true,boardReveal:0});
  try{const session=await this.boardRequest('/board/breakdown',{id:this.data.board.id},90000);this.boardProgressEnd(true);this.boardSet({...session,sha:this.data.board.sha},{boardBusy:false});this.boardRevealFields();const bd=session&&session.breakdown||{};if(this.noteWork)this.noteWork({stage:'已完成拆解',text:String((bd.insight||{}).why||'').slice(0,120)||undefined,planName:bd.planName||''});}catch(error){this.boardFail(error);}
 },
 boardRevealFields(){clearInterval(this.revealTimer);const total=(this.data.board.breakdown&&this.data.board.breakdown.fields||[]).length;this.revealTimer=setInterval(()=>{const next=this.data.boardReveal+1;this.setData({boardReveal:next});if(next>=total||this.stopped)clearInterval(this.revealTimer);},350);},
 boardAdjustInput(e){this.setData({boardAdjust:e.detail.value});},
 async boardAdjustSend(e){const message=clean(this.data.boardAdjust,400);if(!message||this.data.boardBusy)return;const save=e.currentTarget.dataset.save==='1';this.setData({boardBusy:true});try{const session=await this.boardRequest('/board/adjust',{id:this.data.board.id,message,save},120000);this.boardSet({...session,sha:this.data.board.sha},{boardAdjust:'',boardBusy:false});this.boardRevealFields();}catch(error){this.boardFail(error);}},
 async boardOutput(e){
  const route=e.currentTarget.dataset.route;if(this.data.boardBusy)return;
  if(route==='replica')return this.replicaHint();
  if(route==='ai')return this.startWatchChat&&this.startWatchChat();
  this.setData({boardBusy:true,boardRoute:route});
  try{const session=await this.boardRequest(route==='text'?'/board/output/text':'/board/output/package',route==='text'?{id:this.data.board.id}:{id:this.data.board.id,conditions:(this.data.board.answers||{}).conditions||''},120000);this.boardSet({...session,sha:this.data.board.sha},{boardBusy:false,boardPrediction:session.prediction||null,boardDetailOpen:false});if(this.scrollToBlock)this.scrollToBlock('board-output');}catch(error){this.boardFail(error);}
 },
 boardCopyText(){const work=this.data.board&&this.data.board.outputs&&this.data.board.outputs.text;if(!work)return;const text=[work.titles&&work.titles[0],...(work.caption?[work.caption]:work.lines.map(l=>l.text)),(work.hashtags||[]).map(h=>'#'+h).join(' ')].filter(Boolean).join('\n');wx.setClipboardData({data:text,success:()=>wx.showToast({title:'已复制文案',icon:'none'})});},
 async boardRefLoad(){const id=this.data.board&&this.data.board.id;if(!id||this.data.boardRefVideo||this._refFor===id)return;this._refFor=id;this.setData({boardRefLoading:true});try{const r=await this.boardRequest('/board/preview',{id},120000);if(this.data.board&&this.data.board.id===id)this.setData({boardRefVideo:r.url?(/^https?:/.test(r.url)?r.url:config.baseUrl+r.url):'',boardRefLoading:false});}catch(error){this._refFor='';this.setData({boardRefLoading:false});}},
 boardCaptionEdit(e){this.setData({'board.outputs.text.caption':clean(e.detail.value,500)});},
 boardLineEdit(e){const index=Number(e.currentTarget.dataset.index);this.setData({['board.outputs.text.lines['+index+'].text']:clean(e.detail.value,80)});},
 boardTeleprompter(){const pack=this.data.board&&this.data.board.outputs&&this.data.board.outputs.package;const script=pack&&(pack.script||pack.shots.map(s=>s.line).filter(Boolean).join('\n'));if(!script)return wx.showToast({title:'这个创作包没有口播稿',icon:'none'});try{wx.setStorageSync(TELEPROMPTER_KEY,script);}catch(_){}wx.navigateTo({url:'/pages/creation-tool/index?tool=teleprompter'});},
 // ---- optional compose (text work → video)
 boardComposeOpen(){this.setData({boardCompose:{clips:[],uploading:false,position:'bottom',job:null,preview:'',current:''}});},
 boardComposePosition(e){this.setData({'boardCompose.position':e.currentTarget.dataset.position});},
 boardComposeChoose(){
  const compose=this.data.boardCompose;if(!compose||compose.uploading)return;
  wx.chooseMedia({count:Math.max(1,6-compose.clips.length),mediaType:['video'],sourceType:['album','camera'],success:async r=>{
   const files=(r.tempFiles||[]).filter(f=>f.tempFilePath);this.setData({'boardCompose.uploading':true});
   for(const file of files){try{const result=await this.boardUpload(file.tempFilePath);this.setData({boardError:'','boardCompose.clips':[...this.data.boardCompose.clips,{sha:result.asset.sha256,path:file.tempFilePath,seconds:(result.asset.media||{}).durationSeconds}],'boardCompose.preview':this.data.boardCompose.preview||file.tempFilePath});}catch(error){this.boardFail(error);}}
   this.setData({'boardCompose.uploading':false});}});
 },
 boardUpload(filePath){const session=videoSession;return new Promise((resolve,reject)=>{const send=header=>wx.uploadFile({url:config.baseUrl+'/references/upload',filePath,name:'file',header,timeout:600000,success:r=>{let data={};try{data=JSON.parse(r.data||'{}');}catch(_){}r.statusCode===200&&data.asset?resolve(data):reject(Error(data.error||'视频上传失败'));},fail:()=>reject(Error('网络中断，视频未上传'))});if(config.baseUrl.startsWith('http://127.0.0.1:'))return send({});session.session(wx,config.baseUrl).then(login=>send({Authorization:'Bearer '+login.token})).catch(reject);});},
 boardPreviewTime(e){const t=e.detail.currentTime||0;const lines=(this.data.board.outputs.text.lines||[]).filter(l=>typeof l.start==='number'&&t>=l.start&&t<l.end);const current=lines.length?lines[0].text:'';if(current!==this.data.boardCompose.current)this.setData({'boardCompose.current':current});},
 async boardComposeRun(){
  const compose=this.data.boardCompose,work=this.data.board.outputs.text;if(!compose||!compose.clips.length)return this.setData({boardError:'请先选择画面视频'});
  const lines=work.lines.filter(l=>typeof l.start==='number'&&typeof l.end==='number').map(l=>({start:l.start,end:l.end,text:l.text}));
  try{const job=await this.boardRequest('/board/compose',{id:this.data.board.id,clips:compose.clips.map(c=>c.sha),lines,position:compose.position});this.setData({'boardCompose.job':job});this.boardComposePoll(job.id);}catch(error){this.boardFail(error);}
 },
 boardComposePoll(id){clearTimeout(this.composeTimer);this.composeTimer=setTimeout(async()=>{if(this.stopped)return;try{const job=await this.request('/board/jobs/'+id);if(job.video)job.videoUrl=config.baseUrl+job.video;this.setData({'boardCompose.job':job});if(job.status==='running')this.boardComposePoll(id);}catch(error){this.boardFail(error);}},3000);},
 boardVariantOpen(){if(!this.data.boardCompose)this.boardComposeOpen();this.setData({'boardCompose.mode':'variants'});if(this.scrollToBlock)this.scrollToBlock('board-compose');},
 async boardVariantRun(){const compose=this.data.boardCompose;if(!compose||!compose.clips.length)return this.setData({boardError:'请先选择画面视频'});if(this.data.boardVariantBusy)return;
  this.setData({boardVariantBusy:true,boardVariants:null});
  try{const job=await this.boardRequest('/board/variants',{id:this.data.board.id,clips:compose.clips.map(c=>c.sha),position:compose.position},120000);this.setData({boardVariantBusy:false,boardVariants:this.variantView(job)});if(job.status==='running')this.boardVariantPoll(job.id);}catch(error){this.setData({boardVariantBusy:false});this.boardFail(error);}
 },
 variantView(job){return {...job,items:(job.items||[]).map(i=>({...i,videoUrl:i.video?(/^https?:/.test(i.video)?i.video:config.baseUrl+i.video):''}))};},
 boardVariantPoll(id){clearTimeout(this.variantTimer);this.variantTimer=setTimeout(async()=>{if(this.stopped)return;try{const job=await this.request('/board/jobs/'+id);this.setData({boardVariants:this.variantView(job)});if(job.status==='running')this.boardVariantPoll(id);}catch(error){this.boardFail(error);}},4000);},
 boardVariantCopy(e){const item=((this.data.boardVariants||{}).items||[])[Number(e.currentTarget.dataset.index)];if(!item)return;const tags=(((this.data.board.outputs||{}).text||{}).hashtags||[]).map(h=>'#'+h).join(' ');this.copyNow([item.title,item.caption,tags].filter(Boolean).join('\n'));},
 boardVariantSave(e){const item=((this.data.boardVariants||{}).items||[])[Number(e.currentTarget.dataset.index)];if(!item||!item.videoUrl)return;(config.downloadFile?config.downloadFile.bind(null,wx):wx.downloadFile.bind(wx))({url:item.videoUrl,success:r=>{if(r.statusCode!==200)return this.setData({boardError:'下载失败'});wx.saveVideoToPhotosAlbum({filePath:r.tempFilePath,success:()=>wx.showToast({title:'已保存到相册',icon:'success'}),fail:()=>this.setData({boardError:'保存未完成，请检查相册权限'})});},fail:()=>this.setData({boardError:'下载失败，请重试'})});},
 boardSaveComposed(){const job=this.data.boardCompose&&this.data.boardCompose.job;if(!job||!job.videoUrl)return;(config.downloadFile?config.downloadFile.bind(null,wx):wx.downloadFile.bind(wx))({url:job.videoUrl,success:r=>{if(r.statusCode!==200)return this.setData({boardError:'下载失败'});wx.saveVideoToPhotosAlbum({filePath:r.tempFilePath,success:()=>wx.showToast({title:'已保存到相册',icon:'success'}),fail:()=>this.setData({boardError:'保存未完成，请检查相册权限'})});},fail:()=>this.setData({boardError:'下载失败，请重试'})});},
 async boardPublish(){if(this.data.boardBusy)return;this.setData({boardBusy:true});try{const work=await this.boardRequest('/board/works',{id:this.data.board.id,route:this.data.boardRoute||this.data.boardRecommend||'text',caption:((this.data.board.outputs||{}).text||{}).caption||''});this.setData({boardBusy:false,'board.workId':work.id});wx.navigateTo({url:'/pages/board-work/index?id='+work.id});}catch(error){this.boardFail(error);}},
 boardOpenWork(){if(this.data.board&&this.data.board.workId)wx.navigateTo({url:'/pages/board-work/index?id='+this.data.board.workId});}
};
module.exports.bdSections=bdSections;module.exports.commentNote=commentNote;module.exports.methodNote=methodNote;module.exports.bdEvidence=bdEvidence;
