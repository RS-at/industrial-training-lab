"""Export .blend/.glb/.png via Blender background rendering."""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector


def arguments():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--outdir',required=True);p.add_argument('--resolution',type=int,default=960)
    return p.parse_args(args)


def ensure_camera():
    scene=bpy.context.scene
    if scene.camera is not None:return
    obs=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
    if not obs:raise ValueError('场景中没有可渲染 MESH')
    coords=[o.matrix_world@Vector(corner) for o in obs for corner in o.bound_box]
    mn=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    mx=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    center=(mx+mn)*0.5;extent=max((mx-mn).length,0.2)
    cam=bpy.data.cameras.new('V3_AutoCamera');cam_obj=bpy.data.objects.new('V3_AutoCamera',cam)
    scene.collection.objects.link(cam_obj)
    cam_obj.location=center+Vector((extent*0.9,-extent*1.3,extent*0.85))
    target=center-cam_obj.location;cam_obj.rotation_euler=target.to_track_quat('-Z','Y').to_euler()
    cam.type='ORTHO';cam.ortho_scale=extent*1.5
    scene.camera=cam_obj
    lamp_data=bpy.data.lights.new('V3_KeyArea','AREA');lamp_data.energy=900;lamp_data.shape='DISK';lamp_data.size=extent
    lamp_obj=bpy.data.objects.new('V3_KeyArea',lamp_data);scene.collection.objects.link(lamp_obj)
    lamp_obj.location=center+Vector((extent*0.7,-extent*0.8,extent*1.3))
    lamp_obj.rotation_euler=(center-lamp_obj.location).to_track_quat('-Z','Y').to_euler()


def main():
    opts=arguments(); out=Path(opts.outdir).resolve();out.mkdir(parents=True,exist_ok=True)
    mesh_count=sum(1 for o in bpy.data.objects if o.type=='MESH')
    if mesh_count == 0:raise ValueError('不允许导出空场景')
    ensure_camera()
    scene=bpy.context.scene
    scene.render.resolution_x=opts.resolution;scene.render.resolution_y=round(opts.resolution*9/16)
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    blend=out/'model.blend';glb=out/'model.glb';png=out/'preview.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',export_extras=True, export_cameras=False,export_lights=False)
    scene.render.filepath=str(png)
    bpy.ops.render.render(write_still=True)
    result={'files':{'blend':str(blend),'glb':str(glb),'png':str(png)},'mesh_count':mesh_count,
            'render_engine':scene.render.engine,'render_resolution':[scene.render.resolution_x,scene.render.resolution_y]}
    (out/'export_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('V3_RESULT '+json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
