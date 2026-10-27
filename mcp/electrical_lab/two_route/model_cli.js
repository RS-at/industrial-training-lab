'use strict';
const M=require('./engine.js');
function call(req){
 const a=req.arguments||{};
 if(req.name==='get_two_route_lab')return{title:'二路三段照明与独立插座',pins:M.PINS,wires:M.BASE,internal_links:M.INTERNAL,memory_ms:5000,scope:'用户课件教学模型；无交流瞬态、无硬件I/O；实物端子待厂家核对'};
 if(req.name==='list_two_route_faults')return M.FAULTS;
 if(req.name==='validate_two_route_wiring')return M.validate(a.wires);
 if(req.name==='simulate_two_route'){
  const v=M.validate(a.wires);if(!v.ok)return{ok:false,validation:v,timeline:[]};
  return{ok:true,timeline:M.sequence(a.events,a.fault||'none')};
 }
 throw Error('未知工具');
}
module.exports={call};
if(require.main===module){let data='';process.stdin.setEncoding('utf8');process.stdin.on('data',c=>data+=c);process.stdin.on('end',()=>{try{process.stdout.write(JSON.stringify(call(JSON.parse(data))));}catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.message}));process.exitCode=1;}});}
