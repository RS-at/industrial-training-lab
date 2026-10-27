"""Industrial Blender V3.1: one MCP server, internal specialized modules."""
from __future__ import annotations
import json,sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.core import ROOT,blender_exe,dsh_request
from server.pipeline import (inventory,import_asset,render_views,refine,terminal_audit,
                             export,benchmark,connect_terminals)
from server.validators import check_artifacts
from bridge.dsh_gateway import (request as upstream_request, route_call, discover_upstream,
                                GET_ROUTES, POST_ROUTES, DshCallError, watch_frames)

mcp=FastMCP('industrial-blender')

def fail(e):return {'verdict':'FAIL','error':str(e)}

@mcp.tool()
def blender_status() -> dict:
    """唯一 Blender MCP 的就绪检查；无需启动额外 MCP。DSH HTTP 后端可选，非必要。"""
    try:exe=blender_exe();installed=True
    except Exception as e:exe=str(e);installed=False
    try:dsh=json.loads(dsh_request('/health',timeout_s=2));dsh_ok=True
    except Exception:dsh=None;dsh_ok=False
    return {'mcp_server':'industrial-blender','mcp_count':1,'version':'0.4.0',
            'blender_installed':installed,'blender_path':exe,'optional_dsh_backend':dsh_ok, 'upstream_source':discover_upstream(ROOT),
            'capabilities':['scene_inventory','import_glb_gltf_stl_obj_fbx','3_view_render',
                'visual_refinement_loop','terminal_based_wiring','terminals','export_blend_glb_png','web_30fps_benchmark'],
            'note':'一个 MCP 暴露全部 DSH 原始 HTTP 引擎功能和工业建模功能；上游仓库须由安装器克隆并启动本地后端。'}

@mcp.tool()
def blender_inspect(blend_file:str,report_json:str) -> dict:
    """读取本地 BLEND 场景中的真实对象、世界尺寸、材质、三角面、端子；保存可审计 JSON。"""
    try:return inventory(blend_file,report_json)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_import(blend_file:str,asset_file:str,output_blend:str) -> dict:
    """向 BLEND 导入 GLB/GLTF/STL/OBJ/FBX（不覆盖原始工程）。STEP/FCStd 必须先转换并核对单位。"""
    try:return import_asset(blend_file,asset_file,output_blend)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_preview(blend_file:str,output_dir:str,size:int=720) -> dict:
    """从真实 .blend 自动渲染正、侧、斜三张 PNG，AI 必须读取图像分析外形与缺陷。"""
    try:return render_views(blend_file,output_dir,size)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_image(image_path:str) -> Image:
    """将已经渲染的 PNG 真正返回给模型视觉通道，而不是只报告文件路径。"""
    p=Path(image_path).resolve()
    if p.suffix.lower()!='.png' or not p.is_file() or p.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':
        raise ValueError('必须是真实存在的 PNG 图片')
    if p.stat().st_size>12*1024*1024:raise ValueError('PNG 超过 12 MB，先缩小分辨率')
    return Image(path=str(p))

@mcp.tool()
def blender_refine(blend_file:str,patches_json:str,output_dir:str,dry_run:bool=True,size:int=640)->dict:
    """单次纠错闭环：修改前场景审计+三视图，应用白名单 patch，修改后复测+三视图。模型需查看前后图片决定是否再迭代；不冒充自动视觉成功。补丁 op=translate_mm/set_color_rgba/bevel_mm/set_terminal_tags。"""
    try:
        patches=json.loads(patches_json)
        return refine(blend_file,patches,output_dir,size,dry_run)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_connect_terminals(blend_file:str,connections_json:str,output_blend:str)->dict:
    """复用旧版工业 MCP 的导线功能：以已有 terminal_id 为端点画 3D 贝塞尔导线，不凭空猜坐标。JSON 是 [{from_terminal,to_terminal,wire_type,sag_mm,radius_mm}]，wire_type=L/N/PE/DC_PLUS/CTRL；输出新 BLEND。"""
    try:return connect_terminals(blend_file,json.loads(connections_json),output_blend)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_terminal_audit(blend_file:str,reference_spec_json:str,output_dir:str)->dict:
    """读取 Blender 实际 terminal_id/component_id 与毫米坐标、检查数量、重复、归属、偏移及间距；缺少实测基准报 UNRESOLVED。"""
    try:return terminal_audit(blend_file,reference_spec_json,output_dir)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_export(blend_file:str,output_dir:str,render_width:int=960)->dict:
    """在后台 Blender 中生成 model.blend、model.glb 和 preview.png，校验真实文件与哈希。"""
    try:return export(blend_file,output_dir,render_width)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_benchmark(glb_file:str,output_dir:str,chrome_path:str='')->dict:
    """本机 Chrome/Playwright 以硬件 WebGL 加载 GLB，5 秒预热+30 秒实测 FPS/p95；软件渲染与非 NVIDIA 返回 UNRESOLVED。"""
    try:return benchmark(glb_file,output_dir,chrome_path)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_dsh_status() -> dict:
    """检查 DSH 引擎、Blender 桥、可用指令和上游固定版本。需要 doctor 返回 kind=ok。"""
    status={"source":discover_upstream(ROOT)}
    for route in ("/health", "/doctor", "/commands", "/who"):
        try: status[route]=upstream_request(route,timeout=8)
        except Exception as e:status[route]={"unavailable":str(e)}
    return status

@mcp.tool()
def blender_dsh_catalog(query_json:str='{}') -> dict:
    """获取 DSH 建模工具目录、全 186 op 所属 family 与帮助。先查目录，再按需调用 op；不是 186 个 MCP。"""
    try:
        args=json.loads(query_json)
        if not isinstance(args,dict):raise ValueError('query_json 必须为对象')
        return route_call('/plan',{'op':'catalog','args':args},timeout=40)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_dsh_plan(operation:str,args_json:str='{}',timeout_s:int=180) -> dict:
    """DSH 完整建模目录：动态调用 /plan 所有 28 families/186 ops，含 audit/geo/qc/gate/material/motion/deliver 等；不截断白名单。未启用时明确报错。"""
    try:
        args=json.loads(args_json)
        if not isinstance(args,dict):raise ValueError('args_json 必须是 JSON 对象')
        return route_call('/plan',{'op':operation,'args':args},timeout_s)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_dsh_execute_python(code:str,timeout_s:int=120) -> dict:
    """在用户本机可信 Blender 场景中执行 bpy Python（等效 DSH blender_rt_do）。仅用于用户授权的建模任务，任意代码可读写本机文件。"""
    if not code.strip():return fail('不能执行空代码')
    return route_call('/act',{'code':code},timeout_s)

@mcp.tool()
def blender_dsh_commands() -> dict:
    """发现 Blender-side addon 实际可用命令及参数。"""
    try:return upstream_request('/commands',timeout=15)
    except Exception as e:return {'transport':'UNRESOLVED','error':str(e)}

@mcp.tool()
def blender_dsh_command(name:str,params_json:str='{}',timeout_s:int=120) -> dict:
    """完整转发 DSH /cmd → Blender addon 原生命令（例如导出、对象操作），须先调用 blender_dsh_commands。"""
    try:
        params=json.loads(params_json)
        if not isinstance(params,dict):raise ValueError('params 必须为 JSON 对象')
        return route_call('/cmd',{'name':name,'params':params},timeout_s)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_dsh_control(route:str,payload_json:str='{}',timeout_s:int=180) -> dict:
    """访问 DSH 2.5 POST 接口：/loop /perf /opt /headless /worker /job /txn /preset /lease /release /plan /cmd /act 与 /host/selection、/host/selection/consume。长任务用 /job 追踪。"""
    try:
        payload=json.loads(payload_json)
        if not isinstance(payload,dict):raise ValueError('payload_json 必须为 JSON 对象')
        return route_call(route,payload,timeout_s)
    except Exception as e:return fail(e)

@mcp.tool()
def blender_dsh_read(route:str,query_json:str='{}',timeout_s:int=30) -> dict:
    """读 DSH 后端 GET 路由：/health /doctor /status /commands /who /host/*；图像请调用 blender_dsh_view_image。"""
    try:
        q=json.loads(query_json)
        if not isinstance(q,dict):raise ValueError('query_json 必须为对象')
        return {'transport':'OK','route':route,'data':upstream_request(route,query=q,timeout=timeout_s)}
    except Exception as e:return {'transport':'UNRESOLVED','route':route,'error':str(e)}

@mcp.tool()
def blender_dsh_view_image(view_json:str='{}',size:int=800) -> Image:
    """DSH 真实 GUI 视口或任意相机方向截图 → MCP image。view_json={} 用 /frame.png；有 from/look_at 等参数用 /view。"""
    args=json.loads(view_json)
    if not isinstance(args,dict):raise ValueError('view_json 必须为对象')
    if not 120<=size<=1600:raise ValueError('截图大小必须为 120..1600')
    if args.get('source')=='host':
        seq=args.get('seq')
        q={'seq':seq} if seq is not None else {}
        data=upstream_request('/host/view.png',query=q,timeout=120,binary=True)
    elif args:
        data=upstream_request('/view',args,timeout=120,binary=True)
    else:
        data=upstream_request('/frame.png',timeout=45,query={'size':size},binary=True)
    return Image(data=data,format='png')

@mcp.tool()
def blender_dsh_watch(seconds:float=4.0,interval_ms:int=700,size:int=560) -> dict:
    """无需 DSH 宿主 UI，在选定时间窗按间隔采样真实 Blender 视口 PNG，返回样本哈希和变化情况。"""
    try:return watch_frames(seconds,interval_ms,size)
    except Exception as e:return {'transport':'UNRESOLVED','error':str(e)}

if __name__=='__main__':mcp.run(transport='stdio')
