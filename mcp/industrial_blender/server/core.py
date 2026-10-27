"""One MCP, Blender subprocess backend, optional DSH HTTP engine (not an MCP)."""
from __future__ import annotations
import json,os,shutil,subprocess,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=frozenset({'bpy_patch.py','bpy_snapshot.py','bpy_export.py','bpy_inspect.py','bpy_import.py','bpy_render_views.py','bpy_wires.py'})

def blender_exe():
    supplied=os.environ.get('BLENDER_EXE','').strip()
    if supplied:
        path=Path(supplied)
        if not path.is_file():raise FileNotFoundError(f'BLENDER_EXE 路径不存在：{supplied}')
        return str(path)
    found=shutil.which('blender')
    if found:return found
    raise FileNotFoundError('找不到 Blender；请设置 BLENDER_EXE 为 Blender.exe 完整路径')

def run_blender(script:str,blend_file:str,args:list[str],timeout_s:int=180)->dict:
    if script not in RUNTIME:raise ValueError('script not on allowlist')
    src=Path(blend_file).resolve()
    if not src.is_file() or src.suffix.lower()!='.blend':raise ValueError(f'找不到 .blend：{src}')
    script_path=ROOT/'runtime'/script
    command=[blender_exe(),'-b',str(src),'--python-exit-code','3','--python',str(script_path),'--',*args]
    try:
        p=subprocess.run(command,capture_output=True,text=True,timeout=timeout_s,encoding='utf-8',errors='replace')
    except subprocess.TimeoutExpired as e:
        return {'verdict':'FAIL','error':f'Blender 超时：{timeout_s}s','stdout_tail':str(e.stdout or '')[-3000:]}
    marker='V3_RESULT '
    lines=[s[len(marker):] for s in p.stdout.splitlines() if s.startswith(marker)]
    result=None
    if lines:
        try:result=json.loads(lines[-1])
        except json.JSONDecodeError:pass
    return {'verdict':'PASS' if p.returncode==0 and isinstance(result,dict) else 'FAIL',
            'returncode':p.returncode,'result':result,'stdout_tail':p.stdout[-1500:],
            'stderr_tail':p.stderr[-1500:]}

def dsh_request(path,payload=None,timeout_s=8):
    base=os.environ.get('DSH_BASE_URL','http://127.0.0.1:9877').rstrip('/')
    if base not in ('http://127.0.0.1:9877','http://localhost:9877'):raise ValueError('只允许 DSH 本地 9877')
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'} if data else {},method='POST' if data else 'GET')
    with urllib.request.urlopen(req,timeout=timeout_s) as r:
        result=r.read(8*1024*1024)
    return result
