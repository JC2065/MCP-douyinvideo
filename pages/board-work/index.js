// 数据监控：作品列表（YOUAI 作品 + 数据监控）、发布包、数据回传（公开链接 + 后台截图）、每日数据变化、奖励和复盘卡。
const config=require('../../utils/video-service');
const feedback=require('../../utils/data-feedback');
const backFallback=(m=>m&&m.report?m:{report:(api,info,then)=>then&&then()})(require('../../utils/back-fallback'));
const serviceError=require('../../utils/service-error');
const LABELS={play:'播放',completion:'完播率',bounce2s:'2秒跳出率',avgSeconds:'平均播放时长(秒)',followers:'涨粉',likes:'点赞',comments:'评论',shares:'转发',collects:'收藏'};
const PERCENT=['completion','bounce2s'];
Page({
 data:{id:'',work:null,works:[],link:'',day:1,values:[],busy:false,error:'',notice:'',navTitle:'数据面板',panel:{},compare:null,monitor:false,benchmark:false,tab:'own',groups:[],shown:[],trend:[],summary:null,keyLabels:[]},
 onLoad(q){const id=/^[a-f0-9]{32}$/.test(q.id||'')?q.id:'';this.setData({id,navTitle:id?'作品数据':'数据面板',tab:q.tab==='benchmark'?'benchmark':'own'});id?this.load():this.loadList();},
 onShow(){if(!this.data.id&&this._loaded)this.loadList();},
 show(work,extra={}){const monitor=work.kind==='monitor',benchmark=monitor&&work.role!=='own';this.setData({work,monitor,benchmark,navTitle:benchmark?'对标作品':monitor?'我的作品':'作品数据与复盘',...(t=>({trend:t.rows,keyLabels:t.labels}))(feedback.trend(work.metrics)),summary:feedback.decorate(work),...extra});},
 request(path,method='GET',data,timeout=30000){return new Promise((resolve,reject)=>(config.send?config.send.bind(null,wx):wx.request.bind(wx))({url:config.baseUrl+path,method,data,timeout,success:r=>r.statusCode===200?resolve(r.data):reject(serviceError.response(r)),fail:e=>reject(serviceError.network(e))}));},
 async load(){try{const work=await this.request('/board/works/'+this.data.id);this.show(work,{link:work.link||'',values:this.rows({})});}catch(e){this.setData({error:e.message});}},
 async loadList(){this._loaded=true;try{const r=await this.request('/board/works');const works=(r.rows||[]).map(feedback.decorate);this.setData({works,groups:feedback.groups(works),compare:feedback.compare?feedback.compare(works):null,error:''});this.filter();}catch(e){this.setData({error:e.message});}},
 openWork(e){wx.navigateTo({url:'/pages/board-work/index?id='+e.currentTarget.dataset.id});},
 filter(){this.setData({shown:this.data.works.filter(w=>w.group===this.data.tab),panel:feedback.panel?feedback.panel(this.data.works,this.data.tab):{}});},
 tabPick(e){this.setData({tab:e.currentTarget.dataset.tab});this.filter();},
 async switchRole(){if(this.data.busy)return;this.setData({busy:true,error:''});try{const role=this.data.benchmark?'own':'benchmark';const work=await this.request('/board/works/'+this.data.id+'/role','POST',{role});this.show(work,{notice:role==='own'?'已改为我的作品，可以补传后台截图':'已改为对标作品'});}catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}},
 async addMonitor(){const url=String(this.data.link||'').trim();if(!url||this.data.busy)return;this.setData({busy:true,error:''});try{const work=await this.request('/board/monitors','POST',{url,role:this.data.tab},70000);this.setData({link:''});wx.navigateTo({url:'/pages/board-work/index?id='+work.id});}catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}},
 async refreshNow(){if(this.data.busy)return;this.setData({busy:true,error:'',notice:''});try{const work=await this.request('/board/works/'+this.data.id+'/refresh','POST',{},70000);this.show(work,{notice:'已刷新为最新公开数据'});}catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}},
 copyLink(){const link=this.data.work&&this.data.work.link;if(link)wx.setClipboardData({data:link,success:()=>wx.showToast({title:'已复制作品链接',icon:'none'})});},
 removeMonitor(){wx.showModal({title:'移除这条监控？',content:'已记录的数据会一起删除。',confirmText:'移除',success:async r=>{if(!r.confirm)return;this.setData({busy:true});try{await this.request('/board/works/'+this.data.id+'/remove','POST',{});wx.showToast({title:'已移除',icon:'none'});setTimeout(()=>wx.navigateBack({fail:e=>backFallback.report(wx,{reason:'移除监控后返回失败（'+((e&&e.errMsg)||'未知原因')+'）',action:'打开数据面板'},()=>wx.redirectTo({url:'/pages/board-work/index'}))}),500);}catch(e){this.setData({error:e.message,busy:false});}}});},
 rows(values){return Object.keys(LABELS).map(key=>({key,label:LABELS[key]+(PERCENT.includes(key)?'(%)':''),value:values[key]===undefined?'':String(PERCENT.includes(key)?Math.round(values[key]*1000)/10:values[key])}));},
 copyPublish(){if(!this.data.work)return;wx.setClipboardData({data:this.data.work.publishText||'',success:()=>wx.showToast({title:'已复制标题和话题',icon:'none'})});},
 linkInput(e){this.setData({link:e.detail.value});},
 async saveLink(){if(this.data.busy)return;this.setData({busy:true,error:''});try{const work=await this.request('/board/works/'+this.data.id+'/link','POST',{url:this.data.link});this.show(work,{notice:'已关联作品，之后 14 天每天自动记录公开数据'});}catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}},
 subscribe(){const template=this.data.work&&this.data.work.subscribeTemplateId;const done=accepted=>this.request('/board/works/'+this.data.id+'/subscribe','POST',{accepted}).then(work=>this.show(work)).catch(e=>this.setData({error:e.message}));
  if(!template)return this.setData({notice:'提醒功能尚未开通，可以稍后自行回来回传'});
  wx.requestSubscribeMessage({tmplIds:[template],success:r=>done(r[template]==='accept'),fail:()=>done(false)});},
 dayPick(e){this.setData({day:Number(e.currentTarget.dataset.day)});},
 chooseScreenshot(){if(this.data.busy)return;wx.chooseMedia({count:1,mediaType:['image'],sizeType:['compressed'],success:r=>{const path=r.tempFiles&&r.tempFiles[0]&&r.tempFiles[0].tempFilePath;if(!path)return;this.setData({busy:true,error:'',notice:'正在识别截图中的数字…'});
  wx.getFileSystemManager().readFile({filePath:path,encoding:'base64',success:async file=>{try{const result=await this.request('/board/works/'+this.data.id+'/screenshot','POST',{image:file.data},60000);this.setData({values:this.rows(result.values),notice:result.notice});}catch(e){this.setData({error:e.message,notice:''});}finally{this.setData({busy:false});}},fail:()=>this.setData({busy:false,error:'截图读取失败'})});}});},
 valueInput(e){this.setData({['values['+e.currentTarget.dataset.index+'].value']:e.detail.value});},
 async saveMetrics(){if(this.data.busy)return;const values={};for(const row of this.data.values){if(row.value==='')continue;const n=Number(row.value);if(!Number.isFinite(n)||n<0)return this.setData({error:LABELS[row.key]+'需要是数字'});values[row.key]=PERCENT.includes(row.key)?n/100:n;}
  this.setData({busy:true,error:''});try{const work=await this.request('/board/works/'+this.data.id+'/metrics','POST',{day:this.data.day,values});this.show(work,{notice:work.kind==='monitor'?'已保存':'已保存，获得回传奖励'});}catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}}
});
