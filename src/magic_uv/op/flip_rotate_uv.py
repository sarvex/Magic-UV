# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
import bmesh
from bpy.props import (
    BoolProperty,
    IntProperty,
)

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
        return False

    objs = common.get_uv_editable_objects(context)
    return False if not objs else context.object.mode == 'EDIT'


def _get_uv_layer(bm):
    # get UV layer
    return None if not bm.loops.layers.uv else bm.loops.layers.uv.verify()


def _get_src_face_info(bm, uv_layers, only_select=False):
    src_info = {}
    for layer in uv_layers:
        face_info = []
        for face in bm.faces:
            if not only_select or face.select:
                info = {
                    "index": face.index,
                    "uvs": [l[layer].uv.copy() for l in face.loops],
                    "pin_uvs": [l[layer].pin_uv for l in face.loops],
                    "seams": [l.edge.seam for l in face.loops],
                }
                face_info.append(info)
        if not face_info:
            return None
        src_info[layer.name] = face_info

    return src_info


def _paste_uv(bm, src_info, dest_info, uv_layers, strategy, flip,
              rotate, copy_seams):
    for slayer_name, dlayer in zip(src_info.keys(), uv_layers):
        src_faces = src_info[slayer_name]
        dest_faces = dest_info[dlayer.name]

        for idx, dinfo in enumerate(dest_faces):
            sinfo = None
            if strategy == 'N_M':
                sinfo = src_faces[idx % len(src_faces)]

            elif strategy == 'N_N':
                sinfo = src_faces[idx]
            suv = sinfo["uvs"]
            spuv = sinfo["pin_uvs"]
            ss = sinfo["seams"]
            if len(suv) != len(dinfo["uvs"]):
                return -1

            suvs_fr = list(suv)
            spuvs_fr = list(spuv)
            ss_fr = list(ss)

            # flip UVs
            if flip is True:
                suvs_fr.reverse()
                spuvs_fr.reverse()
                ss_fr.reverse()

            # rotate UVs
            for _ in range(rotate):
                uv = suvs_fr.pop()
                pin_uv = spuvs_fr.pop()
                s = ss_fr.pop()
                suvs_fr.insert(0, uv)
                spuvs_fr.insert(0, pin_uv)
                ss_fr.insert(0, s)

            # paste UVs
            for l, suv, spuv, ss in zip(bm.faces[dinfo["index"]].loops,
                                        suvs_fr, spuvs_fr, ss_fr):
                l[dlayer].uv = suv
                l[dlayer].pin_uv = spuv
                if copy_seams is True:
                    l.edge.seam = ss

    return 0


@PropertyClassRegistry()
class _Properties:
    idname = "flip_rotate_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_flip_rotate_uv_enabled = BoolProperty(
            name="Flip/Rotate UV Enabled",
            description="Flip/Rotate UV is enabled",
            default=False
        )
        scene.muv_flip_rotate_uv_seams = BoolProperty(
            name="Seams",
            description="Seams",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_flip_rotate_uv_enabled
        del scene.muv_flip_rotate_uv_seams


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_FlipRotateUV(bpy.types.Operator):
    """
    Operation class: Flip and Rotate UV coordinate
    """

    bl_idname = "uv.muv_flip_rotate_uv"
    bl_label = "Flip/Rotate UV"
    bl_description = "Flip/Rotate UV coordinate"
    bl_options = {'REGISTER', 'UNDO'}

    flip = BoolProperty(
        name="Flip UV",
        description="Flip UV...",
        default=False
    )
    rotate = IntProperty(
        default=0,
        name="Rotate UV",
        min=0,
        max=30
    )
    seams = BoolProperty(
        name="Seams",
        description="Seams",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        return True if common.is_console_mode() else _is_valid_context(context)

    def execute(self, context):
        self.report({'INFO'}, "Flip/Rotate UV")
        objs = common.get_uv_editable_objects(context)

        face_count = 0
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()

            # get UV layer
            uv_layer = _get_uv_layer(bm)
            if not uv_layer:
                self.report({'WARNING'}, f"Object {obj.name} must have more than one UV map")
                return {'CANCELLED'}

            # get selected face
            src_info = _get_src_face_info(bm, [uv_layer], True)
            if not src_info:
                continue

            if ret := _paste_uv(
                bm,
                src_info,
                src_info,
                [uv_layer],
                'N_N',
                self.flip,
                self.rotate,
                self.seams,
            ):
                self.report({'WARNING'}, f"Some Object {obj.name}'s faces are different size")
                return {'CANCELLED'}

            bmesh.update_edit_mesh(obj.data)
            if compat.check_version(2, 80, 0) < 0 and self.seams is True:
                obj.data.show_edge_seams = True

            face_count += len(src_info[list(src_info.keys())[0]])

        if face_count == 0:
            self.report({'WARNING'}, "No faces are selected")
            return {'CANCELLED'}
        self.report({'INFO'}, f"{face_count} face(s) are fliped/rotated")

        return {'FINISHED'}
