"""Local launcher: start the pinned loopback backend when needed, then serve MCP.

Set BLENDER_EXE (and optionally DSH_BLENDER_USER_CONFIG / DSH_BLENDER_USER_SCRIPTS)
in the MCP config env. Run BOOTSTRAP_DSH.ps1 first to fetch vendor/dsh-blender-plugin.
"""
import os, runpy, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
PKG = Path(__file__).resolve().parent
if 'BLENDER_EXE' not in os.environ:
    sys.exit('BLENDER_EXE is not set: point it at blender.exe (Blender 4.5) in the MCP config env.')
os.environ.setdefault('DSH_BLENDER_EXE',os.environ['BLENDER_EXE'])
os.environ.setdefault('DSH_BLENDER_WORKDIR',str(PKG / 'backend-work'))
NODE = os.environ.get('NODE_EXE') or shutil.which('node') or 'node'
def alive():
    try:
        with urllib.request.urlopen('http://127.0.0.1:9877/health',timeout=1) as r:
            return r.status == 200
    except Exception:
        return False
if not alive():
    logs = PKG / 'logs'
    logs.mkdir(exist_ok=True)
    flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
    with (logs/'backend.log').open('ab') as log:
        subprocess.Popen([NODE,str(PKG/'vendor/dsh-blender-plugin/runtime/server.mjs'),'--port','9877'],cwd=PKG,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=flags)
    for _ in range(40):
        if alive():
            break
        time.sleep(.2)
runpy.run_path(str(PKG/'server/main.py'),run_name='__main__')
