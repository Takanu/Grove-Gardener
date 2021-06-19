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
from bpy.props import IntProperty, FloatProperty, BoolProperty, PointerProperty

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
        row.prop(scene, "gardener_thickness_preserve")
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

        row.prop(scene, "gardener_datalayer_x", text="X Axis")
        row.prop(scene, "gardener_datalayer_y", text="Y Axis")
        row.prop(scene, "gardener_datalayer_z", text="Z Axis")



classes = (
    GARDENER_PT_MainPanel,
    GARDENER_PT_FrondSettings,
    GARDENER_PT_LoopSettings,
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

    bpy.types.Scene.gardener_frond_collection = PointerProperty(
        type=bpy.types.Collection,
        name="Frond Collection",
        description="The collection of objects that will be used as Fronds. Grove Gardener will match the length of branches you provide with the length of the twig to be replaced as closely as possible.",
    )

    bpy.types.Scene.gardener_smooth_factor = FloatProperty(
        name="Smoothing",
        description="Determines the tightness of a bend that Gardener will select to automatically smooth (WIP)",
        default=0.4, 
        min=0.0, 
        max=1.0, 
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
    
    bpy.types.Scene.gardener_thickness_preserve = FloatProperty(
        name="Thickness Cutoff",
        description="Decides what branches should not be converted based on their thickness.  Branches equal to or thicker than this will be preserved",
        default=0.1, 
        min=0.0, 
        soft_max=1.0, 
        step=100, 
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
        description="Controls the aggressiveness of the edge loop removal code.  A lower number will remove more loops.",
        default=0.9, 
        min=0.0, 
        soft_max=1.0, 
        step=100, 
        precision=2, 
        subtype='FACTOR',
    )

    bpy.types.Scene.gardener_datalayer_x = BoolProperty(
        name="X Axis Data Layer",
        description="Adds an additional vertex group to bake the relative X position of every node in the tree.",
        default=False,
    )

    bpy.types.Scene.gardener_datalayer_y = BoolProperty(
        name="Y Axis Data Layer",
        description="Adds an additional vertex group to bake the relative Y position of every node in the tree.",
        default=False,
    )

    bpy.types.Scene.gardener_datalayer_z = BoolProperty(
        name="Z Axis Data Layer",
        description="Adds an additional vertex group to bake the relative Z position of every node in the tree.",
        default=False,
    )

    bpy.types.Scene.gardener_datalayer_z = BoolProperty(
        name="Distance From Trunk Layer",
        description="Adds an additional vertex group to bake the relative Z position of every node in the tree.",
        default=False,
    )
    

def unregister():

    del bpy.types.Scene.gardener_use_fronds
    del bpy.types.Scene.gardener_frond_collection
    del bpy.types.Scene.gardener_smooth_factor
    del bpy.types.Scene.gardener_stretch_factor_x
    del bpy.types.Scene.gardener_stretch_factor_yz
    del bpy.types.Scene.gardener_thickness_preserve

    del bpy.types.Scene.gardener_reduce_edgeloops
    del bpy.types.Scene.gardener_edgeloop_reduce_factor

    del bpy.types.Scene.gardener_datalayer_x
    del bpy.types.Scene.gardener_datalayer_y
    del bpy.types.Scene.gardener_datalayer_z

    for cls in classes:
        unregister_class(cls)
