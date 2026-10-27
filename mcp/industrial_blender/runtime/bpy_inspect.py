"""Read an existing .blend; write a deterministic scene inventory with true world bounds."""
import argparse, json, sys
from pathlib import Path
import bpy
from mathutils import Vector

def parse():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);return p.parse_args(argv)

def main():
    dest=Path(parse().out).resolve();dest.parent.mkdir(parents=True,exist_ok=True)
    factor=1000*float(bpy.context.scene.unit_settings.scale_length)
    items=[]
    for o in bpy.context.scene.objects:
        entry={'name':o.name,'type':o.type,'visible':not o.hide_get(),
               'materials':[m.name for m in (getattr(o.data,'materials',[]) or []) if m],
               'component_id':str(o.get('component_id','')),'terminal_id':str(o.get('terminal_id',''))}
        if o.type in {'MESH','CURVE','FONT','SURFACE'}:
            points=[o.matrix_world@Vector(p) for p in o.bound_box]
            entry['bounds_mm']=[round(min(p[i] for p in points)*factor,3) for i in range(3)]+[round(max(p[i] for p in points)*factor,3) for i in range(3)]
        if o.type=='MESH':
            entry['vertices']=len(o.data.vertices);entry['triangles']=sum(max(0,len(f.vertices)-2) for f in o.data.polygons)
        items.append(entry)
    doc={'scene':bpy.context.scene.name,'scale_length':bpy.context.scene.unit_settings.scale_length,
         'objects':items,'counts':{'objects':len(items),'meshes':sum(x['type']=='MESH' for x in items),
                                   'terminals':sum(bool(x['terminal_id']) for x in items),
                                   'triangles':sum(x.get('triangles',0) for x in items)}}
    dest.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
    print('V3_RESULT '+json.dumps({'inventory':str(dest),**doc['counts']},ensure_ascii=False))
if __name__=='__main__':main()
