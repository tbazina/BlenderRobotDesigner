# #####
# This file is part of the RobotDesigner of the Neurorobotics subproject (SP10)
# in the Human Brain Project (HBP).
# It has been forked from the RobotEditor (https://gitlab.com/h2t/roboteditor)
# developed at the Karlsruhe Institute of Technology in the
# High Performance Humanoid Technologies Laboratory (H2T).
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

# #####
#
# Copyright (c) 2015, Karlsruhe Institute of Technology (KIT)
# Copyright (c) 2016, FZI Forschungszentrum Informatik
#
# Changes:
#
#   2015-01-16: Stefan Ulbrich (FZI), Major refactoring. Integrated into complex plugin framework.
#
# ######

# System imports
import logging

# Blender imports
import bpy
from bpy.props import (
    IntProperty,
    IntVectorProperty,
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    StringProperty,
    EnumProperty,
    CollectionProperty,
)

# RobotDesigner imports
from ..core.logfile import operator_logger, gui_logger, prop_logger, core_logger
from ..operators.segments import SelectSegment, UpdateSegments
from ..operators.muscles import SelectMuscle
from ..core.property import PropertyGroupHandlerBase, PropertyHandler


class RDSelectedObjects(PropertyGroupHandlerBase):
    def __init__(self):
        self.visible = PropertyHandler()


class RDGlobals(PropertyGroupHandlerBase):
    """
    Property group that contains all globally defined parameters mostly related to the state of the GUI
    """

    @staticmethod
    def debug_level_callback(self, context):
        level = global_properties.operator_debug_level.get(context.scene)
        operator_logger.info("Switching debug level to: {}".format(level.upper()))
        loggers = [operator_logger, gui_logger, prop_logger, core_logger]
        if level == "debug":
            for logger in loggers:
                logger.setLevel(logging.DEBUG)
        elif level == "info":
            for logger in loggers:
                logger.setLevel(logging.INFO)
        elif level == "warning":
            for logger in loggers:
                logger.setLevel(logging.WARN)
        else:
            for logger in loggers:
                logger.setLevel(logging.ERROR)

    @staticmethod
    def updateGlobals(self, context):
        model_name = context.active_object.name
        segment_name = context.active_bone.name

        UpdateSegments.run(model_name=model_name, segment_name=segment_name)

    @staticmethod
    def updateBoneName(self, context):

        SelectSegment.run(
            segment_name=global_properties.segment_name.get(context.scene)
        )

    @staticmethod
    def display_physics(self, context):
        for physics in [
            physics
            for physics in bpy.data.objects
            if physics.RobotDesigner.tag == "PHYSICS_FRAME"
        ]:
            if self.display_physics_selection == True:
                physics.hide_set(False)
            else:
                physics.hide_set(True)

    @staticmethod
    def attach_world(self, context):
        obj = context.active_object
        if self.world_property is True:
            bpy.data.objects[obj.name].RobotDesigner.world = True
            # export joint with fixed type
        else:
            bpy.data.objects[obj.name].RobotDesigner.world = False

    @staticmethod
    def updateMuscleName(self, context):

        SelectMuscle.run(muscle_name=global_properties.active_muscle.get(context.scene))

    @staticmethod
    def update_geometry_name(self, context):
        print("Update Mesh name")
        for i in [
            i
            for i in bpy.context.selected_objects
            if i.name != context.active_object.name
        ]:
            i.select_set(False)
        try:
            bpy.data.objects[global_properties.mesh_name.get(context.scene)].select_set(
                True
            )
        except KeyError:
            print(
                "Selecting ",
                global_properties.mesh_name.get(context.scene),
                " failed due to key error!",
            )
            pass

    @staticmethod
    def display_geometries(self, context):
        """
        Hides/Shows mesh objects in dependence of the respective Global property
        """

        hide_geometry = global_properties.display_mesh_selection.get(context.scene)
        geometry_name = [
            obj.name
            for obj in bpy.data.objects
            if not obj.parent_bone is None
            and obj.type == "MESH"
            and obj.RobotDesigner.tag != "PHYSICS_FRAME"
            and obj.RobotDesigner.tag != "WRAPPING"
        ]

        for mesh in geometry_name:
            obj = bpy.data.objects[mesh]
            tag = obj.RobotDesigner.tag
            if hide_geometry == "all":
                obj.hide_set(False)
            elif hide_geometry == "collision" and (
                tag == "COLLISION" or "BASIC_COLLISION_" in tag
            ):
                obj.hide_set(False)
            elif hide_geometry == "visual" and tag == "DEFAULT":
                obj.hide_set(False)
            elif hide_geometry == "bascol" and "BASIC_COLLISION_" in tag:
                obj.hide_set(False)
            elif hide_geometry == "none":
                obj.hide_set(True)
            else:
                obj.hide_set(True)

    @staticmethod
    def display_wrapping_geometries(self, context):

        hide_geometry = global_properties.display_wrapping_selection.get(context.scene)
        geometry_name = [
            obj.name
            for obj in bpy.data.objects
            if not obj.parent_bone is None
            and obj.type == "MESH"
            and obj.RobotDesigner.tag == "WRAPPING"
        ]

        for mesh in geometry_name:
            obj = bpy.data.objects[mesh]
            if hide_geometry == "all":
                obj.hide_set(False)
            elif hide_geometry == "none":
                obj.hide_set(True)

    @staticmethod
    def display_muscles(self, context):
        """
        Hides/Shows muscles in dependence of the respective Global property
        """
        hide_muscles = global_properties.display_muscle_selection.get(context.scene)

        muscle_names = [
            obj.name
            for obj in bpy.data.objects
            if bpy.data.objects[obj.name].RobotDesigner.muscles.robotName != ""
        ]

        for muscle in muscle_names:
            obj = bpy.data.objects[muscle]
            muscle_type = obj.RobotDesigner.muscles.muscleType
            if hide_muscles == "all":
                obj.hide_set(False)
            elif hide_muscles == "MYOROBOTICS" and muscle_type == "MYOROBOTICS":
                obj.hide_set(False)
            elif hide_muscles == "MILLARD_EQUIL" and muscle_type == "MILLARD_EQUIL":
                obj.hide_set(False)
            elif hide_muscles == "MILLARD_ACCEL" and muscle_type == "MILLARD_ACCEL":
                obj.hide_set(False)
            elif hide_muscles == "THELEN" and muscle_type == "THELEN":
                obj.hide_set(False)
            elif hide_muscles == "RIGID_TENDON" and muscle_type == "RIGID_TENDON":
                obj.hide_set(False)
            elif hide_muscles == "none":
                obj.hide_set(True)
            else:
                obj.hide_set(True)

    @staticmethod
    def display_sensors(self, context):
        """
        Hides/Shows sensors in dependence of the respective Global property
        """
        hide_sensors = global_properties.display_sensor_type.get(context.scene)

        sensor_names = [
            obj.name
            for obj in bpy.data.objects
            if bpy.data.objects[obj.name].RobotDesigner.tag == "SENSOR"
        ]

        for sensor in sensor_names:
            obj = bpy.data.objects[sensor]
            sensor_type = obj.RobotDesigner.sensor_type
            if hide_sensors == "ALL":
                obj.hide_set(False)
            elif hide_sensors == "CAMERA_SENSOR" and sensor_type == "CAMERA_SENSOR":
                obj.hide_set(False)
            elif (
                hide_sensors == "DEPTH_CAMERA_SENSOR"
                and sensor_type == "DEPTH_CAMERA_SENSOR"
            ):
                obj.hide_set(False)
            elif hide_sensors == "LASER_SENSOR" and sensor_type == "LASER_SENSOR":
                obj.hide_set(False)
            elif hide_sensors == "IMU_SENSOR" and sensor_type == "IMU_SENSOR":
                obj.hide_set(False)
            elif (
                hide_sensors == "ALTIMETER_SENSOR" and sensor_type == "ALTIMETER_SENSOR"
            ):
                obj.hide_set(False)
            elif (
                hide_sensors == "FORCE_TORQUE_SENSOR"
                and sensor_type == "FORCE_TORQUE_SENSOR"
            ):
                obj.hide_set(False)
            elif hide_sensors == "CONTACT_SENSOR" and sensor_type == "CONTACT_SENSOR":
                obj.hide_set(False)
            elif hide_sensors == "none":
                obj.hide_set(True)
            else:
                obj.hide_set(True)

    @staticmethod
    def name_update(self, context):
        """
        updates the robot name of the active object, the armature and  for every assigned muscle
        """
        # update aramture name
        bpy.data.armatures[self.old_name].name = self.model_name

        # update muscle attachement name
        if self.old_name != "":
            muscles = [
                obj
                for obj in bpy.data.objects
                if obj.RobotDesigner.muscles.robotName == self.old_name
            ]

            for muscle in muscles:
                muscle.RobotDesigner.muscles.robotName = self.model_name

            self.old_name = self.model_name

        # update active object name
        bpy.context.active_object.name = self.model_name

    @staticmethod
    def muscle_dim_update(self, context):
        """
        updates the visualization dimension of all muscles in scene
        """
        print("in the function")
        active_model = self.model_name
        for muscle in [
            obj.name
            for obj in bpy.data.objects
            if bpy.data.objects[obj.name].RobotDesigner.muscles.robotName
            == active_model
        ]:
            bpy.data.objects[muscle].data.bevel_depth = self.muscle_dim
            print("changing ----")

    def __init__(self):

        # Holds the current selected kinematics model (armature) name
        self.model_name = PropertyHandler(
            StringProperty(name="Name", update=self.name_update, default="None")
        )
        self.old_name = PropertyHandler(StringProperty(name="Name"))

        # Holds the name of the currently selected segment (Bone)
        self.segment_name = PropertyHandler(StringProperty(update=self.updateBoneName))

        # Holds the name of the currently selected geometry (Mesh object)
        self.mesh_name = PropertyHandler(
            StringProperty(update=self.update_geometry_name)
        )

        # Holds the name of the currently selected physics frame (Empty object)
        self.physics_frame_name = PropertyHandler(StringProperty())

        # Holds the name of the currently selected sensor (Camera or Empty object)
        self.camera_sensor_name = PropertyHandler(StringProperty())

        # Holds the name of the currently selected world (Empty object)
        self.world_name = PropertyHandler(StringProperty(default="Select World"))

        # Used to realize the main tab in the GUI
        self.gui_tab = PropertyHandler(EnumProperty(
            items=[('armatures', 'Robot', 'Modify the Robot'),
                   ('bones', 'Segments', 'Modify segements'),
                   ('meshes', 'Geometries', 'Attach meshes to segments'),
                   ('sensors', 'Sensors', 'Attach sensors to the robot'),
                   ('muscles', 'Muscles', 'Attach muscles to the robot'),
                   # ('markers', 'Markers', 'Assign markers to bones'),
                   ('files', 'Files', 'Export Armature'),
                   ('world', 'World', 'Set world parameters')],
        ))

        # Holds the selection to operate on collision geometries OR visual geometries
        self.mesh_type = PropertyHandler(
            EnumProperty(
                items=[
                    ("DEFAULT", "Visual geometries", "Edit visual geometries"),
                    ("COLLISION", "Collision geometries", "Edit collision geometries"),
                ]
            )
        )

        self.display_sensor_type = PropertyHandler(
            EnumProperty(
                items=[
                    ("ALL", "All", "Show all sensors"),
                    ("CAMERA_SENSOR", "Camera", "Show camera sensors"),
                    (
                        "DEPTH_CAMERA_SENSOR",
                        "Depth Camera",
                        "Show depth camera sensors",
                    ),
                    ("LASER_SENSOR", "Laser", "Show laser scanners"),
                    ("ALTIMETER_SENSOR", "Altimeter", "Show altimeter sensors"),
                    ("IMU_SENSOR", "IMU", "Show IMU sensors"),
                    (
                        "FORCE_TORQUE_SENSOR",
                        "Force Torque",
                        "Show force torque sensors",
                    ),
                    ("CONTACT_SENSOR", "Contact", "Show contact sensors"),
                    # ('POSITION', 'Position sensors', 'Show position sensors')]
                    ("NONE", "None", "Show no sensors"),
                ],
                update=self.display_sensors,
            )
        )

        self.active_sensor = PropertyHandler(
            StringProperty(name="Active Sensor", default="")
        )

        self.physics_type = PropertyHandler(
            EnumProperty(items=[("PHYSICS_FRAME", "Mass Object", "Mass Object")])
        )

        self.display_physics_selection = PropertyHandler(
            BoolProperty(
                name="Show Physics Frames",
                description="Show or Hide Physics Frames",
                default=True,
                update=self.display_physics,
            )
        )

        # attach world property
        self.world_property = PropertyHandler(
            BoolProperty(name="Attach Link to World", update=self.attach_world)
        )

        # Holds the selection to list connected or unassigned meshes in dropdown menus
        self.list_meshes = PropertyHandler(
            EnumProperty(
                items=[
                    (
                        "all",
                        "List All",
                        "Show All Meshes in Menu",
                        "RESTRICT_VIEW_OFF",
                        1,
                    ),
                    (
                        "connected",
                        "List Connected",
                        "Show Only Connected Meshes in Menu",
                        "OUTLINER_OB_ARMATURE",
                        2,
                    ),
                    (
                        "disconnected",
                        "List Disconnected",
                        "Show Only Disconnected Meshes in Menu",
                        "ARMATURE_DATA",
                        3,
                    ),
                ]
            )
        )

        self.assign_collision = PropertyHandler(
            BoolProperty(
                name="Assign as Collision Mesh",
                description="Adds a Collision Tag to the Mesh",
                default=False,
            )
        )

        # Holds the selection of whether do hide/display connected/unassigned meshes in the 3D viewport
        self.display_mesh_selection = PropertyHandler(
            EnumProperty(
                items=[
                    ("all", "All", "Show All Objects in Viewport"),
                    (
                        "collision",
                        "Collision",
                        "Show Only Connected Collision Geometries",
                    ),
                    (
                        "bascol",
                        "BASCOL",
                        "Show Only Connected Basic Collision Geometries",
                    ),
                    ("visual", "Visual", "Show Only Connected Visual Geometries"),
                    ("none", "None", "Show No Connected Geometries"),
                ],
                update=self.display_geometries,
            )
        )

        self.display_wrapping_selection = PropertyHandler(
            EnumProperty(
                items=[
                    ("all", "All", "Show All Wrapping Objects"),
                    ("none", "None", "Show No Wrapping Objects"),
                ],
                update=self.display_wrapping_geometries,
            )
        )

        # Holds the selection to list connected or unassigned segments in dropdown menus
        self.list_segments = PropertyHandler(
            EnumProperty(
                items=[
                    (
                        "all",
                        "List All",
                        "Show All Bones in Menu",
                        "RESTRICT_VIEW_OFF",
                        1,
                    ),
                    (
                        "connected",
                        "List Connected",
                        "Show Only Bones with Connected Meshes in Menu",
                        "OUTLINER_OB_ARMATURE",
                        2,
                    ),
                    (
                        "disconnected",
                        "List Disconnected",
                        "List Only Bones without Connected Meshes in Menu",
                        "ARMATURE_DATA",
                        3,
                    ),
                ]
            )
        )

        self.storage_mode = PropertyHandler(
            EnumProperty(
                items=[
                    (
                        "temporary",
                        "Non-persistant GIT",
                        "Stores/Retrieves Files from GIT Temporary" + " repository",
                    ),
                    (
                        "git",
                        "Persistent GIT",
                        "Stores/Retrieves Files from Persistent GIT Repository",
                    ),
                    ("local", "Local", "Stores/Retrieves from Local Hard Disk"),
                ]
            )
        )
        self.git_url = PropertyHandler(StringProperty(name="GIT URL"))
        self.git_repository = PropertyHandler(StringProperty(name="GIT Repository"))

        self.segment_tab = PropertyHandler(
            EnumProperty(
                items=[
                    ("kinematics", "Kinematics", "Edit Kinematic Properties"),
                    ("dynamics", "Dynamics", "Edit Dynamic Properties"),
                    ("controller", "Controller", "Edit Controller Properties"),
                ],
                name="asdf",
            )
        )

        self.bone_length = PropertyHandler(
            FloatProperty(
                name="Global Bone Length",
                default=1,
                min=0.001,
                update=self.updateGlobals,
            )
        )
        self.do_kinematic_update = PropertyHandler(
            BoolProperty(name="Import Update", default=True)
        )

        self.gazebo_tags = PropertyHandler(
            StringProperty(name="Gazebo Tags", default="")
        )

        self.world_s_name = PropertyHandler(StringProperty(name="World Name"))
        self.gravity = PropertyHandler(
            FloatProperty(name="Gravity", default=9.8, min=0, max=9.8)
        )
        self.light_s_name = PropertyHandler(StringProperty(name="Light Name"))
        self.cast_shadows = PropertyHandler(
            BoolProperty(name="Cast Shadows", default=False)
        )
        self.diffuse = PropertyHandler(
            IntVectorProperty(name="Diffuse", default=(1, 1, 1), min=0, max=255)
        )
        self.specular = PropertyHandler(
            FloatVectorProperty(
                name="Specular", default=(0.1, 0.1, 0.1), min=0, max=255
            )
        )

        self.operator_debug_level = PropertyHandler(
            EnumProperty(
                items=[
                    ("info", "Info", "Log Information"),
                    (
                        "debug",
                        "Debug",
                        "Log Everything Including Debug Messages (Verbose)",
                    ),
                    ("warning", "Warning", "Log Warnings Only"),
                    ("error", "Error", "Log Errors Only"),
                ],
                update=self.debug_level_callback,
            )
        )

        self.active_muscle = PropertyHandler(
            StringProperty(name="Active Muscle", default="")
        )

        self.display_muscle_selection = PropertyHandler(
            EnumProperty(
                items=[
                    ("all", "All", "Show All Muscles"),
                    (
                        "MILLARD_EQUIL",
                        "Millard Equilibrium 2012",
                        "Show only Millard Equilibrium 2012 Muscles",
                    ),
                    (
                        "MILLARD_ACCEL",
                        "Millard Acceleration 2012",
                        "Show only Millard Acceleration 2012 Muscles",
                    ),
                    ("THELEN", "Thelen 2003", "Show only Thelen 2003 Muscles"),
                    ("RIGID_TENDON", "Rigid Tendon", "Show only Rigid Tendon Muscles"),
                    ("MYOROBOTICS", "Myorobotics", "Show only Myorobotics Muscles"),
                    ("none", "None", "Show No Muscles"),
                ],
                update=self.display_muscles,
            )
        )

        self.muscle_dim = PropertyHandler(
            FloatProperty(
                name="Muscle Dimension:",
                default=0.005,
                min=0.0001,
                max=0.1,
                update=self.muscle_dim_update,
            )
        )

        # Export options
        self.export_thumbnail = PropertyHandler(
            BoolProperty(
                name="Create and Export Thumbnail",
                description="Generates and Exports a Rendered \
                                Thumbnail from the Current Scene Image",
                default=True,
            )
        )
        self.export_rqt_multiplot_muscles = PropertyHandler(
            BoolProperty(
                name="Export rqt multiplot for muscles",
                description="Exports a xml description \
                                for rqt multiplot of muscle sensors and actuation",
                default=False,
            )
        )
        self.export_rqt_multiplot_jointcontroller = PropertyHandler(
            BoolProperty(
                name="Export rqt multiplot for joint controller",
                description="Exports a xml description \
                                for rqt multiplot of joint sensors and controller actuation",
                default=False,
            )
        )
        self.export_rqt_ez_publisher_muscles = PropertyHandler(
            BoolProperty(
                name="Export rqt ez publisher for joint controller",
                description="Exports a xml description \
                                for rqt ez publisher of controller actuation",
                default=False,
            )
        )
        self.export_rqt_ez_publisher_jointcontroller = PropertyHandler(
            BoolProperty(
                name="Export rqt multiplot for muscles",
                description="Exports a xml description \
                                for rqt ez publisher of muscle actuation",
                default=False,
            )
        )





global_properties = RDGlobals()
global_properties.register(bpy.types.Scene)
