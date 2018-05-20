# Blender FLIP Fluid Add-on
# Copyright (C) 2018 Ryan L. Guy
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy, math


class FlipFluidDomainTypeStatsPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"
    bl_category = "FLIP Fluid"
    bl_label = "FLIP Fluid Stats"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        obj_props = context.scene.objects.active.flip_fluid
        return obj_props.is_active and obj_props.object_type == "TYPE_DOMAIN"


    def format_bytes(self, num):
        # Method adapted from: http://stackoverflow.com/a/10171475
        unit_list = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB']
        decimal_list = [0, 0, 1, 2, 2, 2]

        if num > 1:
            exponent = min(int(math.log(num, 1024)), len(unit_list) - 1)
            quotient = float(num) / 1024**exponent
            unit, num_decimals = unit_list[exponent], decimal_list[exponent]
            format_string = '{:.%sf} {}' % (num_decimals)
            return format_string.format(quotient, unit)
        if num == 0:
            return '0 bytes'
        if num == 1:
            return '1 byte'


    def format_number(self, num):
        return format(num, "6,d").replace(",", " ")


    def format_time(self, t):
        return "{:0.2f}".format(t) + " s"


    def format_long_time(self, t):
        m, s = divmod(t, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)


    def draw_frame_info_simulation_stats(self, context, box):
        sprops = context.scene.objects.active.flip_fluid.domain.stats

        subbox = box.box()
        row = subbox.row()
        row.prop(sprops, "frame_info_simulation_stats_expanded",
            icon="TRIA_DOWN" if sprops.frame_info_simulation_stats_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label("Simulation Stats")

        if sprops.frame_info_simulation_stats_expanded:
            column = subbox.column()
            split = column.split()
            column = split.column()
            column.label("Frame ID:")
            column.label("Timestep:")
            column.label("Substeps:")
            column.label("Fluid Particles:")
            if sprops.display_frame_diffuse_particle_stats:
                column.label("Whitewater Particles:")
                column.label("             Foam:")
                column.label("             Bubble:")
                column.label("             Spray:")

            column = split.column()
            column.label(str(sprops.frame_info_id))
            column.label(self.format_time(sprops.frame_delta_time))
            column.label(str(sprops.frame_substeps))
            column.label(self.format_number(sprops.frame_fluid_particles).lstrip())
            if sprops.display_frame_diffuse_particle_stats:
                column.label(self.format_number(sprops.frame_diffuse_particles).lstrip())
                column.label(self.format_number(sprops.foam_mesh.verts).lstrip())
                column.label(self.format_number(sprops.bubble_mesh.verts).lstrip())
                column.label(self.format_number(sprops.spray_mesh.verts).lstrip())


    def draw_frame_info_timing_stats(self, context, box):
        sprops = context.scene.objects.active.flip_fluid.domain.stats

        subbox = box.box()
        row = subbox.row()
        row.prop(sprops, "frame_info_timing_stats_expanded",
            icon="TRIA_DOWN" if sprops.frame_info_timing_stats_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label("Timing Stats")

        if sprops.frame_info_timing_stats_expanded:
            column = subbox.column()
            split = column.split(percentage = 0.75)
            column = split.column(align = True)
            column.prop(sprops.time_mesh, "pct", slider = True, text = "Mesh Generation")
            column.prop(sprops.time_advection, "pct", slider = True, text = "Velocity Advection")
            column.prop(sprops.time_particles, "pct", slider = True, text = "Fluid Particles")
            column.prop(sprops.time_pressure, "pct", slider = True, text = "Pressure Solver")
            if sprops.display_frame_diffuse_timing_stats:
                column.prop(sprops.time_diffuse, "pct", slider = True, text = "Whitewater Solver")
            if sprops.display_frame_viscosity_timing_stats:
                column.prop(sprops.time_viscosity, "pct", slider = True, text = "Viscosity Solver")
            column.prop(sprops.time_objects, "pct", slider = True, text = "Simulation Objects")
            column.prop(sprops.time_other, "pct", slider = True, text = "Other")

            column = split.column(align = True)
            padstr = " "
            column.label(padstr + self.format_time(sprops.time_mesh.time))
            column.label(padstr + self.format_time(sprops.time_advection.time))
            column.label(padstr + self.format_time(sprops.time_particles.time))
            column.label(padstr + self.format_time(sprops.time_pressure.time))
            if sprops.display_frame_diffuse_timing_stats:
                column.label(padstr + self.format_time(sprops.time_diffuse.time))
            if sprops.display_frame_viscosity_timing_stats:
                column.label(padstr + self.format_time(sprops.time_viscosity.time))
            column.label(padstr + self.format_time(sprops.time_objects.time))
            column.label(padstr + self.format_time(sprops.time_other.time))

            total_time = (sprops.time_mesh.time + sprops.time_advection.time +
                          sprops.time_particles.time + sprops.time_pressure.time +
                          sprops.time_diffuse.time + sprops.time_viscosity.time +
                          sprops.time_objects.time + sprops.time_other.time)

            column = subbox.column()
            split = column.split()
            column = split.column()
            column = split.column()
            split = column.split()
            column = split.column()
            column.label("      Total:")
            column = split.column()
            column.label(self.format_time(total_time))


    def draw_frame_info_mesh_stats(self, context, box):
        sprops = context.scene.objects.active.flip_fluid.domain.stats

        subbox = box.box()
        row = subbox.row()
        row.prop(sprops, "frame_info_mesh_stats_expanded",
            icon="TRIA_DOWN" if sprops.frame_info_mesh_stats_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label("Mesh Stats")

        if sprops.frame_info_mesh_stats_expanded:
            column = subbox.column()
            split = column.split()
            column1 = split.column()
            column2 = split.column()
            column3 = split.column()
            column4 = split.column()

            column1.label("")
            column2.label("Verts")
            column3.label("Faces")
            column4.label("Size")

            total_bytes = 0
            if sprops.surface_mesh.enabled:
                column1.label("Surface")
                column2.label(self.format_number(sprops.surface_mesh.verts))
                column3.label(self.format_number(sprops.surface_mesh.faces))
                column4.label(self.format_bytes(sprops.surface_mesh.bytes.get()))
                total_bytes += sprops.surface_mesh.bytes.get()

            if sprops.preview_mesh.enabled:
                column1.label("Preview")
                column2.label(self.format_number(sprops.preview_mesh.verts))
                column3.label(self.format_number(sprops.preview_mesh.faces))
                column4.label(self.format_bytes(sprops.preview_mesh.bytes.get()))
                total_bytes += sprops.preview_mesh.bytes.get()

            if sprops.foam_mesh.enabled:
                column1.label("Foam")
                column2.label(self.format_number(sprops.foam_mesh.verts))
                column3.label("")
                column4.label(self.format_bytes(sprops.foam_mesh.bytes.get()))
                total_bytes += sprops.foam_mesh.bytes.get()

            if sprops.bubble_mesh.enabled:
                column1.label("Bubble")
                column2.label(self.format_number(sprops.bubble_mesh.verts))
                column3.label("")
                column4.label(self.format_bytes(sprops.bubble_mesh.bytes.get()))
                total_bytes += sprops.bubble_mesh.bytes.get()

            if sprops.spray_mesh.enabled:
                column1.label("Spray")
                column2.label(self.format_number(sprops.spray_mesh.verts))
                column3.label("")
                column4.label(self.format_bytes(sprops.spray_mesh.bytes.get()))
                total_bytes += sprops.spray_mesh.bytes.get()

            if sprops.particle_mesh.enabled:
                column1.label("Particles")
                column2.label(self.format_number(sprops.particle_mesh.verts))
                column3.label("")
                column4.label(self.format_bytes(sprops.particle_mesh.bytes.get()))
                total_bytes += sprops.particle_mesh.bytes.get()

            if sprops.obstacle_mesh.enabled:
                column1.label("Obstacle")
                column2.label(self.format_number(sprops.obstacle_mesh.verts))
                column3.label(self.format_number(sprops.obstacle_mesh.faces))
                column4.label(self.format_bytes(sprops.obstacle_mesh.bytes.get()))
                total_bytes += sprops.obstacle_mesh.bytes.get()

            column3.label("     Total:")
            column4.label(self.format_bytes(total_bytes))


    def draw_frame_info(self, context, box):
        sprops = context.scene.objects.active.flip_fluid.domain.stats

        column = box.column()
        split = column.split()
        column = split.column()
        column.enabled = not sprops.lock_info_frame_to_timeline
        column.prop(sprops, "current_info_frame")
        column = split.column()
        column.prop(sprops, "lock_info_frame_to_timeline")

        box.separator()
        if not sprops.is_frame_info_available:
            box.label("Data Not Available")
            return

        self.draw_frame_info_simulation_stats(context, box)
        self.draw_frame_info_timing_stats(context, box)
        self.draw_frame_info_mesh_stats(context, box)


    def draw_cache_info_simulation_stats(self, context, box):
        dprops = context.scene.objects.active.flip_fluid.domain
        sprops = dprops.stats

        subbox = box.box()
        row = subbox.row()
        row.prop(sprops, "cache_info_simulation_stats_expanded",
            icon="TRIA_DOWN" if sprops.cache_info_simulation_stats_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label("Simulation Stats")

        if sprops.cache_info_simulation_stats_expanded:
            num_frames = dprops.simulation.frame_end - dprops.simulation.frame_start + 1
            num_baked_frames = sprops.num_cache_frames

            column = subbox.column()
            split = column.split()
            column = split.column()
            column.label("Completed Frames:")

            column = split.column()
            if num_baked_frames > num_frames:
                column.label(str(num_baked_frames))
            else:
                column.label(str(num_baked_frames) + "  /  " + str(num_frames))

            if dprops.bake.is_simulation_running:
                column = subbox.column()
                split = column.split()
                column = split.column()

                if sprops.is_estimated_time_remaining_available:
                    column.label("Estimated Time Remaining:")
                else:
                    column.label("Calculating time remaining...")
                
                column = split.column()
                column.label(sprops.get_time_remaining_string(context))

            

    def draw_cache_info_timing_stats(self, context, box):
        sprops = context.scene.objects.active.flip_fluid.domain.stats

        subbox = box.box()
        row = subbox.row()
        row.prop(sprops, "cache_info_timing_stats_expanded",
            icon="TRIA_DOWN" if sprops.cache_info_timing_stats_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label("Timing Stats")

        if sprops.cache_info_timing_stats_expanded:
            column = subbox.column()
            split = column.split(percentage=0.75)
            column = split.column(align=True)
            column.prop(sprops.time_mesh, "pct", slider=True, text="Mesh Generation")
            column.prop(sprops.time_advection, "pct", slider=True, text="Velocity Advection")
            column.prop(sprops.time_particles, "pct", slider=True, text="Fluid Particles")
            column.prop(sprops.time_pressure, "pct", slider=True, text="Pressure Solver")
            if sprops.display_frame_diffuse_timing_stats:
                column.prop(sprops.time_diffuse, "pct", slider = True, text = "Whitewater Solver")
            if sprops.display_frame_viscosity_timing_stats:
                column.prop(sprops.time_viscosity, "pct", slider = True, text = "Viscosity Solver")
            column.prop(sprops.time_objects, "pct", slider = True, text = "Simulation Objects")
            column.prop(sprops.time_other, "pct", slider = True, text = "Other")

            column = split.column(align=True)
            padstr = " "
            column.label(padstr + self.format_long_time(sprops.time_mesh.time))
            column.label(padstr + self.format_long_time(sprops.time_advection.time))
            column.label(padstr + self.format_long_time(sprops.time_particles.time))
            column.label(padstr + self.format_long_time(sprops.time_pressure.time))
            if sprops.display_frame_diffuse_timing_stats:
                column.label(padstr + self.format_long_time(sprops.time_diffuse.time))
            if sprops.display_frame_viscosity_timing_stats:
                column.label(padstr + self.format_long_time(sprops.time_viscosity.time))
            column.label(padstr + self.format_long_time(sprops.time_objects.time))
            column.label(padstr + self.format_long_time(sprops.time_other.time))

            total_time = (sprops.time_mesh.time + sprops.time_advection.time +
                          sprops.time_particles.time + sprops.time_pressure.time +
                          sprops.time_diffuse.time + sprops.time_viscosity.time +
                          sprops.time_objects.time + sprops.time_other.time)

            column = subbox.column()
            split = column.split()
            column = split.column()
            column = split.column()
            split = column.split()
            column = split.column()
            column.label("      Total:")
            column = split.column()
            column.label(self.format_long_time(total_time))


    def draw_cache_info_mesh_stats(self, context, box):
        sprops = context.scene.objects.active.flip_fluid.domain.stats

        subbox = box.box()
        row = subbox.row()
        row.prop(sprops, "cache_info_mesh_stats_expanded",
            icon="TRIA_DOWN" if sprops.cache_info_mesh_stats_expanded else "TRIA_RIGHT",
            icon_only=True, 
            emboss=False
        )
        row.label("Mesh Stats")

        if sprops.cache_info_mesh_stats_expanded:
            column = subbox.column()
            split = column.split(percentage=0.25)
            column1 = split.column()
            column2 = split.column()

            stats_exist = (sprops.surface_mesh.enabled or 
                           sprops.preview_mesh.enabled or 
                           sprops.foam_mesh.enabled or 
                           sprops.bubble_mesh.enabled or 
                           sprops.spray_mesh.enabled or 
                           sprops.particle_mesh.enabled or
                           sprops.obstacle_mesh.enabled)

            if stats_exist:
                column1.label("")
                column2.label("Size")

            total_size = 0
            row_count = 0
            if sprops.surface_mesh.enabled:
                column1.label("Surface")
                column2.label(self.format_bytes(sprops.surface_mesh.bytes.get()))
                row_count += 1
                total_size += sprops.surface_mesh.bytes.get()

            if sprops.preview_mesh.enabled:
                column1.label("Preview")
                column2.label(self.format_bytes(sprops.preview_mesh.bytes.get()))
                row_count += 1
                total_size += sprops.preview_mesh.bytes.get()

            if sprops.foam_mesh.enabled:
                column1.label("Foam")
                column2.label(self.format_bytes(sprops.foam_mesh.bytes.get()))
                row_count += 1
                total_size += sprops.foam_mesh.bytes.get()

            if sprops.bubble_mesh.enabled:
                column1.label("Bubble")
                column2.label(self.format_bytes(sprops.bubble_mesh.bytes.get()))
                row_count += 1
                total_size += sprops.bubble_mesh.bytes.get()

            if sprops.spray_mesh.enabled:
                column1.label("Spray")
                column2.label(self.format_bytes(sprops.spray_mesh.bytes.get()))
                row_count += 1
                total_size += sprops.spray_mesh.bytes.get()

            if sprops.particle_mesh.enabled:
                column1.label("Particles")
                column2.label(self.format_bytes(sprops.particle_mesh.bytes.get()))
                row_count += 1
                total_size += sprops.particle_mesh.bytes.get()

            if sprops.obstacle_mesh.enabled:
                column1.label("Obstacle")
                column2.label(self.format_bytes(sprops.obstacle_mesh.bytes.get()))
                row_count += 1
                total_size += sprops.obstacle_mesh.bytes.get()

            if stats_exist:
                column = subbox.column()
                split = column.split()
                column1 = split.column()
                column2 = split.column()
                row = column2.row()
                row.label("Total:    " + self.format_bytes(total_size))


    def draw_cache_info(self, context, box):
        sprops = context.scene.objects.active.flip_fluid.domain.stats

        box.separator()
        if not sprops.is_cache_info_available:
            box.label("Data Not Available")
            return

        self.draw_cache_info_simulation_stats(context, box)
        self.draw_cache_info_timing_stats(context, box)
        self.draw_cache_info_mesh_stats(context, box)

    def draw(self, context):
        sprops = context.scene.objects.active.flip_fluid.domain.stats

        row = self.layout.row()
        row.prop(sprops, "cache_info_type", expand=True)

        column = self.layout.column()
        if sprops.cache_info_type == "CACHE_INFO":
            self.draw_cache_info(context, column)
        elif sprops.cache_info_type == "FRAME_INFO":
            self.draw_frame_info(context, column)

        self.layout.separator()
        column = self.layout.column(align=True)
        split = column.split(align=True, percentage=0.33)
        column = split.column(align=True)
        column.enabled = sprops.is_cache_info_available
        column.operator("flip_fluid_operators.export_stats_csv", 
                        text="Export to CSV", 
                        icon='FILE')

        column = split.column(align=True)
        split = column.split(align=True, percentage=0.66)
        column = split.column(align=True)
        column.prop(sprops, "csv_save_filepath")

        column = split.column(align=True)
        row = column.row(align=True)
        row.prop(sprops, "csv_region_format", expand=True)

        self.layout.separator()
        self.layout.separator()
        self.layout.separator()
        
    
def register():
    bpy.utils.register_class(FlipFluidDomainTypeStatsPanel)


def unregister():
    bpy.utils.unregister_class(FlipFluidDomainTypeStatsPanel)
