// Day boundaries follow the product's China time zone, independent of device zone.
const pad=n=>String(n).padStart(2,'0');
function dayKey(time=Date.now()){const d=new Date(time+8*3600000);return `${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}-${pad(d.getUTCDate())}`;}
function ideaDay(idea){const value=idea.createdAt===undefined?idea.id:idea.createdAt;return typeof value==='number'&&Number.isFinite(value)&&value>=946684800000&&value<=Date.now()?dayKey(value):'';}
function shiftMonth(month,delta){const [y,m]=month.split('-').map(Number);const d=new Date(Date.UTC(y,m-1+delta,1));return `${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}`;}
function build(ideas,month=dayKey().slice(0,7),selected=dayKey(),extraEvents=[]){
 const [year,m]=month.split('-').map(Number);const groups={};const ideaGroups={};const unknown=[];const unknownIdeas=[];
 ideas.forEach(idea=>{const key=ideaDay(idea);if(key){(groups[key]||(groups[key]=[])).push(idea);(ideaGroups[key]||(ideaGroups[key]=[])).push(idea);}else{unknown.push(idea);unknownIdeas.push(idea);}});
 (extraEvents||[]).forEach(event=>{const key=typeof event.day==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(event.day)?event.day:'';if(key)(groups[key]||(groups[key]=[])).push(event);else unknown.push(event);});
 const offset=(new Date(Date.UTC(year,m-1,1)).getUTCDay()+6)%7;
 const length=new Date(Date.UTC(year,m,0)).getUTCDate();const totalCells=Math.ceil((offset+length)/7)*7;const days=[];
 let count=0,activeDays=0;
 for(let index=0;index<totalCells;index++){const day=index-offset+1;const valid=day>0&&day<=length;const key=valid?`${month}-${pad(day)}`:'';const size=key?(groups[key]||[]).length:0;if(size){count+=size;activeDays++;}days.push({id:index,key,day:valid?day:'',count:size,today:key===dayKey(),selected:key===selected,level:size===0?0:size<3?1:size<6?2:3});}
 return {month,label:`${year}年${m}月`,days,count,activeDays,unknownCount:unknown.length,selectedLabel:selected==='unknown'?'未标日期':selected,records:selected==='unknown'?unknownIdeas:ideaGroups[selected]||[]};
}
module.exports={dayKey,ideaDay,shiftMonth,build};
