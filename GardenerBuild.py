
# This adds additional functions involved in replicating and transforming frond meshes.

import bpy, bmesh, time
from mathutils import Matrix, Vector, Quaternion

# This code is responsible for drawing branches with an alternate method.
def build_gardener_branch(nodes, pos_offset, tan, axi,
                          v, verts_append, faces_append, uvs_extend):
    
    frond_mesh = load_twig_geom("Cube")

    # Build a matrix given the tangent, axis and it's cross-product.
    mat = Matrix()
    mat[0][0:3] = tan[0]
    mat[1][0:3] = tan[0].cross(axi[0])
    mat[2][0:3] = axi[0]

    twopi=6.2832
    curradius = nodes[0].radius
    
    for co in frond_mesh[0]:
        co_tr = co @ mat
        new_co = co_tr + pos_offset
        verts_append(new_co)

    for face in frond_mesh[1]:
        new_face = []
        for i in face:
            new_face.append(i + v)

        faces_append(new_face)
        uvs_extend([(1, 1), (1,1), (1,1), (1,1)])

    return len(frond_mesh[0])

    

# PLACEHOLDER: Loads the requested type of twig geometry for use in building.
def load_twig_geom(object_name):
    
    # Obtain the flat mesh data.
    obj = bpy.data.objects[object_name]
    mesh = obj.to_mesh(preserve_all_data_layers=False, depsgraph=None)

    # Turn it into from_pydata-compatible datasets.
    vertices = []
    faces = []

    for vertex in mesh.vertices:
        vertices.append(vertex.co)
    
    for face in mesh.polygons:
        faces.append(face.vertices[:])

    return [vertices, faces]