"""Three independent evidence renders from a .blend. No save, source unchanged."""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector

def parse():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--outdir',required=True);p.add_argument('--size',type=int,default=720)
    p.add_argument('--engine',choices=['fast','keep'],default='fast');return p.parse_args(argv)

def main():
    opt=parse();out=Path(opt.outdir).resolve();out.mkdir(parents=True,exist_ok=True)
    if opt.size<320 or opt.size>2048:raise ValueError('size out of range')
    scene=bpy.context.scene
    objects=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
    if not objects:raise ValueError('no visible mesh')
    pts=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    lo=Vector([min(v[i] for v in pts) for i in range(3)])
    hi=Vector([max(v[i] for v in pts) for i in range(3)])
    center=(lo+hi)*.5; size=(hi-lo).length; dist=max(.2,size*1.6)
    scene.render.resolution_x=opt.size;scene.render.resolution_y=opt.size;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    if opt.engine=='fast':
        for engine in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
            try:scene.render.engine=engine;break
            except Exception:continue
    world=scene.world
    if world and world.use_nodes:
        node=world.node_tree.nodes.get('Background')
        if node:node.inputs['Strength'].default_value=max(.3,float(node.inputs['Strength'].default_value))
    cam=bpy.data.cameras.new('V3_EvidenceCam');obj=bpy.data.objects.new('V3_EvidenceCam',cam);scene.collection.objects.link(obj)
    cam.type='ORTHO';cam.ortho_scale=max(.1,size*1.25)
    scene.camera=obj
    area=bpy.data.lights.new('V3_EvidenceLight','AREA');light=bpy.data.objects.new('V3_EvidenceLight',area);scene.collection.objects.link(light)
    area.energy=800;area.size=max(1,size);light.location=center+Vector((dist,-dist,dist))
    light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    dirs={'front':Vector((0,-1,.18)), 'side':Vector((1,0,.18)), 'isometric':Vector((1,-1,.9))}
    files={}
    for name,d in dirs.items():
        obj.location=center+d.normalized()*dist
        obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
        filepath=out/(name+'.png');scene.render.filepath=str(filepath)
        bpy.ops.render.render(write_still=True)
        if not filepath.is_file() or filepath.stat().st_size<100:raise ValueError('render missing: '+name)
        files[name]=str(filepath)
    report={'files':files,'resolution':[opt.size,opt.size], 'mesh_count':len(objects), 'scene_bounds_mm':[(hi[i]-lo[i])*scene.unit_settings.scale_length*1000 for i in range(3)],
            'note':'三视图不是视觉质量 PASS；需要 Codex 阅读图像后判断缺陷'}
    (out/'views.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('V3_RESULT '+json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
