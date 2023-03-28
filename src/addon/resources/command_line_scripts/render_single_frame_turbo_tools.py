import bpy, sys, os, platform, subprocess

argv = sys.argv
argv = argv[argv.index("--") + 1:]
frameno = int(argv[0])
open_image_after = False
if argv[1] == "1":
    open_image_after = True

original_output_path = bpy.context.scene.render.filepath
image_path = bpy.context.scene.render.frame_path(frame=frameno)

bpy.context.scene.frame_set(frameno)
bpy.context.scene.render.filepath = image_path
bpy.ops.threedi.render_still(write_still=True)
bpy.context.scene.render.filepath = original_output_path

if open_image_after:
    print("Attempting to open image: <" + image_path + ">")
    system = platform.system()
    if system == "Windows":
        os.startfile(image_path)
    elif system == "Darwin":
        subprocess.call(["open", image_path])
    elif system == "Linux":
        subprocess.call(["xdg-open", image_path])
        pass