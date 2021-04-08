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
    "description" : "Tools for trimming down trees made from The Grove into game engine-compatible trees.",
    "blender" : (2, 92, 0),
    "version" : (1, 0, 0),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

from bpy.utils import register_class
from bpy.types import Menu
from bpy.types import Operator
from bpy.props import IntProperty, FloatProperty

class GardenerPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Gardener"
    bl_idname = "VIEW3D_PT_Grid_Options"
    bl_space_type = 'VIEW_3D'
    bl_category = "The Grove 10"
    bl_region_type = 'UI'
    

    def draw(self, context):
        layout = self.layout

        scene = bpy.context.scene

        row = layout.column(align=True)
        row.operator("scene.gardener_replacetwigs")


class GARDENER_OT_Replace_Twigs(Operator):
    """Substitutes smaller twigs in the environment with emitter triangles!"""

    bl_idname = "scene.gardener_replacetwigs"
    bl_label = "Replace Twigs"

    def execute(self, context):

        def BM_get_edge_loop(target_edge):
            e_step = target_edge
            # You can uncomment the # in the next line to reverse direction
            loop = e_step.link_loops[0]#.link_loop_next
            current_vertex = loop.vert  # Previous Current Vert (loop's vert)
            
            print("Current edge verts - ", e_step)
            print(current_vertex)
            new_sel = [e_step.index]
            shared_linked_face = True
            
            i = 0
            while i <= 63:
            
                ## Find what vertex linked with this one has three or less linked vertices.
                for ele in current_vertex.link_edges[:]:
                    if ele.is_boundary == True:
                        if ele.index != e_step.index:
                        
                            print("Candidate found : ", ele)
                            new_sel.append(ele.index)
                            
                            e_step = ele
                            current_vertex = ele.other_vert(current_vertex)
                            print("Next vertex : ", current_vertex)
                            
                            if target_edge.link_faces[0].index != ele.link_faces[0].index:
                                shared_linked_face = False
                            
                            break
                
                if loop.edge.other_vert(loop.vert).index == current_vertex.index:
                    break
    
            i += 1

        def bmesh_get_connected(vert):
    
            # The stack of vertex indexes we will end up with for our mesh element.
            vert_stack = [vert.index]
            last_search = [vert]
            
            while len(last_search) != 0:
                
                current_search = last_search.copy()
                last_search.clear()
                
                for search_vert in current_search:
                    for edge in search_vert.link_edges[:]:
                        
                        vert_c = edge.other_vert(search_vert)

                        if vert_c.index not in vert_stack:

                            vert_c.select = True
                            vert_stack.append(vert_c.index)
                            last_search.append(vert_c)
                            

            return vert_stack
        
            
            return new_sel, shared_linked_face
        

        # boop initial setup
        # ///////////////////////
        t0 = time.perf_counter()

        obj = context.edit_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.select_mode |= {'EDGE'}

        boundary_edge_stack = []

        for e in bm.edges:
            if e.is_boundary:
                boundary_edge_stack.append(e.index)


        # Fetch boundary and emitter loops
        # ///////////////////////
        boundary_loops = []
        emitter_loops = []

        while len(boundary_edge_stack) > 0:
            print("next edge")
            target_edge = boundary_edge_stack[0]
            loop_results = BM_get_edge_loop(bm.edges[target_edge])
            loop = loop_results[0]
            
            if loop_results[1] == True:
                emitter_loops.append(loop)
            else:
                boundary_loops.append(loop)
            
            for loop_edge_index in loop:
                boundary_edge_stack.remove(loop_edge_index)
                        
            
            if len(boundary_edge_stack) == 0:
                break
        

        # Get the perimeter lengths of all boundary loops
        # ///////////////////////
        kept_branch_loops = []
        rejected_branch_loops []
        for loop in boundary_loops:
            length = 0.0
            for i in loop:
                length += bm.edges[i].calc_length()
            
            if length > 0.05:
                kept_branch_loops.append(loop.copy())
            else:
                rejected_branch_loops.append(loop.copy())
        
        # Delete EVERYTHING WE DONT NEED
        # ///////////////////////



        # This is used to ensure the BMesh state is correct?  Need to investigate...
        bm.select_flush_mode()   
        me.update()

        t1 = time.perf_counter()
        print("Runtime: %.15f sec" % (t1 - t0))  # Delete me later
        print("Boundary loops found: ",len(boundary_loops))  # Delete me later
        print("Emitter loops found: ",len(emitter_loops))  # Delete me later
        print("---END---")


        return {'FINISHED'}

classes = (
    GardenerPanel,
    GARDENER_OT_Replace_Twigs,
)

def register():
    for cls in classes:
        register_class(cls)
    
    bpy.types.Scene.gardener_thickness_preserve = FloatProperty(
        name="Thickness Preservation",
        description="Decides what branches should not be converted based on their thickness.  Branches equal to or thicker than this will be preserved.",
        min=0.0,
        max=30.0,
        default=1.0,
        update=WHITEBOX_Update_GridOpacity,
    )
    

def unregister():

    for cls in classes:
        unregister_class(cls)
