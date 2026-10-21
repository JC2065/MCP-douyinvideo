const backFallback=require('../../utils/back-fallback');
// 灵感碎片箱：查看、整理碎片，交给 TA 聊、拆链接或做成视频（docs/idea-box-plan.md）。
const ideaBox=require('../../utils/idea-box');
const account=require('../../utils/account');
const {BASE}=require('../../utils/service-endpoints');
const KIND={text:'文字',link:'链接',image:'截图',voice:'语音'};
function age(at){const days=Math.floor((Date.now()/1000-at)/86400);return days<=0?'今天':days===1?'昨天':days<30?days+' 天前':Math.floor(days/30)+' 个月前';}
Page({
 data:{filter:'new',open:{},rows:[],counts:{new:0,used:0,archived:0},loading:false,error:'',loggedIn:true},
 onShow(){const profile=account.cached(wx);if(!profile||!profile.phoneBound)return this.setData({loggedIn:false,rows:[]});this.setData({loggedIn:true});this.load();},
 async load(){this.setData({loading:true,error:''});try{const r=await ideaBox.list(wx,this.data.filter==='all'?'':this.data.filter);this.setData({rows:r.rows.map(row=>({...row,image:row.image&&row.image.startsWith('/')?BASE+row.image:row.image,kindLabel:KIND[row.kind]||'碎片',age:age(row.created)})),counts:r.counts});}catch(e){this.setData({error:e.message});}finally{this.setData({loading:false});}},
 toggle(e){const id=e.currentTarget.dataset.id;this.setData({['open.'+id]:!this.data.open[id]});},
 pick(e){this.setData({filter:e.currentTarget.dataset.filter});this.load();},
 row(e){return this.data.rows.find(r=>r.id===e.currentTarget.dataset.id);},
 chat(e){const row=this.row(e);if(!row)return;try{wx.setStorageSync(ideaBox.FOCUS_KEY,{id:row.id,text:row.text});}catch(_){}wx.navigateBack({fail:e=>backFallback.report(wx,{reason:'返回上一页失败（'+((e&&e.errMsg)||'未知原因')+'）'},()=>wx.reLaunch({url:'/pages/main/index'}))});},
 breakdown(e){const row=this.row(e);if(!row||!row.url)return;wx.navigateTo({url:'/pages/video/index?source=douyin&idea='+encodeURIComponent(row.url)});},
 video(e){const row=this.row(e);if(!row)return;wx.navigateTo({url:'/pages/video/index?source=idea&idea='+encodeURIComponent(row.text)});},
 preview(e){const row=this.row(e);if(row&&row.image)wx.previewImage({urls:[row.image]});},
 async mark(e){const row=this.row(e);if(!row)return;try{await ideaBox.setStatus(wx,row.id,row.status==='new'?'used':'new');this.load();}catch(err){wx.showToast({title:err.message,icon:'none'});}},
 remove(e){const row=this.row(e);if(!row)return;wx.showModal({title:'删除这条碎片？',content:'删除后无法恢复'+(row.kind==='image'?'，截图会一并删除':'')+'。',success:async r=>{if(!r.confirm)return;try{await ideaBox.remove(wx,row.id);this.load();}catch(err){wx.showToast({title:err.message,icon:'none'});}}});},
 login(){wx.navigateBack({fail:e=>backFallback.report(wx,{reason:'返回上一页失败（'+((e&&e.errMsg)||'未知原因')+'）'},()=>wx.reLaunch({url:'/pages/main/index'}))});},
});
