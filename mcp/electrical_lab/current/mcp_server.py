"""Tiny local stdio MCP server; Python 3.10+, no third-party dependencies."""
import json
import sys
from electrical_core import COMPONENTS, FAULTS, BASE, validate_wiring, simulate_lamp
from industrial_catalog import list_categories, search_devices, get_device, scaffold_lab, validate_signal_links, validate_hmi_tags
from asset_tools import ASSET_SOURCES, new_asset_spec, validate_asset_spec, plan_render_pipeline, generate_svg_asset, simulate_motion_step

TOOLS = [
    {"name":"list_components", "description":"列出电工实训教学器件及端子；内置传统电感镇流器荧光灯器件库（非厂家零件库）。", "inputSchema":{"type":"object","properties":{},"additionalProperties":False}},
    {"name":"get_fluorescent_lab", "description":"获取传统220V交流单灯、电感镇流器、辉光启辉器接线任务与示例导线（仅虚拟仿真）。", "inputSchema":{"type":"object","properties":{},"additionalProperties":False}},
    {"name":"validate_wiring", "description":"核验虚拟荧光灯接线端子对，包含漏接、多接、直通短路检查；教学级验证，非安全认证。", "inputSchema":{"type":"object","properties":{"wires":{"type":"array","items":{"type":"array","items":{"type":"string"},"minItems":2,"maxItems":2}}},"required":["wires"],"additionalProperties":False}},
    {"name":"simulate_fluorescent", "description":"对已校验接线执行辉光启辉器-灯丝预热-自感启辉-点亮/故障的教学状态机。", "inputSchema":{"type":"object","properties":{"wires":{"type":"array","items":{"type":"array","items":{"type":"string"},"minItems":2,"maxItems":2}},"powered":{"type":"boolean","default":True},"switch_closed":{"type":"boolean","default":True},"fault":{"type":"string","enum":list(FAULTS),"default":"none"}},"required":["wires"],"additionalProperties":False}},
    {"name":"list_faults", "description":"列出支持的教学故障注入类型", "inputSchema":{"type":"object","properties":{},"additionalProperties":False}},

    {"name":"list_device_categories", "description":"列出工业自动化和机器人教学设备分类及条目数量（含占位模型）", "inputSchema":{"type":"object","properties":{},"additionalProperties":False}},
    {"name":"search_industrial_devices", "description":"搜索 46 类工业元件家族，准确区分已模拟/仅收录", "inputSchema":{"type":"object","properties":{"query":{"type":"string"},"category":{"type":"string"},"status":{"type":"string"},"limit":{"type":"integer"}},"additionalProperties":False}},
    {"name":"get_industrial_device", "description":"读取设备家族教学模型、来源及规格核对状态；不是厂家端子表", "inputSchema":{"type":"object","properties":{"device_id":{"type":"string"}},"required":["device_id"],"additionalProperties":False}},
    {"name":"scaffold_industrial_lab", "description":"生成PLC/HMI/机器人/电机/气动等课程开发需求清单，明确只是规格草案", "inputSchema":{"type":"object","properties":{"title":{"type":"string"},"device_ids":{"type":"array","items":{"type":"string"}},"objectives":{"type":"array","items":{"type":"string"}}},"required":["title","device_ids"],"additionalProperties":False}},
    {"name":"validate_signal_links", "description":"依据调用者显式提供的端口声明做抽象方向/类型/电压检查，不用于实际电气接线安全认证", "inputSchema":{"type":"object","properties":{"devices":{"type":"array","items":{"type":"object"}},"links":{"type":"array","items":{"type":"object"}}},"required":["devices","links"],"additionalProperties":False}},
    {"name":"validate_hmi_tags", "description":"检查用户提供的 PLC 与 HMI 变量名称、数据类型一致性；不测试真实 PLC 通讯", "inputSchema":{"type":"object","properties":{"plc_tags":{"type":"array","items":{"type":"object"}},"hmi_tags":{"type":"array","items":{"type":"object"}}},"required":["plc_tags","hmi_tags"],"additionalProperties":False}},

    {"name":"list_asset_sources", "description":"厂家资料、CAD素材参考站及版权注意事项，仅返回网址和用途，不下载商业资源。", "inputSchema":{"type":"object","properties":{},"additionalProperties":False}},
    {"name":"new_asset_spec", "description":"依据用户照片/尺寸/厂家信息生成非标设备待核对JSON规格草案，绝不编造端子或动作参数。", "inputSchema":{"type":"object","properties":{"name":{"type":"string"},"category":{"type":"string"},"manufacturer":{"type":"string"},"model":{"type":"string"},"drawings":{"type":"array","items":{"type":"string"}},"terminals":{"type":"array","items":{"type":"object"}}},"required":["name"],"additionalProperties":False}},
    {"name":"validate_asset_spec", "description":"检查素材清单字段、版权状态、端子唯一性、核验级别和运动数据声明；不代替制造商技术审查。", "inputSchema":{"type":"object","properties":{"spec":{"type":"object"}},"required":["spec"],"additionalProperties":False}},
    {"name":"plan_render_pipeline", "description":"按教学设备/低配机房选择SVG/Canvas/WebGL及CPU-GPU职责与素材压缩策略。", "inputSchema":{"type":"object","properties":{"spec":{"type":"object"},"target":{"type":"string"},"need_3d":{"type":"boolean"}},"required":["spec"],"additionalProperties":False}},
    {"name":"generate_generic_svg", "description":"从用户提供的设备名/端子生成带显著示意标记的原创SVG底稿，不冒充真实厂家设备。", "inputSchema":{"type":"object","properties":{"spec":{"type":"object"}},"required":["spec"],"additionalProperties":False}},
    {"name":"simulate_motion_step", "description":"按给定行程、方向、速度和步长做线性/旋转位置教学计算；非力学动力学计算。", "inputSchema":{"type":"object","properties":{"motion":{"type":"object"},"position":{"type":"number"},"command":{"type":"string"},"dt_ms":{"type":"number"}},"required":["motion","position","command"],"additionalProperties":False}},
]

def execute(name, args):
    if name == "list_asset_sources": return ASSET_SOURCES
    if name == "new_asset_spec": return new_asset_spec(args.get("name",""),args.get("category","custom_machine"),args.get("model",""),args.get("manufacturer",""),args.get("drawings"),args.get("terminals"))
    if name == "validate_asset_spec": return validate_asset_spec(args.get("spec"))
    if name == "plan_render_pipeline": return plan_render_pipeline(args.get("spec"),args.get("target","classroom_low_end"),args.get("need_3d",False))
    if name == "generate_generic_svg": return generate_svg_asset(args.get("spec"))
    if name == "simulate_motion_step": return simulate_motion_step(args.get("motion"),args.get("position"),args.get("command"),args.get("dt_ms",20))
    if name == "list_components": return COMPONENTS
    if name == "get_fluorescent_lab": return {"title":"传统电感镇流器荧光灯安装与检修", "wires":BASE, "equipment":COMPONENTS, "scope":"单灯单启辉器演示拓扑；非电子镇流器", "safety":"虚拟仿真；实际实训必须断电、验电并由教师监督"}
    if name == "validate_wiring": return validate_wiring(args.get("wires"))
    if name == "simulate_fluorescent": return simulate_lamp(args.get("wires"), powered=args.get("powered",True), switch_closed=args.get("switch_closed",True), fault=args.get("fault","none"))
    if name == "list_faults": return FAULTS
    if name == "list_device_categories": return list_categories()
    if name == "search_industrial_devices": return search_devices(args.get("query", ""), args.get("category", ""), args.get("status", ""), args.get("limit", 60))
    if name == "get_industrial_device": return get_device(args.get("device_id", ""))
    if name == "scaffold_industrial_lab": return scaffold_lab(args.get("title", ""), args.get("device_ids"), args.get("objectives"))
    if name == "validate_signal_links": return validate_signal_links(args.get("devices"), args.get("links"))
    if name == "validate_hmi_tags": return validate_hmi_tags(args.get("plc_tags"), args.get("hmi_tags"))
    raise ValueError(f"unknown tool: {name}")

def write(payload):
    sys.stdout.write(json.dumps(payload,ensure_ascii=False,separators=(',',':')) + '\n')
    sys.stdout.flush()

def handle(request):
    method = request.get("method", "")
    ident = request.get("id")
    if ident is None: return None  # notification
    try:
        if method == "initialize":
            params = request.get("params",{})
            version = params.get("protocolVersion", "2025-03-26")
            result = {"protocolVersion":version, "capabilities":{"tools":{"listChanged":False}},"serverInfo":{"name":"electrical-training-lab","version":"3.0.0"}}
        elif method == "ping": result = {}
        elif method == "tools/list": result = {"tools": TOOLS}
        elif method == "tools/call":
            params = request.get("params",{})
            output = execute(params.get("name"),params.get("arguments") or {})
            result = {"content":[{"type":"text","text":json.dumps(output,ensure_ascii=False)}],"isError":False}
        else:
            return {"jsonrpc":"2.0","id":ident,"error":{"code":-32601,"message":"Method not found"}}
        return {"jsonrpc":"2.0","id":ident,"result":result}
    except Exception as ex:
        return {"jsonrpc":"2.0","id":ident,"error":{"code":-32603,"message":str(ex)}}

def main():
    for line in sys.stdin:
        try:
            obj=json.loads(line)
            if isinstance(obj, list):
                out=[x for req in obj if (x:=handle(req)) is not None]
                if out: write(out)
            else:
                out=handle(obj)
                if out is not None: write(out)
        except Exception as ex:
            write({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":f"Parse error: {ex}"}})

if __name__ == "__main__": main()
