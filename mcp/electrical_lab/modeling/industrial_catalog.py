"""Device-family training inventory. No manufacturer-certified pinouts or live controls."""
from __future__ import annotations
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).resolve().parent / "assets" / "industrial_device_catalog.json").read_text(encoding="utf-8"))
DEVICES = {d["id"]: d for d in CATALOG["devices"]}


def list_categories():
    return [{"id": c["id"], "name": c["name"], "count": sum(x["category"] == c["id"] for x in DEVICES.values())} for c in CATALOG["categories"]]


def search_devices(query: str = "", category: str = "", status: str = "", limit: int = 60):
    if not isinstance(query, str) or not isinstance(category, str) or not isinstance(status, str):
        return {"error": "query/category/status 必须为字符串"}
    limit = max(1, min(100, int(limit)))
    needle = query.casefold().strip()
    items = [d for d in DEVICES.values() if (not category or d["category"] == category) and (not status or d["implementation_status"] == status) and (not needle or needle in " ".join(str(d.get(k,"")) for k in ("name", "id", "vendor", "model_examples", "teaching_behaviors")).casefold())]
    return {"count": len(items), "items": [{k:d[k] for k in ("id", "name", "category", "vendor", "implementation_status", "verified_terminal_pinout")} for d in items[:limit]], "truncated":len(items) > limit}


def get_device(device_id: str):
    if device_id not in DEVICES:
        return {"error": "未知设备类别", "device_id": device_id, "hint":"先调用 search_devices 搜索实际条目"}
    return DEVICES[device_id]


def scaffold_lab(title: str, device_ids: list[str], objectives: list[str] | None = None):
    if not isinstance(title,str) or not title.strip() or not isinstance(device_ids,list) or not device_ids:
        return {"error": "title 和非空 device_ids 为必填"}
    ids = list(dict.fromkeys(device_ids))
    unknown = [x for x in ids if x not in DEVICES]
    if unknown: return {"error": "元件库尚未收录部分设备", "unknown": unknown}
    objectives = objectives or ["识别元件和端口", "完成信号映射", "验证时序并模拟故障"]
    return {
        "title":title, "device_ids":ids,
        "objectives":objectives,
        "development_status":"spec_only_not_simulated",
        "evidence_requirements":["明确每个设备厂家与完整型号", "取得对应硬件版本手册和端子图", "核对供电极性、电压与输入输出类型", "选择可验证的动作/通信接口", "建立标准/错误工况和回归测试"],
        "work_plan":["确认场景与教学目标", "提交设备型号与官方数据表", "建立可复用端口和状态模型", "先写验证器单元测试", "实现离线 HTML 元件与交互", "人工验证误接线/故障/联锁", "再考虑和厂家软件、实体控制器对接"],
        "devices":[{ "id":x, "name":DEVICES[x]["name"], "implementation_status":DEVICES[x]["implementation_status"], "pinout_verified":False} for x in ids],
        "safety":"此工具只生成开发规范，不能生成已验证的现场接线图；机器人动作需要独立的安全仿真和现场风险评估。"
    }


def validate_signal_links(devices: list[dict], links: list[dict]):
    """Check abstract logical signal links specified by caller; NOT conductor routing/safety."""
    errors, warnings = [], []
    if not isinstance(devices,list) or not isinstance(links,list):
        return {"valid":False,"errors":["devices 与 links 必须为列表"],"warnings":[],"scope":"abstract_signal_mapping_only"}
    known={}
    for dev in devices:
        if not isinstance(dev,dict) or not isinstance(dev.get("id"),str) or not isinstance(dev.get("ports"),dict):
            errors.append("设备需要 id 字符串与 ports 字典")
        elif dev["id"] in known:
            errors.append("重复设备 id: " + dev["id"])
        else:known[dev["id"]]=dev["ports"]
    receivers={}
    for i,link in enumerate(links,1):
        if not isinstance(link,dict) or any(not isinstance(link.get(k),str) for k in ("from_device","from_port","to_device","to_port")):
            errors.append(f"第{i}条逻辑信号连线字段不完整");continue
        src,sp,dst,dp=(link[k] for k in ("from_device","from_port","to_device","to_port"))
        if src not in known or dst not in known:
            errors.append(f"第{i}条连接涉及未知设备");continue
        a,b=known[src].get(sp),known[dst].get(dp)
        if not isinstance(a,dict) or not isinstance(b,dict):
            errors.append(f"第{i}条连接涉及未知端口");continue
        if a.get('direction') not in ('out','bidirectional') or b.get('direction') not in ('in','bidirectional'):
            errors.append(f"第{i}条连接方向错误：应为输出→输入")
        if a.get('kind') != b.get('kind') or not a.get('kind'):
            errors.append(f"第{i}条信号类型不匹配：{a.get('kind')}→{b.get('kind')}")
        if a.get('voltage') and b.get('voltage') and a['voltage'] != b['voltage']:
            errors.append(f"第{i}条声明电压不匹配：{a['voltage']}→{b['voltage']}")
        if not a.get('voltage') or not b.get('voltage'):
            warnings.append(f"第{i}条连接缺少完整电气额定值，不能判断硬件兼容性")
        to=(dst,dp)
        if to in receivers:
            errors.append(f"输入端口 {dst}.{dp} 被多处驱动（冲突风险）")
        receivers[to]=src+"."+sp
    return {"valid":not errors,"errors":errors,"warnings":warnings,
            "scope":"abstract_signal_mapping_only",
            "safety":"只检查用户显式提供的方向/类型/声明电压，不验证公共端/接地/隔离/漏电/安全等级或实际电缆接法。"}


def validate_hmi_tags(plc_tags: list[dict], hmi_tags: list[dict]):
    errors=[]; warnings=[]
    if not isinstance(plc_tags,list) or not isinstance(hmi_tags,list):return {"valid":False,"errors":["plc_tags 和 hmi_tags 必须为数组"],"warnings":[]}
    p={}; used=set()
    for t in plc_tags:
        if not isinstance(t,dict) or not isinstance(t.get('name'),str) or not isinstance(t.get('type'),str):errors.append('PLC tag 格式错误');continue
        if t['name'] in p:errors.append('重复 PLC tag '+t['name'])
        p[t['name']]=t['type'].lower()
    for t in hmi_tags:
        if not isinstance(t,dict) or not isinstance(t.get('name'),str) or not isinstance(t.get('plc_tag'),str) or not isinstance(t.get('type'),str):errors.append('HMI tag 格式错误');continue
        if t['name'] in used:errors.append('重复 HMI tag '+t['name'])
        used.add(t['name']); ref=t['plc_tag']
        if ref not in p:errors.append(f"{t['name']} 绑定不存在的 PLC tag：{ref}")
        elif p[ref]!=t['type'].lower():errors.append(f"{t['name']} 数据类型不匹配：{t['type']} vs {p[ref]}")
        if 'address' not in t:warnings.append(f"{t['name']} 未提供地址/通讯驱动信息；仅验证符号绑定")
    return {"valid":not errors,"errors":errors,"warnings":warnings,"scope":"symbolic_tag_type_check_only"}
