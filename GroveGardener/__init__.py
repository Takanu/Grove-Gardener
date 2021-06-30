# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Grove Gardener",
    "author" : "Takanu Kyriako",
    "description" : "Trim down trees made from The Grove into game engine-compatible trees.",
    "blender" : (2, 92, 0),
    "version" : (1, 0, 0),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}


import bpy, bmesh, time
from bpy.utils import register_class, unregister_class
from bpy.types import Menu
from bpy.types import Operator
from bpy.props import IntProperty, FloatProperty, BoolProperty, PointerProperty, EnumProperty

class GARDENER_PT_MainPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Gardener"
    bl_idname = "GARDENER_PT_MainPanel"
    bl_category = "Grove 10"
    
    

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene

        row = layout.column(align=False)
        #row.use_property_split = True
        #row.use_property_decorate = False
        row.prop(scene, "gardener_use_fronds")


class GARDENER_PT_FrondSettings(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Fronds"
    bl_parent_id = "GARDENER_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene

        row = layout.column(align=False)
        row.use_property_split = True
        row.use_property_decorate = False
        row.prop(scene, "gardener_frond_collection")
        row.separator()
        row.prop(scene, "gardener_frond_replace_type")
        row.separator()

        replace_type = scene.gardener_frond_replace_type
        if replace_type == 'Thickness':
            row.prop(scene, "gardener_thickness_cutoff")
        elif replace_type == 'Hierarchy':
            row.prop(scene, "gardener_hierarchy_level")
        elif replace_type == 'HierarchyHybrid':
            row.prop(scene, "gardener_hierarchy_level")
            row.prop(scene, "gardener_thickness_cutoff")

        
        row.separator()
        row.prop(scene, "gardener_smooth_factor")
        row.prop(scene, "gardener_stretch_factor_x")
        row.prop(scene, "gardener_stretch_factor_yz")
        row.separator()

class GARDENER_PT_LoopSettings(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Edge Loops"
    bl_parent_id = "GARDENER_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene

        row = layout.column(align=False)
        row.use_property_split = True
        row.use_property_decorate = False

        
        row.prop(scene, "gardener_reduce_edgeloops")
        row.prop(scene, "gardener_edgeloop_reduce_factor")

class GARDENER_PT_Normals(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Normal Reprojection"
    bl_parent_id = "GARDENER_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene

        row = layout.column(align=False)
        row.use_property_split = True
        row.use_property_decorate = False

        
        row.prop(scene, "gardener_normal_hull_res")
        row.prop(scene, "gardener_normal_hull_size")
    
class GARDENER_PT_DataLayers(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Extra Data Layers"
    bl_parent_id = "GARDENER_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene

        row = layout.column(align=False)
        row.use_property_split = True
        row.use_property_decorate = False

        row.prop(scene, "gardener_datalayer_height")
        row.prop(scene, "gardener_datalayer_trunktobranch")
        row.prop(scene, "gardener_datalayer_branchtofrond")
        row.prop(scene, "gardener_datalayer_branchgroup")
        row.separator()
        row.prop(scene, "gardener_merge_layers")



classes = (
    GARDENER_PT_MainPanel,
    GARDENER_PT_FrondSettings,
    GARDENER_PT_LoopSettings,
    GARDENER_PT_Normals,
    GARDENER_PT_DataLayers,
    
)

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.gardener_use_fronds = BoolProperty(
        name="Build with Grove Gardener",
        description="If true, Grove Gardener will be used during the build process to replace branches and perform other tasks.",
        default=False,
    )

    bpy.types.Scene.gardener_frond_replace_type = EnumProperty(
        name="Replace Method",
        description="Determines how branches are replaced with fronds.",
        items=(
        ('Hierarchy', 'Hierarchy', "This replaces branches depending on how far down they are located in the tree's branch structure."),
        ('Thickness', 'Thickness', "This replaces branches depending on how thick they are relative to the rest of the tree."),
        ('HierarchyHybrid', 'Hierarchy + Thickness', "This replaces branches based on hierarchy parameters first, then by the thickness of the tree.")
        ),
    )

    bpy.types.Scene.gardener_thickness_cutoff = FloatProperty(
        name="Thickness Cutoff",
        description="Decides what branches should not be converted based on their thickness.  Branches equal to or thicker than this will be preserved",
        default=0.1, 
        min=0.0, 
        soft_max=1.0, 
        step=100, 
        precision=2, 
        subtype='FACTOR',
    )

    bpy.types.Scene.gardener_hierarchy_level = IntProperty(
        name="Hierarchy Cutoff",
        description="Decides what branches should not be converted based on how far the branch is down in the tree's hierarchy.",
        default=2, 
        min=1, 
        soft_max=6, 
        subtype='FACTOR',
    )

    bpy.types.Scene.gardener_frond_collection = PointerProperty(
        type=bpy.types.Collection,
        name="Frond Collection",
        description="The collection of objects that will be used as Fronds. Grove Gardener will match the length of branches you provide with the length of the twig to be replaced as closely as possible.",
    )

    bpy.types.Scene.gardener_smooth_factor = FloatProperty(
        name="Smoothing",
        description="Determines the tightness of a bend that Gardener will select to automatically smooth.  WARNING - Work in progress, high values may yield weird results.  When pruning this value will make the frond move away from the actual location of the branch data so beeeee careful!",
        default=0.4, 
        min=0.0, 
        max=5.0, 
        step=10, 
        precision=2, 
        subtype='FACTOR',
    )

    bpy.types.Scene.gardener_stretch_factor_x = FloatProperty(
        name="Stretch X",
        description="Determines how much a frond mesh wiil stretch along the X axis to better match the branch it replaces.",
        default=0.4, 
        min=0.0, 
        max=1.0, 
        step=10, 
        precision=2, 
        subtype='FACTOR',
    )

    bpy.types.Scene.gardener_stretch_factor_yz = FloatProperty(
        name="Stretch Y/Z",
        description="Determines how much a frond mesh wiil stretch along the Y and Z axis in proportion to the amount it stretches on the X axis.",
        default=0.4, 
        min=0.0, 
        max=1.0, 
        step=10, 
        precision=2, 
        subtype='FACTOR',
    )
    
    

    bpy.types.Scene.gardener_reduce_edgeloops = BoolProperty(
        name="Reduce Edge Loops",
        description="If true, edge loops will be reduced in the tree where possible",
        default=False,
    )

    bpy.types.Scene.gardener_edgeloop_reduce_factor = FloatProperty(
        name="Edge Loop Angle Limit",
        description="Controls the aggressiveness of the edge loop removal code.  A lower number will remove more loops.  WARNING - Work in progress, results will often look a lil jagged",
        default=0.9, 
        min=0.0, 
        soft_max=1.0, 
        step=100, 
        precision=2, 
        subtype='FACTOR',
    )

    bpy.types.Scene.gardener_normal_hull_res = FloatProperty(
        name="Hull Resolution",
        description="Affects the voxel size of the normal hull used to create smoother tree normals",
        default=0.5, 
        min=0.1, 
        soft_max=1, 
        precision=2, 
        subtype='DISTANCE',
    )

    bpy.types.Scene.gardener_normal_hull_size = FloatProperty(
        name="Hull Expand",
        description="Affects the amount the hull is scaled up in order to surround the tree before normal reprojection.  Higher values ensure the reprojection mesh will surround the tree, but the mesh will be less accurate",
        default=0.2, 
        min=0.01, 
        soft_max=0.5, 
        precision=1, 
        subtype='DISTANCE',
    )

    bpy.types.Scene.gardener_datalayer_height = BoolProperty(
        name="Height",
        description="Adds an additional vertex group to bake the relative height position of every node in the tree",
        default=False,
    )

    bpy.types.Scene.gardener_datalayer_trunktobranch = BoolProperty(
        name="Trunk to Branch",
        description="Adds an additional vertex group to bake the relative distance between each part of the tree and the trunk",
        default=False,
    )

    bpy.types.Scene.gardener_datalayer_branchtofrond = BoolProperty(
        name="Branch to Frond",
        description="Adds an additional vertex group to bake the relative distance between the branch mesh and the tips of every frond mesh",
        default=False,
    )

    bpy.types.Scene.gardener_datalayer_branchgroup = BoolProperty(
        name="Branch Group",
        description="Adds an additional vertex group that indexes every group of branches from the trunk of the tree",
        default=False,
    )
    
    bpy.types.Scene.gardener_merge_layers = BoolProperty(
        name="Merge to Vertex Colors",
        description="Merges all selected Vertex Layers into a single Vertex Color layer called 'Combined Layers'.  This will also become the active Vertex Color layer",
        default=False,
    )
    

def unregister():

    del bpy.types.Scene.gardener_use_fronds
    del bpy.types.Scene.gardener_frond_collection
    del bpy.types.Scene.gardener_frond_replace_type

    del bpy.types.Scene.gardener_thickness_cutoff

    del bpy.types.Scene.gardener_smooth_factor
    del bpy.types.Scene.gardener_stretch_factor_x
    del bpy.types.Scene.gardener_stretch_factor_yz
    

    del bpy.types.Scene.gardener_reduce_edgeloops
    del bpy.types.Scene.gardener_edgeloop_reduce_factor

    del bpy.types.Scene.gardener_normal_hull_res
    del bpy.types.Scene.gardener_normal_hull_size

    del bpy.types.Scene.gardener_datalayer_x
    del bpy.types.Scene.gardener_datalayer_y
    del bpy.types.Scene.gardener_datalayer_z

    for cls in classes:
        unregister_class(cls)
