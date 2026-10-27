"""Non-destructive deployment probe; writes evidence instead of assuming success."""
from __future__ import annotations
import json,sys,time,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge.dsh_gateway import request, discover_upstream

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports'/'dsh_integration_probe.json'

def probe():
    info={'at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
          'upstream':discover_upstream(ROOT),'checks':{},'verdict':'UNRESOLVED',
          'notes':[]}
    p=ROOT/'bridge'/'upstream.json'
    lock=json.loads(p.read_text('utf-8'))
    repo=ROOT/'vendor'/'dsh-blender-plugin'
    if info['upstream']['source_present'] and shutil.which('git'):
        try:
            cp=subprocess.run(['git','rev-parse','HEAD'],cwd=repo,text=True,capture_output=True,timeout=10)
            sha=cp.stdout.strip()
            info['checks']['pinned_commit']={'pass':cp.returncode==0 and sha==lock['commit'],'actual':sha,'expected':lock['commit']}
        except Exception as e:
            info['checks']['pinned_commit']={'pass':False,'error':str(e)}
    else:
        info['checks']['pinned_commit']={'pass':False,'reason':'源代码或 git 不可用'}
    for path in ('/health','/doctor','/commands'):
        try:
            response=request(path,timeout=15)
            passed=(response.get('addon',response).get('kind')=='ok' if path=='/doctor'
                    else response.get('ok') is True)
            if path=='/health':
                passed=passed and response.get('provenance',{}).get('stale') is False
            info['checks'][path]={'pass':passed,'response':str(response)[:3000]}
        except Exception as e:
            info['checks'][path]={'pass':False,'error':str(e)}
    try:
        png=request('/frame.png',query={'size':560},binary=True,timeout=35)
        info['checks']['frame.png']={'pass':True,'png_bytes':len(png)}
    except Exception as e:info['checks']['frame.png']={'pass':False,'error':str(e)}
    try:
        catalog=request('/plan',{'op':'catalog','args':{}},timeout=50)
        info['checks']['catalog']={'pass':bool(catalog.get('ok')),'response':str(catalog)[:3000]}
    except Exception as e:info['checks']['catalog']={'pass':False,'error':str(e)}
    tests=list(info['checks'].values())
    info['verdict']='PASS' if all(t['pass'] for t in tests) else 'UNRESOLVED'
    info['notes'].append('此探针不修改 Blender 场景，不是材质、造型、自动纠错或帧率测试')
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'verdict':info['verdict'],'checks':{k:v['pass'] for k,v in info['checks'].items()},'report':str(REPORT)},ensure_ascii=False,indent=2))
    return 0 if info['verdict']=='PASS' else 2

if __name__=='__main__':sys.exit(probe())
