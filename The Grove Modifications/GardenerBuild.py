
# This adds additional functions involved in replicating and transforming frond meshes.

import bpy, bmesh, time
from mathutils import Matrix, Vector, Quaternion
from bisect import bisect_left

# This code is responsible for drawing branches with an alternate method.
def build_gardener_branch(nodes, fronds, frond_materials, 
                          origin, scale_to_twig, pos, tan, axi,
                          v, verts_append, faces_append, uvs_extend):
    
    
    
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
        
        diff = abs(d - frond[4].x)
        if j == 0 or diff < target_diff:
            frond_target = frond
            target_diff = diff

    # Create a matrix for stretching the target mesh, 
    # used to better fit the length of the branch.
    stretch_x = bpy.context.scene.gardener_stretch_factor_x
    stretch_yz = bpy.context.scene.gardener_stretch_factor_yz
    mat_stretch = Matrix()

    if stretch_x > 0:
        factor_x = ( ( (d / frond_target[4].x) - 1) * stretch_x) + 1
        axis_x = Vector((factor_x, 0, 0))
        axis_y = Vector((0, 1, 0))
        axis_z = Vector((0, 0, 1))

        if stretch_yz > 0:
            factor_y = ( ( (d / frond_target[4].x) - 1) * stretch_yz) + 1
            factor_z = ( ( (d / frond_target[4].x) - 1) * stretch_yz) + 1
            axis_y = Vector((0, factor_y, 0))
            axis_z = Vector((0, 0, factor_z))
        
        mat_stretch[0][0:3] = axis_x
        mat_stretch[1][0:3] = axis_y
        mat_stretch[2][0:3] = axis_z



    for co in frond_target[0]:
        co_tr = co.copy()

        if stretch_x > 0:
            co_tr = co_tr @ mat_stretch

        border_dist = take_boundaries(node_dist, co.x)
        i_0 = node_dist.index(border_dist[0])
        i_1 = node_dist.index(border_dist[1])
        co_tr.x = co_tr.x - border_dist[0]
        
        
        # Get the initial transform of the point we start from,
        # as well as two tangents used to smooth the rotation of 
        # our points.
        #
        # Causes distortion, will patch in later once fixed
        #
        mat_0 = transform_points[i_0]
        # tan_origin = tan[i_0]
        # tan_0 = ((tan[i_0])).normalized()
        # tan_1 = ((tan[i_1])).normalized()
        
        # if i_1 < len(tan) - 1:
        #     tan_1 = ((tan[i_0] + tan[i_1])).normalized()
        # if i_0 > 0:
        #     tan_0 = ((tan[i_0] + tan[i_0 - 1])).normalized()
        
        # # This lerp code has been verified!  V E R I F I E D
        # lerp_range = (border_dist[1] - border_dist[0])
        # lerp_val = (co.x - border_dist[0]) / lerp_range
        # lerp_val = max(0, min(1, lerp_val))
        # tan_lerp = tan_0.lerp(tan_1, lerp_val)
        
        # rotation_mat = rotate_align(tan_origin, tan_lerp)
        
        # co_tr_xb = co_tr.x
        # co_tr.x = 0
        # co_tr =  rotation_mat @ co_tr
        # co_tr.x += co_tr_xb
        
        co_tr = co_tr @ mat_0
        co_tr = co_tr + pos[i_0]
        verts_append(co_tr.copy())


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