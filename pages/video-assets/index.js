const assets=require('../../utils/creative-assets'),store=require('../../utils/store'),history=require('../../utils/video-history'),records=require('../../utils/analysis-records'),account=require('../../utils/account');
Page({
 data:{items:[],visible:[],filter:'全部',filters:['全部','作品','灵感','AI交流','拆解'],error:'',detail:null},
 async onShow(){this.setData({error:'',detail:null});const user=account.cached(wx)?.userId;this._user=user;this._remote={};this.refresh();if(!user)return;this.setData({loading:true});try{const remote=await assets.cloud(wx);if(this._user!==user||account.cached(wx)?.userId!==user)return;this._remote=remote;this.refresh();}catch(e){this.setData({error:e.message});}finally{this.setData({loading:false});}},
 onHide(){this._user=null;},
 refresh(){const items=assets.decorate(wx,assets.merge(store.load(),history.load(wx),this._remote||{},records.load(wx)));this.setData({items});this.applyFilter();},
 filter(e){this.setData({filter:e.currentTarget.dataset.filter,detail:null});this.applyFilter();},
 applyFilter(){const f=this.data.filter;this.setData({visible:this.data.items.filter(r=>f==='全部'||f==='作品'&&['draft','text','image','video'].includes(r.kind)||f==='灵感'&&r.kind==='idea'||f==='AI交流'&&r.kind==='chat'||f==='拆解'&&r.kind==='analysis')});},
 open(e){const row=this.data.items.find(r=>r.key===e.currentTarget.dataset.key);if(!row)return;const url=assets.route(row);if(url){wx.navigateTo({url});}else {this.setData({detail:row});wx.pageScrollTo({scrollTop:0,duration:200});}},
 closeDetail(){this.setData({detail:null});},
 createFromDetail(){const row=this.data.detail;if(!row)return;wx.navigateTo({url:row.kind==='draft'?'/pages/main/index?workId='+encodeURIComponent(row.id):'/pages/video/index?idea='+encodeURIComponent(row.text||row.title)});}
});
