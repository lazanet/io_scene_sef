#!/bin/python3

bl_info = {
    "name": "PES SEF importer/exporter (.sef)",
    "author": "lazanet",
    "version": (0, 0, 1),
    "blender": (2, 82, 0),
    "location": "File > Import-Export",
    "description": "PES SEF importer/exporter",
    "category": "Import-Export" }

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import (ImportHelper, ExportHelper, path_reference_mode)

###########################################
# Menus
###########################################

from .import_actions import load_sef

class ImportSEF(bpy.types.Operator, ImportHelper):
    """Load a SEF File"""
    bl_idname = "import_sef.sef"
    bl_label = "Import SEF"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".sef"
    filter_glob: StringProperty(
            default="*.sef",
            options={'HIDDEN'},
            )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob",))
        return load_sef(keywords['filepath'])

    def draw(self, context):
        pass

def menu_func_import(self, context):
    self.layout.operator(ImportSEF.bl_idname, text="PES SEF (.sef)")

from .export_actions import save_sef

class ExportSEF(bpy.types.Operator, ExportHelper):
    """Save a SEF File"""
    bl_idname = "export_sef.sef"
    bl_label = "Export SEF"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".sef"
    filter_glob: StringProperty(
            default="*.sef",
            options={'HIDDEN'},
            )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob",))
        return save_sef(keywords['filepath'])

    def draw(self, context):
        pass

def menu_func_export(self, context):
    self.layout.operator(ExportSEF.bl_idname, text="PES SEF (.sef)")

###########################################
# Addon registration
###########################################

classes = [
    ImportSEF,
    ExportSEF
]


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        try:
            unregister_class(cls)
        except RuntimeError:
            pass
    
if __name__ == "__main__":
    unregister()
    register()
