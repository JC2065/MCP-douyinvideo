(function(root){
  'use strict';
  const key='youai-layout-project1-full-v2';
  const escapeHTML=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const tabs=[['inspiration','灵感','inspiration'],['creation','创作','create'],['learning','学习','learn'],['tasks','任务','tasks'],['account','我的','profile']];
  const tools=[['download','视频下载'],['transcript','文案提取'],['audio','音频提取'],['eraser','去水印'],['cover','封面提取'],['teleprompter','提词器']];
  const cases=[
    {id:'87',title:'把平凡的一天，拍成电影',category:'生活记录',image:'case87-cover',method:'环境 → 细节 → 情绪',intro:'用真实的小事，建立属于自己的生活叙事。'},
    {id:'201',title:'一杯咖啡，如何讲好一个故事',category:'产品展示',image:'case201-0',method:'需求 → 过程 → 体验',intro:'让物品进入生活场景，少一点介绍，多一点体验。'},
    {id:'202',title:'开场三句话，让人愿意听下去',category:'口播表达',image:'case202-0',method:'共鸣 → 观点 → 行动',intro:'先说观众正在经历的事，再给出具体的方法。'},
    {id:'203',title:'周末，去城市里找一点绿色',category:'生活记录',image:'case203-0',method:'远景 → 近景 → 留白',intro:'走慢一点，让环境声和镜头共同讲述。'},
    {id:'204',title:'一个小动作，拍出产品质感',category:'产品展示',image:'case204-0',method:'整体 → 材质 → 使用',intro:'从触感、光线与动作里找到细节。'}
  ];
  const dateKey=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const profile=name=>({name,domain:'生活',audience:'喜欢记录生活的人',goal:'分享生活',duration:'30 秒',mood:'自然真实',form:'生活记录',keywords:'咖啡、旅行、生活',platform:'综合',assistant:'先问我再生成',memory:'',weeklyGoal:3,view:'日历',useDefaults:true});
  function initial(now=new Date()){
    const today=dateKey(now);
    return {version:2,nickname:'YOUAI 创作者',role:'个人',ideas:[{id:'idea-1',text:'拍下下班路上十分钟的光影，把忙碌的一天慢慢放下来。',date:today},{id:'idea-2',text:'做一期小空间布置：不买新家具，只改变光线。',date:today}],favorites:['203'],notes:{},works:[{id:'work-1',title:'把平凡的一天，拍成电影',script:'开场：窗边的光照在杯子上。\n中段：记录出门、散步和街角的声音。\n结尾：平凡的一天，也值得被记住。',status:'草稿',image:'case87-cover',date:today,version:1,review:''},{id:'work-2',title:'周末，去城市里找一点绿色',script:'远景交代公园，近景记录树叶，最后让镜头停留在风里。',status:'分镜待确认',image:'case203-0',date:today,version:1,review:''}],assets:[{id:'asset-1',title:'城市日记 · 演示样片',date:today,archived:false}],profiles:[profile('日常创作'),profile('产品分享')],activeProfile:0,model:{default:'通用模型',custom:[],skills:[],scenes:{},keys:{}},interfaces:{},analysis:{mode:'自动',preset:'通用拆解',overrides:{}},tasks:[{id:'task-1',title:'为街角咖啡店记录一个早晨',brief:'30 秒生活方式短片，包含环境、制作过程和顾客体验。',budget:500,date:today,status:'招募中',history:['创建示例需求']},{id:'task-2',title:'一盏灯，让房间温柔下来',brief:'45 秒产品体验，突出光线变化和使用场景。',budget:800,date:today,status:'制作中',history:['示例需求已建立','已确认合作']}],earnings:[]};
  }
  function load(storage){const base=initial();try{const value=JSON.parse(storage.getItem(key));if(value?.version===2){for(const name of ['ideas','works','assets','profiles','tasks','earnings'])if(!Array.isArray(value[name])||value[name].some(x=>!x||typeof x!=='object'))return base;if(!value.profiles.length||!Array.isArray(value.favorites)||!value.model||!value.interfaces||!value.analysis)return base;return {...base,...value,activeProfile:Math.min(Math.max(0,Number(value.activeProfile)||0),value.profiles.length-1)}}const old=JSON.parse(storage.getItem('youai-layout-project1-ideas'));if(Array.isArray(old))base.ideas.unshift(...old.filter(x=>typeof x==='string').map((text,i)=>({id:'migrated-'+i,text,date:dateKey(new Date())})));}catch{}return base}
  function save(storage,state){try{storage.setItem(key,JSON.stringify(state));return true}catch{return false}}
  function calendar(year,month){const offset=new Date(year,month,1).getDay();const count=new Date(year,month+1,0).getDate();return Array.from({length:offset+count},(_,i)=>i<offset?null:dateKey(new Date(year,month,i-offset+1)))}
  function transition(task,role){const routes={'招募中':['个人','报名中'],'报名中':['商家','制作中'],'制作中':['个人','待验收'],'待修改':['个人','待验收'],'待验收':['商家','已完成']};const next=routes[task.status];if(!next||next[0]!==role)return null;return {...task,status:next[1],history:[...task.history,`${role}操作：${next[1]}`]}}
  const api={key,escapeHTML,tabs,tools,cases,dateKey,profile,initial,load,save,calendar,transition};
  if(typeof module!=='undefined')module.exports=api;else root.ProjectOne=api;
})(typeof globalThis!=='undefined'?globalThis:this);
