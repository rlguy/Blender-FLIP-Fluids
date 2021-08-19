# Blender FLIP Fluids Add-on
# Copyright (C) 2021 Ryan L. Guy
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

import bpy, os, sqlite3, math

from .flip_fluid_geometry_export_object import GeometryExportType, MotionExportType
from ..filesystem import filesystem_protection_layer as fpl


class GeometryDatabase():
    def __init__(self, db_filepath, clear_database=False):
        self._conn = None
        self._cursor = None
        self._is_conn_open = False
        self._filepath = db_filepath

        self._initialize_database(db_filepath, clear_database)


    ###########################################################################
    ### Database Operations
    ###########################################################################

    def open(self):
        if self._is_conn_open:
            return
        self._conn = sqlite3.connect(self._filepath)
        self._cursor = self._conn.cursor()
        self._is_conn_open = True


    def close(self):
        if self._is_conn_open:
            self._cursor.close()
            self._conn.close()
            self._is_conn_open = False


    def begin(self):
        self._cursor.execute("begin")


    def is_open(self):
        return self._is_conn_open


    def commit(self):
        self._conn.commit()


    def _format_bytes(self, num):
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


    def get_filesize(self):
        if os.path.isfile(self._filepath):
            num_bytes = os.path.getsize(self._filepath)
            return self._format_bytes(num_bytes)
        else:
            return 0


    def add_object(self, export_obj):
        if self.object_exists(export_obj):
            return

        name = export_obj.name
        slug = export_obj.name_slug
        mtype = export_obj.motion_export_type_to_string()
        ex_mesh     = int(export_obj.is_exporting_mesh())
        ex_vertices = int(export_obj.is_exporting_vertices())
        ex_centroid = int(export_obj.is_exporting_centroid())
        ex_axis     = int(export_obj.is_exporting_axis())
        ex_curve    = int(export_obj.is_exporting_curve())

        insert_command = """INSERT INTO object (
                object_name, 
                object_slug, 
                object_motion_type, 
                export_mesh, 
                export_vertices,
                export_centroid,
                export_axis,
                export_curve   
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        values = (name, slug, mtype, ex_mesh, ex_vertices, ex_centroid, ex_axis, ex_curve)
        self._cursor.execute(insert_command, values)


    def object_exists(self, export_obj):
        cmd = """SELECT EXISTS(SELECT object_id FROM object WHERE object_slug=?)"""
        self._cursor.execute(cmd, (export_obj.name_slug,))
        return self._cursor.fetchone()[0]


    def get_all_objects(self):
        self._cursor.execute("""SELECT * FROM object""")
        return self._cursor.fetchall()


    def get_object_id(self, export_obj):
        cmd = """SELECT object_id FROM object WHERE object_slug=?"""
        self._cursor.execute(cmd, (export_obj.name_slug,))
        return self._cursor.fetchone()[0]


    def get_object_id_by_name_slug(self, name_slug):
        cmd = """SELECT object_id FROM object WHERE object_slug=?"""
        self._cursor.execute(cmd, (name_slug,))
        result = self._cursor.fetchone()
        if not result:
            return None
        return result[0]


    def get_object_geometry_export_types(self, name_slug):
        cmd = """SELECT export_mesh, export_vertices, export_centroid, export_axis, export_curve 
            FROM object WHERE object_slug=?"""
        self._cursor.execute(cmd, (name_slug,))
        result = self._cursor.fetchone()
        export_dict = {}
        export_dict['mesh']     = bool(result[0])
        export_dict['vertices'] = bool(result[1])
        export_dict['centroid'] = bool(result[2])
        export_dict['axis']     = bool(result[3])
        export_dict['curve']    = bool(result[4])
        return export_dict


    def delete_object_by_slug(self, name_slug):
        delete_command = """DELETE FROM object WHERE object_slug=?"""
        self._cursor.execute(delete_command, (name_slug,))


    def add_mesh_static(self, object_id, blob):
        insert_command = """INSERT INTO mesh_static (
                object_id, mesh_static_data
            ) VALUES (?, ?)"""
        values = (object_id, blob)
        self._cursor.execute(insert_command, values)


    def add_mesh_keyframed(self, object_id, frame_id, matrix_world):
        insert_command = """INSERT INTO mesh_keyframed (
                object_id, frame_id, 
                m00, m01, m02, m03,
                m10, m11, m12, m13,
                m20, m21, m22, m23,
                m30, m31, m32, m33
            ) VALUES (?, ?,
                      ?, ?, ?, ?,
                      ?, ?, ?, ?,
                      ?, ?, ?, ?,
                      ?, ?, ?, ?)"""
        m = matrix_world
        values = (object_id, frame_id, 
                  m[0][0], m[0][1], m[0][2], m[0][3],
                  m[1][0], m[1][1], m[1][2], m[1][3],
                  m[2][0], m[2][1], m[2][2], m[2][3],
                  m[3][0], m[3][1], m[3][2], m[3][3])
        self._cursor.execute(insert_command, values)


    def add_mesh_animated(self, object_id, frame_id, blob):
        insert_command = """INSERT INTO mesh_animated (
                object_id, frame_id, mesh_animated_data
            ) VALUES (?, ?, ?)"""
        values = (object_id, frame_id, blob)
        self._cursor.execute(insert_command, values)


    def add_centroid_static(self, object_id, centroid):
        insert_command = """INSERT INTO centroid_static (
                object_id, x, y, z
            ) VALUES (?, ?, ?, ?)"""
        values = (object_id, centroid[0], centroid[1], centroid[2])
        self._cursor.execute(insert_command, values)


    def add_centroid_keyframed(self, object_id, frame_id, centroid):
        insert_command = """INSERT INTO centroid_keyframed (
                object_id, frame_id, x, y, z
            ) VALUES (?, ?, ?, ?, ?)"""
        values = (object_id, frame_id, centroid[0], centroid[1], centroid[2])
        self._cursor.execute(insert_command, values)


    def add_centroid_animated(self, object_id, frame_id, centroid):
        insert_command = """INSERT INTO centroid_animated (
                object_id, frame_id, x, y, z
            ) VALUES (?, ?, ?, ?, ?)"""
        values = (object_id, frame_id, centroid[0], centroid[1], centroid[2])
        self._cursor.execute(insert_command, values)


    def add_axis_static(self, object_id, local_x, local_y, local_z):
        insert_command = """INSERT INTO axis_static (
                object_id, 
                localx_x, localx_y, localx_z,
                localy_x, localy_y, localy_z,
                localz_x, localz_y, localz_z
            ) VALUES (?, 
                      ?, ?, ?,
                      ?, ?, ?,
                      ?, ?, ?)"""
        values = (object_id, 
                  local_x[0], local_x[1], local_x[2],
                  local_y[0], local_y[1], local_y[2],
                  local_z[0], local_z[1], local_z[2])
        self._cursor.execute(insert_command, values)


    def add_axis_keyframed(self, object_id, frame_id, local_x, local_y, local_z):
        insert_command = """INSERT INTO axis_keyframed (
                object_id, frame_id, 
                localx_x, localx_y, localx_z,
                localy_x, localy_y, localy_z,
                localz_x, localz_y, localz_z
            ) VALUES (?, ?,
                      ?, ?, ?,
                      ?, ?, ?,
                      ?, ?, ?)"""
        values = (object_id, frame_id,
                  local_x[0], local_x[1], local_x[2],
                  local_y[0], local_y[1], local_y[2],
                  local_z[0], local_z[1], local_z[2])
        self._cursor.execute(insert_command, values)


    def add_axis_animated(self, object_id, frame_id, local_x, local_y, local_z):
        insert_command = """INSERT INTO axis_animated (
                object_id, frame_id, 
                localx_x, localx_y, localx_z,
                localy_x, localy_y, localy_z,
                localz_x, localz_y, localz_z
            ) VALUES (?, ?,
                      ?, ?, ?,
                      ?, ?, ?,
                      ?, ?, ?)"""
        values = (object_id, frame_id,
                  local_x[0], local_x[1], local_x[2],
                  local_y[0], local_y[1], local_y[2],
                  local_z[0], local_z[1], local_z[2])
        self._cursor.execute(insert_command, values)


    def add_curve_static(self, object_id, blob):
        insert_command = """INSERT INTO curve_static (
                object_id, curve_static_data
            ) VALUES (?, ?)"""
        values = (object_id, blob)
        self._cursor.execute(insert_command, values)


    def add_curve_keyframed(self, object_id, frame_id, matrix_world):
        insert_command = """INSERT INTO curve_keyframed (
                object_id, frame_id, 
                m00, m01, m02, m03,
                m10, m11, m12, m13,
                m20, m21, m22, m23,
                m30, m31, m32, m33
            ) VALUES (?, ?,
                      ?, ?, ?, ?,
                      ?, ?, ?, ?,
                      ?, ?, ?, ?,
                      ?, ?, ?, ?)"""
        m = matrix_world
        values = (object_id, frame_id, 
                  m[0][0], m[0][1], m[0][2], m[0][3],
                  m[1][0], m[1][1], m[1][2], m[1][3],
                  m[2][0], m[2][1], m[2][2], m[2][3],
                  m[3][0], m[3][1], m[3][2], m[3][3])
        self._cursor.execute(insert_command, values)


    def add_curve_animated(self, object_id, frame_id, blob):
        insert_command = """INSERT INTO curve_animated (
                object_id, frame_id, curve_animated_data
            ) VALUES (?, ?, ?)"""
        values = (object_id, frame_id, blob)
        self._cursor.execute(insert_command, values)


    def static_geometry_exists(self, object_id, geometry_export_type):
        if geometry_export_type == GeometryExportType.MESH:
            table = "mesh_static"
        elif geometry_export_type == GeometryExportType.VERTICES:
            table = "points_static"
        elif geometry_export_type == GeometryExportType.CENTROID:
            table = "centroid_static"
        elif geometry_export_type == GeometryExportType.AXIS:
            table = "axis_static"
        elif geometry_export_type == GeometryExportType.CURVE:
            table = "curve_static"

        cmd = """SELECT EXISTS(SELECT object_id FROM {0} WHERE object_id=?)"""
        cmd = cmd.format(table)
        self._cursor.execute(cmd, (object_id,))
        return self._cursor.fetchone()[0]


    def get_dynamic_geometry_exported_frames(self, object_id, motion_export_type, geometry_export_type):
        if geometry_export_type == GeometryExportType.MESH:
            table = "mesh_"
        elif geometry_export_type == GeometryExportType.VERTICES:
            table = "points_"
        elif geometry_export_type == GeometryExportType.CENTROID:
            table = "centroid_"
        elif geometry_export_type == GeometryExportType.AXIS:
            table = "axis_"
        elif geometry_export_type == GeometryExportType.CURVE:
            table = "curve_"

        if motion_export_type == MotionExportType.KEYFRAMED:
            table += "keyframed"
        elif motion_export_type == MotionExportType.ANIMATED:
            table += "animated"

        cmd = """SELECT frame_id FROM {0} WHERE object_id=? ORDER BY frame_id"""
        cmd = cmd.format(table)
        self._cursor.execute(cmd, (object_id,))

        frames = []
        for row in self._cursor.fetchall():
            frames.append(row[0])

        return frames


    def get_object_motion_export_type(self, name_slug):
        cmd = """SELECT object_motion_type FROM object WHERE object_slug=?"""
        self._cursor.execute(cmd, (name_slug,))
        return self._cursor.fetchone()[0]


    def is_object_dynamic(self, name_slug):
        motion_type = self.get_object_motion_export_type(name_slug)
        return motion_type == 'KEYFRAMED' or motion_type == 'ANIMATED'


    def get_mesh_static(self, name_slug):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT mesh_static_data FROM mesh_static WHERE object_id=?"""
        self._cursor.execute(cmd, (object_id,))
        result = self._cursor.fetchone()
        if not result:
            return None
        return result[0]


    def mesh_animated_exists(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return False
        cmd = """SELECT EXISTS(SELECT object_id FROM mesh_animated WHERE object_id=? AND frame_id=?)"""
        self._cursor.execute(cmd, (object_id, frameno))
        return self._cursor.fetchone()[0]


    def mesh_keyframed_exists(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return False
        cmd = """SELECT EXISTS(SELECT object_id FROM mesh_keyframed WHERE object_id=? AND frame_id=?)"""
        self._cursor.execute(cmd, (object_id, frameno))
        return self._cursor.fetchone()[0]


    def get_mesh_keyframed_transform(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """
            SELECT m00, m01, m02, m03, 
                   m10, m11, m12, m13, 
                   m20, m21, m22, m23, 
                   m30, m31, m32, m33 FROM mesh_keyframed 
            WHERE object_id=? AND frame_id=?
            """
        self._cursor.execute(cmd, (object_id, frameno))
        result = self._cursor.fetchone()
        if not result:
            return None
        return list(result)


    def get_mesh_animated(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT mesh_animated_data FROM mesh_animated WHERE object_id=? AND frame_id=?"""
        self._cursor.execute(cmd, (object_id, frameno))
        result = self._cursor.fetchone()
        if not result:
            return None
        return result[0]


    def get_mesh_animated_blob_length(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT LENGTH(mesh_animated_data) FROM mesh_animated WHERE object_id=? AND frame_id=?"""
        self._cursor.execute(cmd, (object_id, frameno))
        result = self._cursor.fetchone()
        if not result:
            return None
        return result[0]


    def get_centroid_static(self, name_slug):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT x, y, z FROM centroid_static WHERE object_id=?"""
        self._cursor.execute(cmd, (object_id,))
        result = self._cursor.fetchone()
        if not result:
            return None
        return list(result)


    def get_centroid_keyframed(self, name_slug, frame_id):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT x, y, z FROM centroid_keyframed WHERE object_id=? AND frame_id=?"""
        self._cursor.execute(cmd, (object_id, frame_id))
        result = self._cursor.fetchone()
        if not result:
            return None
        return list(result)


    def get_centroid_animated(self, name_slug, frame_id):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT x, y, z FROM centroid_animated WHERE object_id=? AND frame_id=?"""
        self._cursor.execute(cmd, (object_id, frame_id))
        result = self._cursor.fetchone()
        if not result:
            return None
        return list(result)


    def centroid_animated_exists(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return False
        cmd = """SELECT EXISTS(SELECT object_id FROM centroid_animated WHERE object_id=? AND frame_id=?)"""
        self._cursor.execute(cmd, (object_id, frameno))
        return self._cursor.fetchone()[0]


    def centroid_keyframed_exists(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return False
        cmd = """SELECT EXISTS(SELECT object_id FROM centroid_keyframed WHERE object_id=? AND frame_id=?)"""
        self._cursor.execute(cmd, (object_id, frameno))
        return self._cursor.fetchone()[0]


    def get_axis_static(self, name_slug):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT localx_x, localx_y, localx_z,
                        localy_x, localy_y, localy_z,
                        localz_x, localz_y, localz_z FROM axis_static 
                 WHERE object_id=?"""
        self._cursor.execute(cmd, (object_id,))
        result = self._cursor.fetchone()
        local_x = [result[0], result[1], result[2]]
        local_y = [result[3], result[4], result[5]]
        local_z = [result[6], result[7], result[8]]
        return local_x, local_y, local_z


    def get_axis_keyframed(self, name_slug, frame_id):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT localx_x, localx_y, localx_z,
                        localy_x, localy_y, localy_z,
                        localz_x, localz_y, localz_z FROM axis_keyframed 
                 WHERE object_id=? AND frame_id=?"""
        self._cursor.execute(cmd, (object_id, frame_id))
        result = self._cursor.fetchone()
        local_x = [result[0], result[1], result[2]]
        local_y = [result[3], result[4], result[5]]
        local_z = [result[6], result[7], result[8]]
        return local_x, local_y, local_z


    def get_axis_animated(self, name_slug, frame_id):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT localx_x, localx_y, localx_z,
                        localy_x, localy_y, localy_z,
                        localz_x, localz_y, localz_z FROM axis_animated 
                 WHERE object_id=? AND frame_id=?"""
        self._cursor.execute(cmd, (object_id, frame_id))
        result = self._cursor.fetchone()
        local_x = [result[0], result[1], result[2]]
        local_y = [result[3], result[4], result[5]]
        local_z = [result[6], result[7], result[8]]
        return local_x, local_y, local_z


    def curve_animated_exists(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return False
        cmd = """SELECT EXISTS(SELECT object_id FROM curve_animated WHERE object_id=? AND frame_id=?)"""
        self._cursor.execute(cmd, (object_id, frameno))
        return self._cursor.fetchone()[0]


    def curve_keyframed_exists(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return False
        cmd = """SELECT EXISTS(SELECT object_id FROM curve_keyframed WHERE object_id=? AND frame_id=?)"""
        self._cursor.execute(cmd, (object_id, frameno))
        return self._cursor.fetchone()[0]


    def get_curve_static(self, name_slug):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT curve_static_data FROM curve_static WHERE object_id=?"""
        self._cursor.execute(cmd, (object_id,))
        result = self._cursor.fetchone()
        if not result:
            return None
        return result[0]


    def get_curve_keyframed_transform(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """
            SELECT m00, m01, m02, m03, 
                   m10, m11, m12, m13, 
                   m20, m21, m22, m23, 
                   m30, m31, m32, m33 FROM curve_keyframed 
            WHERE object_id=? AND frame_id=?
            """
        self._cursor.execute(cmd, (object_id, frameno))
        result = self._cursor.fetchone()
        if not result:
            return None
        return list(result)


    def get_curve_animated(self, name_slug, frameno):
        object_id = self.get_object_id_by_name_slug(name_slug)
        if object_id is None:
            return None
        cmd = """SELECT curve_animated_data FROM curve_animated WHERE object_id=? AND frame_id=?"""
        self._cursor.execute(cmd, (object_id, frameno))
        result = self._cursor.fetchone()
        if not result:
            return None
        return result[0]




    ###########################################################################
    ### Initialize Database
    ###########################################################################

    def _generate_create_mesh_table_commands(self):
        mesh_static_table = """
            CREATE TABLE mesh_static ( 
                mesh_static_id    INTEGER  PRIMARY KEY, 
                object_id         INTEGER  NOT NULL,
                mesh_static_data  BLOB     NOT NULL
            )"""

        mesh_keyframed_table = """
            CREATE TABLE mesh_keyframed ( 
                mesh_keyframed_id  INTEGER  PRIMARY KEY, 
                object_id          INTEGER  NOT NULL,
                frame_id           INTEGER  NOT NULL,

                m00                REAL     NOT NULL,
                m01                REAL     NOT NULL,
                m02                REAL     NOT NULL,
                m03                REAL     NOT NULL,

                m10                REAL     NOT NULL,
                m11                REAL     NOT NULL,
                m12                REAL     NOT NULL,
                m13                REAL     NOT NULL,

                m20                REAL     NOT NULL,
                m21                REAL     NOT NULL,
                m22                REAL     NOT NULL,
                m23                REAL     NOT NULL,

                m30                REAL     NOT NULL,
                m31                REAL     NOT NULL,
                m32                REAL     NOT NULL,
                m33                REAL     NOT NULL
            )"""

        mesh_animated_table = """
            CREATE TABLE mesh_animated ( 
                mesh_animated_id    INTEGER  PRIMARY KEY, 
                object_id           INTEGER  NOT NULL,
                frame_id            INTEGER  NOT NULL,
                mesh_animated_data  BLOB,
                reference           INTEGER
            )"""

        return [mesh_static_table, mesh_keyframed_table, mesh_animated_table]


    def _generate_create_points_table_commands(self):
        points_static_table = """
            CREATE TABLE points_static ( 
                points_static_id    INTEGER  PRIMARY KEY, 
                object_id           INTEGER  NOT NULL,
                points_static_data  BLOB     NOT NULL
            )"""

        points_keyframed_table = """
            CREATE TABLE points_keyframed ( 
                points_keyframed_id  INTEGER  PRIMARY KEY, 
                object_id            INTEGER  NOT NULL,
                frame_id             INTEGER  NOT NULL,

                m00                  REAL     NOT NULL,
                m01                  REAL     NOT NULL,
                m02                  REAL     NOT NULL,
                m03                  REAL     NOT NULL,

                m10                  REAL     NOT NULL,
                m11                  REAL     NOT NULL,
                m12                  REAL     NOT NULL,
                m13                  REAL     NOT NULL,

                m20                  REAL     NOT NULL,
                m21                  REAL     NOT NULL,
                m22                  REAL     NOT NULL,
                m23                  REAL     NOT NULL,

                m30                  REAL     NOT NULL,
                m31                  REAL     NOT NULL,
                m32                  REAL     NOT NULL,
                m33                  REAL     NOT NULL
            )"""

        points_animated_table = """
            CREATE TABLE points_animated ( 
                points_animated_id    INTEGER  PRIMARY KEY, 
                object_id             INTEGER  NOT NULL,
                frame_id              INTEGER  NOT NULL,
                points_animated_data  BLOB,
                reference             INTEGER
            )"""

        return [points_static_table, points_keyframed_table, points_animated_table]


    def _generate_create_centroid_table_commands(self):
        centroid_static_table = """
            CREATE TABLE centroid_static ( 
                centroid_static_id  INTEGER  PRIMARY KEY, 
                object_id           INTEGER  NOT NULL,
                x                   REAL     NOT NULL,
                y                   REAL     NOT NULL,
                z                   REAL     NOT NULL
            )"""

        centroid_keyframed_table = """
            CREATE TABLE centroid_keyframed ( 
                centroid_keyframed_id  INTEGER  PRIMARY KEY, 
                object_id              INTEGER  NOT NULL,
                frame_id               INTEGER  NOT NULL,
                x                      REAL     NOT NULL,
                y                      REAL     NOT NULL,
                z                      REAL     NOT NULL
            )"""

        centroid_animated_table = """
            CREATE TABLE centroid_animated ( 
                centroid_animated_id  INTEGER  PRIMARY KEY, 
                object_id             INTEGER  NOT NULL,
                frame_id              INTEGER  NOT NULL,
                x                     REAL     NOT NULL,
                y                     REAL     NOT NULL,
                z                     REAL     NOT NULL
            )"""

        return [centroid_static_table, centroid_keyframed_table, centroid_animated_table]


    def _generate_create_axis_table_commands(self):
        axis_static_table = """
            CREATE TABLE axis_static ( 
                axis_static_id  INTEGER  PRIMARY KEY, 
                object_id       INTEGER  NOT NULL,

                localx_x        REAL     NOT NULL,
                localx_y        REAL     NOT NULL,
                localx_z        REAL     NOT NULL,

                localy_x        REAL     NOT NULL,
                localy_y        REAL     NOT NULL,
                localy_z        REAL     NOT NULL,

                localz_x        REAL     NOT NULL,
                localz_y        REAL     NOT NULL,
                localz_z        REAL     NOT NULL
            )"""

        axis_keyframed_table = """
            CREATE TABLE axis_keyframed ( 
                axis_keyframed_id  INTEGER  PRIMARY KEY, 
                object_id          INTEGER  NOT NULL,
                frame_id          INTEGER  NOT NULL,

                localx_x           REAL     NOT NULL,
                localx_y           REAL     NOT NULL,
                localx_z           REAL     NOT NULL,

                localy_x           REAL     NOT NULL,
                localy_y           REAL     NOT NULL,
                localy_z           REAL     NOT NULL,

                localz_x           REAL     NOT NULL,
                localz_y           REAL     NOT NULL,
                localz_z           REAL     NOT NULL
            )"""

        axis_animated_table = """
            CREATE TABLE axis_animated ( 
                axis_animated_id  INTEGER  PRIMARY KEY, 
                object_id         INTEGER  NOT NULL,
                frame_id         INTEGER  NOT NULL,

                localx_x          REAL     NOT NULL,
                localx_y          REAL     NOT NULL,
                localx_z          REAL     NOT NULL,

                localy_x          REAL     NOT NULL,
                localy_y          REAL     NOT NULL,
                localy_z          REAL     NOT NULL,

                localz_x          REAL     NOT NULL,
                localz_y          REAL     NOT NULL,
                localz_z          REAL     NOT NULL
            )"""

        return [axis_static_table, axis_keyframed_table, axis_animated_table]


    def _generate_create_curve_table_commands(self):
        curve_static_table = """
            CREATE TABLE curve_static ( 
                curve_static_id    INTEGER  PRIMARY KEY, 
                object_id          INTEGER  NOT NULL,
                curve_static_data  BLOB     NOT NULL
            )"""

        curve_keyframed_table = """
            CREATE TABLE curve_keyframed ( 
                curve_keyframed_id  INTEGER  PRIMARY KEY, 
                object_id           INTEGER  NOT NULL,
                frame_id            INTEGER  NOT NULL,

                m00                 REAL     NOT NULL,
                m01                 REAL     NOT NULL,
                m02                 REAL     NOT NULL,
                m03                 REAL     NOT NULL,

                m10                 REAL     NOT NULL,
                m11                 REAL     NOT NULL,
                m12                 REAL     NOT NULL,
                m13                 REAL     NOT NULL,

                m20                 REAL     NOT NULL,
                m21                 REAL     NOT NULL,
                m22                 REAL     NOT NULL,
                m23                 REAL     NOT NULL,

                m30                REAL     NOT NULL,
                m31                REAL     NOT NULL,
                m32                REAL     NOT NULL,
                m33                REAL     NOT NULL
            )"""

        curve_animated_table = """
            CREATE TABLE curve_animated ( 
                curve_animated_id    INTEGER  PRIMARY KEY, 
                object_id            INTEGER  NOT NULL,
                frame_id             INTEGER  NOT NULL,
                curve_animated_data  BLOB,
                reference            INTEGER
            )"""

        return [curve_static_table, curve_keyframed_table, curve_animated_table]


    def _generate_trigger_commands(self):
        table_names = [
            "mesh_static", "mesh_keyframed", "mesh_animated",
            "points_static", "points_keyframed", "points_animated",
            "centroid_static", "centroid_keyframed", "centroid_animated",
            "axis_static", "axis_keyframed", "axis_animated",
            "curve_static", "curve_keyframed", "curve_animated"
        ]

        trigger_cmd = """
            CREATE TRIGGER delete_object_from_{0}
                AFTER DELETE ON object
            BEGIN
                DELETE FROM {0}
                WHERE object_id = OLD.object_id;
            END;
        """

        commands = []
        for tname in table_names:
            cmd = trigger_cmd.format(tname)
            commands.append(cmd)

        return commands


    def _generate_create_table_commands(self):
        object_table = """
            CREATE TABLE object ( 
                object_id           INTEGER  PRIMARY KEY, 
                object_name         TEXT     NOT NULL,
                object_slug         TEXT     NOT NULL UNIQUE,
                object_motion_type  TEXT     CHECK(object_motion_type IN ('STATIC','KEYFRAMED','ANIMATED')) NOT NULL,
                export_mesh         INTEGER  DEFAULT 0,
                export_vertices     INTEGER  DEFAULT 0,
                export_centroid     INTEGER  DEFAULT 0,
                export_axis         INTEGER  DEFAULT 0,
                export_curve        INTEGER  DEFAULT 0
            )"""

        version_table = """
            CREATE TABLE version ( 
                version_id        INTEGER  PRIMARY KEY CHECK(version_id = 1), 
                version_label     TEXT    NOT NULL,
                version_major     INTEGER NOT NULL,
                version_minor     INTEGER NOT NULL,
                version_revision  INTEGER NOT NULL,
                version_patch     INTEGER NOT NULL
            )"""

        cmds = []
        cmds.append(object_table)
        cmds.append(version_table)
        cmds += self._generate_create_mesh_table_commands()
        cmds += self._generate_create_points_table_commands()
        cmds += self._generate_create_centroid_table_commands()
        cmds += self._generate_create_axis_table_commands()
        cmds += self._generate_create_curve_table_commands()
        cmds += self._generate_trigger_commands()

        return cmds


    def _initialize_database(self, db_filepath, clear_database=False):
        if clear_database and os.path.isfile(db_filepath):
            fpl.delete_file(db_filepath)

        if os.path.isfile(db_filepath):
            return sqlite3.connect(db_filepath)
        
        create_table_commands = self._generate_create_table_commands()

        directory = os.path.dirname(db_filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        conn = sqlite3.connect(db_filepath)
        c = conn.cursor()
        for cmd in create_table_commands:
            c.execute(cmd)
        c.close()
        conn.commit()
        conn.close()


