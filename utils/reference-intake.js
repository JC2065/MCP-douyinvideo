// Link intake for the 拆解 page: platform routing, the usage notice (three buttons) and
// uploading the original video. Mixed into pages/video (required as a top-level constant).
const platform=require('./link-platform');
const notice=require('./link-notice');
const config=require('./video-service');
const session=require('./video-session');
const MAX_BYTES=200*1024*1024;
module.exports={
 intakeLink(value){
  const found=platform.detect(value);
  if(found.platform==='none')return;
  if(!found.supported)return this.setData({linkPlatform:found.platform,referenceStatus:'failed',referenceMessage:found.message,referenceNeedsConfig:false,reference:null,referenceStep:0,referenceDetail:'点“上传原视频”继续'});
  this.setData({linkPlatform:found.platform});
  if(notice.shouldShow(wx)){this._analysisConsent=false;return this.setData({linkNotice:true,linkNoticeText:notice.TEXT,linkNoticeRecognition:notice.RECOGNITION,linkNoticeSnooze:false});}
  // 1 小时内已确认过使用说明（含内容识别说明）：取到视频后直接开始识别，不再二次确认。
  this._analysisConsent=true;this.checkReference();
 },
 linkNoticeSnooze(e){this.setData({linkNoticeSnooze:!!(e.detail.value||[]).length});},
 linkNoticeAccept(){if(this.data.linkNoticeSnooze)notice.snooze(wx);this._analysisConsent=true;this.setData({linkNotice:false});this.checkReference();},
 linkNoticeAbort(){if(this.data.linkNoticeSnooze)notice.snooze(wx);this._analysisConsent=false;this._sourceVersion=(this._sourceVersion||0)+1;clearTimeout(this.referenceTimer);this.setData({linkNotice:false,sourceValue:'',linkPlatform:'',referenceStatus:'idle',referenceMessage:'',reference:null,referenceStep:0,referenceDetail:''});},
 linkNoticeUpload(){if(this.data.linkNoticeSnooze)notice.snooze(wx);this._analysisConsent=true;this.setData({linkNotice:false});this.chooseReferenceVideo();},
 chooseReferenceVideo(){
  if(this.data.referenceStatus==='checking')return;
  wx.chooseMedia({count:1,mediaType:['video'],sourceType:['album','camera'],success:r=>{const file=r.tempFiles&&r.tempFiles[0];if(!file||!file.tempFilePath)return;if(file.size>MAX_BYTES)return this.setData({referenceStatus:'failed',referenceMessage:'原视频超过 200MB，请压缩后上传',reference:null});this.uploadReferenceVideo(file.tempFilePath);}});
 },
 uploadReferenceVideo(filePath){
  const version=this._sourceVersion=(this._sourceVersion||0)+1;clearTimeout(this.referenceTimer);
  this.setData({board:null,sourceValue:'',linkPlatform:'upload',referenceStatus:'checking',referenceMessage:'正在上传原视频…',referenceNeedsConfig:false,reference:null,referenceStep:3,referenceElapsed:'',referenceDetail:'已上传 0%',analysisStatus:'idle',analysisJobId:'',analysisUnderstanding:''});
  const fail=message=>{if(version!==this._sourceVersion||this.stopped)return;this.setData({referenceStatus:'failed',referenceMessage:message||'原视频上传失败，请重试',reference:null,referenceStep:0,referenceDetail:''});};
  const send=header=>{const task=wx.uploadFile({url:config.baseUrl+'/references/upload',filePath,name:'file',header,timeout:600000,
   success:r=>{let data={};try{data=JSON.parse(r.data||'{}');}catch(_){}if(r.statusCode!==200||!data.asset)return fail(data.error);if(version!==this._sourceVersion||this.stopped)return;this.applyReference(data);},
   fail:()=>fail('网络中断，原视频未上传完成，请重试')});
   if(task&&task.onProgressUpdate)task.onProgressUpdate(p=>{if(version===this._sourceVersion)this.setData({referenceDetail:'已上传 '+p.progress+'%'});});};
  if(config.baseUrl.startsWith('http://127.0.0.1:'))return send({});
  session.session(wx,config.baseUrl).then(login=>send({Authorization:'Bearer '+login.token})).catch(e=>fail(e.message));
 },
 noop(){},
 requestGlance(reference){const version=this._sourceVersion;this.setData({glance:null,glanceState:'loading'});if(!this.request){this.setData({glanceState:''});return Promise.resolve('none');}const settle=state=>{if(version===this._sourceVersion&&!this.stopped)this.setData({glanceState:state});};return this.request('/references/glance','POST',{reference},25000).then(value=>{if(version===this._sourceVersion&&!this.stopped&&value&&value.status==='ready'){this.setData({glance:value,glanceState:'ready'});return 'ready';}settle('none');return 'none';}).catch(()=>{settle('none');return 'none';});},
 applyReference(result){
  if(this.stopReferenceProgress)this.stopReferenceProgress();
  const media=result.asset.media||{};
  this.setData({referenceStatus:'acquired',referenceMessage:result.platform==='upload'?'原视频已上传并验证':'视频素材已获取并验证',referenceNeedsConfig:false,reference:result,referenceStep:4,referenceDetail:`${media.width||'?'}×${media.height||'?'} · ${media.durationSeconds||'?'} 秒 · ${(result.asset.sizeBytes/1024/1024).toFixed(1)} MB`});
  this.confirmAnalysis(result);
 }
};
