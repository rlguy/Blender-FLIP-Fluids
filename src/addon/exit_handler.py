import bpy, os, shutil

# These variables are used when running an exit handler where
# access to Blender data may no longer be available
IS_BLEND_FILE_SAVED = False
CACHE_DIRECTORY = ""

def on_exit():
    global IS_BLEND_FILE_SAVED
    global CACHE_DIRECTORY
    if not IS_BLEND_FILE_SAVED:
        if os.path.exists(CACHE_DIRECTORY):
            shutil.rmtree(CACHE_DIRECTORY)


def save_post():
    global IS_BLEND_FILE_SAVED
    IS_BLEND_FILE_SAVED = True


def load_post():
    global IS_BLEND_FILE_SAVED
    base = os.path.basename(bpy.data.filepath)
    save_file = os.path.splitext(base)[0]
    is_unsaved = not base or not save_file
    IS_BLEND_FILE_SAVED = not is_unsaved


def set_cache_directory(dirpath):
    global CACHE_DIRECTORY
    CACHE_DIRECTORY = dirpath