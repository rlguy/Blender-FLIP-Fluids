# Blender FLIP Fluids Add-on
# Copyright (C) 2024 Ryan L. Guy
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
from mathutils import Vector, Matrix, Quaternion, Euler, Color
from . import version_compatibility_utils as vcu


def flip_fluid_object_to_dict(obj, object_properties):
    object_properties.refresh_property_registry()

    d = {}
    for p in object_properties.property_registry.properties:
        path_elements = p.path.split('.')
        identifier = path_elements[-1]
        path_elements.pop(0)
        path_elements.pop()

        group = object_properties
        dict_group = d
        for subgroup in path_elements:
            if subgroup not in dict_group.keys():
                dict_group[subgroup] = {}
            group = getattr(group, subgroup)
            dict_group = dict_group[subgroup]

        item = getattr(group, identifier)
        dict_group[identifier] = item

        if (isinstance(item, Vector) or isinstance(item, Color) or 
                (hasattr(item, "__iter__") and not isinstance(item, str))):
            dict_group[identifier] = get_vector_property_data_dict(obj, group, identifier, len(item))
        elif hasattr(item, "is_min_max_property"):
            dict_group[identifier] = get_min_max_property_data_dict(obj, group, identifier)
        else:
            full_path = "flip_fluid." + p.path
            dict_group[identifier] = get_property_data_dict_from_path(obj, group, full_path)

    return d


def is_property_animated(obj, prop_name, index=0, use_exact_path=False):
    anim_data = obj.animation_data
    if not anim_data or not anim_data.action or not anim_data.action.fcurves:
        return False

    for fcurve in anim_data.action.fcurves:
        path = fcurve.data_path
        is_match = path.endswith(prop_name)
        if use_exact_path:
            is_match = path == prop_name
        if is_match and fcurve.array_index == index:
            return True
    return False


def is_property_path_animated(obj, path_name, index = 0):
    anim_data = obj.animation_data
    if not anim_data or not anim_data.action or not anim_data.action.fcurves:
        return False

    for fcurve in anim_data.action.fcurves:
        if fcurve.data_path == path_name and fcurve.array_index == index:
            return True
    return False


def is_vector_animated(obj, prop_name, vector_size = 3):
    is_animated = False
    for i in range(vector_size):
        is_animated = is_animated or is_property_animated(obj, prop_name, i)
    return is_animated


def get_property_fcurve(obj, prop_name, index=0, use_exact_path=False):
    anim_data = obj.animation_data
    for fcurve in anim_data.action.fcurves:
        path = fcurve.data_path

        is_match = path.endswith(prop_name)
        if use_exact_path:
            is_match = path == prop_name
        if is_match and fcurve.array_index == index:
            return fcurve


def get_property_fcurve_from_path(obj, path_name, index = 0):
    anim_data = obj.animation_data
    for fcurve in anim_data.action.fcurves:
        if fcurve.data_path == path_name and fcurve.array_index == index:
            return fcurve


def get_property_data_dict(obj, prop_group, prop_name, index=None, use_exact_path=False):
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()

    is_index_set = index != None
    if not is_index_set:
        index = 0

    if is_property_animated(obj, prop_name, index, use_exact_path=use_exact_path):
        values = []
        fcurve = get_property_fcurve(obj, prop_name, index, use_exact_path=use_exact_path)
        frame_start, frame_end = dprops.simulation.get_frame_range()
        for i in range(frame_start, frame_end + 1):
            values.append(fcurve.evaluate(i))

        is_values_constant = True
        for i in range(len(values)):
            if values[i] != values[0]:
                is_values_constant = False
                break

        if is_values_constant:
            return {'is_animated' : False, 'data' : values[0]}
        else:
            return {'is_animated' : True, 'data' : values}
    else:
        prop_name_suffix = prop_name.split(".")[-1]
        value = getattr(prop_group, prop_name_suffix)
        if is_index_set:
            value = value[index]
        return {'is_animated' : False, 'data' : value}


def get_property_data_dict_from_path(obj, prop_group, path_name, index = None):
    dprops = bpy.context.scene.flip_fluid.get_domain_properties()
    
    is_index_set = index != None
    if not is_index_set:
        index = 0

    if is_property_path_animated(obj, path_name, index):
        values = []
        fcurve = get_property_fcurve_from_path(obj, path_name, index)
        frame_start, frame_end = dprops.simulation.get_frame_range()
        for i in range(frame_start, frame_end + 1):
            values.append(fcurve.evaluate(i))

        is_values_constant = True
        for i in range(len(values)):
            if values[i] != values[0]:
                is_values_constant = False
                break

        if is_values_constant:
            return {'is_animated' : False, 'data' : values[0]}
        else:
            return {'is_animated' : True, 'data' : values}
    else:
        prop_name = path_name.split(".")[-1]
        value = getattr(prop_group, prop_name)
        if is_index_set:
            value = value[index]
        return {'is_animated' : False, 'data' : value}


def get_vector_property_data_dict(obj, prop_group, prop_name, vector_size=3, use_exact_path=False):
    component_dicts = []
    for i in range(vector_size):
        component_dicts.append(get_property_data_dict(obj, 
                                                      prop_group, 
                                                      prop_name, i, use_exact_path=use_exact_path))
    is_animated = False
    for i in range(vector_size):
        is_animated = is_animated or component_dicts[i]['is_animated']

    if is_animated:
        numvals = 0
        for i in range(vector_size):
            if component_dicts[i]['is_animated']:
                numvals = max(numvals, len(component_dicts[i]['data']))
        
        for i in range(vector_size):
            if not component_dicts[i]['is_animated']:
                component_dicts[i]['data'] = [component_dicts[i]['data']] * numvals
        
        values = []
        for i in range(numvals):
            vector = []
            for j in range(vector_size):
                vector.append(component_dicts[j]['data'][i])
            values.append(vector)
        
        return {'is_animated' : True, 'data' : values}
    else:
        value = []
        for i in range(vector_size):
            value.append(component_dicts[i]['data'])
        
        return {'is_animated' : False, 'data' : value}


def get_min_max_property_data_dict(obj, prop_group, prop_name):
    prop_group = getattr(prop_group, prop_name)

    # Multiple properties attached to a single object may have 
    # 'value_min' or 'value_max' as the name. In order to correctly
    # search for the property, set the identifier as a path 
    #     Ex: prop_name.value_min
    identifier_min = prop_name + ".value_min"
    identifier_max = prop_name + ".value_max"
    min_dict = get_property_data_dict(obj, prop_group, identifier_min)
    max_dict = get_property_data_dict(obj, prop_group, identifier_max)

    is_animated = min_dict['is_animated'] or max_dict['is_animated']
    if is_animated:
        numvals = 0
        if min_dict['is_animated']:
                numvals = max(numvals, len(min_dict['data']))
        if max_dict['is_animated']:
                numvals = max(numvals, len(max_dict['data']))

        if not min_dict['is_animated']:
                min_dict['data'] = [min_dict['data']] * numvals
        if not max_dict['is_animated']:
                max_dict['data'] = [max_dict['data']] * numvals
        
        values = []
        for i in range(numvals):
            values.append([min_dict['data'][i], max_dict['data'][i]])
        return {'is_animated' : True, 'data' : values}
    else:
        value = [min_dict['data'], max_dict['data']]
        return {'is_animated' : False, 'data' : value}


def get_rotation_mode_data_dict(obj):
    data = get_property_data_dict(obj, obj, 'rotation_mode')
    if not data['is_animated']:
        return data

    str_values = []
    for n in data['data']:
        strval = ''
        if n == -1:
            strval = 'AXIS_ANGLE'
        elif n == 0: 
            strval = 'QUATERNION'
        elif n == 1: 
            strval = 'XYZ'
        elif n == 2: 
            strval = 'XZY'
        elif n == 3: 
            strval = 'YXZ'
        elif n == 4:
            strval = 'YZX'
        elif n == 5:
            strval = 'ZXY'
        elif n == 6: 
            strval = 'ZYX'

        str_values.append(strval)
    data['data'] = str_values

    return data


def convert_to_animated_data_dict(d, numvals):
    if d['is_animated']:
        padval = d['data'][-1]
        npad = numvals - len(d['data'])
        if npad > 0:
            d['data'] = d['data'] + [padval] * npad
    else:
        d['is_animated'] = True
        d['data'] = [d['data']] * numvals


def is_object_keyframe_animated(obj):
    loc_data = get_vector_property_data_dict(obj, obj, 'location', 3)
    rot_mode_data = get_rotation_mode_data_dict(obj)
    euler_rot_data = get_vector_property_data_dict(obj, obj, 'rotation_euler', 3)
    axis_rot_data = get_vector_property_data_dict(obj, obj, 'rotation_axis_angle', 4)
    quat_rot_data = get_vector_property_data_dict(obj, obj, 'rotation_quaternion', 4)
    scale_data = get_vector_property_data_dict(obj, obj, 'scale', 3)

    is_rotation_animated = (euler_rot_data['is_animated'] or 
                            axis_rot_data['is_animated'] or 
                            quat_rot_data['is_animated'] or
                            rot_mode_data['is_animated'])

    if is_rotation_animated and not rot_mode_data['is_animated']:
        rot_mode = rot_mode_data['data']
        if rot_mode == "AXIS_ANGLE":
            is_rotation_animated = axis_rot_data['is_animated']
        elif rot_mode == "QUATERNION":
            is_rotation_animated = quat_rot_data['is_animated']
        else:
            is_rotation_animated = euler_rot_data['is_animated']

    is_animated = (loc_data['is_animated'] or 
                   is_rotation_animated or
                   scale_data['is_animated'])

    return is_animated


def get_object_transform_data_dict(obj):
    
    loc_data = get_vector_property_data_dict(obj, obj, 'location', 3)
    rot_mode_data = get_rotation_mode_data_dict(obj)
    euler_rot_data = get_vector_property_data_dict(obj, obj, 'rotation_euler', 3)
    axis_rot_data = get_vector_property_data_dict(obj, obj, 'rotation_axis_angle', 4)
    quat_rot_data = get_vector_property_data_dict(obj, obj, 'rotation_quaternion', 4)
    scale_data = get_vector_property_data_dict(obj, obj, 'scale', 3)

    is_rotation_animated = (euler_rot_data['is_animated'] or 
                            axis_rot_data['is_animated'] or 
                            quat_rot_data['is_animated'] or
                            rot_mode_data['is_animated'])

    if is_rotation_animated and not rot_mode_data['is_animated']:
        rot_mode = rot_mode_data['data']
        if rot_mode == "AXIS_ANGLE":
            is_rotation_animated = axis_rot_data['is_animated']
        elif rot_mode == "QUATERNION":
            is_rotation_animated = quat_rot_data['is_animated']
        else:
            is_rotation_animated = euler_rot_data['is_animated']

    is_animated = (loc_data['is_animated'] or 
                   is_rotation_animated or
                   scale_data['is_animated'])

    if not is_animated:
        transform = {}
        transform['location'] = loc_data['data']
        transform['rotation_mode'] = rot_mode_data['data']
        if transform['rotation_mode'] == "AXIS_ANGLE":
            transform['rotation'] = axis_rot_data['data']
        elif transform['rotation_mode'] == "QUATERNION":
            transform['rotation'] = quat_rot_data['data']
        else:
            transform['rotation'] = euler_rot_data['data']
        transform['scale'] = scale_data['data']
        return {'is_animated' : False, 'data' : transform}

    numvals = 0
    if loc_data['is_animated']:
        numvals = max(numvals, len(loc_data['data']))
    if rot_mode_data['is_animated']:
        numvals = max(numvals, len(rot_mode_data['data']))
    if euler_rot_data['is_animated']:
        numvals = max(numvals, len(euler_rot_data['data']))
    if axis_rot_data['is_animated']:
        numvals = max(numvals, len(axis_rot_data['data']))
    if quat_rot_data['is_animated']:
        numvals = max(numvals, len(quat_rot_data['data']))
    if scale_data['is_animated']:
        numvals = max(numvals, len(scale_data['data']))

    convert_to_animated_data_dict(loc_data, numvals)
    convert_to_animated_data_dict(rot_mode_data, numvals)
    convert_to_animated_data_dict(euler_rot_data, numvals)
    convert_to_animated_data_dict(axis_rot_data, numvals)
    convert_to_animated_data_dict(quat_rot_data, numvals)
    convert_to_animated_data_dict(scale_data, numvals)

    transforms = []
    for i in range(numvals):
        t = {}
        t['location'] = loc_data['data'][i]
        t['rotation_mode'] = rot_mode_data['data'][i]
        if t['rotation_mode'] == "AXIS_ANGLE":
            t['rotation'] = axis_rot_data['data'][i]
        elif t['rotation_mode'] == "QUATERNION":
            t['rotation'] = quat_rot_data['data'][i]
        else:
            t['rotation'] = euler_rot_data['data'][i]
        t['scale'] = scale_data['data'][i]

        transforms.append(t)

    return {'is_animated' : True, 'data' : transforms}


def transform_data_to_world_matrix(transform):
    mat_loc = Matrix.Translation(transform['location']).to_4x4()

    if transform['rotation_mode'] == "AXIS_ANGLE":
        angle = transform['rotation'][0]
        axis = Vector(transform['rotation'][1],
                      transform['rotation'][2],
                      transform['rotation'][3])
        mat_rot =  Matrix.Rotation(angle, 4, axis)
    elif transform['rotation_mode'] == "QUATERNION":
        q = Quaternion(transform['rotation'])
        mat_rot = q.to_matrix().to_4x4()
    else:
        e = Euler(transform['rotation'], transform['rotation_mode'])
        mat_rot = e.to_matrix().to_4x4()

    mat_scale = Matrix.Identity(4)
    mat_scale[0][0] = transform['scale'][0]
    mat_scale[1][1] = transform['scale'][1]
    mat_scale[2][2] = transform['scale'][2]

    return vcu.element_multiply(vcu.element_multiply(mat_loc, mat_rot), mat_scale)


def get_object_world_matrix_data_dict(obj):
    tdata = get_object_transform_data_dict(obj)

    if tdata['is_animated']:
        matrices = []
        for transform in tdata['data']:
            matrices.append(transform_data_to_world_matrix(transform))
        return {'is_animated' : True, 'data' : matrices}
    else:
        m = transform_data_to_world_matrix(tdata['data'])
        return {'is_animated' : False, 'data' : m}


def get_object_bbox_center(obj):
        local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
        global_bbox_center = vcu.element_multiply(obj.matrix_world, local_bbox_center)
        return global_bbox_center


def get_object_center_data_dict(obj):
    matdata = get_object_world_matrix_data_dict(obj)
    orig_matrix_world = obj.matrix_world

    ret_dict = {}
    if matdata['is_animated']:
        center_data = []
        for m in matdata['data']:
            obj.matrix_world = m
            center = get_object_bbox_center(obj)
            center_data.append(center)
        ret_dict['is_animated'] = True
        ret_dict['data'] = center_data
    else:
        obj.matrix_world = matdata['data']
        center = get_object_bbox_center(obj)
        ret_dict['is_animated'] = False
        ret_dict['data'] = center

    obj.matrix_world = orig_matrix_world
    vcu.depsgraph_update()

    return ret_dict


# Vector of obj1 towards obj2
def get_object_to_object_vector_data_dict(obj1, obj2):
    cdata1 = get_object_center_data_dict(obj1)
    cdata2 = get_object_center_data_dict(obj2)

    is_animated = cdata1['is_animated'] or cdata2['is_animated']
    if is_animated:
        numvals = 0
        if cdata1['is_animated']:
            numvals = max(numvals, len(cdata1['data']))
        if cdata2['is_animated']:
            numvals = max(numvals, len(cdata2['data']))

        convert_to_animated_data_dict(cdata1, numvals)
        convert_to_animated_data_dict(cdata2, numvals)

        vector_data = []
        for i in range(numvals):
            v = cdata2['data'][i] - cdata1['data'][i]
            vector_data.append(v)
        return {'is_animated' : True, 'data' : vector_data}
    else:
        v = cdata2['data'] - cdata1['data']
        return {'is_animated' : False, 'data' : v}
