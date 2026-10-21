const presets=require('../utils/analysis-presets');
const store=require('../utils/store');
function create(item,prepare,api,repository=store,pages=()=>getCurrentPages()){
 return {
 data:{item,section:'看懂作品',sections:['看懂作品','逐段拆解','跟着练习'],active:-1,favorited:false,error:false,errorMessage:'',videoSrc:'',loading:true,theme:'',checks:[false,false,false],analysis:null,detailsOpen:false,supplementsOpen:false,analysisIndex:0,analysisOptions:['跟随设置','自动选择'].concat(presets.presets.map(p=>p.name))},
 onLoad(){this.prepareVideo();},
 onShow(){this.syncHandle=presets.connect(api,state=>{this.setData({templateSyncState:state.message,templateSyncBusy:!state.ready});if(state.ready)this.refreshAnalysis();});this.setData({favorited:repository.load().favorites.includes(item.id)});this.refreshAnalysis();},
 onHide(){if(this.syncHandle)this.syncHandle.close();},
 onUnload(){this.disposed=true;if(this.syncHandle)this.syncHandle.close();},
 toggleDetails(){this.setData({detailsOpen:!this.data.detailsOpen});},
 toggleSupplements(){this.setData({supplementsOpen:!this.data.supplementsOpen});},
 refreshAnalysis(){const prefs=presets.load(api),analysis=presets.analyze(item,prefs),o=prefs.overrides[item.id],rows=presets.catalog(prefs);this.setData({analysis,supplementsOpen:false,analysisOptions:['跟随设置','自动选择'].concat(rows.map(row=>row.name)),analysisIds:rows.map(row=>row.id),analysisIndex:!o?0:o==='auto'?1:rows.findIndex(p=>p.id===o)+2,materialOptions:presets.templates.types,materialIndex:presets.templates.types.findIndex(type=>type.id===analysis.materialType),analysisGoals:presets.templates.goals.map(goal=>({...goal,picked:analysis.goals.some(row=>row.id===goal.id)}))});},
 chooseAnalysis(e){if(this.data.templateSyncBusy)return api.showToast({title:'请等待账号同步完成',icon:'none'});const i=Number(e.detail.value);if(!Number.isInteger(i)||i<0||i>=this.data.analysisOptions.length)return;const prefs=presets.load(api),rows=presets.catalog(prefs);if(i===0)delete prefs.overrides[item.id];else prefs.overrides[item.id]=i===1?'auto':rows[i-2].id;presets.save(api,prefs);this.refreshAnalysis();api.showToast({title:'已更新本案例拆解',icon:'none'});},
 analysisGoal(e){if(this.data.templateSyncBusy)return api.showToast({title:'请等待账号同步完成',icon:'none'});const id=e.currentTarget.dataset.id,prefs=presets.load(api),current=this.data.analysis.goals.map(goal=>goal.id),next=current.includes(id)?current.filter(value=>value!==id):current.concat(id);if(!next.length)return api.showToast({title:'至少保留一个目标',icon:'none'});prefs.goalOverrides[item.id]=next;presets.save(api,prefs);this.refreshAnalysis();},
 analysisMaterial(e){if(this.data.templateSyncBusy)return api.showToast({title:'请等待账号同步完成',icon:'none'});const type=presets.templates.types[Number(e.detail.value)];if(!type)return;const prefs=presets.load(api);prefs.materialOverrides[item.id]=type.id;prefs.overrides[item.id]='auto';presets.save(api,prefs);this.refreshAnalysis();},
 settings(){api.navigateTo({url:'/pages/settings/index'});},
 async prepareVideo(force=false){if(this.preparing)return;this.preparing=true;this.setData({loading:true,error:false,errorMessage:'',videoSrc:''});try{const videoSrc=await prepare(force);if(!this.disposed)this.setData({videoSrc,loading:false});}catch(e){if(!this.disposed)this.setData({loading:false,error:true,errorMessage:'本地视频准备失败：'+(e.errMsg||e.message||'未知错误')});}finally{this.preparing=false;}},
 section(e){this.setData({section:e.currentTarget.dataset.name});},
 seek(e){const i=Number(e.currentTarget.dataset.index);if(!Number.isInteger(i)||!item.segments[i])return;if(!this.data.videoSrc||this.data.loading||this.data.error)return api.showToast({title:'请先加载视频或点击重试',icon:'none'});this.setData({active:i});const v=api.createVideoContext('caseVideo',this);v.seek(item.segments[i].start);v.play();api.pageScrollTo({scrollTop:0,duration:250});},
 time(e){const t=e.detail.currentTime,active=item.segments.findIndex(s=>t>=s.start&&t<s.end);if(active!==this.data.active)this.setData({active});},
 failed(e){const d=e&&e.detail||{};this.setData({error:true,errorMessage:d.errMsg||'视频读取或解码失败，请重新加载'});},
 retry(){return this.prepareVideo(true);},
 favorite(){const s=repository.load(),i=s.favorites.indexOf(item.id);if(i<0)s.favorites.push(item.id);else s.favorites.splice(i,1);repository.save(s);this.setData({favorited:i<0});},
 theme(e){this.setData({theme:e.detail.value});},
 check(e){const i=Number(e.currentTarget.dataset.index);if(!Number.isInteger(i)||i<0||i>2)return;const checks=this.data.checks.slice();checks[i]=!checks[i];this.setData({checks});},
 create(){const theme=this.data.theme.trim();if(!theme)return api.showToast({title:'先填写你的创作主题',icon:'none'});const stack=pages(),main=stack[stack.length-2];if(!main||typeof main.applyCase!=='function')return;const analysis=this.data.analysis||presets.analyze(item,presets.load(api));const selected=presets.practiceCase(item,analysis.preset.id,analysis);const apply=()=>{main.setData({selected,title:theme,draft:'',learningForDraft:true,workId:null,source:{type:'学习案例',id:item.id,text:item.title+' · '+analysis.preset.name}});main.applyCase();api.navigateBack();};if(main.data&&main.data.draft&&main.data.draft.trim())api.showModal({title:'创建新的练习草稿',content:'将替换编辑区未保存的内容；已保存作品不受影响。',success:r=>{if(r.confirm)apply();}});else apply();},
 note(){const s=repository.load(),analysis=this.data.analysis||presets.analyze(item,presets.load(api));s.ideas.unshift({id:Date.now(),text:'案例学习：'+item.title+'\n拆解方案：'+analysis.preset.name+'\n'+item.method+'\n我的尝试：'+(this.data.theme.trim()||'补充自己的主题与可核实信息'),caseId:item.id});repository.save(s);api.showToast({title:'已存入灵感记录',icon:'success'});},
 source(){api.setClipboardData({data:'https://ads.tiktok.com/business/en-US/creative-codes'});}
 };
}
module.exports={create};
