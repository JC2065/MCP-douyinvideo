const KEY = 'youai-demo-v1';
function initial() { return { role:'个人', name:'小有同学', ideas:[{id:1,text:'用三个生活细节，拍出下班后的松弛感'}], works:[], favorites:[], favoriteAt:{}, tasks:[{id:11,title:'为街角咖啡店拍一条秋日新品短片',brief:'面向年轻人的桂花拿铁，温暖自然，展示制作过程与第一口体验。交付 30 秒竖屏视频，附脚本。',budget:800,date:'2026-11-15',status:'招募中',history:['商家发布任务'],owner:false},{id:12,title:'用镜头记录一件旧物的新生活',brief:'为生活方式品牌创作 45 秒故事短片，体现旧物改造的过程。',budget:1200,date:'2026-11-20',status:'招募中',history:['商家发布任务'],owner:false}], earnings:[] }; }
function transition(state,id,action,payload) {
 const t=state.tasks.find(x=>x.id===id); if(!t) throw Error('任务不存在');
 const rules={apply:['个人','招募中','待选人','创作者申请接单'],select:['商家','待选人','制作中','商家选定创作者'],submit:['个人','制作中','待验收','创作者提交作品'],resubmit:['个人','待修改','待验收','创作者重新提交作品'],revise:['商家','待验收','待修改','商家要求修改'],accept:['商家','待验收','已完成','商家验收通过']};
 const r=rules[action]; if(!r||state.role!==r[0]||t.status!==r[1]) throw Error('当前身份或状态不允许此操作');
 if((action==='submit'||action==='resubmit')&&!payload) throw Error('请先选择已完成作品');
 if(action==='revise'&&!payload) throw Error('请填写修改建议');
 t.status=r[2]; t.history.push(r[3]+(payload?'：'+payload:''));
 if(action==='accept') state.earnings.push({taskId:id,title:t.title,amount:t.budget}); return state;
}
// Merge onto defaults so data saved by an older build (no favoriteAt) still loads.
function load(){const saved=wx.getStorageSync(KEY);return saved?Object.assign(initial(),saved,{favoriteAt:saved.favoriteAt||{}}):initial();}
function save(s){wx.setStorageSync(KEY,s);}
module.exports={initial,transition,load,save};
