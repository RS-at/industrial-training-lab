"""Pure validators, safe to test without Blender or MCP runtime."""
from __future__ import annotations
import hashlib
import json
import math
import struct
from pathlib import Path


def validate_terminals(snapshot: dict, spec: dict) -> dict:
    findings, unresolved = [], []
    terminals = snapshot.get("terminals", [])
    components = spec.get("components", [])
    if not components:
        return {"verdict": "UNRESOLVED", "failures": [], "unresolved": ["规格未定义 components"], "checked": 0}
    seen = set()
    for term in terminals:
        key = str(term.get("terminal_id", ""))
        if not key:
            findings.append("存在无 terminal_id 的端子对象")
        if key in seen:
            findings.append(f"重复端子 ID: {key}")
        seen.add(key)
    term_by_id = {str(t.get("terminal_id")): t for t in terminals}
    checked = 0
    expected_ids = set()
    tolerance_default = float(spec.get("max_position_error_mm", 5))
    for component in components:
        cid = str(component["id"])
        rules = component.get("expected_terminals", [])
        if not rules:
            unresolved.append(f"{cid} 未配置 expected_terminals")
        for expected in rules:
            tid = str(expected["id"])
            checked += 1
            if tid in expected_ids:
                findings.append(f"规格自身存在重复 ID: {tid}")
            expected_ids.add(tid)
            got = term_by_id.get(tid)
            if got is None:
                findings.append(f"{cid} 缺少端子 {tid}")
                continue
            if str(got.get("component_id")) != cid:
                findings.append(f"{tid} 组件归属错误: {got.get('component_id')} ≠ {cid}")
            pos = got.get("world_mm")
            if not isinstance(pos, list) or len(pos) != 3 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in pos):
                findings.append(f"{tid} 的 world_mm 非有效三维坐标")
                continue
            ref = expected.get("expected_world_mm")
            if ref is None:
                unresolved.append(f"{tid} 没有实测世界坐标基准，无法判定位置")
                continue
            if not isinstance(ref, list) or len(ref) != 3 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in ref):
                findings.append(f"{tid} 的参考坐标无效")
                continue
            dist = math.dist(pos, ref)
            tolerance = float(expected.get("tolerance_mm", tolerance_default))
            if dist > tolerance:
                findings.append(f"{tid} 位置误差 {dist:.2f}mm 超过 {tolerance:.2f}mm")
    extras = sorted(set(term_by_id).difference(expected_ids))
    if extras:
        findings.append("存在额外/未知端子: " + ", ".join(extras))
    min_spacing = float(spec.get("min_terminal_spacing_mm", 0))
    for index, first in enumerate(terminals):
        for second in terminals[index+1:]:
            if first.get("component_id") != second.get("component_id"):
                continue
            p1, p2 = first.get("world_mm"), second.get("world_mm")
            if not (isinstance(p1, list) and isinstance(p2, list) and len(p1) == len(p2) == 3):
                continue
            try:
                distance = math.dist(p1,p2)
            except (ValueError, TypeError):
                continue
            if distance < min_spacing:
                findings.append(f"同组件端子间距过小: {first.get('terminal_id')} ↔ {second.get('terminal_id')} ({distance:.2f}mm)")
    verdict = "FAIL" if findings else ("UNRESOLVED" if unresolved else "PASS")
    return {"verdict": verdict, "failures": findings, "unresolved": unresolved, "checked": checked,
            "observed": len(terminals), "expected": len(expected_ids)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda:fp.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def inspect_glb(path: Path) -> dict:
    """Structural glTF v2 GLB check. Not a substitute for Khronos glTF Validator."""
    data = path.read_bytes()
    if len(data) < 20: raise ValueError("GLB 文件短于 20 字节")
    magic, version, size = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or size != len(data):
        raise ValueError("GLB 头损坏、版本不是 2、或长度错误")
    chunk_len, chunk_type = struct.unpack_from("<I4s", data, 12)
    if chunk_type != b"JSON" or chunk_len + 20 > len(data):
        raise ValueError("GLB 第一个 chunk 不是完整 JSON")
    doc = json.loads(data[20:20+chunk_len].decode("utf-8").rstrip(" \t\r\n\x00"))
    if doc.get("asset", {}).get("version") != "2.0":
        raise ValueError("GLB 内部 glTF 版本无效")
    meshes = doc.get("meshes", [])
    nodes = doc.get("nodes", [])
    if not meshes: raise ValueError("GLB 没有 mesh 网格")
    if not nodes: raise ValueError("GLB 没有节点")
    return {"mesh_count": len(meshes), "node_count":len(nodes),
            "material_count": len(doc.get("materials", [])),
            "terminal_nodes": [n.get("name") for n in nodes if str(n.get("name","")).startswith("TERM_")]}


def check_artifacts(output_dir: str) -> dict:
    out=Path(output_dir)
    names=["model.blend","model.glb","preview.png"]
    missing=[n for n in names if not (out/n).is_file() or (out/n).stat().st_size < 100]
    files={n:{"bytes":(out/n).stat().st_size,"sha256":sha256(out/n)} for n in names if n not in missing}
    errors=[]
    if not missing:
        try: files["model.glb"].update(inspect_glb(out/"model.glb"))
        except Exception as e: errors.append(f"GLB 无效: {e}")
        if not (out/"preview.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("preview.png 签名无效")
        if not (out/"model.blend").read_bytes().startswith(b"BLENDER"):
            errors.append("model.blend 签名无效")
    return {"verdict":"FAIL" if missing or errors else "PASS", "missing":missing,"errors":errors,"files":files,
            "limitations":["仅文件结构检查；视觉真实性、端子语义与 Khronos glTF 合规性需另行复核"]}
