"""
The module that encapsulates all blender calls and offers the importer and exporter for the RobotDesigner
"""
# todo add logging
# todo add GPL headers

__author__ = 'ulbrich'

# system imports
import os

# Blender-specific imports
import bpy
from mathutils import *
from math import *

# RobotDesigner-specific imports
from ... import armatures

# URDF-specific imports
# from . import urdf_dom
from . import urdf_tree
from . import urdf_dom
from .helpers import string_to_list, get_value, list_to_string


def import_(file_name):
    """
    Imports a URDF file into the RobotDesigner.
    :param file_name: string referring to the file to be opened
    """
    robot_name, root_links, kinematic_chains = urdf_tree.URDFTree.parse(file_name)

    print([i.name for i in root_links])

    armature_name = bpy.context.active_object.name

    def import_geometry(visual):
        """
        Adds a geometry to the blender scene. Uses the file_name variable of the parenting context
        :param visual: A urdf_dom.visual object.
        :return: Returns the transformation in the origin element (a 4x4 blender matrix).
        """
        file = os.path.join(os.path.dirname(file_name), visual.geometry.mesh.filename.lstrip("package://"))
        # print(file, os.path.exists(file))
        fn, extension = os.path.splitext(file)
        if extension == ".stl":
            bpy.ops.import_mesh.stl(filepath=file)
        elif extension == ".dae":
            bpy.ops.wm.collada_import(filepath=file, import_units=True)
            # bpy.context.active_object.matrix_world = Matrix()

        # store origin in a transformation matrix
        # bpy.context.active_object.location = Vector(string_to_list(get_value(visual.origin.xyz, '0 0 0')))
        # bpy.context.active_object.rotation_euler = Euler(string_to_list(visual.origin.rpy), 'XYZ')
        return Matrix.Translation(Vector(string_to_list(visual.origin.xyz))) * \
               Euler(string_to_list(visual.origin.rpy), 'XYZ').to_matrix().to_4x4()

    def parse(tree, parent_name=None):

        armatures.createBone(armature_name, tree.joint.name, parent_name)
        bone_name = tree.joint.name

        bpy.ops.roboteditor.selectbone(boneName=tree.joint.name)

        xyz = string_to_list(get_value(tree.joint.origin.xyz, "0 0 0"))
        euler = string_to_list(get_value(tree.joint.origin.rpy, '0 0 0'))

        axis = string_to_list(tree.joint.axis.xyz)
        for i, element in enumerate(axis):
            if element == -1.0:
                # bpy.context.active_bone.RobotEditor.axis_revert = True
                axis[i] = 1.0

        if axis == [1.0, 0.0, 0.0]:
            bpy.context.active_bone.RobotEditor.axis = 'X'
        elif axis == [0.0, 1.0, 0.0]:
            bpy.context.active_bone.RobotEditor.axis = 'Y'
        elif axis == [0.0, 0.0, 1.0]:
            bpy.context.active_bone.RobotEditor.axis = 'Z'
        else:
            # todo throw exception -- only main axes are supported. Add a limitations section to documentation
            # (which has to be created as well)!
            pass

        bpy.context.active_bone.RobotEditor.Euler.x.value = xyz[0]
        bpy.context.active_bone.RobotEditor.Euler.y.value = xyz[1]
        bpy.context.active_bone.RobotEditor.Euler.z.value = xyz[2]

        bpy.context.active_bone.RobotEditor.Euler.alpha.value = round(degrees(euler[0]), 0)
        bpy.context.active_bone.RobotEditor.Euler.beta.value = round(degrees(euler[1]), 0)
        bpy.context.active_bone.RobotEditor.Euler.gamma.value = round(degrees(euler[2]), 0)

        if tree.joint.dynamics:
            bpy.context.active_bone.RobotEditor.controller.maxVelocity = float(tree.joint.limit.velocity)
            # bpy.context.active_bone.RobotEditor.controller.maxVelocity = float(tree.joint.limit.friction)

        if tree.joint.type_ == 'revolute':
            bpy.context.active_bone.RobotEditor.jointMode = 'REVOLUTE'
            bpy.context.active_bone.RobotEditor.theta.max = float(get_value(tree.joint.limit.upper, 0))
            bpy.context.active_bone.RobotEditor.theta.min = float(get_value(tree.joint.limit.lower, 0))
        else:
            bpy.context.active_bone.RobotEditor.jointMode = 'PRISMATIC'
            if tree.joint.limit is not None:
                bpy.context.active_bone.RobotEditor.d.max = float(get_value(tree.joint.limit.upper, 0))
                bpy.context.active_bone.RobotEditor.d.min = float(get_value(tree.joint.limit.lower, 0))

        # todo set the dynamics properties

        # if None and tree.link.inertial is not None:
        #     # dynamics is not associated to a bone!
        #     origin = tree.link.inertial.origin
        #     i = tree.link.inertial.inertia
        #     if tree.joint.inertial is not None:
        #         bpy.ops.roboteditor.createphysicsframe(tree.link.name)
        #         # todo select physic frame and assign it to the current bone then select it and assign the values
        #         bpy.context.active_object.RobotEditor.dynamics.mass = tree.link.inertial.mass.value
        #         # todo until now only diagonal elements are supported. Throw an exception or show a dialog.
        #         matrix = [[i.ixx, i.ixz, i.ixz], [i.iyy, i.iyz], [i.izz]]
        # get the transformation of the bone

        bone_transformation = bpy.context.active_object.matrix_world * bpy.context.active_object.pose.bones[
            bone_name].matrix

        for visual in tree.link.visual:
            # geometry is not optional in the xml
            if visual.geometry.mesh is not None:

                trafo = import_geometry(visual)
                # URDF (the import in ROS) exhibits a strange behavior:
                # If there is a transformation preceding the mesh in a .dae file, only the scale is
                # extracted and the rest is omitted. Therefore, we store the scale after import and
                # multiply it to the scale given in the xml attribute.

                s1 = string_to_list(visual.geometry.mesh.scale)
                s2 = bpy.context.active_object.scale
                scale = Matrix(
                    [[s1[0] * s2[0], 0, 0, 0], [0, s1[1] * s2[1], 0, 0], [0, 0, s1[2] * s2[2], 0], [0, 0, 0, 1]])

                # todo catch if there are more than 1 mesh (and resolve names)
                bpy.context.active_object.name = tree.link.name
                bpy.context.active_object.matrix_world = bone_transformation * trafo * scale

                # connect the meshes
                bpy.ops.roboteditor.selectarmature(armatureName=armature_name)
                bpy.ops.roboteditor.selectbone(boneName=bone_name)
                bpy.data.objects[tree.link.name].select = True
                bpy.ops.object.parent_set(type='BONE', keep_transform=True)

            else:
                # todo debug message or throw exception if it is a primitive -- better create mesh from primitive
                pass
        # todo process collision meshes
        for collision in tree.link.collision:
            pass

        for sub_tree in tree.children:
            parse(sub_tree, bone_name)
        return

    for link in root_links:
        for visual in link.visual:
            if visual.geometry.mesh is not None:
                trafo = import_geometry(visual)
                s1 = string_to_list(visual.geometry.mesh.scale)
                s2 = bpy.context.active_object.scale
                scale = Matrix(
                    [[s1[0] * s2[0], 0, 0, 0], [0, s1[1] * s2[1], 0, 0], [0, 0, s1[2] * s2[2], 0], [0, 0, 0, 1]])
                bpy.context.active_object.matrix_world = trafo * scale

    for chain in kinematic_chains:
        parse(chain)


# Note: move to different file
def export(file_name):
    """
    Exports the selected robot to an URDF File
    """

    def export_mesh(name):
        file_path = os.path.join(os.path.dirname(file_name), "test", name + '.dae')
        print(file_path)
        armature_name = bpy.context.active_object.name
        # todo: deselect all
        # todo: call the collada export
        # todo: set the right name and return it
        # todo: select the original object
        bpy.ops.object.select_all(action='DESELECT')
        context.scene.objects.active = bpy.data.objects[name]
        context.active_object.select = True
        bpy.ops.wm.collada_export(filepath=file_path, selected=True)
        bpy.ops.roboteditor.selectarmature(armatureName=armature_name)
        return "package://" + os.path.join("test", name + '.dae')

    def build(bone, tree):
        child = tree.add()

        trafo, dummy = bone.RobotEditor.getTransform()
        child.joint.origin.rpy = list_to_string(trafo.to_euler())
        child.joint.origin.xyz = list_to_string(trafo.translation)
        child.joint.name = bone.name
        print(child.joint.name, "trafo", trafo, "rpy", child.joint.origin.rpy)
        if bone.RobotEditor.axis == 'X':
            child.joint.axis.xyz = '1 0 0'
        elif bone.RobotEditor.axis == 'Y':
            child.joint.axis.xyz = '0 1 0'
        elif bone.RobotEditor.axis == 'Z':
            child.joint.axis.xyz = '0 0 1'

        if bone.RobotEditor.jointMode == 'REVOLUTE':
            child.joint.limit.lower = bone.RobotEditor.theta.min
            child.joint.limit.upper = bone.RobotEditor.theta.max
            child.joint.type_ = 'revolute'
        else:
            child.joint.limit.lower = bone.RobotEditor.d.min
            child.joint.limit.upper = bone.RobotEditor.d.max
            child.joint.type_ = 'prismatic'
        # Add properties
        connected_meshes = [mesh.name for mesh in bpy.data.objects if
                            mesh.type == 'MESH' and mesh.parent_bone == bone.name]
        if len(connected_meshes) > 0:
            child.link.name = connected_meshes[0]
        else:
            child.link.name = child.joint.name + '_link'
            # todo: the RobotDesigner does not have the concept of links further it is possible to have
            # todo: several meshes assigned to the same bone
            # todo: solutions add another property to a bone or chose the name from the list of connected meshes
        for mesh in connected_meshes:
            visual = child.add_mesh(export_mesh(mesh))

        # Add geometry
        for child_bones in bone.children:
            build(child_bones, child)

    context = bpy.context  # The armature

    robot_name = context.active_object.name
    root = urdf_tree.URDFTree.create_empty(robot_name)

    # add root geometries to root.link

    root_bones = [b for b in context.active_object.data.bones if b.parent is None]

    for bone in root_bones:
        build(bone, root)
    root.write(file_name)


def draw():
    # todo should also include the blender operator
    pass