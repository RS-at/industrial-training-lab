"""Run with blender -b scene.blend --python bpy_snapshot.py -- --out snapshot.json."""
import argparse, json, sys
from pathlib import Path
import bpy


def arguments():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser();p.add_argument('--out', required=True); return p.parse_args(args)


def main():
    opts = arguments()
    scale_mm = float(bpy.context.scene.unit_settings.scale_length)*1000
    items=[]
    for ob in bpy.data.objects:
        if 'terminal_id' not in ob:
            continue
        co = ob.matrix_world.translation
        items.append({'object_name':ob.name, 'terminal_id':str(ob['terminal_id']),
                      'component_id':str(ob.get('component_id','')),
                      'world_mm':[round(float(axis)*scale_mm,4) for axis in co]})
    result={'unit':'mm','scene':bpy.context.scene.name, 'scale_length':bpy.context.scene.unit_settings.scale_length,
            'terminals':items}
    target = Path(opts.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('V3_RESULT '+json.dumps({'path':str(target),'terminal_count':len(items)},ensure_ascii=False))


if __name__=='__main__':main()
