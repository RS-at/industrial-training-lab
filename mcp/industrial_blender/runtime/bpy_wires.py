"""Connect existing terminal markers with realistic cable curves; save a new blend."""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector

def parse():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--connections',required=True);p.add_argument('--out',required=True)
    return p.parse_args(argv)

COLORS={
    'L':(0.75,0.12,0.09,1), 'N':(0.16,0.53,0.87,1), 'PE':(0.15,0.7,0.20,1),
    'DC_PLUS':(0.52,0.21,0.08,1),'CTRL':(0.9,0.49,0.08,1),
}

def terminals():
    found={}
    for obj in bpy.data.objects:
        tid=obj.get('terminal_id')
        if not tid:continue
        if str(tid) in found:raise ValueError('Duplicate terminal_id: '+str(tid))
        found[str(tid)]=obj
    return found

def main():
    opt=parse();data=json.loads(Path(opt.connections).read_text(encoding='utf-8'))
    if not isinstance(data,list) or not 1<=len(data)<=100:raise ValueError('connections length must be 1..100')
    factor=float(bpy.context.scene.unit_settings.scale_length)*1000
    if factor<=0:raise ValueError('invalid scene scale')
    index=terminals();created=[];pairs=set()
    for i,row in enumerate(data):
        start=str(row['from_terminal']);end=str(row['to_terminal'])
        if start==end:raise ValueError('Self loop: '+start)
        if start not in index or end not in index:raise ValueError('Missing real terminal marker: '+start+' / '+end)
        key=tuple(sorted((start,end)))
        if key in pairs:raise ValueError('Duplicated link: '+str(key))
        pairs.add(key)
        start_ob=index[start];end_ob=index[end]
        a=start_ob.matrix_world.translation.copy();b=end_ob.matrix_world.translation.copy()
        if (a-b).length<0.002:raise ValueError('Terminal anchors coincide: '+start+' / '+end)
        sag_mm=float(row.get('sag_mm',70));radius_mm=float(row.get('radius_mm',2))
        if not all(math.isfinite(x) for x in (sag_mm,radius_mm)) or not 0<=sag_mm<=2000 or not .1<=radius_mm<=15:
            raise ValueError('Cable sag/radius invalid')
        color_code=str(row.get('wire_type','CTRL')).upper()
        if color_code not in COLORS:raise ValueError('Unknown wire_type: '+color_code)
        material=bpy.data.materials.new('V3_CableMat_'+color_code);material.diffuse_color=COLORS[color_code]
        material.use_nodes=True
        bsdf=material.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            bsdf.inputs['Base Color'].default_value=COLORS[color_code]
            bsdf.inputs['Roughness'].default_value=.45
            bsdf.inputs['Metallic'].default_value=0
        curve=bpy.data.curves.new('CableGeom_'+str(i),'CURVE');curve.dimensions='3D';curve.resolution_u=20
        curve.bevel_depth=radius_mm/factor;curve.bevel_resolution=4
        spline=curve.splines.new('BEZIER');spline.bezier_points.add(2)
        c=(a+b)*0.5;c.z-=sag_mm/factor
        for bp,point in zip(spline.bezier_points,(a,c,b)):
            bp.co=point;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
        obj=bpy.data.objects.new('Wire_'+start+'__'+end,curve);bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(material);obj['from_terminal']=start;obj['to_terminal']=end
        obj['wire_type']=color_code;obj['radius_mm']=radius_mm
        created.append(obj.name)
    output=Path(opt.out).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print('V3_RESULT '+json.dumps({'output':str(output),'wires':created,'count':len(created)},ensure_ascii=False))
if __name__=='__main__':main()
