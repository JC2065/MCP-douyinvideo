(function(){
 const M=window.WorkflowMapping,D=window.WorkflowDesign;let p=M.project(),bundle=null,serial=0,view=null;
 const el=(tag,value,cls)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=value;if(cls)n.className=cls;return n;};
 const button=(label,fn,cls)=>{const n=el('button',label,cls);n.type='button';n.onclick=()=>{try{fn();}catch(e){view.querySelector('[role=status]').textContent=e.message;}};return n;};
 function render(){
  if(!view)return;view.replaceChildren();const heading=el('div',undefined,'panel-heading');heading.append(el('h2','三阶段共用一条创作记录'),el('span','本地模拟 · 不执行AI或付费生成'));view.append(heading);
  const track=el('div',undefined,'mapping-track');for(const [stage,name]of [['requirements','需求设计'],['analysis','作品拆解'],['production','作品产出']]){const s=el('section');s.append(el('strong',name),el('p',M.contracts[stage].input),el('small',M.contracts[stage].output));track.append(s);}view.append(track);
  const actions=el('div',undefined,'mapping-actions');actions.append(button('采用当前草案并开始演练',()=>{bundle=M.release(draft,'preview-'+(++serial));M.start(p,bundle);render();},'primary'),button('清空项目演练',()=>{p=M.project();bundle=null;render();},'quiet'));view.append(actions);
  view.append(el('p','演练路径：需求确认 → 可选拆解 → 作品产出。切换左侧板块后采用该阶段草案；独立拆解也可先保存。','hint'));
  const body=el('div',undefined,'mapping-body'),phone=el('section',undefined,'mapping-phone');phone.append(el('div','YOUAI · 用户执行界面','mapping-phone-nav'));const step=M.current(p),run=p.run;
  if(step){phone.append(el('small',`${D.boards.find(b=>b.id===run.stage).name} · ${run.index+1}/${run.flow.steps.length}`),el('h3',step.title),el('p',M.components[step.capability]));
   if(run.error){phone.append(el('p',run.error,'mapping-error'),button('重试当前步骤',()=>{M.retry(p);render();},'primary'));}
   else {const content={input:'咖啡店的第一杯早晨 · 视频号 · 15秒',skill:'先拍磨豆与倒奶细节，再给出赶路前的轻松片刻。',evidence:'00:00–00:03 杯口特写；00:03–00:08 制作过程。仅为示例证据。',review:'确认本阶段结果后继续；修改需求将形成新版本。',generate:'示例生成结果，不调用真实模型，不产生费用。',package:'脚本、分镜与视频占位结果一起预览。',archive:'作品已保存，飞书归档通过队列独立处理。'};phone.append(el('p',content[step.capability],'mapping-example'));
    const check=el('input');check.type='checkbox';const label=el('label');label.append(check,document.createTextNode(step.capability==='generate'?'我已确认方案与费用上限（演练）':'我已检查并确认当前结果'));
    if(['review','generate'].includes(step.capability))phone.append(label);
    phone.append(button(step.capability==='review'?'确认结果并继续':'完成当前步骤（模拟）',()=>{M.advance(p,{accepted:check.checked,budgetConfirmed:check.checked,actionId:run.id+'-'+run.index});render();},'primary'),button('模拟接口超时',()=>{M.fail(p);render();},'quiet'));
   }
  }else phone.append(el('h3',p.work?'作品已保存':run?'本阶段已确认':'从一个创作想法开始'),el('p',p.work?'作品资产可查看；飞书归档当前为待处理。':'在左侧选阶段，用当前默认或自定义草案开始演练。'));
  const data=el('section',undefined,'mapping-data');data.append(el('h3','同一个项目，逐步积累'),el('p','运行版本：'+(run?run.revision:'尚未开始')),el('p','需求简报：'+(p.brief?p.brief.topic:'待确认')),el('p','拆解方法：'+(p.analysis?p.analysis.method:'可选，尚未确认')),el('p','作品资产：'+(p.work?p.work.assets.join(' / '):'待产出')),el('p','飞书归档：'+({not_requested:'尚未产生归档事件',pending:'待处理，失败可重试'}[p.archive])),el('p','运行中使用流程快照；左侧修改草案不会改变当前任务。','hint'));body.append(phone,data);view.append(body,el('p','', 'mapping-message'));view.lastChild.setAttribute('role','status');
  const table=el('table');const caption=el('caption','网页配置与小程序组件映射');table.append(caption);for(const [key,name]of Object.entries(M.components)){const row=el('tr');row.append(el('th',D.capabilities[key]),el('td',name));table.append(row);}view.append(table);
 }
 view=el('section',undefined,'panel mapping-panel');document.getElementById('workspace').prepend(view);render();
})();
