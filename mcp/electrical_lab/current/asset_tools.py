"""Offline educational asset manifests, license checks, generic SVG and motion previews.
Not a CAD solver, industrial control system or physical-safety validation library.
Python 3.10+, standard library only.
"""
from __future__ import annotations
import html
import json
import math
import re

ASSET_SOURCES = [
    {"name":"Manufacturer documentation","url":"https://support.industry.siemens.com/","purpose":"具体型号数据表、接线、安装和用户手册","licensing":"逐份资料核实复制/再分发权限"},
    {"name":"TraceParts","url":"https://www.traceparts.com/zh","purpose":"厂家发布的CAD外观、装配与尺寸参考","licensing":"CAD 下载条件并不自动授予再分发许可"},
    {"name":"3Dfindit","url":"https://www.3dfindit.com/","purpose":"厂商零件CAD与尺寸","licensing":"检查厂商及平台许可"},
    {"name":"EPLAN Data Portal","url":"https://dataportal.eplan.com/","purpose":"电气零件数据与宏、连接参考","licensing":"需账号/授权；不可未经许可批量采集"},
    {"name":"MISUMI inCAD Library","url":"https://www.misumi.com.cn/asia/incadlibrary/","purpose":"非标机构设计思路与结构参考","licensing":"下载及使用条款需确认"}
]

ALLOWED_PHASES = {"catalog_only", "appearance_draft", "terminal_draft", "logic_prototype", "teaching_verified", "manufacturer_reviewed"}
DRAW_MODES = {"2d_svg", "2_5d_canvas", "3d_webgl"}
SUPPORTED_MOTION = {"linear", "rotary"}
KNOWN_RIGHTS = {"original", "permission_granted", "open_license", "unknown", "restricted"}
SAFE_ID = re.compile(r"^[a-zA-Z0-9_.-]{1,80}$")


def new_asset_spec(name, category="custom_machine", model="", manufacturer="", drawings=None, terminals=None):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("非标/标准元件名称不可为空")
    return {
        "schema_version": "3.0", "asset_id": "custom.pending", "name": name.strip(),
        "category": category, "manufacturer": manufacturer, "model": model,
        "stage": "appearance_draft", "source": {"description":"待补充图片、铭牌及厂商资料", "urls": [], "verified_against_manual": False},
        "rights": {"status":"unknown", "license":"", "reproduction_allowed": False, "notes":"用户自有照片不代表第三方商标或CAD可再分发"},
        "geometry": {"type":"generic_enclosure", "width_mm":None, "height_mm":None, "depth_mm":None, "drawing":"2d_svg", "texture_source":"none", "model_source":"original"},
        "terminals": terminals if isinstance(terminals, list) else [],
        "control": {"io_map":[], "voltage_verified":False, "program_verified":False, "real_device_connection":False},
        "motion": {"type":"none", "axis":"x", "min_position":0, "max_position":0, "max_speed_per_s":0, "units":"mm", "verified":False},
        "evidence": {"photos": drawings if isinstance(drawings, list) else [], "datasheets":[], "wiring_diagrams":[], "videos":[], "measured_dimensions":False},
        "notes": ["仅可用于教学草模；不可据此对实物接线或运行", "请补正/侧/背面照片、铭牌、接线图、动作视频和尺寸"]
    }


def validate_asset_spec(spec):
    errors=[]; warnings=[]
    if not isinstance(spec, dict):return {"ok":False,"errors":["资产数据必须为 JSON object"],"warnings":[]}
    for field in ("asset_id","name","category","stage","geometry","terminals","rights","source","motion","control"):
        if field not in spec: errors.append(f"缺少字段: {field}")
    aid=spec.get("asset_id","")
    if not isinstance(aid,str) or not SAFE_ID.fullmatch(aid):errors.append("asset_id 只能用字母数字 . _ -，且最多80字符")
    if not isinstance(spec.get("name"),str) or not spec["name"].strip(): errors.append("name 不能为空")
    if spec.get("stage") not in ALLOWED_PHASES:errors.append("stage 非法")
    geometry=spec.get("geometry",{})
    if not isinstance(geometry,dict): errors.append("geometry 必须为对象"); geometry={}
    for k in ("width_mm","height_mm","depth_mm"):
        v=geometry.get(k)
        if v is None:warnings.append(f"未测量 {k}，只能生成示意外观")
        elif isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0:errors.append(f"{k} 必须为正数")
    if geometry.get("drawing") not in DRAW_MODES: errors.append("绘制方式需为 2d_svg / 2_5d_canvas / 3d_webgl")
    rights=spec.get("rights",{})
    if not isinstance(rights,dict): rights={}; errors.append("rights 必须为对象")
    if rights.get("status") not in KNOWN_RIGHTS:errors.append("rights.status 非法")
    if rights.get("status") in ("unknown","restricted") or not rights.get("reproduction_allowed"):
        warnings.append("许可不足或不明：不得将第三方CAD、贴图、图片打包再分发")
    terminals=spec.get("terminals",[])
    if not isinstance(terminals,list):errors.append("terminals 必须为列表");terminals=[]
    seen=set()
    for i,t in enumerate(terminals):
        if not isinstance(t,dict):errors.append(f"端子{i}不是对象");continue
        label=t.get("label")
        if not isinstance(label,str) or not label.strip():errors.append(f"端子{i}缺少 label");continue
        if label in seen:errors.append(f"重复端子: {label}")
        seen.add(label)
        if not t.get("reference_verified"): warnings.append(f"端子 {label} 未经资料核对，不得用于实际接线")
    source=spec.get("source",{})
    if not isinstance(source,dict):source={};errors.append("source 必须为对象")
    if spec.get("stage") in ("teaching_verified","manufacturer_reviewed"):
        if not source.get("verified_against_manual"):
            errors.append("标为已验证前，必须有具体型号的厂家手册核对记录")
        if not terminals:
            errors.append("已验证模型必须有核验后的端子定义")
        if any(not t.get("reference_verified") for t in terminals if isinstance(t,dict)):
            errors.append("已验证模型不得含未核对端子")
    ctrl=spec.get("control",{})
    if isinstance(ctrl,dict) and ctrl.get("real_device_connection"):
        errors.append("本教学资产包不允许真实设备写入控制/使能")
    motion=spec.get("motion",{})
    if not isinstance(motion,dict): motion={};errors.append("motion 必须为对象")
    if motion.get("type") not in {"none"}|SUPPORTED_MOTION: errors.append("motion.type 非法")
    if motion.get("type") in SUPPORTED_MOTION:
        for key in ("min_position","max_position","max_speed_per_s"):
            val=motion.get(key)
            if isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(val):errors.append(f"运动 {key} 必须是有限数")
        if all(isinstance(motion.get(k),(int,float)) for k in ("min_position","max_position","max_speed_per_s")):
            if motion["min_position"]>=motion["max_position"]:errors.append("运动上下限无效")
            if motion["max_speed_per_s"]<=0:errors.append("运动速度必须大于零")
        if not motion.get("verified"):warnings.append("行程与速度未经实测，运动仅为演示")
    return {"ok":not errors,"errors":errors,"warnings":list(dict.fromkeys(warnings)),
            "readiness":"teaching_only" if errors or warnings else "metadata_checked_not_safety_certified"}


def plan_render_pipeline(spec, target="classroom_low_end", need_3d=False):
    if not isinstance(spec,dict):raise ValueError("spec 必须是对象")
    complex_category=spec.get("category") in {"robot", "industrial_robot", "robotics", "assembly_cell", "custom_machine"}
    drawing=(spec.get("geometry") or {}).get("drawing","2d_svg")
    mode="3d_webgl" if need_3d or drawing=="3d_webgl" else ("2_5d_canvas" if complex_category and target!="classroom_low_end" else "2d_svg")
    return {"mode":mode,"target":target,
       "cpu_work":"教学控制状态机、PLC 扫描模型、端子网络检查、插补/运动状态计算、基础碰撞",
       "gpu_work":"浏览器2D合成或WebGL三维几何、材质纹理、光照与屏幕显示；2D不要求独显",
       "recommended_timestep_ms":20,"render_fps_goal":30 if target=="classroom_low_end" else 60,
       "resource_policy":"课程按需打包。重复设备使用实例复用；纹理按屏幕尺寸压缩；离线静态文件优先",
       "texture_formats":["webp","png"] if mode!="3d_webgl" else ["webp","ktx2_if_supported"],
       "model_formats":["svg"] if mode=="2d_svg" else (["svg","canvas"] if mode=="2_5d_canvas" else ["glb" ,"gltf"]),
       "truth_boundary":"该建议是资源策略，不是现场GPU性能测量或厂家级物理仿真；真实运动控制须独立通过PLC/驱动器/机器人控制器和安全回路"}


def generate_svg_asset(spec):
    """Generate generic educational illustration only; never masquerades as exact manufacturer model."""
    if not isinstance(spec,dict):raise ValueError("spec 必须是对象")
    title=html.escape(str(spec.get("name") or "未命名设备"))
    subtitle=html.escape(str(spec.get("model") or "非标示意 / 待核对"))
    terminals=spec.get("terminals") or []
    if len(terminals)>24: raise ValueError("示意图最多显示24个端子")
    circles=[]
    for i,p in enumerate(terminals):
        if not isinstance(p,dict):continue
        x=40+(i%8)*45;y=205+(i//8)*33
        label=html.escape(str(p.get("label","?"))[:14])
        circles.append(f'<circle cx="{x}" cy="{y}" r="8" fill="#d0d6db" stroke="#35485c"/><text x="{x}" y="{y+22}" text-anchor="middle" font-size="10" fill="#26384b">{label}</text>')
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="350" viewBox="0 0 640 350" role="img" aria-label="教学用设备外观示意">
<rect width="640" height="350" fill="#e6eef5"/><rect x="22" y="23" width="596" height="303" rx="17" fill="#ffffff" stroke="#455f77" stroke-width="3"/>
<rect x="37" y="38" width="566" height="140" rx="12" fill="#b7c9d9" stroke="#536c83" stroke-width="2"/>
<text x="320" y="88" fill="#203449" font-family="Arial,sans-serif" text-anchor="middle" font-size="24" font-weight="bold">{title}</text>
<text x="320" y="120" fill="#34516a" font-family="Arial,sans-serif" text-anchor="middle" font-size="15">{subtitle}</text>
<text x="320" y="154" fill="#8a2929" text-anchor="middle" font-size="15" font-weight="bold">示意外观 · 未按实物校验</text>
<g font-family="Arial,sans-serif">{''.join(circles)}</g>
<text x="320" y="307" text-anchor="middle" font-size="12" fill="#5c6670">端子仅用于教学草稿 · 不可凭此接线</text></svg>'''
    return {"svg":svg,"status":"illustration_only","warnings":["本函数不生成厂商真实外观、纹理或带物理碰撞的3D模型"]}


def simulate_motion_step(motion, position, command, dt_ms=20):
    """Kinematic preview. No inertia/friction/force/current/trajectory-safety model."""
    if not isinstance(motion,dict) or motion.get("type") not in SUPPORTED_MOTION:
        raise ValueError("只支持 linear/rotary 演示运动")
    lo=float(motion["min_position"]);hi=float(motion["max_position"]);speed=float(motion["max_speed_per_s"])
    dt=float(dt_ms);pos=float(position)
    if not all(map(math.isfinite,(lo,hi,speed,dt,pos))) or lo>=hi or speed<=0 or dt<0 or dt>500:
        raise ValueError("运动数值无效；dt_ms 必须在0~500")
    if command not in ("extend","retract","forward","reverse","stop"):
        raise ValueError("command: extend/retract/forward/reverse/stop")
    direction=1 if command in ("extend","forward") else (-1 if command in ("retract","reverse") else 0)
    result=max(lo,min(hi,pos+direction*speed*dt/1000))
    return {"position":result,"at_min":result<=lo,"at_max":result>=hi,
            "units":motion.get("units","mm"),"model":"kinematic_demo_only", "dt_ms":dt_ms,
            "warning":"不模拟真实力矩、惯量、碰撞安全或实际伺服闭环"}
