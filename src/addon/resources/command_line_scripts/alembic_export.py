import bpy, os, time, sys


def check_cache_exists():
    cache_directory = dprops.cache.get_cache_abspath()
    bakefiles_directory = os.path.join(cache_directory, "bakefiles")

    file_count = 0
    cache_exists = False
    if os.path.isdir(bakefiles_directory):
        cache_exists = True
        file_count = len(os.listdir(bakefiles_directory))

    if not cache_exists or file_count == 0:
        print("\nError: Simulation cache does not exist. Nothing to export. Exiting.")
        return False
    return True


def initialize_simulation_mesh_selection():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    hprops = bpy.context.scene.flip_fluid_helper

    print("Searching for simulation meshes:")

    bpy.ops.object.select_all(action='DESELECT')
    num_export_meshes = 0
    if hprops.alembic_export_surface:
        print("Searching for fluid surface mesh...", end="")
        bl_surface = dprops.mesh_cache.surface.get_cache_object()
        if bl_surface is not None:
            bl_surface.select_set(True)
            num_export_meshes += 1
            print(" FOUND <" + bl_surface.name + ">")
        else:
            print(" NOT FOUND")
    else:
        dprops.mesh_cache.disable_simulation_mesh_load('SURFACE')
        print("Fluid surface export disabled, skipping...")

    if hprops.alembic_export_fluid_particles:
        print("Searching for fluid particles mesh...", end="")
        bl_fluid_particles = dprops.mesh_cache.particles.get_cache_object()
        if bl_fluid_particles is not None:
            bl_fluid_particles.select_set(True)
            num_export_meshes += 1
            print(" FOUND <" + bl_fluid_particles.name + ">")
        else:
            print(" NOT FOUND")
    else:
        dprops.mesh_cache.disable_simulation_mesh_load('FLUID_PARTICLES')
        print("Fluid particles export disabled, skipping...")

    if hprops.alembic_export_foam:
        print("Searching for whitewater foam mesh...", end="")
        bl_foam = dprops.mesh_cache.foam.get_cache_object()
        if bl_foam is not None:
            bl_foam.select_set(True)
            num_export_meshes += 1
            print(" FOUND <" + bl_foam.name + ">")
        else:
            print(" NOT FOUND")
    else:
        dprops.mesh_cache.disable_simulation_mesh_load('FOAM')
        print("Whitewater foam export disabled, skipping...")

    if hprops.alembic_export_bubble:
        print("Searching for whitewater bubble mesh...", end="")
        bl_bubble = dprops.mesh_cache.bubble.get_cache_object()
        if bl_bubble is not None:
            bl_bubble.select_set(True)
            num_export_meshes += 1
            print(" FOUND <" + bl_bubble.name + ">")
        else:
            print(" NOT FOUND")
    else:
        dprops.mesh_cache.disable_simulation_mesh_load('BUBBLE')
        print("Whitewater bubble export disabled, skipping...")

    if hprops.alembic_export_spray:
        print("Searching for whitewater spray mesh...", end="")
        bl_spray = dprops.mesh_cache.spray.get_cache_object()
        if bl_spray is not None:
            bl_spray.select_set(True)
            num_export_meshes += 1
            print(" FOUND <" + bl_spray.name + ">")
        else:
            print(" NOT FOUND")
    else:
        dprops.mesh_cache.disable_simulation_mesh_load('SPRAY')
        print("Whitewater spray export disabled, skipping...")

    if hprops.alembic_export_dust:
        print("Searching for whitewater dust mesh...", end="")
        bl_dust = dprops.mesh_cache.dust.get_cache_object()
        if bl_dust is not None:
            bl_dust.select_set(True)
            num_export_meshes += 1
            print(" FOUND <" + bl_dust.name + ">")
        else:
            print(" NOT FOUND")
    else:
        dprops.mesh_cache.disable_simulation_mesh_load('DUST')
        print("Whitewater dust export disabled, skipping...")

    dprops.mesh_cache.disable_simulation_mesh_load('OBSTACLE_DEBUG')
    dprops.mesh_cache.disable_simulation_mesh_load('PARTICLE_DEBUG')
    dprops.mesh_cache.disable_simulation_mesh_load('FORCE_FIELD_DEBUG')

    print("Finished searching for simulation meshes.")

    if num_export_meshes == 0:
        print("\nError: Nothing to export. Exiting.")
        return False
    return True


def get_geomety_nodes_motion_blur_scale(bl_object):
    gn_modifier = None
    for mod in bl_object.modifiers:
        if mod.type == 'NODES' and mod.name.startswith("FF_MotionBlur"):
            gn_modifier = mod
            break

    if gn_modifier is not None:
        try:
            # Depending on FLIP Fluids version, the GN set up may not
            # have an Input_4
            return gn_modifier["Input_4"]
        except:
            return 1.0
    return 1.0


def set_geometry_nodes_alembic_velocity_export_motion_blur_scale(bl_object, scale):
    gn_modifier = None
    for mod in bl_object.modifiers:
        if mod.type == 'NODES' and mod.name.startswith("FF_AlembicVelocityExport"):
            gn_modifier = mod
            break

    if gn_modifier is not None:
        try:
            # Depending on FLIP Fluids version, the GN set up may not
            # have an Input_4
            gn_modifier["Input_4"] = scale
            return scale
        except:
            return 1.0
    return 1.0


def initialize_velocity_export_and_attributes():
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    hprops = bpy.context.scene.flip_fluid_helper

    surface_motion_blur_scale = 1.0
    fluid_particles_motion_blur_scale = 1.0
    foam_motion_blur_scale = 1.0
    bubble_motion_blur_scale = 1.0
    spray_motion_blur_scale = 1.0
    dust_motion_blur_scale = 1.0

    bl_surface = dprops.mesh_cache.surface.get_cache_object()
    if bl_surface is not None:
        surface_motion_blur_scale = get_geomety_nodes_motion_blur_scale(bl_surface)
    bl_fluid_particles = dprops.mesh_cache.particles.get_cache_object()
    if bl_fluid_particles is not None:
        fluid_particles_motion_blur_scale = get_geomety_nodes_motion_blur_scale(bl_fluid_particles)
    bl_foam = dprops.mesh_cache.foam.get_cache_object()
    if bl_foam is not None:
        foam_motion_blur_scale = get_geomety_nodes_motion_blur_scale(bl_foam)
    bl_bubble = dprops.mesh_cache.bubble.get_cache_object()
    if bl_bubble is not None:
        bubble_motion_blur_scale = get_geomety_nodes_motion_blur_scale(bl_bubble)
    bl_spray = dprops.mesh_cache.spray.get_cache_object()
    if bl_spray is not None:
        spray_motion_blur_scale = get_geomety_nodes_motion_blur_scale(bl_spray)
    bl_dust = dprops.mesh_cache.dust.get_cache_object()
    if bl_dust is not None:
        dust_motion_blur_scale = get_geomety_nodes_motion_blur_scale(bl_dust)

    print("\nRemoving motion blur render setup:")
    bpy.ops.flip_fluid_operators.helper_remove_motion_blur('INVOKE_DEFAULT', resource_prefix="FF_MotionBlur")
    print("Finished removing motion blur render setup.")

    if hprops.alembic_export_velocity:
        print("\nInitializing Alembic velocity export setup:")
        bpy.ops.flip_fluid_operators.helper_initialize_motion_blur('INVOKE_DEFAULT',  resource_prefix="FF_AlembicVelocityExport")

        bl_surface = dprops.mesh_cache.surface.get_cache_object()
        if bl_surface is not None:
            value = set_geometry_nodes_alembic_velocity_export_motion_blur_scale(bl_surface, surface_motion_blur_scale)
            print("Info: Set fluid surface Alembic velocity scale to " + '{0:.2f}'.format(value))

        bl_fluid_particles = dprops.mesh_cache.particles.get_cache_object()
        if bl_fluid_particles is not None:
            value = set_geometry_nodes_alembic_velocity_export_motion_blur_scale(bl_fluid_particles, fluid_particles_motion_blur_scale)
            print("Info: Set fluid particles Alembic velocity scale to " + '{0:.2f}'.format(value))

        bl_foam = dprops.mesh_cache.foam.get_cache_object()
        if bl_foam is not None:
            value = set_geometry_nodes_alembic_velocity_export_motion_blur_scale(bl_foam, foam_motion_blur_scale)
            print("Info: Set whitewater foam Alembic velocity scale to " + '{0:.2f}'.format(value))
        bl_bubble = dprops.mesh_cache.bubble.get_cache_object()
        if bl_bubble is not None:
            value = set_geometry_nodes_alembic_velocity_export_motion_blur_scale(bl_bubble, bubble_motion_blur_scale)
            print("Info: Set whitewater bubble Alembic velocity scale to " + '{0:.2f}'.format(value))
        bl_spray = dprops.mesh_cache.spray.get_cache_object()
        if bl_spray is not None:
            value = set_geometry_nodes_alembic_velocity_export_motion_blur_scale(bl_spray, spray_motion_blur_scale)
            print("Info: Set whitewater spray Alembic velocity scale to " + '{0:.2f}'.format(value))
        bl_dust = dprops.mesh_cache.dust.get_cache_object()
        if bl_dust is not None:
            value = set_geometry_nodes_alembic_velocity_export_motion_blur_scale(bl_dust, dust_motion_blur_scale)
            print("Info: Set whitewater dust Alembic velocity scale to " + '{0:.2f}'.format(value))
        print("Finished initializing Alembic velocity export setup.")

    print("\nOptimizing attribute loading:")
    if hprops.alembic_export_velocity:
        if not dprops.surface.enable_velocity_vector_attribute:
            dprops.surface.enable_velocity_vector_attribute = True
            print("Enabled fluid surface velocity attribute loading")
        if not dprops.particles.enable_fluid_particle_velocity_vector_attribute:
            dprops.particles.enable_fluid_particle_velocity_vector_attribute = True
            print("Enabled fluid particles velocity attribute loading")
        if not dprops.whitewater.enable_velocity_vector_attribute:
            dprops.whitewater.enable_velocity_vector_attribute = True
            print("Enabled whitewater velocity attribute loading")
    else:
        if dprops.surface.enable_velocity_vector_attribute:
            dprops.surface.enable_velocity_vector_attribute = False
            print("Disabled fluid surface velocity attribute from loading")
        if dprops.particles.enable_fluid_particle_velocity_vector_attribute:
            dprops.particles.enable_fluid_particle_velocity_vector_attribute = False
            print("Disabled fluid particles velocity attribute from loading")
        if dprops.whitewater.enable_velocity_vector_attribute:
            dprops.whitewater.enable_velocity_vector_attribute = False
            print("Disabled fluid whitewater velocity attribute from loading")

    if dprops.surface.enable_speed_attribute:
        dprops.surface.enable_speed_attribute = False
        print("Disabled fluid surface Speed attribute from loading")
    if dprops.surface.enable_vorticity_vector_attribute:
        dprops.surface.enable_vorticity_vector_attribute = False
        print("Disabled fluid surface Vorticity attribute from loading")
    if dprops.surface.enable_viscosity_attribute:
        dprops.surface.enable_viscosity_attribute = False
        print("Disabled fluid surface Viscosity attribute from loading")
    if dprops.surface.enable_color_attribute:
        dprops.surface.enable_color_attribute = False
        print("Disabled fluid surface Color attribute from loading")
    if dprops.surface.enable_age_attribute:
        dprops.surface.enable_age_attribute = False
        print("Disabled fluid surface Age attribute from loading")
    if dprops.surface.enable_lifetime_attribute:
        dprops.surface.enable_lifetime_attribute = False
        print("Disabled fluid surface Lifetime attribute from loading")
    if dprops.surface.enable_whitewater_proximity_attribute:
        dprops.surface.enable_whitewater_proximity_attribute = False
        print("Disabled fluid surface Whitewater Proximity attribute from loading")
    # User may want source ID attribute for geoemtry nodes post processing
    """
    if dprops.surface.enable_source_id_attribute:
        dprops.surface.enable_source_id_attribute = False
        print("Disabled fluid surface Source ID attribute from loading")
    """

    if dprops.particles.enable_fluid_particle_speed_attribute:
        dprops.particles.enable_fluid_particle_speed_attribute = False
        print("Disabled fluid particles Speed attribute from loading")
    if dprops.particles.enable_fluid_particle_vorticity_vector_attribute:
        dprops.particles.enable_fluid_particle_vorticity_vector_attribute = False
        print("Disabled fluid particles Vorticity attribute from loading")
    if dprops.particles.enable_fluid_particle_color_attribute:
        dprops.particles.enable_fluid_particle_color_attribute = False
        print("Disabled fluid particles Color attribute from loading")
    if dprops.particles.enable_fluid_particle_age_attribute:
        dprops.particles.enable_fluid_particle_age_attribute = False
        print("Disabled fluid particles Age attribute from loading")
    if dprops.particles.enable_fluid_particle_lifetime_attribute:
        dprops.particles.enable_fluid_particle_lifetime_attribute = False
        print("Disabled fluid particles Lifetime attribute from loading")
    if dprops.particles.enable_fluid_particle_whitewater_proximity_attribute:
        dprops.particles.enable_fluid_particle_whitewater_proximity_attribute = False
        print("Disabled fluid particles Whitewater Proximity attribute from loading")
    # User may want source ID attribute for geoemtry nodes post processing
    """
    if dprops.particles.enable_fluid_particle_source_id_attribute:
        dprops.particles.enable_fluid_particle_source_id_attribute = False
        print("Disabled fluid particles Source ID attribute from loading")
    """

    if dprops.whitewater.enable_id_attribute:
        dprops.whitewater.enable_id_attribute = False
        print("Disabled whitewater ID attribute from loading")
    if dprops.whitewater.enable_lifetime_attribute:
        dprops.whitewater.enable_lifetime_attribute = False
        print("Disabled whitewater Lifetime attribute from loading")
    print("Finished optimizing attribute loading.")


def get_export_frame_range():
    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end
    hprops = bpy.context.scene.flip_fluid_helper
    if hprops.alembic_frame_range_mode == 'FRAME_RANGE_CUSTOM':
        frame_start = hprops.alembic_frame_range_custom.value_min
        frame_end = hprops.alembic_frame_range_custom.value_max
    return frame_start, frame_end


def check_cache_velocity_data():
    hprops = bpy.context.scene.flip_fluid_helper
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    if not hprops.alembic_export_velocity:
        return

    print("\nSearching for velocity attribute cache data:")

    cache_directory = dprops.cache.get_cache_abspath()
    bakefiles_directory = os.path.join(cache_directory, "bakefiles")

    file_list = []
    if os.path.isdir(bakefiles_directory):
        file_list = os.listdir(bakefiles_directory)

    surface_velocity_filecount         = len([f for f in file_list if f.startswith("velocity")])
    fluid_particles_velocity_filecount = len([f for f in file_list if f.startswith("fluidparticlesvelocity")])
    foam_velocity_filecount            = len([f for f in file_list if f.startswith("velocityfoam")])
    bubble_velocity_filecount          = len([f for f in file_list if f.startswith("velocitybubble")])
    spray_velocity_filecount           = len([f for f in file_list if f.startswith("velocityspray")])
    dust_velocity_filecount            = len([f for f in file_list if f.startswith("velocitydust")])
    surface_velocity_filecount = (surface_velocity_filecount
                                  - foam_velocity_filecount 
                                  - bubble_velocity_filecount 
                                  - spray_velocity_filecount 
                                  - dust_velocity_filecount)

    display_warning = False
    if hprops.alembic_export_surface:
        bl_surface = dprops.mesh_cache.surface.get_cache_object()
        if bl_surface is not None:
            print("Searching for fluid surface velocity data...", end="")
            print(" FOUND " + str(surface_velocity_filecount) + " cache files.")
            if surface_velocity_filecount == 0:
                display_warning = True
    if hprops.alembic_export_fluid_particles:
        bl_fluid_particles = dprops.mesh_cache.particles.get_cache_object()
        if bl_fluid_particles is not None:
            print("Searching for fluid particles velocity data...", end="")
            print(" FOUND " + str(fluid_particles_velocity_filecount) + " cache files.")
            if fluid_particles_velocity_filecount == 0:
                display_warning = True
    if hprops.alembic_export_foam:
        bl_foam = dprops.mesh_cache.foam.get_cache_object()
        if bl_foam is not None:
            print("Searching for whitewater foam velocity data...", end="")
            print(" FOUND " + str(foam_velocity_filecount) + " cache files.")
            if foam_velocity_filecount == 0:
                display_warning = True
    if hprops.alembic_export_bubble:
        bl_bubble = dprops.mesh_cache.bubble.get_cache_object()
        if bl_bubble is not None:
            print("Searching for whitewater bubble velocity data...", end="")
            print(" FOUND " + str(bubble_velocity_filecount) + " cache files.")
            if bubble_velocity_filecount == 0:
                display_warning = True
    if hprops.alembic_export_spray:
        bl_spray = dprops.mesh_cache.spray.get_cache_object()
        if bl_spray is not None:
            print("Searching for whitewater spray velocity data...", end="")
            print(" FOUND " + str(spray_velocity_filecount) + " cache files.")
            if spray_velocity_filecount == 0:
                display_warning = True
    if hprops.alembic_export_dust:
        bl_dust = dprops.mesh_cache.dust.get_cache_object()
        if bl_dust is not None:
            print("Searching for whitewater dust velocity data...", end="")
            print(" FOUND " + str(dust_velocity_filecount) + " cache files.")
            if dust_velocity_filecount == 0:
                display_warning = True

    if display_warning:
        warning_msg = "WARNING: One or more meshes contain no velocity data in the simulation"
        warning_msg += " cache files. Baking the surface, fluid particles, and/or whitewater velocity attribute"
        warning_msg += " is required for exporting velocity data to Alembic."
        print(warning_msg)

    print("Finished searching for velocity attribute cache data.")


def get_alembic_output_filepath():
    hprops = bpy.context.scene.flip_fluid_helper

    script_arguments = None
    if "--" in sys.argv:
        script_arguments = sys.argv[sys.argv.index("--") + 1:]

    # If an argument has been passed in, override the 'alembic_output_filepath' property
    if script_arguments is not None and len(script_arguments) >= 1:
        override_filepath = script_arguments[0]
        hprops.alembic_output_filepath = override_filepath
        print("Overriding Alembic output filepath to script argument at position 0: <" + override_filepath + ">")

    alembic_filepath = hprops.get_alembic_output_abspath()
    if not alembic_filepath.endswith(".abc"):
        if alembic_filepath.endswith("."):
            alembic_filepath += "abc"
        else:
            alembic_filepath += ".abc"

    return alembic_filepath


dprops = bpy.context.scene.flip_fluid.get_domain_properties()
if dprops is None:
    print("\nError: No domain found in Blend file. Hint: Did you remember to save the Blend file before running this operator? Exiting.")
    exit()

hprops = bpy.context.scene.flip_fluid_helper

print("\n*** Preparing Alembic Export ***\n")

retval = check_cache_exists()
if not retval:
    exit()

retval = initialize_simulation_mesh_selection()
if not retval:
    exit()

initialize_velocity_export_and_attributes()
check_cache_velocity_data()

print("\n*** Starting Alembic Export ***\n")

global_scale = hprops.alembic_global_scale
frame_start, frame_end = get_export_frame_range()
alembic_filepath = get_alembic_output_filepath()

print("Exporting Alembic to: <" + alembic_filepath + ">")
print("Frame Range: " + str(frame_start) + " to " + str(frame_end))
print("")

mesh_export_str = ""
bl_surface = dprops.mesh_cache.surface.get_cache_object()
if hprops.alembic_export_surface and bl_surface is not None:
    mesh_export_str += "Surface"
bl_fluid_particles = dprops.mesh_cache.particles.get_cache_object()
if hprops.alembic_export_fluid_particles and bl_fluid_particles is not None:
    mesh_export_str += "/FluidParticles"
bl_foam = dprops.mesh_cache.foam.get_cache_object()
if hprops.alembic_export_foam and bl_foam is not None:
    mesh_export_str += "/Foam"
bl_bubble = dprops.mesh_cache.bubble.get_cache_object()
if hprops.alembic_export_bubble and bl_bubble is not None:
    mesh_export_str += "/Bubble"
bl_spray = dprops.mesh_cache.spray.get_cache_object()
if hprops.alembic_export_spray and bl_spray is not None:
    mesh_export_str += "/Spray"
bl_dust = dprops.mesh_cache.dust.get_cache_object()
if hprops.alembic_export_dust and bl_dust is not None:
    mesh_export_str += "/Dust"


EXPORT_FINISHED = False
FRAME_END = frame_end
TIMESTAMP = time.time()
TOTAL_TIME = 0.0
def frame_change_handler(scene):
    global EXPORT_FINISHED
    global FRAME_END
    global TIMESTAMP
    global TOTAL_TIME
    
    if not EXPORT_FINISHED:
        current_time = time.time()
        elapsed_time = current_time - TIMESTAMP
        TIMESTAMP = current_time
        TOTAL_TIME += elapsed_time
        
        info_msg = "Exported <" + mesh_export_str + ">"
        if hprops.alembic_export_velocity:
            info_msg += " with velocity data"
        info_msg += " for frame " + str(scene.frame_current)
        info_msg += " in " + '{0:.3f}'.format(elapsed_time) + " seconds  (total: " + '{0:.3f}'.format(TOTAL_TIME) + "s)"
        print(info_msg)
        
    if scene.frame_current == FRAME_END:
        EXPORT_FINISHED = True

bpy.app.handlers.frame_change_post.append(frame_change_handler)

bpy.ops.wm.alembic_export(filepath=alembic_filepath, selected=True, start=frame_start, end=frame_end, global_scale=global_scale)