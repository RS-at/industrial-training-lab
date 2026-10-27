"""Whitelist-only patch operation. Never edit the input .blend in place."""
import argparse, json, math, sys
from pathlib import Path
import bpy


def arguments():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--patches',required=True);p.add_argument('--out',required=True)
    return p.parse_args(args)


def ensure_vec(vals,size):
    if not isinstance(vals,list) or len(vals)!=size or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in vals):
        raise ValueError(f'expected {size} finite numeric values')
    return [float(x) for x in vals]


def apply_one(patch,scale_mm):
    name=patch.get('object');ob=bpy.data.objects.get(name)
    if ob is None: raise ValueError(f'找不到对象 {name}')
    operation=patch.get('op')
    before={'location':list(ob.location),'materials':[m.name for m in (ob.data.materials if hasattr(ob.data,'materials') else [])]}
    if operation=='translate_mm':
        delta=ensure_vec(patch.get('delta_mm'),3)
        from mathutils import Vector
        bpy.context.view_layer.update()
        world = ob.matrix_world.copy()
        world.translation += Vector(delta)/scale_mm
        ob.matrix_world = world
    elif operation=='set_color_rgba':
        vals=ensure_vec(patch.get('rgba'),4)
        if any(not 0<=v<=1 for v in vals): raise ValueError('RGBA each in 0..1')
        if not hasattr(ob.data,'materials'): raise ValueError('对象不可分配材质')
        if len(ob.data.materials)==0:
            mat=bpy.data.materials.new(name=f'{ob.name}_Material'); ob.data.materials.append(mat)
        else:
            mat=ob.data.materials[0].copy();ob.data.materials[0]=mat
        mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        if bsdf: bsdf.inputs['Base Color'].default_value=vals
        mat.diffuse_color=vals
    elif operation=='bevel_mm':
        width=float(patch.get('width_mm',0))
        if ob.type!='MESH' or not math.isfinite(width) or not 0.01<=width<=20:
            raise ValueError('bevel_mm only MESH, width_mm 0.01..20')
        modifier=ob.modifiers.new('V3_Bevel',type='BEVEL')
        modifier.width=width/scale_mm;modifier.segments=3
    elif operation=='set_terminal_tags':
        # Only tag known object, for validation. Does not invent correct positions.
        for field in ('component_id','terminal_id'):
            value=patch.get(field)
            if not isinstance(value,str) or not value or len(value)>100:
                raise ValueError(f'{field} must be non-empty string <=100')
            ob[field]=value
    else:raise ValueError(f'未允许的修改动作: {operation}')
    return {'object':name,'op':operation,'before':before}


def main():
    args=arguments();patches=json.loads(Path(args.patches).read_text(encoding='utf-8'))
    if not isinstance(patches,list) or not 1<=len(patches)<=30: raise ValueError('patches must be 1..30 items')
    scale_mm=float(bpy.context.scene.unit_settings.scale_length)*1000
    if scale_mm<=0: raise ValueError('scene scale_length invalid')
    report=[apply_one(item,scale_mm) for item in patches]
    output=Path(args.out).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    # save_as_mainfile only after all patch validation; source path remains untouched
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    result={'corrected_blend':str(output),'patches':report,'count':len(report)}
    (output.parent/'patch_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('V3_RESULT '+json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
