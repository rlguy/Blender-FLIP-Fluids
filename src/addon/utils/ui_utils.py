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

import bpy

def partition_chunks_column3(chunks):
    """
    Partition a list a chunks into three columns in a way that minimizes the 
    maximum height of all columns
    
    chunk = {
                'label': Display label text,
                'size': number of elements in chunk,
                'collection': collection that this chunk is associated with,
                'is_continuation': whether this chunk is a continuation of a 
                                   previous chunk,
                'id': index that this chunk belongs to
            }
    """
    n = len(chunks)
    if n <= 3:
        partitions = [[], [], []]
        for i in range(n):
            partitions[i] = [chunks[i]]
    else:
        current_min = 1e6
        min_candidates = []
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                sum1 = sum(chunks[x]['size'] for x in range(0, i))
                sum2 = sum(chunks[x]['size'] for x in range(i, j))
                sum3 = sum(chunks[x]['size'] for x in range(j, n))
                maxsum = max(sum1, sum2, sum3)
                if maxsum <= current_min:
                    if maxsum < current_min:
                        current_min = maxsum
                        min_candidates = []
                    candidate = {
                        'score': maxsum, 'sums': [sum1, sum2, sum3], 'i': i, 'j': j
                    }
                    min_candidates.append(candidate)
        
        min_range = 1e6
        winner = None
        final_candidates = []
        for m in min_candidates:
            sum_range = max(m['sums']) - min(m['sums'])
            if sum_range <= min_range:
                if sum_range < current_min:
                    min_range = sum_range
                    final_candidates = []
                final_candidates.append(m)

        winner = final_candidates[0]
        for m in final_candidates:
            if (m['sums'][0] <= m['sums'][1]) and (m['sums'][1] <= m['sums'][2]):
                winner = m

        p1 = [chunks[x] for x in range(0, winner['i'])]
        p2 = [chunks[x] for x in range(winner['i'], winner['j'])]
        p3 = [chunks[x] for x in range(winner['j'], n)]
        partitions = [p1, p2, p3]

    merged_partitions = []
    for p in partitions:
        if not p:
            merged_partitions.append([])
            continue

        newp = []
        current_chunk = p[0]
        for i in range(1, len(p)):
            next_chunk = p[i]
            if next_chunk['id'] == current_chunk['id']:
                current_chunk['size'] += next_chunk['size']
            else:
                newp.append(current_chunk)
                current_chunk = next_chunk
        newp.append(current_chunk)
        merged_partitions.append(newp)
    partitions = merged_partitions

    all_chunks = partitions[0] + partitions[1] + partitions[2]
    for i, c in enumerate(all_chunks):
        if c['is_continuation']:
            last_c = all_chunks[i - 1]
            c['range'] = [last_c['range'][1], last_c['range'][1] + c['size']]
        else:
            c['range'] = [0, c['size']]

        del c['size']
        del c['id']

    return partitions


def get_domain_panel_enums_from_paths(property_paths):
    enabled_panels = {
        "simulation": False,
        "render":     False,
        "surface":    False,
        "whitewater": False,
        "world":      False,
        "materials":  False,
        "advanced":   False,
        "debug":      False,
        "stats":      False
    }

    for path in property_paths:
        split = path.split('.')
        enabled_panels[split[1]] = True

    enums = []
    if enabled_panels['simulation']:
        enums.append(('simulation', "Simulation", "FLIP Fluid Simulation", 1))
    if enabled_panels['render']:
        enums.append(('render', "Display", "FLIP Fluid Display Settings", 2))
    if enabled_panels['surface']:
        enums.append(('surface', "Surface", "FLIP Fluid Surface", 3))
    if enabled_panels['whitewater']:
        enums.append(('whitewater', "Whitewater", "FLIP Fluid Whitewater", 4))
    if enabled_panels['world']:
        enums.append(('world', "World", "FLIP Fluid World", 5))
    if enabled_panels['materials']:
        enums.append(('materials', "Materials", "FLIP Fluid Materials", 6))
    if enabled_panels['advanced']:
        enums.append(('advanced', "Advanced", "FLIP Fluid Advanced", 7))
    if enabled_panels['debug']:
        enums.append(('debug', "Debug", "FLIP Fluid Debug", 8))
    if enabled_panels['stats']:
        enums.append(('stats', "Stats", "FLIP Fluid Stats", 9))

    if not enums:
        enums.append(('NONE', "None", "No panel to select", 0))
    return enums

def force_ui_redraw():
    """
    Create an object and then immediately remove it
    This is a hack to force the ui and 3D viewport to redraw
    """
    mesh_data = bpy.data.meshes.new("test_mesh_data")
    mesh_data.from_pydata([], [], [])
    obj = bpy.data.objects.new("test_object", mesh_data)
    bpy.context.scene.objects.link(obj)
    bpy.data.objects.remove(obj, True)
    mesh_data.user_clear()
    bpy.data.meshes.remove(mesh_data)