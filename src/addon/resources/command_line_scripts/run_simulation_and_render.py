import bpy
bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()
bpy.ops.render.render(animation=True)