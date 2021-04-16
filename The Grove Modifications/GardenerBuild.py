
# This adds additional functions involved in replicating and transforming frond meshes.

import bpy, bmesh, time
from mathutils import Matrix, Vector, Quaternion
from bisect import bisect_left

# This code is responsible for drawing branches with an alternate method.
def build_gardener_branch(nodes, fronds, origin, scale_to_twig, tan, axi,
                          v, verts_append, faces_append, uvs_extend):
    
    frond_mesh = fronds[0][0]
    
    # Sort branch nodes by distance.
    i = 0
    d = 0.0
    node_dist = []
    while i < (len(nodes) - 1):
        p_diff = nodes[i + 1].pos - nodes[i].pos
        d += abs(p_diff.length)
        node_dist.append(d)
        i += 1


    for co in frond_mesh[0]:
        border_dist = take_boundaries(node_dist, co.x)
        i_0 = node_dist.index(border_dist[0])
        i_1 = node_dist.index(border_dist[1])

        n_0 = nodes[i_0]
        n_1 = nodes[i_1]
        tan_0 = tan[i_0]
        tan_1 = tan[i_1]
        axi_0 = axi[i_0]
        axi_1 = axi[i_1]
        pos_0 = n_0.pos
        pos_1 = n_1.pos

        lerp_range = (border_dist[1] - border_dist[0])
        lerp_val = (co.x - border_dist[0]) / lerp_range
        lerp_val = max(0, min(1, lerp_val))

        co_tan = tan_0.lerp(tan_1, lerp_val)
        co_axi = axi_0.lerp(axi_1, lerp_val)
        co_pos = pos_0.lerp(pos_1, lerp_val)

        mat = Matrix()
        mat[0][0:3] = co_tan
        mat[1][0:3] = co_axi
        mat[2][0:3] = co_tan.cross(co_axi)

        mat_scl = Matrix.Scale((1/ scale_to_twig), 4)

        co_tr = co @ mat
        co_tr = co_tr @ mat_scl
        new_co = co_tr + (co_pos - origin)
        verts_append(new_co)


    # Build a matrix given the tangent, axis and it's cross-product.
    # mat = Matrix()
    # mat[0][0:3] = tan[0]
    # mat[1][0:3] = axi[0]
    # mat[2][0:3] = tan[0].cross(axi[0])
    
    # for co in frond_mesh[0]:
    #     co_tr = co @ mat
    #     new_co = co_tr + pos_offset
    #     verts_append(new_co)

    for face in frond_mesh[1]:
        new_face = []
        for i in face:
            new_face.append(i + v)
        faces_append(new_face)

    for uv in frond_mesh[2]:
        uvs_extend(uv)

    return len(frond_mesh[0])

    

# PLACEHOLDER: Loads the requested type of twig geometry for use in building.
def load_frond_set(collection):

    """
    Loads a mesh-based object and returns it's individual components (minus normals).
    TODO: Add length and width data so frond substitions can be smarter.
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

            for vertex in me.vertices:
                vertices.append(vertex.co.copy())

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
                    material_layers.append(mat.name)
            
            frond_data.append([vertices, faces, uvs, mat_ids])

            id_index += len(mat_names)
    

    return [frond_data, material_layers]



def sort_vertices_on_x(verts):
    """
    Takes a set of vertices and returns a list of indexes sorted on their X value. 
    lowest is first.  Not sure if I need this anymore.    
    """

    indexes = []
    i = 0
    while i < len(vertices):
        indexes.append(i)
        i += 1

    indexed_t = tuple(zip(indexes, verts))
    sorted_t = sorted(indexed_t, key = lambda p: p[1].x)
    return [p[0] for p in sorted_tuple]


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