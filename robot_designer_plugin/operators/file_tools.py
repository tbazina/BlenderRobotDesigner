# #####
#  This file is part of the RobotDesigner developed in the Neurorobotics
#  subproject of the Human Brain Project (https://www.humanbrainproject.eu).
#
#  The Human Brain Project is a European Commission funded project
#  in the frame of the Horizon2020 FET Flagship plan.
#  (http://ec.europa.eu/programmes/horizon2020/en/h2020-section/fet-flagships)
#
#  The Robot Designer has initially been forked from the RobotEditor
#  (https://gitlab.com/h2t/roboteditor) developed at the Karlsruhe Institute
#  of Technology in the High Performance Humanoid Technologies Laboratory (H2T).
# #####

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# System imports
import os

# Blender imports
import bpy

# RobotDesigner imports
from ..core import config, PluginManager, RDOperator
from .dae_sdf_converter import dae_sdf_converter
from ..core.logfile import operator_logger


@PluginManager.register_class
class ConvertDAEPackages(RDOperator):
    """
    :ref:`operator` for converting the .dae files in a folder to SDF packages.
    **Preconditions:**
    **Postconditions:**
    """

    bl_idname = config.OPERATOR_PREFIX + "convertdaepackages"
    bl_label = "Convert All '.dae' Files in a Folder to SDF Packages"

    # need to set a path so so we can get the file name and path
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filename: bpy.props.StringProperty(subtype="FILE_NAME")
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    @classmethod
    def poll(cls, context):
        return True

    @RDOperator.OperatorLogger
    def execute(self, context):
        # print(self.filepath)
        dae_sdf_converter(self.directory)
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


@PluginManager.register_class
class StlToDaeConverter(RDOperator):
    """
    :ref:`operator` for converting all .stl files in a folder to .dae files.
    **Preconditions:**
    **Postconditions:**
    """

    bl_idname = config.OPERATOR_PREFIX + "convert_stl_to_dae"
    bl_label = "Convert All '.stl' Files in a Folder to '.dae' Files"

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    @classmethod
    def poll(cls, context):
        return True

    @RDOperator.OperatorLogger
    def execute(self, context):
        operator_logger.info(".stl input folder is:", self.directory)

        output_dir = os.path.join(self.directory, "dae_files")
        os.mkdir(output_dir)

        for file in os.listdir(self.directory):
            if file.endswith(".stl"):
                # import .stl file, export .dae file, delete mesh in blender
                operator_logger.info("Converting file: ", file)
                bpy.ops.import_mesh.stl(filepath=os.path.join(self.directory, file))
                bpy.ops.wm.collada_export(
                    filepath=os.path.join(output_dir, file.replace(".stl", ".dae"))
                )
                bpy.ops.object.delete()

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


@PluginManager.register_class
class PrintTransformations(RDOperator):
    """
    :ref:`operator` for print transformation matrix from active object to all selected objects.

    **Preconditions:**

    **Postconditions:**
    """

    bl_idname = config.OPERATOR_PREFIX + "printtransformations"
    bl_label = "Print Transformation Matrix from Active Object to All Selected Objects"

    @classmethod
    def poll(cls, context):
        return True

    @RDOperator.OperatorLogger
    def execute(self, context):
        active_object = bpy.context.active_object

        for ob in [obj for obj in context.scene.objects if obj.select_get()]:
            operator_logger.info(
                "Transformation from %(from)s to %(to)s:"
                % {"from": active_object.name, "to": ob.name}
            )
            transform = active_object.matrix_world.inverted() @ ob.matrix_world
            operator_logger.info(transform)

        return {"FINISHED"}
