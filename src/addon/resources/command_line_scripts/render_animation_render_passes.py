import bpy, sys, os, platform, subprocess, pathlib

_USE_OVERWRITE = False # TODO

def render_script():

    hprops = bpy.context.scene.flip_fluid_helper

    blend_file_directory = os.path.dirname(bpy.data.filepath)
    base_file_name = pathlib.Path(bpy.path.basename(bpy.data.filepath)).stem

    pass_suffixes = [
        ("catchers_only",       hprops.render_passes_catchers_only),
        ("objects_only",        hprops.render_passes_objects_only),
        ("fluidparticles_only", hprops.render_passes_fluidparticles_only),
        ("fluid_only",          hprops.render_passes_fluid_only),
        ("fluid_shadows_only",  hprops.render_passes_fluid_shadows_only),
        ("reflr_only",          hprops.render_passes_reflr_only),
        ("bubblesanddust_only", hprops.render_passes_bubblesanddust_only),
        ("foamandspray_only",   hprops.render_passes_foamandspray_only),
        # ("object_shadows_only", hprops.render_passes_object_shadows_only),  # Disabled for now
    ]

    render_pass_blend_filepaths = []
    enabled_passes = [suffix for suffix, enabled in pass_suffixes if enabled]

    for idx, (render_pass, enabled) in enumerate(pass_suffixes):
        if not enabled:
            continue
        number = enabled_passes.index(render_pass) + 1
        render_pass_blend_filename = f"{number}_{base_file_name}_{render_pass}.blend"
        blend_filepath = os.path.join(blend_file_directory, render_pass_blend_filename)
        if not os.path.isfile(blend_filepath):
            print(f"Warning: {render_pass} is enabled, but the blend file was not found: <{blend_filepath}>. This file will be skipped.")
            continue
        render_pass_blend_filepaths.append(blend_filepath)

    blender_binary_path = bpy.app.binary_path
    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end
    frame_step = bpy.context.scene.frame_step

    render_command_queue = []
    for frameno in range(frame_start, frame_end + 1, frame_step):
        for blend_filepath in render_pass_blend_filepaths:
            command = [blender_binary_path, "-b", blend_filepath, "-f", str(frameno)]
            render_command_queue.append(command)

    for command in render_command_queue:
        print(f"Executing render command: {command}")
        subprocess.call(command, shell=False)
        print(f"Render command completed: {command}")

render_script()

