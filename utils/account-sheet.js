const account=require('./account');
const statement=(m=>m&&typeof m.agreed==='function'?m:{ITEMS:[],agreed:()=>false,setAgreed(){}})(require('./collect-statement'));
module.exports={
 data:{busy:false,ready:false,error:'',profile:null,authVisible:false,authPrompt:'',authAgree:false,collectItems:statement.ITEMS,collectOpen:false},
 toggleAgree(){const next=!this.data.authAgree;statement.setAgreed(wx,next);this.setData({authAgree:next,error:''});},
 toggleCollect(){this.setData({collectOpen:!this.data.collectOpen});},
 needAgree(){this.setData({error:'请先阅读并勾选同意《用户信息采集声明》'});},

 async prepare(){
  const canPreview=typeof account.canPreview==='function'&&account.canPreview(wx);this.setData({canPreview,canTrial:typeof account.canTrial==='function'&&account.canTrial(wx)});
  if(typeof account.previewActive==='function'&&account.previewActive(wx)){this.setData({authVisible:false});return;}
  if(this.data.busy)return;this.setData({busy:true,error:'',ready:false});
  try{const profile=await account.load(wx);this.setData({profile,accountProfile:profile,ready:true,authVisible:!!this._loginRequested&&!profile.phoneBound});if(profile.phoneBound)this._loginRequested=false;if(this.startTopicChat)this.startTopicChat(profile);}
  catch(e){if(this.resetTopicChat)this.resetTopicChat();this.setData({error:e.message,authVisible:!!this._loginRequested});}finally{this.setData({busy:false});}
 },
 async openLogin(e){this._loginRequested=true;const message=e&&e.currentTarget&&e.currentTarget.dataset&&e.currentTarget.dataset.message;this.setData({authVisible:true,authPrompt:message||'登录后可同步创作资产并使用账号专属功能',error:'',authAgree:statement.agreed(wx),collectOpen:false});if(!this.data.ready&&!this.data.busy)await this.prepare();},
 closeLogin(){this._loginRequested=false;this.setData({authVisible:false,error:'',authPrompt:''});},
 async authorize(e){
  if(this.data.busy)return;
  const detail=e&&e.detail||{},code=detail.code,errno=Number(detail.errno);
  if(errno===1400001){this.setData({error:'微信手机号授权额度已达上限，暂时无法弹出授权框。请小程序管理员在微信公众平台「管理 → 付费管理 → 手机号快速验证」补充额度后再试。'});return;}
  if(!code){const errMsg=String(detail.errMsg||'').replace(/[\r\n\t]+/g,' ').slice(0,120),codeText=Number.isFinite(errno)&&errno!==0?`（微信错误码 ${errno}）`:'';if(errno===112||/api scope is not declared in the privacy agreement/i.test(errMsg)){this.setData({error:'微信拒绝手机号验证：小程序的《用户隐私保护指引》尚未声明手机号信息。请管理员在微信公众平台补充手机号的收集和使用目的（账号注册登录与账号安全），提交生效后再试。'});return;}this.setData({error:/deny|cancel/i.test(errMsg)?'你已取消手机号授权；如仍要继续，请重新点击并在微信弹窗中确认。':`微信未返回手机号授权凭证${codeText}${errMsg?`：${errMsg}`:'，请重试'}。若重试仍失败，请将此错误信息提供给管理员检查小程序手机号授权配置。`});return;}
  this.setData({busy:true,error:''});
  try{const profile=await account.bind(wx,code);if(!profile.phoneBound)throw Error('手机号绑定未完成，请重新授权');this.setData({profile});this.enter();}
  catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}
 },
 enter(){this._loginRequested=false;this.setData({accountProfile:this.data.profile,authVisible:false,authPrompt:''});if(this.startTopicChat)this.startTopicChat(this.data.profile);},
 async trialLogin(){if(!this.data.authAgree)return this.needAgree();
  if(this.data.busy)return;this.setData({busy:true,error:''});
  try{const profile=await account.createTrial(wx);this.setData({profile});this.enter();wx.showModal({title:'已切换到体验版账号',content:'手机号 '+profile.trialPhone+'（虚构号段，仅供上线前全量验证）。该账号的数据照常上传，并在中台标注为“体验版”。',showCancel:false});}
  catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}
 },
 exitTrial(){wx.showModal({title:'退出体验账号？',content:'退出后回到你自己的微信账号；体验账号的数据保留在中台。',success:r=>{if(!r.confirm)return;account.exitTrial(wx);if(this.resetTopicChat)this.resetTopicChat();this.setData({profile:null,accountProfile:null,ready:false});this.prepare();}});},
 privacy(){wx.openPrivacyContract({fail:()=>this.setData({error:'隐私指引暂不可用，请联系管理员完善配置。'})});},
 previewLocally(){if(account.enablePreview&&account.enablePreview(wx)){this._loginRequested=false;this.setData({authVisible:false});if(this.restorePreviewHotspotWatches)this.restorePreviewHotspotWatches();}},
 stopAuthTouch(){},
};
