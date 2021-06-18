
# This adds additional functions involved in replicating and transforming frond meshes.

import bpy, bmesh, time
from mathutils import Matrix, Vector, Quaternion
from bisect import bisect_left

# This code is responsible for drawing branches with an alternate method.
def build_gardener_branch(nodes, fronds, frond_materials, 
                          origin, scale_to_twig, pos, tan, axi,
                          v, verts_append, faces_append, uvs_extend):
    
    

    #print("/n")
    #print("*** NEW FROND! ***")
    #print("/n")
    
    # Sort branch nodes by distance.
    i = 0
    d = 0.0
    node_dist = [0.0]
    
    while i < (len(nodes) - 1):
        p_diff = pos[i + 1] - pos[i]
        d += p_diff.length
        node_dist.append(d)
        i += 1
    
    # Build transform points
    i = 0
    transform_points = []
    while i < (len(nodes)):
        pos_i = pos[i]
        tan_i = tan[i]
        axi_i = axi[i]
        
        # NOTE - The tangents used are not a full direction towards the next node,
        # keep that in mind when making transformations
        mat_i = Matrix()
        mat_i[0][0:3] = tan_i
        mat_i[1][0:3] = axi_i
        mat_i[2][0:3] = tan_i.cross(axi_i)

        #mat_i.normalize()  # This didnt seem to help, presumably because it's already normalized.
        #offset_pos = pos_i - pos[0]
        #mat_i.col[3] = Vector((offset_pos.x, offset_pos.y, offset_pos.z, 1)) # Neither did this T _ T
        transform_points.append(mat_i)

        i += 1
    
    # Pick the right frond mesh
    
    frond_target = None
    target_diff = 0.0
    for j, frond in enumerate(fronds[0]):
        print(frond[4])
        
        diff = abs(d - frond[4].x)
        print(diff)
        if j == 0 or diff < target_diff:
            frond_target = frond
            target_diff = diff



    for co in frond_target[0]:
        border_dist = take_boundaries(node_dist, co.x)
        i_0 = node_dist.index(border_dist[0])
        i_1 = node_dist.index(border_dist[1])
        co_tr = co.copy()
        #print("Current Vertex Distance - ", co.x)
        co_tr.x = co_tr.x - border_dist[0]

        # print("X: ", co.x)
        # print("Indexes Found: ", i_0, i_1)

        mat_0 = transform_points[i_0]
        #mat_1 = transform_points[i_1]
        #print("MAT 0 - ", mat_0)
        #print("MAT 1 - ", mat_1)
        
        
        #lerp_range = (border_dist[1] - border_dist[0])
        #lerp_val = (co.x - border_dist[0]) / lerp_range
        #lerp_val = max(0, min(1, lerp_val))
        #mat_tf = mat_0.lerp(mat_1, lerp_val)
        #print("Lerp Value - ", lerp_val)
        
        #print("New TF - ", mat_tf)
        #print("Current Vertex - ", co_tr)
        
        new_co = co_tr @ mat_0
        new_co = new_co + pos[i_0]
        #print("New Vertex - ", new_co)
        #print("*"*20)
        verts_append(new_co)


    for face in frond_target[1]:
        new_face = []
        for i in face:
            new_face.append(i + v)
        faces_append(new_face)

    for uv in frond_target[2]:
        uvs_extend(uv)

    # Copies the same system for data layers as simulation_items to keep things uniform.
    # ...just in a clunkier way Q _ Q
    i = 0
    
    for mat_id in frond_target[3]:
        for id_list in frond_materials.values():
            if i == mat_id:
                id_list.append(1.0)
            else:
                id_list.append(0.0)
            i += 1
        i = 0

    return len(frond_target[0])

    

# PLACEHOLDER: Loads the requested type of twig geometry for use in building.
def load_frond_set(collection, scale_to_twig):

    """
    Loads a mesh-based object and returns it's individual components (minus normals).
    TODO: Add length and width data so frond substitions can be smarter.
    TODO: Make this a dictionary/tuple thing, otherwise data access will get bad fast.
    """

    frond_data = []
    material_layers = []
    id_index = 0

    for obj in collection.all_objects:
        if obj.type == 'MESH':

            # Obtain the flat mesh data.
            obj = bpy.data.objects[obj.name]
            me = obj.to_mesh(preserve_all_data_layers=False, depsgraph=None)
            uv_layer = me.uv_layers.active.data

            # Turn it into from_pydata-compatible datasets.
            vertices = []
            faces = []
            uvs = []
            mat_ids = []
            mat_names = []

            # Get bounds for the object
            bounds = get_bounds(obj)
            bound_dist = Vector((bounds.x.distance, bounds.y.distance, bounds.z.distance))
            bound_dist = bound_dist / scale_to_twig
            print(" B O U N D A R Y - ", bound_dist)

            mat_scl = Matrix.Scale((1/ scale_to_twig), 4)

            for vertex in me.vertices:
                co_scale = vertex.co.copy() @ mat_scl
                vertices.append(co_scale)

            for poly in me.polygons:
                f = []
                u = []

                for loop_index in poly.loop_indices:
                    f.append(me.loops[loop_index].vertex_index)
                    u.append(uv_layer[loop_index].uv.copy())
                
                faces.append(f)
                uvs.append(u)
                mat_ids.append(poly.material_index + id_index)

            for i, mat in enumerate(me.materials):

                if mat.name in material_layers:
                    new_id = material_layers.index(mat.name)

                    # Collapse all indexes higher than it, replace matches
                    for idx, item in enumerate(mat_ids):
                        if item == i:
                            mat_ids[idx] = new_id
                        elif item > i:
                            mat_ids[idx] = item - 1

                else:
                    mat_names.append(mat.name)
                    material_layers.append(mat.name)
            
            print("Frond Mat ID Count:", len(mat_ids))

            frond_data.append([vertices, faces, uvs, mat_ids, bound_dist])

            id_index += len(mat_names)
    

    return [frond_data, material_layers]

def get_bounds(obj):
    """
    Returns useful information from the bounds of an object.
    """

    local_coords = obj.bound_box[:]
    om = obj.matrix_world

    coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)


def sort_vertices_on_x(verts):
    """
    Takes a set of vertices and returns a list of indexes sorted on their X value. 
    lowest is first.  Not sure if I need this anymore.   

    NOTE - No longer used, here just in case.
    """

    indexes = []
    i = 0
    while i < len(verts):
        indexes.append(i)
        i += 1

    indexed_t = tuple(zip(indexes, verts))
    sorted_t = sorted(indexed_t, key = lambda p: p[1].x)
    return [p[0] for p in sorted_t]


def take_boundaries(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.

    Returns the closest number, and the number higher/lower than it.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return [myList[0], myList[1]]
    if pos == len(myList):
        return [myList[-2], myList[-1]]

    before = myList[pos - 1]
    after = myList[pos]
    return [before, after]