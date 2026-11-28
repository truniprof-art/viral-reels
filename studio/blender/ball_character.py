import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24; sc.cycles.use_denoising=False
sc.render.resolution_x=540; sc.render.resolution_y=960; sc.render.fps=30
def mat(c,r=.4):
    m=bpy.data.materials.new('m'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(*c,1); b.inputs['Roughness'].default_value=r; return m
bpy.ops.mesh.primitive_uv_sphere_add(radius=1,segments=64,ring_count=32); body=bpy.context.object; body.data.materials.append(mat((1,.55,.08))); bpy.ops.object.shade_smooth()
for x in (-.35,.35):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.22,location=(x,-.85,.25)); e=bpy.context.object; e.data.materials.append(mat((1,1,1),.2)); e.parent=body
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.1,location=(x,-1.04,.22)); p=bpy.context.object; p.data.materials.append(mat((0,0,0),.1)); p.parent=body
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,-1)); bpy.context.object.data.materials.append(mat((.08,.09,.15),.8))
# squash-and-stretch bounce
for f,(z,sx,sz) in {1:(2.5,1,1),12:(0,1.3,.7),20:(1.2,.9,1.1),30:(0,1.1,.9)}.items():
    body.location=(0,0,z); body.scale=(sx,sx,sz); body.keyframe_insert('location',frame=f); body.keyframe_insert('scale',frame=f)
bpy.ops.object.light_add(type='AREA',location=(3,-4,6)); L=bpy.context.object; L.data.energy=1500; L.data.size=4
bpy.ops.object.camera_add(location=(0,-7,1.2),rotation=(math.radians(84),0,0)); sc.camera=bpy.context.object
sc.world=bpy.data.worlds.new('w'); sc.world.color=(.05,.05,.1)
sc.frame_start=1; sc.frame_end=30; sc.render.filepath='/tmp/bl/f_'
sc.render.image_settings.file_format='PNG'
