const ai=require('../../utils/ai-config');
const insights=require('../../utils/model-insights');
Page({
 data:{state:null,models:ai.models,scenesView:[],modelsView:[],insightsView:[],insightsUpdated:insights.updated,draft:{name:'',baseUrl:'',model:'',key:''},bundleLink:'',error:'',saved:false},
 onLoad(){this.setData({state:ai.load(wx)});this.refresh();},
 refresh(){const s=this.data.state;const sceneName=id=>{const hit=ai.scenes.find(x=>x.id===id);return hit?hit.name:id;};this.setData({modelsView:[...ai.models,...s.custom],insightsView:insights.sorted().map(v=>Object.assign({},v,{name:ai.modelName(s,v.id),goodForText:v.goodFor.map(sceneName).join('、'),isDefault:s.defaultModel===v.id})),scenesView:ai.scenes.map(x=>{const resolved=ai.resolve(s,x.id);const bundleState={};for(const b of resolved.bundles)bundleState[b.id]=true;return {id:x.id,name:x.name,desc:x.desc,cfg:s.scenes[x.id],resolved,bundleState};})});},
 commit(next){try{this.setData({state:ai.save(wx,next),saved:true,error:''});this.refresh();}catch(e){this.setData({error:'保存失败，请检查本机存储后重试'});}},
 save(){this.commit(this.data.state);wx.showToast({title:'配置已保存',icon:'success'});},
 chooseDefault(e){const s=this.data.state;s.defaultModel=e.currentTarget.dataset.id;this.commit(s);},
 keyInput(e){const s=this.data.state;s.keys[e.currentTarget.dataset.id]=e.detail.value;this.commit(s);},
 customField(e){this.setData({draft:Object.assign({},this.data.draft,{[e.currentTarget.dataset.field]:e.detail.value}),saved:false});},
 addCustom(){const s=this.data.state;if(s.custom.length>=3)return this.setData({error:'最多支持 3 个自定义模型'});const d=this.data.draft;if(!d.name.trim())return this.setData({error:'请填写自定义模型名称'});s.custom.push({id:'c'+Date.now()+Math.floor(Math.random()*1e6),name:d.name.trim(),baseUrl:d.baseUrl.trim(),model:d.model.trim(),key:d.key.trim()});this.setData({draft:{name:'',baseUrl:'',model:'',key:''}});this.commit(s);},
 removeCustom(e){const s=this.data.state;s.custom=s.custom.filter(c=>c.id!==e.currentTarget.dataset.id);this.commit(s);},
 sceneToggle(e){const s=this.data.state;s.scenes[e.currentTarget.dataset.id].enabled=e.detail.value;this.commit(s);},
 sceneModel(e){const s=this.data.state;s.scenes[e.currentTarget.dataset.id].model=e.currentTarget.dataset.model;this.commit(s);},
 scenePrompt(e){const s=this.data.state;s.scenes[e.currentTarget.dataset.id].prompt=e.detail.value;this.commit(s);},
 bundleLinkInput(e){this.setData({bundleLink:e.detail.value,saved:false});},
 addBundleLink(){const s=this.data.state;if(s.bundles.length>=5)return this.setData({error:'最多支持 5 个工具包'});const url=this.data.bundleLink.trim();if(!/^https?:\/\//.test(url))return this.setData({error:'请粘贴以 http(s):// 开头的 .mcpb 链接'});const file=decodeURIComponent(url.split('?')[0].split('/').pop()||'').replace(/\.mcpb$/i,'')||'未命名工具包';s.bundles.push({id:'b'+Date.now()+Math.floor(Math.random()*1e6),name:file.slice(0,30),version:'',publisher:'',source:'link',url,fileName:'',tools:[],enabled:true});this.setData({bundleLink:''});this.commit(s);},
 uploadBundle(){const s=this.data.state;if(s.bundles.length>=5)return this.setData({error:'最多支持 5 个工具包'});wx.chooseMessageFile({count:1,type:'file',extension:['mcpb'],success:r=>{const f=(r.tempFiles||[])[0];if(!f)return;const st=this.data.state;st.bundles.push({id:'b'+Date.now()+Math.floor(Math.random()*1e6),name:String(f.name||'未命名工具包').replace(/\.mcpb$/i,'').slice(0,30),version:'',publisher:'',source:'file',url:'',fileName:String(f.name||'').slice(0,100),tools:[],enabled:true});this.commit(st);},fail:()=>{}});},
 removeBundle(e){const s=this.data.state;const id=e.currentTarget.dataset.id;s.bundles=s.bundles.filter(b=>b.id!==id);for(const k of Object.keys(s.scenes))if(s.scenes[k].bundles)s.scenes[k].bundles=s.scenes[k].bundles.filter(x=>x!==id);this.commit(s);},
 bundleToggle(e){const s=this.data.state;const hit=s.bundles.find(b=>b.id===e.currentTarget.dataset.id);if(hit)hit.enabled=e.detail.value;this.commit(s);},
 sceneBundle(e){const s=this.data.state;const {id,bundle}=e.currentTarget.dataset;const sc=s.scenes[id];const current=sc.bundles?s.scenes[id].bundles.slice():s.bundles.filter(b=>b.enabled).map(b=>b.id);const i=current.indexOf(bundle);if(i>=0)current.splice(i,1);else current.push(bundle);sc.bundles=current;this.commit(s);},
 reset(){wx.showModal({title:'恢复默认模型配置',content:'清空全部 Key、自定义模型与各场景覆盖，不影响创作档案与作品。',success:r=>{if(r.confirm){this.commit(ai.normalize({}));wx.showToast({title:'已恢复默认',icon:'success'});}}});}
});
