"""Educational fluorescent-lamp wiring validator. Not a SPICE / electrical safety solver."""
from __future__ import annotations
from itertools import product
from typing import Any

COMPONENTS = {
    "source": {"label": "交流电源（示意）", "terminals": ["L", "N"], "notes": "教学专用虚拟220V交流电源；绝不可依据仿真直接接市电"},
    "switch": {"label": "单极控制开关", "terminals": ["1", "2"], "notes": "断开相线 L，不能替代隔离开关"},
    "ballast": {"label": "电感镇流器（传统荧光灯）", "terminals": ["1", "2"], "notes": "限流；启辉器断开时电流突变形成感应高压。非电子镇流器。"},
    "lamp": {"label": "双灯丝荧光灯管", "terminals": ["A1", "A2", "B1", "B2"], "notes": "灯管两端各有一组灯丝 A1-A2、B1-B2"},
    "starter": {"label": "辉光启辉器", "terminals": ["1", "2"], "notes": "预热期间闭合后断开，正常点亮后保持断开；不是简单延时开关"},
}
FAULTS = {
    "none": "无故障",
    "starter_open": "启辉器不闭合（无法充分预热）",
    "starter_stuck_closed": "启辉器触点粘连（灯丝持续预热，灯管不正常点亮）",
    "ballast_open": "电感镇流器断路",
    "filament_a_open": "灯管 A 端灯丝断路",
    "filament_b_open": "灯管 B 端灯丝断路",
    "worn_lamp": "灯管老化（反复尝试仍无法正常点亮）",
}
# A traditional single-lamp *electromagnetic* ballast + glow-starter topology.
BASE = [
    ["source.L", "switch.1"],
    ["switch.2", "ballast.1"],
    ["ballast.2", "lamp.A1"],
    ["lamp.A2", "starter.1"],
    ["starter.2", "lamp.B2"],
    ["lamp.B1", "source.N"],
]

def _edge(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))

def _variants():
    for flip_switch, flip_ballast, flip_starter, flip_ends, flip_a, flip_b in product((False, True), repeat=6):
        mapping = {}
        for c, v in (("switch", flip_switch), ("ballast", flip_ballast), ("starter", flip_starter)):
            mapping[f"{c}.1"] = f"{c}.{'2' if v else '1'}"
            mapping[f"{c}.2"] = f"{c}.{'1' if v else '2'}"
        for end, pin_flip in (("A", flip_a), ("B", flip_b)):
            other = ("B" if end == "A" else "A") if flip_ends else end
            mapping[f"lamp.{end}1"] = f"lamp.{other}{'2' if pin_flip else '1'}"
            mapping[f"lamp.{end}2"] = f"lamp.{other}{'1' if pin_flip else '2'}"
        yield {_edge(mapping.get(a, a), mapping.get(b, b)) for a, b in BASE}

VARIANTS = tuple(_variants())
VALID_TERMINALS = {f"{name}.{t}" for name, data in COMPONENTS.items() for t in data["terminals"]}

def validate_wiring(wires: Any) -> dict:
    if not isinstance(wires, list):
        return {"valid": False, "status": "invalid_input", "errors": ["wires 必须为端子对列表"], "missing": [], "extra": []}
    edges = []
    errors = []
    for i, wire in enumerate(wires):
        if not isinstance(wire, (list, tuple)) or len(wire) != 2 or not all(isinstance(x, str) for x in wire):
            errors.append(f"第 {i+1} 根导线格式不正确，要求 [\"source.L\", \"switch.1\"]")
            continue
        a, b = wire
        if a not in VALID_TERMINALS or b not in VALID_TERMINALS:
            errors.append(f"第 {i+1} 根导线端子不存在：{a} / {b}")
        elif a == b:
            errors.append(f"第 {i+1} 根导线连接自身")
        else:
            edges.append(_edge(a, b))
    if len(set(edges)) != len(edges):
        errors.append("存在重复导线")
    unique = set(edges)
    # Direct conductor-only line-neutral bridge; this is an especially dangerous mistake.
    graph = {x: set() for x in VALID_TERMINALS}
    for a, b in unique:
        graph[a].add(b)
        graph[b].add(a)
    seen, stack = set(), ["source.L"]
    while stack:
        current = stack.pop()
        if current not in seen:
            seen.add(current)
            stack.extend(graph[current] - seen)
    direct_short = "source.N" in seen
    if direct_short:
        errors.append("危险：导线直接连通电源 L 与 N（不经过元件）")
    if not errors and unique in VARIANTS:
        return {"valid": True, "status": "correct", "errors": [], "missing": [], "extra": [], "score": 100, "note": "符合本教学模块所采用的传统单灯、电感镇流器、辉光启辉器拓扑"}
    best = min(VARIANTS, key=lambda v: (len(v - unique) + len(unique - v), len(v - unique)))
    return {"valid": False, "status": "danger" if direct_short else "incorrect", "errors": errors or ["与教学拓扑不符；可能缺线、错接或多接"], "missing": [list(x) for x in sorted(best - unique)], "extra": [list(x) for x in sorted(unique - best)], "score": max(0, 100 - 12 * len(best - unique) - 16 * len(unique - best) - 30 * len(errors)), "note": "错误提示是教学级检查，不代表真实电路安全认证"}

def simulate_lamp(wires: Any, *, powered: bool = True, switch_closed: bool = True, fault: str = "none") -> dict:
    check = validate_wiring(wires)
    if fault not in FAULTS:
        return {"status": "invalid_input", "error": f"未知故障 {fault}", "faults": FAULTS}
    if not check["valid"]:
        return {"status": "blocked", "lit": False, "wiring": check, "timeline": [], "warning": "接线检查不合格，禁止执行通电动画"}
    if not powered or not switch_closed:
        return {"status": "off", "lit": False, "timeline": [{"t": 0, "state": "off", "message": "电源或开关断开"}]}
    if fault == "ballast_open":
        timeline = [{"t": 0, "state": "off", "message": "镇流器断路，无预热回路"}]
    elif fault in ("filament_a_open", "filament_b_open"):
        timeline = [{"t": 0, "state": "off", "message": "灯丝断路，无法形成完整预热回路"}]
    elif fault == "starter_open":
        timeline = [{"t": 0, "state": "starter_failed", "message": "启辉器不闭合；正常预热/启辉顺序未建立"}]
    elif fault == "starter_stuck_closed":
        timeline = [{"t": 0, "state": "starter_closed", "message": "启辉器触点始终闭合"}, {"t": 0.6, "state": "preheat", "message": "两端灯丝持续预热，但缺少正常断开产生的启辉脉冲"}]
    else:
        timeline = [
            {"t": 0, "state": "starter_glow", "message": "启辉器辉光放电，双金属片受热"},
            {"t": 0.55, "state": "preheat", "message": "启辉器触点闭合，两端灯丝串联预热"},
            {"t": 1.45, "state": "starter_opens", "message": "启辉器触点断开，镇流器自感产生启辉电压峰值"},
            {"t": 1.55, "state": "flash", "message": "灯管尝试击穿，出现瞬态闪光"},
        ]
        if fault == "worn_lamp":
            timeline.extend([{"t": 2.1, "state": "starter_glow", "message": "未稳定点亮，启辉器再次尝试"}, {"t": 2.7, "state": "preheat", "message": "再次预热"}, {"t": 3.2, "state": "flash", "message": "再次闪烁但未维持放电"}, {"t": 3.5, "state": "failed", "message": "演示结束：老化故障，无法稳定点亮"}])
        else:
            timeline.append({"t": 1.85, "state": "lit", "message": "放电建立，镇流器限制工作电流；启辉器保持断开"})
    return {"status": "completed", "lit": fault == "none", "fault": fault, "timeline": timeline, "model": "teaching_state_machine", "note": "所有时间为演示设定，不是产品实测；不计算瞬态电压/电流"}

if __name__ == "__main__":
    import json
    print(json.dumps(simulate_lamp(BASE), ensure_ascii=False, indent=2))
