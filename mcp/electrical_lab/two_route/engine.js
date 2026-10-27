/* Original teaching model. No physical hardware access. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.LabModel=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const PINS=['电源.L','电源.N','电源.PE','QF.L入','QF.N入','QF.L出','QF.N出','S1.L1','S1.L11','S1.L12','S2.L2','S2.L21','S2.L22','SA.1','SA.2','SA.3','SA.4','SA.5','EL1.L','EL1.N','EL2.L','EL2.N','插座.L','插座.N','插座.PE'];
for(let n=1;n<=10;n++)PINS.push('X.'+n+'a','X.'+n+'b');
const BASE=[['电源.L','QF.L入'],['电源.N','QF.N入'],['电源.PE','X.3a'],['QF.L出','X.1a'],['QF.N出','X.2a'],['X.1b','S1.L1'],['S1.L1','S2.L2'],['S1.L11','X.4a'],['X.4b','SA.1'],['S2.L21','X.5a'],['X.5b','插座.L'],['X.2b','插座.N'],['X.3b','插座.PE'],['X.2b','SA.2'],['SA.3','X.6a'],['X.6b','EL1.L'],['SA.4','X.7a'],['X.7b','EL2.L'],['SA.5','EL1.N'],['EL1.N','EL2.N']];
const INTERNAL=[['SA.2','SA.5'],...Array.from({length:10},(_,i)=>['X.'+(i+1)+'a','X.'+(i+1)+'b'])];
const FAULTS={none:'正常设备',el1_open:'EL1 灯负载断路',el2_open:'EL2 灯负载断路',sa_n_open:'分段器内部 N 供电断路',y1_stuck:'分段器第 1 路触点粘连',s2_open:'S2 工作触点断路',el1_short:'EL1 负载短路（触发教学跳闸）'};
const STAGES=[[true,false],[false,true],[true,true]];
function key(w){return [...w].sort().join('|');}
function graph(edges){const par=Object.fromEntries(PINS.map(p=>[p,p]));function find(x){while(par[x]!==x){par[x]=par[par[x]];x=par[x];}return x;}for(const [a,b] of edges){if(a in par&&b in par)par[find(a)]=find(b);}return{same:(a,b)=>find(a)===find(b),find};}
function contacts(qf,s1,s2,stage){const e=[...INTERNAL];if(qf)e.push(['QF.L入','QF.L出'],['QF.N入','QF.N出']);e.push(['S1.L1',s1?'S1.L11':'S1.L12'],['S2.L2',s2?'S2.L21':'S2.L22']);if(qf&&s1&&stage>=0){if(STAGES[stage][0])e.push(['SA.1','SA.3']);if(STAGES[stage][1])e.push(['SA.1','SA.4']);}return e;}
function validate(wires){
 const errors=[],danger=[],seen=new Set();if(!Array.isArray(wires))return{ok:false,errors:['导线必须是数组'],danger:[],missing:[],extra:[]};
 for(const w of wires){if(!Array.isArray(w)||w.length!==2||!w.every(p=>PINS.includes(p))){errors.push('存在未知端子或格式错误');continue;}if(w[0]===w[1])errors.push('不允许端子自接');if(seen.has(key(w)))errors.push('存在重复导线：'+key(w));seen.add(key(w));}
 if(errors.length)return{ok:false,errors:[...new Set(errors)],danger:[],missing:[],extra:[]};
 for(const qf of [false,true])for(const s1 of [false,true])for(const s2 of [false,true])for(let stage=0;stage<3;stage++){
  const g=graph([...wires,...contacts(qf,s1,s2,stage)]);
  if(g.same('电源.L','电源.N'))danger.push('L-N 直接短接，含开关切换后短接');
  if(g.same('电源.L','电源.PE'))danger.push('相线与 PE 直接相连');
  if(g.same('电源.N','电源.PE'))danger.push('N 与 PE 混接');
 }
 const expected=graph([...BASE,...INTERNAL]),actual=graph([...wires,...INTERNAL]);const missing=[],extra=[];
 for(let i=0;i<PINS.length;i++)for(let j=i+1;j<PINS.length;j++){
  const a=PINS[i],b=PINS[j],e=expected.same(a,b),v=actual.same(a,b);
  if(e&&!v)missing.push(a+' ↔ '+b);if(!e&&v)extra.push(a+' ↔ '+b);
 }
 if(missing.length)errors.push('有应连通的端子未接通');if(extra.length)errors.push('有不应相连的端子被并接');
 return{ok:!errors.length&&!danger.length,errors,danger:[...new Set(danger)],missing,extra};
}
function create(){return{qf:false,s1:false,s2:false,stage:-1,offAt:null,supply:false,fault:'none',tripped:false};}
function output(s){const supply=s.qf&&s.s1&&s.fault!=='sa_n_open';let [y1,y2]=supply&&s.stage>=0?STAGES[s.stage]:[false,false];if(supply&&s.fault==='y1_stuck')y1=true;return{supply,y1,y2,el1:y1&&s.fault!=='el1_open'&&s.fault!=='el1_short',el2:y2&&s.fault!=='el2_open',socket:s.qf&&s.s2&&s.fault!=='s2_open',stage:s.stage,tripped:s.tripped};}
function transition(state,event,time){
 if(!Number.isFinite(time)||time<0)throw Error('时间必须是非负毫秒值');
 let s={...state};if(event.type==='reset')return create();
 if(event.type==='fault'){if(s.qf)throw Error('更换故障前必须断电');if(!(event.value in FAULTS))throw Error('未知故障');s.fault=event.value;}
 else if(['qf','s1','s2'].includes(event.type)){if(typeof event.value!=='boolean')throw Error('开关状态必须是布尔值');if(event.type==='qf'&&event.value&&s.tripped){s.stage=-1;s.offAt=null;s.tripped=false;}s[event.type]=event.value;}
 else if(event.type!=='fault')throw Error('未知动作');
 const on=s.qf&&s.s1&&s.fault!=='sa_n_open';
 if(on&&!state.supply){s.stage=s.offAt===null||time-s.offAt>5000?0:(s.stage+1)%3;}
 if(!on&&state.supply)s.offAt=time;s.supply=on;
 if(s.qf&&output(s).y1&&s.fault==='el1_short'){s.qf=false;s.supply=false;s.tripped=true;s.offAt=time;}
 return s;
}
function sequence(events,fault='none'){if(!Array.isArray(events)||events.length>10000)throw Error('动作列表格式错误或过长');let s=create(),last=0;s=transition(s,{type:'fault',value:fault},0);return events.map(e=>{if(e.time<last)throw Error('时间必须递增或相等');last=e.time;s=transition(s,e,e.time);return{time:e.time,state:{...s},output:output(s)};});}
function measure(wires,s,a,b){if(!PINS.includes(a)||!PINS.includes(b))return{label:'请选择两个有效端子'};let c=contacts(s.qf,s.s1,s.s2,s.stage);const o=output(s);c=c.filter(w=>!(s.fault==='s2_open'&&w.includes('S2.L21'))&&!(w.includes('SA.3')&&!o.y1)&&!(w.includes('SA.4')&&!o.y2));if(o.y1&&!c.some(w=>w.includes('SA.3')))c.push(['SA.1','SA.3']);const g=graph([...wires,...c]);if(!s.qf)return{label:g.same(a,b)?'导通 · 低阻示意':'不导通 / 含负载的路径不作判断',mode:'continuity'};const potential=p=>g.same(p,'电源.L')?220:g.same(p,'电源.N')||g.same(p,'电源.PE')?0:null;const va=potential(a),vb=potential(b);return{label:va===null||vb===null?'浮空 / 未建模电位':Math.abs(va-vb)+' V~ · 理想逻辑示意',value:va===null||vb===null?null:Math.abs(va-vb),mode:'voltage'};}
return{PINS,BASE,INTERNAL,FAULTS,STAGES,validate,create,output,transition,sequence,measure,graph,key};
});
