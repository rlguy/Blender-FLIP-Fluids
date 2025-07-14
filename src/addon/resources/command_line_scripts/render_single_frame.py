import bpy, sys, os, platform, subprocess

argv = sys.argv
argv = argv[argv.index("--") + 1:]
frameno = int(argv[0])
open_image_after = False
if argv[1] == "1":
    open_image_after = True

# Video formats not support for single frame render
# Set to a default image format
video_formats = ["FFMPEG", "AVI_RAW", "AVI_JPEG"]
if bpy.context.scene.render.image_settings.file_format in video_formats:
    default_image_format = "PNG"
    bpy.context.scene.render.image_settings.file_format = default_image_format

original_output_path = bpy.context.scene.render.filepath
image_path = bpy.context.scene.render.frame_path(frame=frameno)

bpy.context.scene.frame_set(frameno)
bpy.context.scene.render.filepath = image_path
bpy.ops.render.render(write_still=True)
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