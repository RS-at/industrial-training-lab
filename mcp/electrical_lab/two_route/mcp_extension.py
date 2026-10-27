"""Local extension for electrical_lab. Shared JS model, no network/hardware I/O."""
import json
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
NODE = shutil.which('node')
if not NODE:
    candidate = pathlib.Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    NODE = str(candidate) if candidate.exists() else None
WIRES = {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 2, 'maxItems': 2}}
TOOLS = [
    {'name': 'get_two_route_lab', 'description': '获取二路三段分段照明与独立插座教学回路、端子和标准导线。非双控开关。', 'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
    {'name': 'list_two_route_faults', 'description': '列出二路三段教学模型的6种故障与正常状态。', 'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
    {'name': 'validate_two_route_wiring', 'description': '按端子网络验证二路三段教学接线；检查缺接、错接、重复、L-N与PE混接，覆盖开关各状态。', 'inputSchema': {'type': 'object', 'properties': {'wires': WIRES}, 'required': ['wires'], 'additionalProperties': False}},
    {'name': 'simulate_two_route', 'description': '先校验接线，再执行带毫秒时间戳的QF/S1/S2动作；验证三段、5秒记忆、插座独立和故障。非真实220V瞬态。', 'inputSchema': {'type': 'object', 'properties': {'wires': WIRES, 'events': {'type': 'array', 'maxItems': 10000, 'items': {'type': 'object', 'properties': {'type': {'type': 'string', 'enum': ['qf', 's1', 's2', 'reset']}, 'value': {'type': 'boolean'}, 'time': {'type': 'number', 'minimum': 0}}, 'required': ['type', 'time'], 'additionalProperties': False}}, 'fault': {'type': 'string', 'enum': ['none','el1_open','el2_open','sa_n_open','y1_stuck','s2_open','el1_short']}}, 'required': ['wires','events'], 'additionalProperties': False}}
]

def execute(name, args):
    if not NODE:
        raise RuntimeError('Node.js runtime not found')
    result = subprocess.run([NODE, str(ROOT/'model_cli.js')], input=json.dumps({'name': name, 'arguments': args}, ensure_ascii=False), capture_output=True, text=True, encoding='utf-8', timeout=30, cwd=str(ROOT))
    if not result.stdout.strip():
        raise RuntimeError('Model process failed: '+result.stderr[:300])
    output = json.loads(result.stdout)
    if result.returncode:
        raise ValueError(output.get('error','Invalid model request'))
    return output
