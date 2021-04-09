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
from bpy.props import IntProperty, FloatProperty

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
            
            # print("Current edge verts - ", e_step)
            # print(current_vertex)
            new_sel = [e_step.index]
            shared_face = True
            
            i = 0
            while i <= 63:
            
                ## Find what vertex linked with this one has three or less linked vertices.
                for ele in current_vertex.link_edges[:]:
                    if ele.is_boundary == True:
                        if ele.index != e_step.index:
                        
                            # print("Candidate found : ", ele)
                            new_sel.append(ele.index)
                            
                            e_step = ele
                            current_vertex = ele.other_vert(current_vertex)
                            # print("Next vertex : ", current_vertex)
                            
                            if target_edge.link_faces[0].index != ele.link_faces[0].index:
                                shared_face = False
                            
                            break
                
                if loop.edge.other_vert(loop.vert).index == current_vertex.index:
                    break
    
                i += 1

            return new_sel, shared_face


        def bmesh_get_connected(vert, hidden_verts):
    
            # The stack of vertex indexes we will end up with for our mesh element.
            vert_stack = [vert]
            last_search = [vert]
            
            while len(last_search) != 0:
                
                current_search = last_search.copy()
                last_search.clear()
                
                for search_vert in current_search:
                    for edge in search_vert.link_edges[:]:
                        
                        vert_c = edge.other_vert(search_vert)

                        if vert_c not in vert_stack:

                            # vert_c.select = True
                            vert_stack.append(vert_c)
                            last_search.append(vert_c)
            
            # Remove hidden verts from the list
            for hidden_v in hidden_verts:
                try: 
                    vert_stack.remove(hidden_v)
                except ValueError:
                    continue        

            return vert_stack
        
        

        # boop initial setup
        # ///////////////////////
        t0 = time.perf_counter()
        bpy.ops.object.mode_set(mode='EDIT')

        obj = context.edit_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.select_mode |= {'EDGE'}

        boundary_edge_stack = []

        for e in bm.edges:
            if e.is_boundary:
                boundary_edge_stack.append(e.index)
        
        bm.edges.ensure_lookup_table()

        # Fetch boundary and emitter loops
        # ///////////////////////
        boundary_loops = []
        emitter_loops = []

        while len(boundary_edge_stack) > 0:
            # print("next edge")
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
        t1 = time.perf_counter()
        rejected_branch_loops = []

        for loop in boundary_loops:
            length = 0.0
            for i in loop:
                length += bm.edges[i].calc_length()
            
            if length < 0.05:
                vertex_data = []
            
                for edge_index in loop:
                    edge = bm.edges[edge_index]
                    
                    for vert in edge.verts:
                        if vert not in vertex_data:
                            vertex_data.append(vert)

                rejected_branch_loops.append(vertex_data)
        
        
        rejected_emitter_loops = []

        for loop in emitter_loops:
            vertex_data = []

            for edge_index in loop:
                edge = bm.edges[edge_index]
                
                for vert in edge.verts:
                    if vert not in vertex_data:
                        vert.select = True
                        vertex_data.append(vert)

            rejected_emitter_loops.append(vertex_data)
        
        boundary_loops.clear()
        emitter_loops.clear()
            

        # For every rejected branch, cap the boundary, flip the
        # normal and get everything but the cap
        # ///////////////////////
        t2 = time.perf_counter()
        for reject in rejected_branch_loops:
            
            try:
                new_mesh_data = bmesh.ops.contextual_create(bm, geom=reject, mat_nr=0, use_smooth=False)
            except TypeError:
                continue

            new_face = new_mesh_data["faces"][0]
            bmesh.ops.reverse_faces(bm, faces=[new_face], flip_multires=False)

            # Then delete it!
            branch_geom = bmesh_get_connected(reject[0], reject)
            bmesh.ops.delete(bm, geom=branch_geom, context='VERTS')
        
        for reject in rejected_emitter_loops:
            bmesh.ops.delete(bm, geom=reject, context='VERTS')
        
        t3 = time.perf_counter()

        bmesh.update_edit_mesh(me, True)
        #bm.select_flush_mode()   
        me.update()
        bm.free()

        #bpy.ops.object.mode_set(mode='OBJECT')
        
        collect_time = t1 - t0
        vert_set_time = t2 - t1
        deletion_time = t3 - t2
        print("Collection Time: %.15f sec" % (collect_time))  
        print("Vertex Gatheting Time: %.15f sec" % (vert_set_time))  
        print("Deletion Time: %.15f sec" % (deletion_time))  

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
    )
    

def unregister():

    for cls in classes:
        unregister_class(cls)
