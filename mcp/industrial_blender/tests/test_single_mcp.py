"""Offline checks. Do not imply Blender GUI/rendering has been validated."""
import ast,json
from pathlib import Path
from server import core,pipeline

ROOT=Path(__file__).resolve().parents[1]


def test_only_one_mcp_registered():
    config=json.loads((ROOT/'mcp.json').read_text('utf-8'))
    assert list(config['mcpServers'])==['industrial_blender']


def test_one_server_entrypoint_and_tools():
    source=(ROOT/'server/main.py').read_text('utf-8')
    tree=ast.parse(source)
    tools=[]
    for item in tree.body:
        if isinstance(item,ast.FunctionDef) and any(isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=='tool' for d in item.decorator_list):
            tools.append(item.name)
    assert 'blender_connect_terminals' in tools
    assert 'blender_preview' in tools
    assert 'blender_image' in tools
    assert 'blender_benchmark' in tools
    assert len(tools)==len(set(tools))>=18


def test_import_step_requires_conversion():
    r=pipeline.import_asset('unused.blend','real_part.step','output.blend')
    assert r['verdict']=='UNRESOLVED'
    assert 'FreeCAD' in r['reason']


def test_refine_dry_run_does_not_launch_blender(tmp_path,monkeypatch):
    blend=tmp_path/'source.blend';blend.write_bytes(b'BLENDER'+b'0'*130)
    def forbidden(*args,**kwargs):raise AssertionError('Blender should not be called')
    monkeypatch.setattr(pipeline,'run_blender',forbidden)
    r=pipeline.refine(str(blend),[{'op':'bevel_mm','object':'Lamp','width_mm':1}],str(tmp_path/'out'),dry_run=True)
    assert r['verdict']=='UNRESOLVED' and r['dry_run']
    assert not (tmp_path/'out').exists()


def test_wiring_same_source_destination_rejected():
    try:pipeline.connect_terminals('model.blend',[{'from_terminal':'a','to_terminal':'b'}],'model.blend')
    except ValueError as e:assert '禁止覆盖' in str(e)
    else:raise AssertionError('expected ValueError')


def test_blender_allowlist_contains_all_render_tools():
    assert {'bpy_wires.py','bpy_render_views.py','bpy_inspect.py','bpy_import.py'} <= core.RUNTIME


def test_venv_mcp_major_version_pinned():
    pyproject=(ROOT/'pyproject.toml').read_text('utf-8')
    assert 'mcp>=1.15,<2' in pyproject
