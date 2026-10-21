const creatorPrefs=require('../../utils/creator-preferences');
const discovery=require('../../utils/hotspot-discovery');
const store=require('../../utils/store');
Page({
 data:{mode:'rising',platform:'综合',platforms:discovery.platforms,results:[],rows:[],visible:[],feedStatus:'正在同步热榜…',query:'',context:{},messages:[],reply:'',error:'',selected:null,content:null,contentLoading:false,suggestions:['口红','咖啡','旅行','生活']},
 onLoad(options={}){this._detailId=options.id;const p=creatorPrefs.active(wx);this.setData({mode:['chat','rank','new','rising'].includes(options.mode)?options.mode:'rising',platform:p.useDefaults?p.platform:'综合',suggestions:p.useDefaults&&p.keywords.length?p.keywords:['口红','咖啡','旅行','生活'],preferredTopic:p.useDefaults?({美妆:'口红',美食:'咖啡',旅行:'旅行',生活:'生活'}[p.domain]||''):''});this.refresh();},
 onShow(){discovery.start(this,wx,feed=>{this._feed=feed;this.setData({rows:discovery.decorate(feed.rows)});if(this.data.context.topic){const result=discovery.search(this.data.context.topic,{},this.data.rows);this.setData({results:result.results,reply:result.message});}this.refresh();if(this._detailId){this.detail({currentTarget:{dataset:{id:this._detailId}}});this._detailId=null;}else if(this.data.selected&&this.data.contentLoading)this.loadContent();});},
 onHide(){discovery.stop(this);this.cancelContent();},
 onUnload(){discovery.stop(this);this.cancelContent();},
 reload(){this.onShow();},
 mode(e){this.cancelContent();this.setData({mode:e.currentTarget.dataset.mode,selected:null,error:''});this.refresh();},
 platform(e){this.setData({platform:e.currentTarget.dataset.platform});this.refresh();},
 refresh(){const base=this.data.mode==='chat'?this.data.results:this.data.rows;this.setData({feedStatus:discovery.status(this._feed,this.data.platform),visible:discovery.select(this.data.mode==='chat'&&!this.data.messages.length?[]:base,this.data.platform,this.data.mode)});},
 input(e){this.setData({query:e.detail.value,error:''});},
 suggest(e){this.setData({query:e.currentTarget.dataset.query});this.send();},
 send(){try{const query=this.data.query.trim();const result=discovery.search(query,this.data.context,this.data.rows);this.setData({mode:'chat',context:result.context,results:result.results,reply:result.message,messages:this.data.messages.concat([{query,reply:result.message}]).slice(-6),query:'',error:'',selected:null});this.refresh();}catch(e){this.setData({error:e.message});}},
 reset(){this.setData({context:{},results:[],visible:[],messages:[],reply:'',query:'',error:'',selected:null,platform:'综合'});},
 cancelContent(){this._contentSeq=(this._contentSeq||0)+1;if(this._contentTimer)clearTimeout(this._contentTimer);this._contentTimer=null;},
 detail(e){this.cancelContent();const row=this.data.rows.find(r=>r.id===e.currentTarget.dataset.id);this.setData({selected:row||null,content:null,contentLoading:!!row,error:row?'':'该话题已离开当前榜单，请选择其他话题。'});if(row)this.loadContent();},
 retryContent(){this.loadContent(true);},
 loadContent(retry=false){this.cancelContent();const row=this.data.selected;if(!row)return;const seq=this._contentSeq;this.setData({contentLoading:true});let count=0;let first=true;const poll=()=>{const force=first&&retry;first=false;return discovery.content(wx,row.id,force).then(value=>{if(seq!==this._contentSeq||!this.data.selected)return;if(value.status==='pending'&&count++<20){this.setData({content:value});this._contentTimer=setTimeout(poll,2000);}else this.setData({content:value.status==='pending'?{status:'error',items:[],notice:'获取超时，请稍后重试。'}:value,contentLoading:false});});};poll();},
 copyContent(e){const item=(this.data.content&&this.data.content.items||[]).find(r=>r.id===e.currentTarget.dataset.id);if(item)wx.setClipboardData({data:item.url});},
 viewVideo(e){const item=(this.data.content&&this.data.content.items||[]).find(r=>r.id===e.currentTarget.dataset.id);if(item&&/^https:\/\/(?:www\.)?douyin\.com\/video\/\d+/.test(item.url))wx.navigateTo({url:'/pages/creation-tool/index?tool=download&sourceUrl='+encodeURIComponent(item.url)});},

 noop(){},
 copySource(e){const row=this.data.rows.find(r=>r.id===e.currentTarget.dataset.id);if(row&&row.url)wx.setClipboardData({data:row.url});},
 close(){this.cancelContent();this.setData({selected:null,content:null,contentLoading:false});},
 save(e){const row=this.data.rows.find(r=>r.id===e.currentTarget.dataset.id);if(!row)return;const state=store.load();if(state.ideas.some(x=>x.hotspotId===row.id))return wx.showToast({title:'已存入灵感',icon:'none'});state.ideas.unshift({id:Date.now(),text:row.title,hotspotId:row.id,source:{type:'平台热榜',platform:row.platform,url:row.url,rank:row.rank,fetchedAt:row.fetchedAt}});store.save(state);wx.showToast({title:'已存入灵感',icon:'success'});},
 create(e){const row=this.data.rows.find(r=>r.id===e.currentTarget.dataset.id);if(row)wx.navigateTo({url:'/pages/video/index?idea='+encodeURIComponent(row.title)});}
});
