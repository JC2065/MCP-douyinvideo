// Breakdown plans: built-in and mine; create by chat, induce from 3–5 sample videos, fork, edit, roll back.
const config=require('../../utils/video-service');
const serviceError=require('../../utils/service-error');
const FORMATS=[{id:'text',name:'一段文字'},{id:'list',name:'要点列表'},{id:'timeline',name:'时间轴'},{id:'score',name:'打分'},{id:'option',name:'选项'}];
const USES=[{id:'script',name:'脚本/提词器'},{id:'shotlist',name:'分镜清单'},{id:'rhythm',name:'节奏卡'},{id:'checklist',name:'准备清单'},{id:'brief',name:'简报'},{id:'text',name:'文字作品'}];
Page({
 data:{tab:'mine',builtin:[],mine:[],busy:false,error:'',chat:'',draft:null,links:'',job:null,editing:null,formats:FORMATS,uses:USES},
 onLoad(){this.load();},onUnload(){this.stopped=true;clearTimeout(this.timer);},
 request(path,method='GET',data,timeout=60000){return new Promise((resolve,reject)=>(config.send?config.send.bind(null,wx):wx.request.bind(wx))({url:config.baseUrl+path,method,data,timeout,success:r=>r.statusCode===200?resolve(r.data):reject(serviceError.response(r)),fail:e=>reject(serviceError.network(e))}));},
 async load(){try{const plans=await this.request('/board/plans');this.setData({builtin:plans.builtin,mine:plans.mine});}catch(e){this.setData({error:e.message});}},
 tab(e){this.setData({tab:e.currentTarget.dataset.tab});},
 act(action,data){if(this.data.busy)return Promise.resolve();this.setData({busy:true,error:''});return this.request('/board/plans','POST',{action,...data},120000).then(r=>{this.setData({busy:false});return r;}).catch(e=>{this.setData({busy:false,error:e.message});throw e;});},
 chatInput(e){this.setData({chat:e.detail.value});},
 async chatDraft(){try{const r=await this.act('chat',{message:this.data.chat});this.setData({draft:r.draft});}catch(_){}},
 async saveDraft(){if(!this.data.draft)return;try{await this.act('save',{plan:{...this.data.draft,source:'chat'}});this.setData({draft:null,chat:'',tab:'mine'});this.load();}catch(_){}},
 linksInput(e){this.setData({links:e.detail.value});},
 async induce(){const urls=(this.data.links.match(/https:\/\/v\.douyin\.com\/[^\s]+/g)||[]).slice(0,5);if(urls.length<3)return this.setData({error:'请粘贴同一位博主的 3–5 条抖音链接'});try{const job=await this.act('induce',{urls});this.setData({job});this.poll(job.id);}catch(_){}},
 poll(id){clearTimeout(this.timer);this.timer=setTimeout(async()=>{if(this.stopped)return;try{const job=await this.request('/board/jobs/'+id);this.setData({job});if(job.status==='running')this.poll(id);else if(job.status==='done'){this.setData({tab:'mine'});this.load();}}catch(e){this.setData({error:e.message});}},4000);},
 async fork(e){try{await this.act('fork',{planId:e.currentTarget.dataset.id});this.setData({tab:'mine'});this.load();}catch(_){}},
 async remove(e){const planId=e.currentTarget.dataset.id;wx.showModal({title:'删除方案',content:'删除后不可恢复，确定吗？',success:async r=>{if(!r.confirm)return;try{const plans=await this.act('delete',{planId});this.setData({mine:plans.mine});}catch(_){}}});},
 async rollback(e){const {id,version}=e.currentTarget.dataset;try{await this.act('rollback',{planId:id,version:Number(version)});this.load();}catch(_){}},
 edit(e){const plan=this.data.mine.find(p=>p.id===e.currentTarget.dataset.id);if(plan)this.setData({editing:JSON.parse(JSON.stringify(plan))});},
 editField(e){const {index,key}=e.currentTarget.dataset;this.setData({['editing.fields['+index+'].'+key]:e.detail.value});},
 editPick(e){const {index,key}=e.currentTarget.dataset;const list=key==='format'?FORMATS:USES;this.setData({['editing.fields['+index+'].'+key]:list[Number(e.detail.value)].id});},
 editName(e){this.setData({['editing.'+e.currentTarget.dataset.key]:e.detail.value});},
 addField(){const fields=this.data.editing.fields;if(fields.length>=12)return;this.setData({'editing.fields':[...fields,{key:'f'+(fields.length+1)+'_'+Date.now()%1000,label:'新字段',ask:'要模型回答什么',format:'text',useIn:'brief',needTime:false}]});},
 removeField(e){const fields=this.data.editing.fields.slice();fields.splice(Number(e.currentTarget.dataset.index),1);this.setData({'editing.fields':fields});},
 cancelEdit(){this.setData({editing:null});},
 async saveEdit(){const plan=this.data.editing;try{await this.act('save',{planId:plan.id,plan:{name:plan.name,fitFor:plan.fitFor,fields:plan.fields}});this.setData({editing:null});this.load();}catch(_){}}
});
