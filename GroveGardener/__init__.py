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
from bpy.props import IntProperty, FloatProperty, BoolProperty

class GardenerPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Gardener"
    bl_idname = "VIEW3D_PT_Grove_Gardener"
    bl_space_type = 'VIEW_3D'
    bl_category = "Grove 10"
    bl_region_type = 'UI'
    

    def draw(self, context):
        layout = self.layout

        scene = bpy.context.scene

        row = layout.column(align=False)
        #row.operator("scene.gardener_replacetwigs")
        row.prop(scene, "gardener_use_fronds")
        row.prop(scene, "gardener_thickness_preserve")
        row.prop(scene, "gardener_reduce_edgeloops")
        row.prop(scene, "gardener_edgeloop_reduce_factor")




classes = (
    GardenerPanel,
)

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.gardener_use_fronds = BoolProperty(
        name="Use Fronds",
        description="If true, small branches will be replaced with fronds that match their curvature and shape.",
        default=False,
    )
    
    bpy.types.Scene.gardener_thickness_preserve = FloatProperty(
        name="Thickness Cutoff",
        description="Decides what branches should not be converted based on their thickness.  Branches equal to or thicker than this will be preserved",
        min=0.0,
        max=1.0,
        default=0.1,
    )

    bpy.types.Scene.gardener_reduce_edgeloops = BoolProperty(
        name="Reduce Edge Loops",
        description="If true, edge loops will be reduced in the tree where possible",
        default=False,
    )

    bpy.types.Scene.gardener_edgeloop_reduce_factor = FloatProperty(
        name="Edge Loop Angle Limit",
        description="Controls the aggressiveness of the edge loop removal code.  A lower number will remove more loops.",
        min=0.0,
        max=1.0,
        default=0.5,
    )
    

def unregister():

    del bpy.types.Scene.gardener_use_fronds
    del bpy.types.Scene.gardener_thickness_preserve
    del bpy.types.Scene.gardener_reduce_edgeloops
    del bpy.types.Scene.gardener_edgeloop_reduce_factor

    for cls in classes:
        unregister_class(cls)
