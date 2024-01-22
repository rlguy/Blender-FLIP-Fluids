import bpy, os, json, time

def play_sound(json_audio_filepath, block=False):
    if not (bpy.app.version >= (2, 80, 0)):
        # aud not supported in Blender 2.79 or lower
        return

    try:
    	prefs = bpy.context.preferences.addons["flip_fluids_addon"].preferences
    except:
    	print("FLIP Fluids: Unable to locate addon preferences")
    	return
    if not prefs.enable_bake_alarm:
    	return

    import aud

    with open(json_audio_filepath, 'r', encoding='utf-8') as f:
        json_data = json.loads(f.read())

    audio_length = float(json_data["length"])
    audio_filename = json_data["filename"]
    audio_filepath = os.path.join(os.path.dirname(json_audio_filepath), audio_filename)
    
    device = aud.Device()
    sound = aud.Sound(audio_filepath)
    handle = device.play(sound)

    if block:
        time.sleep(audio_length)
        handle.stop()



bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()
bpy.ops.wm.revert_mainfile()
bpy.ops.render.render(animation=True)

resources_directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
audio_json_filepath = os.path.join(resources_directory, "sounds", "alarm", "sound_data.json")
play_sound(audio_json_filepath, block=True)