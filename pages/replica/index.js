// 1:1 replica with the user's own Bailian / Qwen AI key. The key stays on this phone
// (only if the user chooses to remember it) and is sent with each request; YOUAI's
// server never stores it. Billing goes to the user's own account.
const config=require('../../utils/video-service');
const serviceError=require('../../utils/service-error');
const KEY_STORE='youai-replica-key-v1';
const PROVIDERS=[{id:'bailian',name:'阿里云百炼'},{id:'qianwen',name:'千问AI平台'}];
const PRICE={'wan-std':0.4};
Page({
 data:{providers:PROVIDERS,provider:'bailian',key:'',remember:true,keyStatus:'',sha:'',seconds:0,photoPath:'',mode:'wan-std',consent:false,busy:false,job:null,jobs:[],error:'',videoUrl:'',saving:false},
 onLoad(q){const sha=/^[a-f0-9]{64}$/.test(q.sha||'')?q.sha:'';const seconds=Math.min(30,Math.max(0,Number(q.seconds)||0));let saved={};try{saved=wx.getStorageSync(KEY_STORE)||{};}catch(_){}
  this.setData({sha,seconds,provider:PROVIDERS.some(p=>p.id===saved.provider)?saved.provider:'bailian',key:typeof saved.key==='string'?saved.key:'',remember:saved.key?true:this.data.remember});this.loadJobs();},
 onUnload(){this.stopped=true;clearTimeout(this.timer);},
 request(path,method='GET',data,timeout=20000){return new Promise((resolve,reject)=>(config.send?config.send.bind(null,wx):wx.request.bind(wx))({url:config.baseUrl+path,method,data,timeout,success:r=>r.statusCode===200?resolve(r.data):reject(serviceError.response(r)),fail:e=>reject(serviceError.network(e))}));},
 credentials(){return {provider:this.data.provider,key:this.data.key.trim()};},
 persistKey(){try{if(this.data.remember&&this.data.key.trim())wx.setStorageSync(KEY_STORE,this.credentials());else wx.removeStorageSync(KEY_STORE);}catch(_){}},
 providerChange(e){const p=PROVIDERS[Number(e.detail.value)];if(p)this.setData({provider:p.id,keyStatus:''});},
 keyFocus(){this.setData({keyFocused:true});},keyBlur(){this.setData({keyFocused:false});},keyInput(e){this.setData({key:String(e.detail.value||''),keyStatus:''});},
 rememberChange(e){this.setData({remember:!!(e.detail.value||[]).length});this.persistKey();},
 consentChange(e){this.setData({consent:!!(e.detail.value||[]).length});},
 modeChange(e){const mode=e.currentTarget.dataset.mode;if(['wan-std','wan-pro'].includes(mode))this.setData({mode});},
 forgetKey(){try{wx.removeStorageSync(KEY_STORE);}catch(_){}this.setData({key:'',keyStatus:'已从本机清除'});},
 openGuide(){wx.setClipboardData({data:'https://bailian.console.aliyun.com/',success:()=>wx.showToast({title:'控制台地址已复制',icon:'none'})});},
 async checkKey(){if(this.data.busy)return;this.setData({busy:true,error:'',keyStatus:'检测中…'});try{const r=await this.request('/replica/check','POST',this.credentials());this.setData({keyStatus:r.message||'Key 可用'});this.persistKey();}catch(e){this.setData({keyStatus:'',error:e.message});}finally{this.setData({busy:false});}},
 choosePhoto(){wx.chooseMedia({count:1,mediaType:['image'],sizeType:['compressed'],success:r=>{const path=r.tempFiles&&r.tempFiles[0]&&r.tempFiles[0].tempFilePath;if(path)this.setData({photoPath:path,error:''});}});},
 estimate(){const price=PRICE[this.data.mode];return price&&this.data.seconds?'约 ¥'+(price*this.data.seconds).toFixed(2):'按平台高质量档单价计费';},
 submit(){if(this.data.busy)return;const c=this.credentials();
  if(!this.data.sha)return this.setData({error:'请先在“爆款拆解复刻”里获取参考视频'});
  if(!c.key)return this.setData({error:'请填写你自己的 API Key'});
  if(!this.data.photoPath)return this.setData({error:'请选择人物照片'});
  if(!this.data.consent)return this.setData({error:'请先确认素材授权'});
  wx.showModal({title:'确认生成',content:'将用你的 Key 调用 wan2.2-animate-move，'+this.estimate()+'，费用从你的账户直接扣除，生成约 3–6 分钟。继续？',success:r=>{if(r.confirm)this.create();}});},
 async create(){this.setData({busy:true,error:'',job:null,videoUrl:''});this.persistKey();
  try{const fs=wx.getFileSystemManager();const photo=await new Promise((resolve,reject)=>fs.readFile({filePath:this.data.photoPath,encoding:'base64',success:r=>resolve(r.data),fail:()=>reject(Error('照片读取失败，请重新选择'))}));
   const job=await this.request('/replica/jobs','POST',{...this.credentials(),reference:{asset:{sha256:this.data.sha}},photo,mode:this.data.mode,consent:true},120000);
   this.setData({job});this.poll(job.id);}catch(e){this.setData({error:e.message});}finally{this.setData({busy:false});}},
 poll(id,delay=15000){clearTimeout(this.timer);if(this.stopped)return;this.timer=setTimeout(async()=>{try{const job=await this.request('/replica/status','POST',{id,...this.credentials()},120000);this.setData({job,videoUrl:job.video?config.baseUrl+job.video:''});if(job.status==='running'||job.status==='submitting')this.poll(id);else this.loadJobs();}catch(e){this.setData({error:e.message});this.poll(id,30000);}},delay);},
 async loadJobs(){try{const r=await this.request('/replica/jobs');const jobs=r.jobs||[];this.setData({jobs});const running=jobs.find(j=>j.status==='running');if(running&&!this.data.job&&this.data.key){this.setData({job:running});this.poll(running.id,1000);}}catch(_){}},
 openJob(e){const job=this.data.jobs.find(j=>j.id===e.currentTarget.dataset.id);if(!job)return;this.setData({job,videoUrl:job.video?config.baseUrl+job.video:''});if(job.status==='running')this.poll(job.id,500);},
 async save(){if(this.data.saving||!this.data.videoUrl)return;this.setData({saving:true,error:''});let filePath;
  try{filePath=await new Promise((resolve,reject)=>(config.downloadFile?config.downloadFile.bind(null,wx):wx.downloadFile.bind(wx))({url:this.data.videoUrl,success:r=>r.statusCode===200&&r.tempFilePath?resolve(r.tempFilePath):reject(Error('下载失败')),fail:()=>reject(Error('下载失败，请重试'))}));
   await new Promise((resolve,reject)=>wx.saveVideoToPhotosAlbum({filePath,success:resolve,fail:e=>reject(Error(/auth|deny/.test(e.errMsg)?'未获得相册权限，请在设置中允许后重试':'保存未完成'))}));wx.showToast({title:'已保存到相册',icon:'success'});}
  catch(e){this.setData({error:e.message});}finally{if(filePath)wx.getFileSystemManager().unlink({filePath,fail(){}});this.setData({saving:false});}}
});
