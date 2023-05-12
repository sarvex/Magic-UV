# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy

from .. import common


class BlClassRegistry:
    class_list = []

    def __init__(self, *_, **kwargs):
        self.legacy = kwargs.get('legacy', False)

    def __call__(self, cls):
        if hasattr(cls, "bl_idname"):
            BlClassRegistry.add_class(cls.bl_idname, cls, self.legacy)
        elif hasattr(cls, "bl_context"):
            bl_idname = f"{cls.bl_space_type}{cls.bl_region_type}{cls.bl_context}{cls.bl_label}"
            BlClassRegistry.add_class(bl_idname, cls, self.legacy)
        else:
            bl_idname = f"{cls.bl_space_type}{cls.bl_region_type}{cls.bl_label}"
            BlClassRegistry.add_class(bl_idname, cls, self.legacy)
        return cls

    @classmethod
    def add_class(cls, bl_idname, op_class, legacy):
        for class_ in cls.class_list:
            if (class_["bl_idname"] == bl_idname) and \
                   (class_["legacy"] == legacy):
                raise RuntimeError(f"{bl_idname} is already registered")

        new_op = {
            "bl_idname": bl_idname,
            "class": op_class,
            "legacy": legacy,
        }
        cls.class_list.append(new_op)
        common.debug_print(f"{bl_idname} is registered.")

    @classmethod
    def register(cls):
        for class_ in cls.class_list:
            bpy.utils.register_class(class_["class"])
            common.debug_print(f'{class_["bl_idname"]} is registered to Blender.')

    @classmethod
    def unregister(cls):
        for class_ in cls.class_list:
            bpy.utils.unregister_class(class_["class"])
            common.debug_print(f'{class_["bl_idname"]} is unregistered from Blender.')

    @classmethod
    def cleanup(cls):
        cls.class_list = []
        common.debug_print("Cleanup registry.")
