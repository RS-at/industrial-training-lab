"""Tiny local stdio MCP server; Python 3.10+, no third-party dependencies."""
import json
import sys
from electrical_core import COMPONENTS, FAULTS, BASE, validate_wiring, simulate_lamp
from industrial_catalog import list_categories, search_devices, get_device, scaffold_lab, validate_signal_links, validate_hmi_tags
from nonstandard_assets import list_material_sources, intake_checklist, new_asset_template, validate_asset_manifest, render_asset_svg

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
    {"name":"list_material_sources", "description":"列出已整理的工业元件与非标设备素材来源及授权提醒；不自动采集或下载第三方资产", "inputSchema":{"type":"object","properties":{"search":{"type":"string"}},"additionalProperties":False}},
    {"name":"get_asset_intake_checklist", "description":"生成非标设备的照片、铭牌、端子图、尺寸、动作视频及授权建档清单；只返回清单", "inputSchema":{"type":"object","properties":{"category":{"type":"string"},"intended_use":{"type":"string"},"private":{"type":"boolean"}},"additionalProperties":False}},
    {"name":"new_nonstandard_asset", "description":"依据名称和示意尺寸生成空白设备元数据；不会自动识别照片或制造商接线参数", "inputSchema":{"type":"object","properties":{"asset_id":{"type":"string"},"display_name":{"type":"string"},"category":{"type":"string"},"width_mm":{"type":"number"},"height_mm":{"type":"number"}},"required":["asset_id","display_name"],"additionalProperties":False}},
    {"name":"validate_asset_manifest", "description":"检查非标设备档案格式、端子核验标记、授权证据与仿真准备状态；非安全合格认证", "inputSchema":{"type":"object","properties":{"manifest":{"type":"object"}},"required":["manifest"],"additionalProperties":False}},
    {"name":"render_nonstandard_svg", "description":"依据用户明确提供的尺寸和端子草图生成轻量 SVG 示意外形；非照片逆向与 CAD 精确重建", "inputSchema":{"type":"object","properties":{"manifest":{"type":"object"}},"required":["manifest"],"additionalProperties":False}},

]

def execute(name, args):
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
    if name == "list_material_sources": return list_material_sources(args.get("search", ""))
    if name == "get_asset_intake_checklist": return intake_checklist(args.get("category", "nonstandard_machine"), args.get("intended_use", "teaching"), args.get("private", True))
    if name == "new_nonstandard_asset": return new_asset_template(args.get("asset_id"), args.get("display_name"), args.get("category", "nonstandard_machine"), args.get("width_mm", 300), args.get("height_mm", 180))
    if name == "validate_asset_manifest": return validate_asset_manifest(args.get("manifest"))
    if name == "render_nonstandard_svg": return render_asset_svg(args.get("manifest"))
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
