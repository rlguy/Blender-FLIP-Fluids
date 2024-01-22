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

class Map(dict):
    def __init__(self, dict_data):
        super(Map, self).__init__(dict_data)
        for k, v in dict_data.items():
            if isinstance(v, dict):
                self[k] = Map(v)
            elif isinstance(v, list):
                new_list = []
                for list_element in v:
                    if isinstance(list_element, dict):
                        new_list.append(Map(list_element))
                    else:
                        new_list.append(list_element)
                self[k] = new_list

            else:
                self[k] = v


    def __getattr__(self, attr):
        return self.get(attr)


    def __setattr__(self, key, value):
        self.__setitem__(key, value)


    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})


    def __delattr__(self, item):
        self.__delitem__(item)


    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]
