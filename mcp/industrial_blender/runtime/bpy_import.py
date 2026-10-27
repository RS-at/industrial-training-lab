"""Import mesh assets into a saved .blend without replacing source or changing unit scale."""
import argparse,json,sys
from pathlib import Path
import bpy

def parse():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--asset',required=True);p.add_argument('--out',required=True);return p.parse_args(argv)

def main():
    opt=parse();asset=Path(opt.asset).resolve();output=Path(opt.out).resolve()
    if not asset.is_file():raise ValueError('asset not found')
    if asset.suffix.lower() in ('.step','.stp','.fcstd'):
        raise ValueError('STEP/FCStd 需要先用 FreeCAD 转为 GLB/STL；Blender bpy 不原生支持 STEP')
    before={o.name for o in bpy.data.objects}
    ext=asset.suffix.lower()
    if ext in {'.glb','.gltf'}:bpy.ops.import_scene.gltf(filepath=str(asset))
    elif ext=='.fbx':bpy.ops.import_scene.fbx(filepath=str(asset))
    elif ext=='.obj':bpy.ops.wm.obj_import(filepath=str(asset))
    elif ext=='.stl':
        if hasattr(bpy.ops.wm,'stl_import'):bpy.ops.wm.stl_import(filepath=str(asset))
        else: bpy.ops.import_mesh.stl(filepath=str(asset))
    else:raise ValueError('unsupported asset format: '+ext)
    imported=[o.name for o in bpy.data.objects if o.name not in before]
    if not imported:raise ValueError('import operation created no objects')
    output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    result={'source':str(asset),'output':str(output),'imported_names':imported,'scene_scale_length':bpy.context.scene.unit_settings.scale_length,
            'warning':'源文件若采用 mm 而 Blender 按 m 解释，需根据实际尺寸核对后修正；不会自动臆测单位。'}
    print('V3_RESULT '+json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
