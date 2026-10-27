// Launch with V3_URL=http://127.0.0.1:8765/index.html npm run perf
// Software renderers are invalid as a proxy for NVIDIA performance.
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';
const url = process.env.V3_URL || 'http://127.0.0.1:8765/index.html';
const resultFile = process.env.V3_PERF_REPORT || './fps_report.json';
const chrome = process.env.CHROME_PATH || undefined;
let browser;
try {
  browser=await chromium.launch({headless:false,executablePath:chrome,args:['--enable-gpu-rasterization']});
  const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
  await page.goto(url,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.__v3Metrics?.ready || window.__v3Metrics?.error,null,{timeout:60000});
  const first=await page.evaluate(()=>window.__v3Metrics);
  if(first.error) throw Error(first.error);
  await page.waitForTimeout(5000); // warmup
  await page.evaluate(()=>{window.__v3Metrics.samples.length=0});
  await page.waitForTimeout(30000);
  const data=await page.evaluate(()=>({...window.__v3Metrics,samples:[...window.__v3Metrics.samples]}));
  const samples=data.samples.map(s=>s.ms).sort((a,b)=>a-b);
  const measuredMs=samples.reduce((a,b)=>a+b,0);
  const averageFps=samples.length?1000*samples.length/measuredMs:0;
  const p95Ms=samples.length?samples[Math.min(samples.length-1,Math.floor(samples.length*.95))]:Infinity;
  const invalidRenderer=/swiftshader|llvmpipe|software|warp|microsoft basic/i.test(data.webglRenderer);
  const isNvidia=/nvidia|geforce|rtx/i.test(data.webglRenderer);
  const pass=data.visibility==='visible' && !invalidRenderer && isNvidia && samples.length>300 && averageFps>=29 && p95Ms<=40;
  const verdict=invalidRenderer||!isNvidia||data.visibility!=='visible'?'UNRESOLVED':pass?'PASS':'FAIL';
  const report={verdict,average_fps:Math.round(averageFps*100)/100,p95_frame_ms:Math.round(p95Ms*100)/100,
    sample_count:samples.length, duration_s:30, warmup_s:5,
    target:'>=29fps average and <=40ms p95 frame interval on hardware GPU',
    webgl_renderer:data.webglRenderer,canvas:data.canvas,dpr:data.dpr,
    window_visibility:data.visibility,model:data.model,url,notes:invalidRenderer?'software renderer; cannot establish RTX performance':(!isNvidia?'NVIDIA GPU not detected; RTX 3070 unverified':null)};
  fs.mkdirSync(path.dirname(resultFile),{recursive:true});fs.writeFileSync(resultFile,JSON.stringify(report,null,2));
  await page.screenshot({path:path.join(path.dirname(resultFile),'web_preview.png')});
  console.log(JSON.stringify(report,null,2));
  process.exitCode=verdict==='PASS'?0:2;
}catch(e){console.error('PERF_ERROR',e);process.exitCode=2;}
finally{if(browser)await browser.close();}
