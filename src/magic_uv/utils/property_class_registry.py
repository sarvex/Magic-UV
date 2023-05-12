# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

from .. import common


class PropertyClassRegistry:
    class_list = []

    def __init__(self, *_, **kwargs):
        self.legacy = kwargs.get('legacy', False)

    def __call__(self, cls):
        PropertyClassRegistry.add_class(cls.idname, cls, self.legacy)
        return cls

    @classmethod
    def add_class(cls, idname, prop_class, legacy):
        for class_ in cls.class_list:
            if (class_["idname"] == idname) and (class_["legacy"] == legacy):
                raise RuntimeError(f"{idname} is already registered")

        new_op = {
            "idname": idname,
            "class": prop_class,
            "legacy": legacy,
        }
        cls.class_list.append(new_op)
        common.debug_print(f"{idname} is registered.")

    @classmethod
    def init_props(cls, scene):
        for class_ in cls.class_list:
            class_["class"].init_props(scene)
            common.debug_print(f'{class_["idname"]} is initialized.')

    @classmethod
    def del_props(cls, scene):
        for class_ in cls.class_list:
            class_["class"].del_props(scene)
            common.debug_print(f'{class_["idname"]} is cleared.')

    @classmethod
    def cleanup(cls):
        cls.class_list = []
        common.debug_print("Cleanup registry.")
