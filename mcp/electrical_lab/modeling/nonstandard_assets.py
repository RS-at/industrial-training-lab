"""Lightweight educational material registry and *illustrative* SVG generator.
No web scraping, no photo recognition, no electrical safety assertions.
No third-party dependencies. Python 3.10+.
"""
from __future__ import annotations
import copy
from html import escape
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
SOURCES=json.loads((ROOT/'assets'/'material_sources.json').read_text(encoding='utf-8'))
TEMPLATE=json.loads((ROOT/'materials'/'非标设备建档_样例.json').read_text(encoding='utf-8'))
ID_RE=re.compile(r'^[a-z][a-z0-9_-]{2,63}$')
CATEGORIES={'industrial_electrical','plc','hmi','servo','stepper','pneumatic','hydraulic','robot','sensor','nonstandard_machine','other'}
VALID_FLAGS={'unverified','reviewed','manufacturer_document_verified','measured_verified'}


def list_material_sources(search:str=''):
    q=str(search or '').strip().casefold()
    rows=[x for x in SOURCES['sources'] if not q or q in json.dumps(x,ensure_ascii=False).casefold()]
    return {'count':len(rows),'sources':rows,'notice':SOURCES['notice']}


def intake_checklist(category:str='nonstandard_machine', intended_use:str='teaching', private:bool=True):
    category=str(category or 'nonstandard_machine')
    return {
      'category':category,'intended_use':intended_use,'visibility':'private' if private else 'pending_permission_review',
      'minimum_materials':['设备正面/背面/左右侧照片（避免曝光学生或人员）','铭牌、完整型号、硬件版本','带尺寸参照物的测量记录','清晰可读的端子特写与端子说明','工作原理/动作时序说明'],
      'for_simulation':['厂家说明书或经审核的电气/气路图','I/O与气口/触点清单','动作视频/触发条件/安全联锁信息','至少一例正常流程和两例故障案例'],
      'if_robot_or_servo':['额定参数、驱动器型号、安全功能说明','限位/原点、机械行程、碰撞区域与急停条件'],
      'gates':['未核实端子仅能生成示意外观','端子与额定值须有来源才能生成可用于实训教学的接线模型','动作模型须经过状态测试与教师复核','任何模型都不可直接用于带电实操或驱动真实设备'],
      'source_policy':'自有设备照片和图纸需要学校授权；禁止未经许可抓取/再分发商业素材。'
    }


def new_asset_template(asset_id:str, display_name:str, category:str='nonstandard_machine', width_mm:float=300, height_mm:float=180):
    if not isinstance(asset_id,str) or not ID_RE.fullmatch(asset_id):
        return {'error':'asset_id 须以小写字母开头，长度3-64，仅含字母数字下划线和连字符'}
    if not isinstance(display_name,str) or not display_name.strip(): return {'error':'display_name 不能为空'}
    if category not in CATEGORIES:return {'error':'不支持的 category','allowed':sorted(CATEGORIES)}
    if any(type(x) not in (int,float) or not 1<=x<=100000 for x in (width_mm,height_mm)):
        return {'error':'宽高须为1至100000之间的正数（单位mm），示意值需标明未核实'}
    t=copy.deepcopy(TEMPLATE)
    t.update(asset_id=asset_id,display_name=display_name.strip(),category=category)
    t['geometry'].update(width_mm=width_mm,height_mm=height_mm,dimensions_verified=False)
    t['ports']=[]
    t['notes']='未上传证据或核验前：仅示意外观、禁止作为现场端子接线依据'
    return t


def validate_asset_manifest(item:dict):
    errors,warnings=[],[]
    if not isinstance(item,dict): return {'valid':False,'errors':['设备档案必须是 JSON 对象'],'warnings':[],'capabilities':{'illustrative_svg':False,'terminal_training':False,'behavior_simulation':False,'public_distribution':False}}
    aid=item.get('asset_id')
    if not isinstance(aid,str) or not ID_RE.fullmatch(aid):errors.append('asset_id 格式错误')
    if not isinstance(item.get('display_name'),str) or not item['display_name'].strip():errors.append('display_name 不能为空')
    if item.get('category') not in CATEGORIES:errors.append('category 不受支持')
    geo=item.get('geometry')
    if not isinstance(geo,dict):errors.append('geometry 必须是对象');geo={}
    for k in ('width_mm','height_mm'):
        v=geo.get(k)
        if type(v) not in (int,float) or not 1<=v<=100000:errors.append(f'{k} 必须为合理正数（单位mm）')
    if not geo.get('dimensions_verified'):warnings.append('尺寸未经测绘核对；仅生成示意外观')
    ports=item.get('ports')
    if not isinstance(ports,list):errors.append('ports 必须是数组');ports=[]
    seen=set()
    for i,p in enumerate(ports):
        if not isinstance(p,dict):errors.append(f'ports[{i}] 必须为对象');continue
        pid=p.get('id')
        if not isinstance(pid,str) or not pid.strip():errors.append(f'ports[{i}] 缺少 id');continue
        if pid in seen:errors.append('重复端子 id: '+pid)
        seen.add(pid)
        if p.get('position_side','left') not in ('left','right','top','bottom'):
            errors.append(f'{pid} 的 position_side 不合法')
        if not p.get('verified',False):warnings.append(f'{pid} 未核实，不可作为现场接线依据')
        if p.get('verified',False) and not p.get('source_ref'):errors.append(f'{pid} 声称已核实但缺 source_ref')
        if not p.get('kind') or p.get('kind')=='unknown':warnings.append(f'{pid} 缺少信号/气口类型')
    rights=item.get('rights')
    if not isinstance(rights,dict):errors.append('rights 对象缺失');rights={}
    if rights.get('can_redistribute') and not rights.get('license_evidence'):
        errors.append('公开/再次分发声明必须有 license_evidence')
    ver=item.get('verification') or {}
    if not isinstance(ver,dict):errors.append('verification 必须为对象');ver={}
    for k in ('visual','terminals','behavior'):
        if ver.get(k,'unverified') not in VALID_FLAGS:errors.append('verification.'+k+' 状态无效')
    if item.get('visibility') not in ('private','institution_internal','public','pending_permission_review'):
        errors.append('visibility 不合法')
    electrical_ready=bool(ports) and all(p.get('verified') and p.get('source_ref') and p.get('kind') not in ('unknown',None) for p in ports if isinstance(p,dict)) and len(ports)==sum(isinstance(p,dict) for p in ports) and ver.get('terminals') in ('manufacturer_document_verified','measured_verified')
    simulation_ready=electrical_ready and bool(item.get('behaviors')) and ver.get('behavior') in ('manufacturer_document_verified','measured_verified')
    rights_ready=bool(rights.get('can_redistribute') and rights.get('license_evidence')) and item.get('visibility')=='public'
    if not electrical_ready:warnings.append('当前档案不能用于真实端子实训接线（需逐端子来源与审核）')
    if not simulation_ready:warnings.append('缺少经过核对的行为模型，暂不支持可靠的动作仿真')
    if item.get('visibility')=='private':warnings.append('该设备应保持本地/私有云存储，不可公开传播素材')
    return {'valid':not errors,'errors':errors,'warnings':list(dict.fromkeys(warnings)),
      'capabilities':{'illustrative_svg':not errors,'terminal_training':bool(not errors and electrical_ready),'behavior_simulation':bool(not errors and simulation_ready),'public_distribution':bool(not errors and rights_ready)},
      'scope':'metadata_consistency_check_only_not_engineering_safety_certification'}


def render_asset_svg(item:dict):
    checked=validate_asset_manifest(item)
    if not checked['valid']:return {'error':'档案校验未通过','details':checked}
    geo=item['geometry'];w=float(geo['width_mm']);h=float(geo['height_mm'])
    # fixed viewbox, proportional casing; illustration only, never physical scale drawing
    inner_w=480 if w>=h else max(260,round(430*w/h));inner_h=300 if w>=h else 460
    W,H=inner_w+160,inner_h+155
    left=80; top=82
    esc=lambda s:escape(str(s),quote=True)
    draw=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="示意模型 {esc(item["display_name"])}">',
      '<rect width="100%" height="100%" fill="#f3f6fa"/>',
      f'<rect x="{left}" y="{top}" width="{inner_w}" height="{inner_h}" rx="16" fill="#dae2e9" stroke="#455b6d" stroke-width="4"/>',
      f'<rect x="{left+14}" y="{top+14}" width="{inner_w-28}" height="{inner_h-28}" rx="12" fill="#e9eef3" stroke="#98a7b5"/>',
      f'<text x="{W/2}" y="32" font-size="18" fill="#1c3143" text-anchor="middle">{esc(item["display_name"])}</text>',
      f'<text x="{W/2}" y="55" font-size="11" fill="#6e2020" text-anchor="middle">教学示意 / 非厂家原图 / 非现场接线依据</text>',
      f'<text x="{W/2}" y="{top+inner_h/2}" font-size="16" fill="#415466" text-anchor="middle">{esc(item.get("category","nonstandard_machine"))}</text>']
    sidecounts={'left':0,'right':0,'top':0,'bottom':0}
    for p in item.get('ports',[]):sidecounts[p.get('position_side','left')]+=1
    sideindex={s:0 for s in sidecounts}
    for p in item.get('ports',[]):
        side=p.get('position_side','left');idx=sideindex[side];sideindex[side]+=1
        n=sidecounts[side]
        if side=='left': x,y=left,top+inner_h*(idx+1)/(n+1);tx,ty=x+12,y-12
        elif side=='right':x,y=left+inner_w,top+inner_h*(idx+1)/(n+1);tx,ty=x-110,y-12
        elif side=='top': x,y=left+inner_w*(idx+1)/(n+1),top;tx,ty=x-10,y+26
        else:x,y=left+inner_w*(idx+1)/(n+1),top+inner_h;tx,ty=x-10,y-15
        draw.extend([f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#edb84c" stroke="#222" stroke-width="2"/>',
           f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="11" fill="#233b4d">{esc(p["id"])}{ " · 待核实" if not p.get("verified") else ""}</text>'])
    draw.append(f'<text x="{W/2}" y="{H-20}" text-anchor="middle" font-size="11" fill="#445">示意尺寸：{w:g} × {h:g} mm（{ "已测绘" if geo.get("dimensions_verified") else "待测绘"}）</text>')
    draw.append('</svg>')
    return {'asset_id':item['asset_id'],'svg':'\n'.join(draw),'content_type':'image/svg+xml','verification':checked['capabilities'],'note':'SVG 仅示意外观；非厂家 CAD，不能反推端子功能。'}


if __name__ == '__main__':
    if len(sys.argv)<3 or sys.argv[1] not in ('validate','svg'):
        print('Usage: python nonstandard_assets.py validate|svg equipment.json [output.svg]',file=sys.stderr);sys.exit(2)
    manifest=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    if sys.argv[1]=='validate':
        report=validate_asset_manifest(manifest);print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['valid'] else 1)
    rendered=render_asset_svg(manifest)
    if 'error' in rendered:print(json.dumps(rendered,ensure_ascii=False,indent=2),file=sys.stderr);sys.exit(1)
    destination=Path(sys.argv[3]) if len(sys.argv)>3 else Path(sys.argv[2]).with_suffix('.svg')
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(rendered['svg'],encoding='utf-8')
    print(f'SVG 已生成（教学示意，未经实际端子验证）：{destination}')
