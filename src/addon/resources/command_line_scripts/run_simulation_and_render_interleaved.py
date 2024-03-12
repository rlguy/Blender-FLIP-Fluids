import bpy, sys, os, threading, time, subprocess, queue

argv = sys.argv
argv = argv[argv.index("--") + 1:]
num_render_instances_option = int(argv[0])
use_overwrite_option = int(argv[1])

_NUM_RENDER_INSTANCES = num_render_instances_option
_USE_OVERWRITE = bool(use_overwrite_option)
_RENDER_THREADS = []
_IS_SIMULATION_FINISHED = False


def _get_max_bakefile_frame(bakefiles_directory):
        bakefiles = os.listdir(bakefiles_directory)
        max_frameno = -1
        for f in bakefiles:
            base = f.split(".")[0]
            if not base.startswith("finished"):
                # a file named in the form finished######.txt is created
                # to signal that all cache files for the frame have been generated.
                continue

            try:
                frameno = int(base[-6:])
                max_frameno = max(frameno, max_frameno)
            except:
                # In the case that there is a bakefile without a number
                pass
        return max_frameno


def _render_thread(settings, frameno):
    command = [settings["blender_binary_path"], "-b", settings["blend_filepath"], "-f", str(frameno)] 
    subprocess.call(command, shell=False)


def render_loop(settings):
    global _NUM_RENDER_INSTANCES
    global _RENDER_THREADS
    global _IS_SIMULATION_FINISHED

    _RENDER_THREADS = [None] * _NUM_RENDER_INSTANCES

    bakefiles_directory = os.path.join(settings["cache_directory"], "bakefiles")
    baked_frames = []
    render_frame_queue = queue.Queue()

    updates_per_second = 60
    while True:
        if not os.path.isdir(bakefiles_directory):
            continue

        # Update render queue
        max_frameno = _get_max_bakefile_frame(bakefiles_directory)
        if max_frameno < 0:
            continue

        if max_frameno not in baked_frames:
            if baked_frames:
                next_frame = baked_frames[-1] + 1
            else:
                next_frame = settings["frame_start"]

            for i in range(next_frame, max_frameno + 1):
                is_valid_frame = ((i - settings["frame_start"]) % settings["frame_step"]) == 0
                if is_valid_frame:
                    baked_frames.append(i)
                    render_frame_queue.put(i)

        # Launch render worker thread
        if not render_frame_queue.empty():
            available_thread_id = -1
            is_thread_available = False
            for i in range(len(_RENDER_THREADS)):
                if _RENDER_THREADS[i] is None or not _RENDER_THREADS[i].is_alive():
                    available_thread_id = i
                    is_thread_available = True
                    break

            if is_thread_available:
                frameno = -1
                while not render_frame_queue.empty():
                    next_frameno = render_frame_queue.get()
                    image_path = settings["frame_filepaths"][next_frameno]
                    if not settings["use_overwrite"] and os.path.isfile(image_path):
                        print("skipping existing frame \"" + image_path + "\"")
                        continue
                    frameno = next_frameno
                    break

                if frameno != -1:
                    _RENDER_THREADS[available_thread_id] = threading.Thread(target=_render_thread, args=(settings, frameno))
                    _RENDER_THREADS[available_thread_id].start()

        # Check if render finished
        if _IS_SIMULATION_FINISHED:
            last_frameno = baked_frames[-1]
            if last_frameno == settings["frame_end"]:
                is_threads_running = False
                for thread in _RENDER_THREADS:
                    if thread is not None and thread.is_alive():
                        is_threads_running = True
                        break
                if not is_threads_running:
                    return

        time.sleep(1.0/updates_per_second)    


frame_filepaths = []
for frameno in range(0, bpy.context.scene.frame_end + 1):
    frame_filepaths.append(bpy.context.scene.render.frame_path(frame=frameno))

dprops = bpy.context.scene.flip_fluid.get_domain_properties()

settings = {}
settings["cache_directory"] = dprops.cache.get_cache_abspath()
settings["blender_binary_path"] = bpy.app.binary_path
settings["blend_filepath"] = bpy.data.filepath
settings["frame_start"] = bpy.context.scene.frame_start
settings["frame_end"] = bpy.context.scene.frame_end
settings["frame_step"] = bpy.context.scene.frame_step
settings["use_overwrite"] = _USE_OVERWRITE
settings["frame_filepaths"] = frame_filepaths

render_loop_thread = threading.Thread(target=render_loop, args=(settings,))
render_loop_thread.start()

bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()
_IS_SIMULATION_FINISHED = True

render_loop_thread.join()