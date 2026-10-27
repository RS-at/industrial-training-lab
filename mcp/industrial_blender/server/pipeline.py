"""Orchestrated, checkable operations shared by the only exposed MCP server."""
from __future__ import annotations
import json,shutil,os,subprocess,tempfile,threading,http.server
from pathlib import Path
from .core import ROOT,run_blender,blender_exe,dsh_request
from .validators import validate_terminals,check_artifacts,inspect_glb

def inventory(blend_file,output_json):
    out=Path(output_json).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    result=run_blender('bpy_inspect.py',blend_file,['--out',str(out)])
    if result['verdict']=='PASS':result['inventory_path']=str(out)
    return result

def import_asset(blend_file,asset_path,output_blend):
    src=Path(blend_file).resolve();dest=Path(output_blend).resolve()
    if src==dest:raise ValueError('禁止覆盖原始 BLEND')
    if Path(asset_path).suffix.lower() in ('.step','.stp','.fcstd'):
        return {'verdict':'UNRESOLVED','reason':'先通过 FreeCAD 将 STEP/FCStd 转为 GLB/STL 并核对长度单位'}
    return run_blender('bpy_import.py',str(src),['--asset',str(Path(asset_path).resolve()),'--out',str(dest)],300)

def render_views(blend_file,output_dir,size=720,engine='fast'):
    out=Path(output_dir).resolve()
    result=run_blender('bpy_render_views.py',blend_file,['--outdir',str(out),'--size',str(size),'--engine',engine],420)
    if result['verdict']!='PASS':return result
    files=result['result']['files']
    for file in files.values():
        path=Path(file)
        if not path.is_file() or path.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':
            return {'verdict':'FAIL','error':'渲染 PNG 不完整：'+str(path),'execution':result}
    return result

def patch_blend(blend_file,patches,output_blend,dry_run=True):
    if not isinstance(patches,list) or not 1<=len(patches)<=30:raise ValueError('补丁数量需在 1..30')
    allowed={'translate_mm','set_color_rgba','bevel_mm','set_terminal_tags'}
    if any(not isinstance(p,dict) or p.get('op') not in allowed or not isinstance(p.get('object'),str) for p in patches):
        raise ValueError('补丁格式不符合白名单')
    src=Path(blend_file).resolve();out=Path(output_blend).resolve()
    if src==out:raise ValueError('禁止覆盖原始 BLEND')
    if not src.is_file():raise FileNotFoundError(str(src))
    if dry_run:return {'verdict':'UNRESOLVED','dry_run':True,'patches':patches,'source':str(src),'target':str(out)}
    out.parent.mkdir(parents=True,exist_ok=True)
    patch_file=out.with_suffix('.patches.json')
    patch_file.write_text(json.dumps(patches,ensure_ascii=False,indent=2),encoding='utf-8')
    return run_blender('bpy_patch.py',str(src),['--patches',str(patch_file),'--out',str(out)],300)

def refine(blend_file,patches,output_dir,size=640,dry_run=True):
    out=Path(output_dir).resolve();src=Path(blend_file).resolve()
    dest=out/'corrected.blend'
    if dry_run:return patch_blend(str(src),patches,str(dest),True)
    if src.parent==out or src==dest:raise ValueError('输出文件夹不能与源项目目录相同，以避免覆盖已有产物')
    out.mkdir(parents=True,exist_ok=True)
    before=inventory(str(src),str(out/'before_scene.json'))
    if before['verdict']!='PASS':return {'verdict':'FAIL','stage':'before_inspect','result':before}
    before_view=render_views(str(src),str(out/'before_views'),size)
    if before_view['verdict']!='PASS':return {'verdict':'FAIL','stage':'before_render','result':before_view}
    edit=patch_blend(str(src),patches,str(dest),False)
    if edit['verdict']!='PASS':return {'verdict':'FAIL','stage':'patch','result':edit}
    after=inventory(str(dest),str(out/'after_scene.json'))
    if after['verdict']!='PASS':return {'verdict':'FAIL','stage':'after_inspect','result':after}
    after_view=render_views(str(dest),str(out/'after_views'),size)
    if after_view['verdict']!='PASS':return {'verdict':'FAIL','stage':'after_render','result':after_view}
    a=json.loads((out/'before_scene.json').read_text('utf-8'));b=json.loads((out/'after_scene.json').read_text('utf-8'))
    results={'verdict':'UNRESOLVED','source':str(src),'corrected_blend':str(dest),
             'before_views':before_view['result']['files'],'after_views':after_view['result']['files'],
             'before_counts':a['counts'],'after_counts':b['counts'],
             'patch_count':len(patches),'next':'Codex 必须读取前后 6 张图片并判定修改是否达到明确视觉目标，必要时迭代。'}
    (out/'refine_report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    return results

def connect_terminals(blend_file,connections,output_blend):
    if not isinstance(connections,list) or not 1<=len(connections)<=100:
        raise ValueError('connections 数量需在 1..100')
    src=Path(blend_file).resolve();dest=Path(output_blend).resolve()
    if dest==src:raise ValueError('禁止覆盖原始 .blend')
    dest.parent.mkdir(parents=True,exist_ok=True)
    data=dest.with_suffix('.connections.json')
    data.write_text(json.dumps(connections,ensure_ascii=False,indent=2),encoding='utf-8')
    return run_blender('bpy_wires.py',str(src),['--connections',str(data),'--out',str(dest)],300)

def terminal_audit(blend_file,spec_json,output_dir):
    out=Path(output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    snap=out/'terminals.json';r=run_blender('bpy_snapshot.py',blend_file,['--out',str(snap)])
    if r['verdict']!='PASS':return {'verdict':'FAIL','stage':'snapshot','details':r}
    spec=json.loads(Path(spec_json).read_text(encoding='utf-8'))
    check=validate_terminals(json.loads(snap.read_text('utf-8')),spec)
    check['snapshot']=str(snap)
    (out/'terminal_audit.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    return check

def export(blend_file,output_dir,render_width=960):
    if not 320<=render_width<=2560:raise ValueError('render_width out of range')
    src=Path(blend_file).resolve();out=Path(output_dir).resolve()
    if src.parent==out:raise ValueError('导出目录不得等于原始 BLEND 所在目录')
    r=run_blender('bpy_export.py',str(src),['--outdir',str(out),'--resolution',str(render_width)],600)
    if r['verdict']!='PASS':return {'verdict':'FAIL','execution':r}
    check=check_artifacts(str(out))
    return {'verdict':check['verdict'],'audit':check,'execution':r}

class LocalHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def benchmark(glb_path,output_dir,chrome_path=''):
    """Runs a visible 30 s Playwright benchmark on user's own GPU. No simulated fps."""
    glb=Path(glb_path).resolve();inspect_glb(glb)
    node=shutil.which('node')
    if not node:return {'verdict':'UNRESOLVED','reason':'未安装 Node.js'}
    web=ROOT/'web'
    if not (web/'vendor'/'build'/'three.module.js').is_file():
        return {'verdict':'UNRESOLVED','reason':'缺少 Three.js 静态依赖；请先在 web 目录执行 npm install'}
    if not (web/'node_modules'/'playwright').is_dir():
        return {'verdict':'UNRESOLVED','reason':'缺少 Playwright；请先在 web 目录执行 npm install && npx playwright install chromium'}
    dest=Path(output_dir).resolve();dest.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='v3_serve_') as folder:
        site=Path(folder);shutil.copy2(web/'index.html',site/'index.html');shutil.copy2(glb,site/'model.glb')
        shutil.copytree(web/'vendor',site/'vendor')
        class Handler(LocalHandler):
            def __init__(self,*args,**kw):super().__init__(*args,directory=str(site),**kw)
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            env=os.environ.copy();env.update({'V3_URL':f'http://127.0.0.1:{server.server_address[1]}/index.html','V3_PERF_REPORT':str(dest/'fps_report.json')})
            if chrome_path:env['CHROME_PATH']=chrome_path
            p=subprocess.run([node,str(web/'perf.mjs')],cwd=web,env=env,capture_output=True,text=True,timeout=100,encoding='utf-8',errors='replace')
            report_path=dest/'fps_report.json'
            if report_path.is_file():
                report=json.loads(report_path.read_text(encoding='utf-8'))
                report['process_exit']=p.returncode
                return report
            return {'verdict':'UNRESOLVED','process_exit':p.returncode,'stderr':p.stderr[-1500:],'stdout':p.stdout[-1000:]}
        except subprocess.TimeoutExpired:
            return {'verdict':'FAIL','reason':'Playwright 测试超时'}
        finally:
            server.shutdown();thread.join(timeout=4);server.server_close()
