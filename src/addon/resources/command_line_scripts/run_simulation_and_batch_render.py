import bpy
bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()
retcode = bpy.ops.flip_fluid_operators.helper_cmd_render_to_scriptfile()
if retcode != {'CANCELLED'}:
    bpy.ops.flip_fluid_operators.helper_run_scriptfile()