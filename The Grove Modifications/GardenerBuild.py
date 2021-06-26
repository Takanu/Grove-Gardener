
# This adds additional functions involved in replicating and transforming frond meshes.

import bpy
from mathutils import Matrix, Vector, Quaternion
from numpy import array, take, empty, vstack
from bisect import bisect_left

def load_frond_set(collection, scale_to_twig):

    """
    Loads a mesh-based object and returns it's individual components (minus normals).
    TODO: Add width data so frond substitions can be smarter.
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

            frond_data.append([vertices, faces, uvs, mat_ids, bound_dist])

            id_index += len(mat_names)
    

    return [frond_data, material_layers]

def get_bounds(obj):
    """
    Returns useful information from the bounds of an object.
    Thanks zeffii!
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


def rotate_align(v1, v2):
    """
    Returns the matrix that would allow v1 to be rotated to become v2.
    
    Adapted from https://gist.github.com/kevinmoran/b45980723e53edeb8a5a43c49f134724
    """

    axis = v1.cross(v2);
    cosA = v1.dot(v2);
    k = 1.0 / (1.0 + cosA);
    
    rot_matrix = Matrix()
    rot_matrix[0][0] = (axis.x * axis.x * k) + cosA
    rot_matrix[0][1] = (axis.y * axis.x * k) - axis.z
    rot_matrix[0][2] = (axis.z * axis.x * k) + axis.y
    
    rot_matrix[1][0] = (axis.x * axis.y * k) + axis.z
    rot_matrix[1][1] = (axis.y * axis.y * k) + cosA
    rot_matrix[1][2] = (axis.z * axis.y * k) - axis.x

    rot_matrix[2][0] = (axis.x * axis.z * k) - axis.y
    rot_matrix[2][1] = (axis.y * axis.z * k) + axis.x
    rot_matrix[2][2] = (axis.z * axis.z * k) + cosA

    return rot_matrix;


def build_normal_reprojection(ob, scale_to_twig, hull_res, hull_expand):
    """
    Uses a mix of remeshing, scaling and Data Transfer operations to create
    better face corner normals for fronds.
    
    TODO - Add the ability to keep the hull mesh after creation, so people can see exactly what the addon is trying to do.
    """

    # i dont wan't to do this elsewhere, so just add the object to a fake
    # collection to consider it "registered"
    collection = bpy.data.collections.new("Gardener's Terrible Little Secret")
    bpy.context.scene.collection.children.link(collection)
    collection.objects.link(ob)

    # select tree and duplicate
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob 
    ob.select_set(True)

    bpy.ops.object.duplicate()
    ob_hull = bpy.context.active_object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob_hull 

    # add remesh modifier and apply
    bpy.ops.object.modifier_add(type='REMESH')
    remesh = ob_hull.modifiers['Remesh']
    remesh.mode = 'VOXEL'
    remesh.use_smooth_shade = True
    remesh.voxel_size = hull_res / scale_to_twig
    bpy.ops.object.modifier_apply({"object" : ob_hull}, modifier=remesh.name)
    
    # enter edit mode and shrink/fatten model
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    bpy.ops.transform.shrink_fatten(value=(hull_expand / scale_to_twig), 
        mirror=False, use_proportional_edit=False, snap=False, release_confirm=False)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # add another remesh modifier to smooth it out
    bpy.ops.object.modifier_add(type='REMESH')
    remesh = ob_hull.modifiers['Remesh']
    remesh.mode = 'VOXEL'
    remesh.use_smooth_shade = True
    remesh.voxel_size = hull_res / scale_to_twig
    bpy.ops.object.modifier_apply({"object" : ob_hull}, modifier=remesh.name)

    # select original tree
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob 
    ob.select_set(True)

    # add data transfer and apply
    ob.data.use_auto_smooth = True
    bpy.ops.object.modifier_add(type='DATA_TRANSFER')
    data_transfer = ob.modifiers['DataTransfer']
    data_transfer.vertex_group = "layer_frond"
    data_transfer.object = ob_hull
    data_transfer.use_loop_data = True
    data_transfer.data_types_loops = {'CUSTOM_NORMAL'}
    data_transfer.loop_mapping = 'NEAREST_POLYNOR'
    bpy.ops.object.modifier_apply({"object" : ob}, modifier=data_transfer.name)

    # this process adds sharp edges to everything that isnt the fronds due to auto-smooth,
    # we need to remove them.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='layer_frond')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.mark_sharp(clear=True)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # delete the trash and run away
    bpy.data.objects.remove(ob_hull, do_unlink=True)
    bpy.context.scene.collection.children.unlink(collection)
    bpy.data.collections.remove(collection)

    bpy.ops.object.select_all(action='DESELECT') 

def vertex_colors_layer_from_colors(ob, name, red, green, blue, alpha):
    """
    GARDENER - This adapts the Vertex Color code from The Grove to create a color layer where every color
    channel has one set of data.

    Original code Copyright (c) 2016 - 2021, Wybren van Keulen, The Grove.
    -------------------------------------------------------------------------
    Add a new named Vertex Colors layer to the given mesh object. Fill the layer with the given data, an array
    of floats. The list indexing matches the mesh's vertex indexing.

    Vertex colors can be used in Cycles materials with the Attribute node. They are very different from
    Vertex Groups. Similar to UV's, each corner of each face has a separate value. A vertex with four attached
    faces has 4 color values, one for each face.

    Blender stores Vertex Colors as layers in the object data. A layer is a list of tuples representing a color.
    The order of this list is defined by the object's mesh's loops list. Loops is a list of integers representing
    vertex indices for each face for each vertex in the face.

    This version is very different from all other attempts found on the internet. It was a puzzle to find
    a way to solve it without for loops. The solution uses numpy and is about 4x as fast as for loops. """

    vertex_colors = ob.data.vertex_colors.new(name=name)

    if vertex_colors is None:
        return False
    
    indices = empty([len(vertex_colors.data)], dtype=int)
    ob.data.loops.foreach_get("vertex_index", indices)

    indices = array(indices, dtype=int)
    ob.data.loops.foreach_get("vertex_index", indices)
    
    # There is probably a nicer soultion here, but I could not find it.
    rsort = take(red, indices)
    gsort = take(green, indices)
    bsort = take(blue, indices)
    asort = take(alpha, indices)
    rgba = vstack((rsort, gsort, bsort, asort)).T

    rgba = rgba.flatten()
    rgba = rgba.tolist()  # foreach_set is over twice as fast when using a regular list over a numpy array.
    vertex_colors.data.foreach_set("color", rgba)

    return True