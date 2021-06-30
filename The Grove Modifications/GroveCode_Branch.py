


# INSTALLATION : Add this to the top of the Branch file (around line 21)

import bl_math
from numpy import array, amax, arange, concatenate
from numpy import delete as numpy_delete
from .GardenerBuild import take_boundaries


# -------------------------------------------------------

# This function is a modified version of build_branches_mesh, inside the Branch file.
#
# INSTALLATION : Replace the original definition inside Branch with this 
# and ensure the indentation is correct.
#
# This function is located at line at around line 1440 (depending on where you add the import
# statement above)


def build_branches_mesh(self, lateral_on_apical,
                        profile_resolution, profile_resolution_reduction, twist, u_repeat, texture_aspect_ratio, scale_to_twig,
                        root_distribution, root_shape, root_scale, root_bump, base_weight,
                        parent_previous_node, parent_node, parent_next_node, v, verts, faces, uvs, shape, layers, fronds, frond_materials, 
                        branch_index, branch_index_parent, branch_group, curr_trunk_distance,  trunk_distance_index, hierarchy,
                        origin, circles,
                        lateral_twig_age_limit, dead_twig_wither, branch_angle, branching, plagiotropism_buds, add_planar, 
                        wind_force, tree_age,
                        vector_zero=Vector((0.0, 0.0, 0.0)),
                        vector_z=Vector((0.0, 0.0, 1.0)),
                        vector_y=Vector((0.0, 1.0, 0.0)),
                        twopi=6.2832, spring_shape=False, wind_shape=False):
    """
    Create an adaptive mesh of branches with UV's and data layers.
    New and improved meshing of branches, no more using Blender's curves.
    Includes perfect UV control, twisting and roots!

    Variable v keeps track of the total number of vertices added. Used as an offset for creating faces
    between vertices.

    Add twig duplicator triangles straight into the branches mesh. This will make the entire tree one object.
    It will also make wind animation and vertex layers a lot easier.
    Use the lateral and apical vertex groups to distribute twigs from the right polygons.
    Let the Density parameter affect the amount of particles, but build all of the triangles, this will
    make the tree flexible for later editing.

    Option spring_shape builds the tree with last year's thicknesses and positions.
        It does use this year's thicknesses for resolution to keep the polycount stable.
        It skips building data layers.
    Option wind_shape builds without wasting time on UVs, faces and data layers.
        Just the new positions are interesting, everything else has been calculated already on a regular build.
    
    """

    # Randomize UV's for every branch.
    uv_offset_x = self.uv_offset_x
    uv_offset_y = self.uv_offset_y

    build_skeleton = False

    # TK NOTE - The next 200 lines or so are just for the smoothing of nodes, not relevant!

    # Smooth branching. Replace the base node with a fluent transition from the parent branch.
    nodes = []
    if parent_previous_node and not build_skeleton:

        # NODE 1.
        node = Node(parent_previous_node.direction)

        # Branch smoothing modulation.
        # No smoothing on new branches, full smoothing from 10cm.
        way_back = parent_previous_node.pos
        smooth = self.nodes[0].radius / 0.05
        if smooth > 1.0:
            smooth = 1.0
        smooth = smooth ** 0.7
        node.pos = smooth * way_back + (1.0 - smooth) * self.nodes[0].pos


        if spring_shape:  # Growth animation.
            # Fix sliding of the first node along the branch with recording.
            # Use exactly the same code as above for the summer shape, but then with the values of last year.
            way_back_last_year = parent_previous_node.pos_last_year
            smooth = self.nodes[0].radius_last_year / 0.05
            if smooth > 1.0:
                smooth = 1.0
            smooth = smooth ** 0.7
            node.pos = smooth * way_back_last_year + (1.0 - smooth) * self.nodes[0].pos_last_year

            node.pos_last_year = node.pos * 1.0
        node.weight = parent_previous_node.weight
        node.radius = parent_node.radius * 0.9

        node.radius_last_year = parent_node.radius_last_year * 0.9

        # Thickness is not used for building, just radius.
        # This line below allows smooth flowing of thickness data layer.
        node.thickness = parent_previous_node.thickness
        node.age = parent_previous_node.age
        node.photosynthesis = parent_previous_node.photosynthesis
        nodes.append(node)

        # NODE 2.

        # Below line skips the interpolation if the parent node is thicker than internode length.
        # At this point, this interpolation will have no effect, as it is all happening within the thick
        # parent branch. If this happens, apply a different kind of smoothing later on.
        # Check if the second node is within the thickness of the lead branch.
        if parent_next_node is None:
            lead_dir = parent_node.direction
        else:
            lead_dir = parent_next_node.pos - parent_node.pos
        sub_dir = self.nodes[1].pos - parent_node.pos

        lead_sub_angle = sub_dir.angle(lead_dir)
        distance_from_lead = cos((0.5 * pi) - lead_sub_angle) * sub_dir.length

        if distance_from_lead > parent_node.radius:  # * 1.2:  # or u_repeat == 4:  # * 0.7 So it kicks in a little earlier.
            node2 = Node(vector_zero)
            posa = node.pos + (self.nodes[1].pos - node.pos) / 2  # Halfway between node and node[1].
            posb = posa + (self.nodes[0].pos - posa) / 2  # Halfway between posa and node[0].
            node2.pos = posb

            if spring_shape:
                posa = node.pos_last_year + (self.nodes[1].pos_last_year - node.pos_last_year) / 2  # Halfway between node and node[1].
                posb = posa + (self.nodes[0].pos_last_year - posa) / 2  # Halfway between posa and node[0].
                node2.pos = posb
                node2.pos_last_year = posb * 1.0

            # Thickness is not used for building, just radius. Below line allows
            # smooth flowing of thickness data layer.
            node2.radius = (parent_previous_node.radius + self.nodes[0].radius) / 2.0
            node2.radius_last_year = (parent_previous_node.radius_last_year + self.nodes[0].radius_last_year) / 2.0  # WIP Growth animation.

            # Thickness is not used for building, just radius. So instead of setting it to the correct
            # radius * 2.0, set it so that it provides smooth flowing of thickness data layer.
            node2.thickness = parent_previous_node.thickness
            node2.age = parent_previous_node.age

            # Do not smooth much thinner sub branches, that will give an unnaturally thick transition.
            if self.nodes[1].radius / parent_node.radius < 0.25:
                node2.radius = self.nodes[1].radius
                node2.radius_last_year = self.nodes[1].radius_last_year
                node2.thickness = parent_previous_node.thickness
                node2.age = parent_previous_node.age

            node2.photosynthesis = parent_previous_node.photosynthesis
            node2.weight = parent_previous_node.weight
            nodes.append(node2)

            # NODE 3.

            if len(self.nodes) > 1:
                node3 = Node(vector_zero)
                node3.pos = self.nodes[0].pos + (self.nodes[1].pos - self.nodes[0].pos) / 2
                if len(self.nodes) > 2:
                    back_from_node_1 = self.nodes[1].pos + (self.nodes[1].pos - self.nodes[2].pos) / 2
                    node3.pos = (node3.pos * 2 + back_from_node_1) / 3
                
                if spring_shape:
                    node3.pos = self.nodes[0].pos_last_year + (self.nodes[1].pos_last_year - self.nodes[0].pos_last_year) / 2
                    if len(self.nodes) > 2:
                        back_from_node_1 = self.nodes[1].pos_last_year + (self.nodes[1].pos_last_year - self.nodes[2].pos_last_year) / 2
                        node3.pos = (node3.pos * 2 + back_from_node_1) / 3
                    
                    node3.pos_last_year = node3.pos * 1.0
                
                node3.weight = self.nodes[1].weight
                node3.thickness = self.nodes[0].thickness
                node3.radius = self.nodes[0].radius * 1.0
                node3.radius_last_year = self.nodes[0].radius_last_year
                node3.photosynthesis = self.nodes[0].photosynthesis
                # Thickness is not used for building, just radius. This provides smooth flowing of thickness data layer.
                node3.thickness = parent_node.thickness
                node3.age = parent_previous_node.age
                nodes.append(node3)
            
            # NODE 4 and on.
            nodes.extend(self.nodes[1:])
        else:
            # If the parent node radius is wider than the internode length, apply a different type of smoothing.
            # Node index 1 is then completely engulfed in the parent branch.

            node2 = Node(vector_zero)
            # node2.pos = parent_previous_node.pos + (self.nodes[0].pos - parent_previous_node.pos) / 2
            # R6 - Even smoother branching. Three lines below replace the line above.
            posa = (self.nodes[0].pos + self.nodes[1].pos) / 2
            node2.pos = posa
            if spring_shape:
                posa = (self.nodes[0].pos_last_year + self.nodes[1].pos_last_year) / 2
                node2.pos = posa
                node2.pos_last_year = node2.pos * 1.0
            node2.radius = self.nodes[0].radius * 1.0
            node2.radius_last_year = self.nodes[0].radius_last_year * 1.0
            node2.thickness = self.nodes[0].radius * 2.0
            node2.thickness = parent_previous_node.thickness * 1.0  # Thickness is not used for building, just radius. This provides smooth flowing of thickness data layer.
            node2.age = parent_previous_node.age * 1.0
            # Do not smooth much thinner sub branches, that will give an unnaturally thick transition.
            if self.nodes[1].radius / parent_node.radius < 0.5:
                node2.radius = self.nodes[1].radius
                node2.radius_last_year = self.nodes[1].radius_last_year
                node2.thickness = node2.radius * 2.0
                node2.thickness = parent_previous_node.thickness * 1.0
                node2.age = parent_previous_node.age * 1.0
                node2.photosynthesis = parent_previous_node.photosynthesis * 1.0
            nodes.append(node2)

            # To keep the number of nodes constant during wind animation, add an extra node so
            # that this smoothing method has the same number of nodes.
            node3 = Node(vector_zero)  # Direction doesn't matter, this node only exists during build.
            node3.pos = (self.nodes[1].pos + node2.pos) / 2.0  # Medium position.
            if spring_shape:
                node3.pos = (self.nodes[1].pos_last_year + node2.pos_last_year) / 2.0
                node3.pos_last_year = node3.pos * 1.0
            node3.radius = (self.nodes[1].radius + node2.radius) / 2.0
            node3.radius *= 1.0
            node3.radius_last_year = (self.nodes[1].radius_last_year + node2.radius_last_year) / 2.0  # WIP Growth animation.
            node3.thickness = self.nodes[1].thickness * 1.0  # node3.radius * 2.0
            node3.age = parent_previous_node.age
            node3.photosynthesis = parent_previous_node.photosynthesis * 1.0
            nodes.append(node3)

            nodes.extend(self.nodes[1:])

            # The thicker the sub branch, the thicker the first node and the more it gets pulled back along
            # the parent branch.
            ratio = nodes[1].radius / parent_node.radius
            nodes[0].pos = parent_previous_node.pos * ratio + (1.0 - ratio) * parent_node.pos
            # Reduce radius on first node, but first adjust radius so that its effect is bigger.
            # So only really thin branches will get thinner.
            ratio = pow(ratio, 0.5)
            nodes[0].radius = parent_node.radius * ratio + (1.0 - ratio) * nodes[1].radius

            nodes[0].pos = parent_previous_node.pos.copy()
            if spring_shape:
                nodes[0].pos = parent_previous_node.pos_last_year.copy()

            if nodes[1].radius / parent_node.radius > 0.5:
                nodes[1].radius *= 1.3

            nodes[1].radius = parent_node.radius
            nodes[1].pos = parent_node.pos
            if spring_shape:
                nodes[1].pos = parent_node.pos_last_year
    
    else:
        nodes = self.nodes
    
    if self.is_trunk:
        # If the first node's direction isn't pointing straight up, prepend a root node to ensure a flush base.
        first_node = self.nodes[0]
        if first_node.direction.x != 0.0 or first_node.direction.y != 0.0:
            root_node = Node(Vector((0.0, 0.0, 0.1)))
            deep = first_node.radius * 1.0
            if deep > 0.05:
                deep = 0.05
            deep = Vector((0.0, 0.0, deep))
            root_node.pos = first_node.pos - deep
            root_node.pos_last_year = root_node.pos
            root_node.thickness = first_node.thickness
            root_node.age = first_node.age
            root_node.radius = first_node.radius
            root_node.radius_last_year = first_node.radius_last_year
            nodes = [root_node] + self.nodes
        else:
            nodes = self.nodes
    
    # DEBUG: Enable to skip smoothing.
    # nodes = self.nodes


    # TK NOTE - Okay the smoothing has ended, this is where more important stuff happens.

    number_of_nodes = len(nodes)
    circle = []
    previous_y = uv_offset_y
    current_y = uv_offset_y

    verts_append = verts.append
    verts_extend = verts.extend
    faces_append = faces.append
    uvs_extend = uvs.extend
    shape_extend = shape.extend

    do_layers = not (wind_shape or spring_shape)
    
    if do_layers:
        layers_shade_extend = layers['layer_shade'].extend
        layers_thickness_extend = layers['layer_thickness'].extend
        layers_age_extend = layers['layer_age'].extend
        layers_weight_extend = layers['layer_weight'].extend
        layers_power_extend = layers['layer_power'].extend
        layers_health_extend = layers['layer_health'].extend
        layers_dead_extend = layers['layer_dead'].extend
        layers_pitch_extend = layers['layer_pitch'].extend
        layers_apical_extend = layers['layer_apical'].extend
        layers_upward_extend = layers['layer_upward'].extend
        layers_dead_twig_extend = layers['layer_dead_twig'].extend  
        layers_lateral_extend = layers['layer_lateral'].extend
        layers_branch_index_extend = layers['layer_branch_index'].extend
        layers_branch_index_parent_extend = layers['layer_branch_index_parent'].extend
        
        # GARDENER - Gardener-specific data layers
        layers_frond_extend = layers['layer_frond'].extend
        layer_height_extend = layers['layer_height'].extend
        layer_trunk_distance_extend = layers['layer_trunk_distance'].extend
        layer_branch_distance_extend = layers['layer_branch_distance'].extend
        layer_branch_group_extend = layers['layer_branch_group'].extend

        # Prevent division by zero when creating vertex groups.
        if base_weight == 0.0:
            base_weight = 0.0001

    last_node_index = len(nodes) - 1
    cur_twist = 0.0

    # Reduce repeat with branch thickness.
    repeat = int(u_repeat * self.nodes[0].thickness)
    if repeat < 1:
        repeat = 1
    
    # TK NOTE - USEFUL DATA FOR ALL NODES IN THE CURRENT BRANCH CALCULATED HERE!

    # GARDENER - Set some values for easy access.
    gardener_reduce_el = bpy.context.scene.gardener_reduce_edgeloops
    gardener_reduce_el_value = bpy.context.scene.gardener_edgeloop_reduce_factor
    gardener_use_fronds = bpy.context.scene.gardener_use_fronds
    gardener_replace_type = bpy.context.scene.gardener_frond_replace_type
    

    # GARDENER - Does Grove Gardener need to intervene?  DECIDE NOW.
    thickness_intervention_value = bpy.context.scene.gardener_thickness_cutoff
    hierarchy_intervention_value = bpy.context.scene.gardener_hierarchy_level
    gardener_intervention = False

    if gardener_use_fronds is True:
        if gardener_replace_type == 'Thickness': 
            if self.nodes[0].thickness < thickness_intervention_value:
                gardener_intervention = True
        elif gardener_replace_type == 'Hierarchy':
            if hierarchy >= hierarchy_intervention_value:
                gardener_intervention = True
        elif gardener_replace_type == 'HierarchyHybrid':
            if hierarchy >= hierarchy_intervention_value:
                if self.nodes[0].thickness < thickness_intervention_value:
                    gardener_intervention = True
    
    # Calculate tangent and axis for each node.
    pos = []  # pos
    tan = []  # tangent
    axi = []  # axis
    dir = []  # direction (like tangent, but has length)
    dist = [0.0] # distances (calculated using direction)

    # this is slightly modified to remove references to variables not
    # currently applicable.

    last_node_index = len(nodes) - 1
    last_direction = nodes[1].pos - nodes[0].pos
    cur_twist = 0.0

    # Defines what range of nodes the smoothing process uses.
    # 3 seems to work so far, this solution requires more effort though
    smooth_range = 3
    if smooth_range > len(nodes):
        smooth_range = len(nodes)

    # This defines how much corners are smoothed, proportional to the
    # sharpness of each node
    smooth_value = bpy.context.scene.gardener_smooth_factor
    
    for j, n in enumerate(nodes):
        
        tangent = Vector()
        direction = Vector()

        if spring_shape:
            pos.append(n.pos_last_year)

            if j == last_node_index:
                direction = last_direction
            else:
                direction = nodes[j + 1].pos - n.pos
        
        # No smooth value or Gardener Build?  No problem.
        elif smooth_value == 0 or gardener_intervention is False:
            pos.append(n.pos)

            if j == last_node_index:
                direction = last_direction
            else:
                direction = nodes[j + 1].pos - n.pos

            if j == 0:
                tangent = direction
            else:
                tangent = (direction + last_direction) / 2.0
        
        # GARDENER - If we have a smoothing value, we have to do a LOT more.
        else:

            if j >= last_node_index - smooth_range:
                smooth_range -= 1

            # First and last positions require little change.
            if j == 0:
                pos.append(n.pos)
            
            # If we're at the last index we need nothing more than 
            # the last tangent
            elif j == last_node_index:
                direction = last_direction
                tangent = direction
            
            # If we're at the penultimate index, we can't use trigonometry
            # and just have to set the last position
            elif j == last_node_index - 1:
                pos.append(nodes[j + 1].pos)
                direction = nodes[j + 1].pos - pos[j]
                tangent = direction
            
            # Otherwise we need both the current tangent and the next position
            # derived from it.
            #
            # This finds a rotated version of a direction that points towards
            # the position afterwards, using trigonometry to keep the lengths
            # proportional.
            #
            if j < last_node_index - 1:
                current_direction = nodes[j + 1].pos - pos[j]
                next_direction = nodes[j + smooth_range].pos - nodes[j + 1].pos
                
                unit_0 = current_direction.normalized()
                unit_1 = next_direction.normalized()
                dot = unit_0.dot(unit_1)
                sharpness = ((dot * -1) + 1) / 2
                lerp = min((sharpness * smooth_value), 1)

                # Once we have our lerp value, we need a projection axis
                # with which we can collapse this into two dimensions.
                p_0 = pos[j]
                p_1 = nodes[j + 1].pos
                p_2 = nodes[j + smooth_range].pos
                v_0 = p_1 - p_0
                v_1 = p_2 - p_0
                z_axis = v_0.cross(v_1)
                y_axis = v_0.cross(z_axis)
                
                trig_mat = Matrix()
                trig_mat[0][0:3] = v_0.normalized()
                trig_mat[1][0:3] = y_axis.normalized()
                trig_mat[2][0:3] = z_axis.normalized()
                
                # Transform the vectors we need for trigonometry
                v_A = (v_0 @ trig_mat).xy
                v_B = (v_1 @ trig_mat).xy
                
                # Get the angle between, and then solve for v_B's true length.
                angle = v_A.angle(v_B)
                len_B = v_A.length * cos(angle)
                
                # Turn v_1 into a unit vector and multiply by the length,
                # we're finally done!
                d_unit = v_1.normalized()
                max_direction = Vector((d_unit.x * len_B, d_unit.y * len_B, d_unit.z * len_B))
                direction = current_direction.lerp(max_direction, lerp)
                tangent = direction
                pos.append(pos[j] + direction)

        
        tangent.normalize()
        tan.append(tangent)
        dir.append(direction)
        last_direction = direction

        # GARDENER - This didn't work T _ T
        # if j != 0:
        #     dist.append(dist[-1] + direction.length)
    
    # Distance calculation
    i = 0
    d = 0.0
    while i < (len(nodes) - 1):
            p_diff = pos[i + 1] - pos[i]
            d += p_diff.length
            dist.append(d)
            i += 1

    # Axis calculations
    for j, n in enumerate(nodes):
        
        direction = dir[j]
        # axis.
        if j == 0:
            axis = direction.to_track_quat('X', 'Z') @ Vector((0.0, 1.0, 0.0))
            axis.normalize()
        else:
            axis = last_direction.cross(direction).normalized()
            if axis.length == 0.0:
                axis = Vector((0.0, 1.0, 0.0))
        axi.append(axis)

        last_direction = direction * 1.0
    
    # Minimize twisting around the tangent.
    for j, n in enumerate(nodes):
        if j == 0:
            continue

        # Reflect previous nodes's tangent and axis of rotation onto the current point.
        # through the plane at the point in the middle.
        v1 = pos[j] - pos[j - 1]
        c1 = v1.dot(v1)

        if v1.length == 0.0:
            print(str(j) + ' out of ' + str(len(nodes)))
            print('zerooooooooo')
        
        axi_flipped = axi[j - 1] - (2 / c1) * v1.dot(axi[j - 1]) * v1
        tan_flipped = tan[j - 1] - (2 / c1) * v1.dot(tan[j - 1]) * v1

        # Second reflection over a plane at the current point,
        # to align the frame tangent with the curve tangent again.
        v2 = tan[j] - tan_flipped
        c2 = v2.dot(v2)

        axi[j] = axi_flipped - v2 * (2 / c2 * v2.dot(axi_flipped))

    # Smooth out extreme thicknesses steps for a nice taper.
    # WATCH OUT: This messes up wind animation! Repeated building adds thickness!
    # It strengthens branches and lessens bending over time, causing the loop to stutter.
    if not wind_shape:
        for o in range(len(nodes)):
            if o < 5 or o == len(nodes) - 1:
                continue
            median_radius = (nodes[o - 1].radius + nodes[o + 1].radius) / 2
            if nodes[o].radius < median_radius:
                nodes[o].radius = median_radius * 1


    # ////////////////////////////////////////////////////////////////////////
    # -----------------------------------------------------------------------
    # ////////////////////////////////////////////////////////////////////////

    # GARDENER - If it intervenes, its time to perform the "real" drawing code.
    gardener_loop_inc = (1 - gardener_reduce_el_value) / 10
    gardener_cur_reduc_val = gardener_reduce_el_value
    disable_twigs = gardener_intervention
    
    if gardener_intervention is True:
        
        # preserve the pitch value of the last node.
        j = len(nodes) - 1
        n = nodes[-1]
        radius = nodes[0].radius
        branch_length = dist[-1]            
        # Build transform points
        i = 0
        node_tf_points = []
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

            node_tf_points.append(mat_i)

            i += 1
        
        # Pick the right frond mesh
        frond_target = None
        target_diff = 0.0
        for j, frond in enumerate(fronds[0]):
            
            diff = abs(branch_length - frond[4].x)
            if j == 0 or diff < target_diff:
                frond_target = frond
                target_diff = diff

        # Create a matrix for stretching the target mesh, 
        # used to better fit the length of the branch.
        stretch_x = bpy.context.scene.gardener_stretch_factor_x
        stretch_yz = bpy.context.scene.gardener_stretch_factor_yz
        mat_stretch = Matrix()

        if stretch_x > 0:
            factor_x = ( ( (branch_length / frond_target[4].x) - 1) * stretch_x) + 1
            axis_x = Vector((factor_x, 0, 0))
            axis_y = Vector((0, 1, 0))
            axis_z = Vector((0, 0, 1))

            if stretch_yz > 0:
                factor_y = ( ( (branch_length / frond_target[4].x) - 1) * stretch_yz) + 1
                factor_z = ( ( (branch_length / frond_target[4].x) - 1) * stretch_yz) + 1
                axis_y = Vector((0, factor_y, 0))
                axis_z = Vector((0, 0, factor_z))
            
            mat_stretch[0][0:3] = axis_x
            mat_stretch[1][0:3] = axis_y
            mat_stretch[2][0:3] = axis_z


        for co in frond_target[0]:
            co_tr = co.copy()

            if stretch_x > 0:
                co_tr = co_tr @ mat_stretch

            border_dist = take_boundaries(dist, co.x)
            i_0 = dist.index(border_dist[0])
            i_1 = dist.index(border_dist[1])
            co_tr.x = co_tr.x - border_dist[0]

            # Used to interpolate layer data between the previous and next node.
            lerp_range = (border_dist[1] - border_dist[0])
            lerp_val = (co.x - border_dist[0]) / lerp_range
            lerp_val = max(0, min(1, lerp_val))
            
            
            # Get the initial transform of the point we start from,
            # as well as two tangents used to smooth the rotation of 
            # our points.
            
            mat_0 = node_tf_points[i_0]
            tan_origin = tan[i_0]
            tan_0 = ((tan[i_0])).normalized()
            tan_1 = ((tan[i_1])).normalized()
            

            # This ended up causing distortion, will patch in later once fixed
            # if i_1 < len(tan) - 1:
            #     tan_1 = ((tan[i_0] + tan[i_1])).normalized()
            # if i_0 > 0:
            #     tan_0 = ((tan[i_0] + tan[i_0 - 1])).normalized()
            # tan_lerp = tan_0.lerp(tan_1, lerp_val)
            
            # rotation_mat = rotate_align(tan_origin, tan_lerp)
            
            # co_tr_xb = co_tr.x
            # co_tr.x = 0
            # co_tr =  rotation_mat @ co_tr
            # co_tr.x += co_tr_xb
            
            co_tr = co_tr @ mat_0
            co_tr = co_tr + pos[i_0]
            verts_append(co_tr.copy())

            if do_layers:
                number = 1
                n_0 = nodes[i_0]
                n_1 = nodes[i_1]
                v_thickness = bl_math.lerp(n_0.thickness, n_1.thickness, lerp_val)
                v_age = bl_math.lerp(n_0.age, n_1.age, lerp_val)
                v_weight = bl_math.lerp(n_0.weight, n_1.weight, lerp_val)
                v_photosys = bl_math.lerp(n_0.photosynthesis, n_1.photosynthesis, lerp_val)
                v_height = bl_math.lerp(n_0.pos.z, n_1.pos.z, lerp_val)
                pitch_tan = tan_0.lerp(tan_1, lerp_val)
                pitch = 1.0 - (vector_z.angle(pitch_tan, 0.0) / pi)
                length_fract = co.x / frond_target[4].x
                dist_to_trunk = curr_trunk_distance + dist[i_0] + (lerp_range * lerp_val)

                layers_shade_extend([self.shade] * number)
                layers_thickness_extend([v_thickness] * number)
                layers_age_extend([v_age / tree_age] * number)
                layers_weight_extend([v_weight / base_weight] * number)
                layers_power_extend([self.power] * number)
                layers_health_extend([pow(v_photosys, 0.2)] * number)
                if self.dead:
                    layers_dead_extend([1.0] * number)
                else:
                    layers_dead_extend([0.0] * number)
                layers_pitch_extend([pitch] * number)
                layers_apical_extend([0.0] * number)
                layers_upward_extend([0.0] * number)
                layers_dead_twig_extend([0.0] * number)
                layers_lateral_extend([0.0] * number)
                layers_branch_index_extend([branch_index] * number)
                layers_branch_index_parent_extend([branch_index_parent] * number)

                # GARDENER - Extra layers
                layers_frond_extend([1.0] * number)
                layer_height_extend([v_height] * number)
                if self.is_trunk:
                    layer_trunk_distance_extend([0] * number)
                else:
                    layer_trunk_distance_extend([dist_to_trunk] * number)
                layer_branch_distance_extend([length_fract] * number)
                layer_branch_group_extend([branch_group] * number)


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
        
        # Populate data layers
        v += len(frond_target[0])
        

    # GARDENER - Standard branch build code.
    # Draw current node's profile and connect it to the previous profile with faces.
    else:

        for j, n in enumerate(nodes):
            aspect = texture_aspect_ratio * repeat

            # GARDENER - First attempt at reducing loop count by skipping out of nodes early.
            # TODO: This break wind and recording and it isnt really elegant.
            if gardener_reduce_el == True:

                if j > 1 and j != (len(nodes) - 1):
                    
                    dot = last_loop_tan.dot(tan[j]) / (last_loop_tan.length * tan[j].length)
                    print(dot)
                    print(gardener_cur_reduc_val)
                    print("*"*50)
                    
                    if dot > gardener_cur_reduc_val:
                        if len(n.sub_branches) == 0:
                            # Everytime we skip a loop, the threshold gets higher
                            gardener_cur_reduc_val += gardener_loop_inc
                            previous_y = current_y
                            if j != 0:
                                current_y += aspect / circumference * abs((n.pos_last_year - nodes[j - 1].pos_last_year).length)
                            continue        
                    else:
                        last_loop_tan = tan[j]
                        gardener_cur_reduc_val = gardener_reduce_el_value
                
                else:
                    last_loop_tan = tan[j]
            

            if spring_shape: 
                pos_offset = n.pos_last_year - origin
                radius = n.radius_last_year
                circumference = 2 * pi * radius
                previous_y = current_y
                if j != 0:
                    current_y += aspect / circumference * abs((n.pos_last_year - nodes[j - 1].pos_last_year).length)
                
            else:
                pos_offset = n.pos - origin
                radius = n.radius
                circumference = 2 * pi * n.radius
                previous_y = current_y
                if j != 0:
                    current_y += aspect / circumference * abs((n.pos - nodes[j - 1].pos).length)

            # Scale root of the trunk.
            if self.is_trunk:
                root_scale_reach = root_distribution * number_of_nodes
                if j < root_scale_reach:
                    x = 1.0 - (j / root_scale_reach)
                    y = pow(x, root_shape * 75.0)
                    multiplier = y * (root_scale - 1.0)
                    radius += radius * multiplier

                    amount = multiplier * 0.2 * root_bump * radius
            
            pitch = 1.0 - (vector_z.angle(tan[j], 0.0) / pi)  # Used for pitch data layer.

            if j > 0:
                cur_twist += twist

            # Reduce profile resolution on thinner branches, imited to one vertex per node. Minimum of 3 vertices.
            cur_res = profile_resolution * n.thickness
            if j == 0:
                # Start with the original first node's thickness, without the nodes added for smoothing.
                # Without this the different smoothing methods will mess up building with wind.
                cur_res = profile_resolution * self.nodes[0].thickness
            cur_res = profile_resolution_reduction * cur_res + (1.0 - profile_resolution_reduction) * profile_resolution
            cur_res = int(cur_res)
            if cur_res < 3:
                cur_res = 3
            # The first node has no previous resolution, set it equal to the current resolution.
            if j == 0:
                prev_res = cur_res
            elif cur_res < prev_res - 1:
                cur_res = prev_res - 1
            elif cur_res == 3 and prev_res == 4:
                # When the resolution steps down from 4 to 3, the tesselation of the first quad produces ugly triangles.
                # Very visible with high polygon reduction. Fix this by slightly twisting back.
                cur_twist += 0.5
            elif cur_res > prev_res:
                # This can happen because we're starting with the original first node's thickness and not the smoothed nodes.
                # Then for the following nodes, I take the smoothed node's thickness which is thicker.
                cur_res = prev_res
            
            if cur_res > profile_resolution:
                cur_res = profile_resolution * 1
            
            # Use pre-calculated circles for a speed-up.
            circle = circles[cur_res]

            # GARDENER - Variable to keep faces indexed.
            face_number = 0

            if build_skeleton:
                cur_res = 1

            for i in range(cur_res):
                a = (i - 1) / cur_res * repeat + uv_offset_x
                b = i / cur_res * repeat + uv_offset_x
                c = (1 / prev_res) * repeat

                # Root shape.
                if self.is_trunk:
                    curradius = radius + amount * (1.0 + 0.5 * sin(i * 6 / cur_res * twopi))
                    curradius += amount * (1.0 + 0.5 * cos(i * 9 / cur_res * twopi)) * 0.5
                else:
                    curradius = radius

                if build_skeleton:
                    curradius = 0.0

                # Rotate the normal of the node along the tangent to draw the circle points.
                co = Quaternion(tan[j], (i / cur_res) * twopi + cur_twist) @ (axi[j] * curradius) + pos_offset

                if wind_shape or spring_shape:
                    shape_extend(co)
                if not wind_shape:
                    verts_append(co)
                    v += 1

                    # Create faces between vertices.
                    if j > 0 and i > 0:
                        offset = v - 1
                        faces_append((offset - 1 - cur_res,
                                    offset - cur_res,
                                    offset,
                                    offset - 1))
                        face_number += 1

                        if prev_res == cur_res:
                            uvs_extend([(a, previous_y),
                                        (b, previous_y),
                                        (b, current_y),
                                        (a, current_y)])

                        elif prev_res == cur_res + 1:
                            uvs_extend([((i - 1) / prev_res * repeat + uv_offset_x + ((1 / prev_res) * repeat), previous_y),
                                        (i / prev_res * repeat + uv_offset_x + ((1 / prev_res) * repeat), previous_y),
                                        (i / cur_res * repeat + uv_offset_x, current_y),
                                        ((i - 1) / cur_res * repeat + uv_offset_x, current_y)])

            if j > 0 and not wind_shape:
                # Close the loop by creating the last face between the last vertices
                # and the first vertices in this loop.

                move_back_x = repeat  # Shift the triangle and slanted rectangle to the left to fix the jagged border of UV maps.

                offset = v - 1 - i

                a = i / cur_res * repeat + uv_offset_x
                b = repeat + uv_offset_x
                c = (1 / prev_res) * repeat

                if prev_res == cur_res and cur_res != 2:  # LOD
                    faces_append((offset - 1,
                                offset - cur_res,
                                offset,
                                offset + cur_res - 1))
                    face_number += 1

                    uvs_extend([(a - move_back_x, previous_y),
                                (b - move_back_x, previous_y),
                                (b - move_back_x, current_y),
                                (a - move_back_x, current_y)])

                # Step down resolution. Fill the gap with a triangle.
                elif prev_res == cur_res + 1:
                    prev_a = (i + 1) / prev_res * repeat + uv_offset_x

                    faces_append((offset - cur_res - 1,
                                offset - cur_res,
                                offset,
                                offset + cur_res - 1))
                    face_number += 1

                    uvs_extend([(prev_a + c - move_back_x, previous_y),
                                (b + c - move_back_x, previous_y),
                                (b - move_back_x, current_y),
                                (a - move_back_x, current_y)])

                    faces_append((offset - 1,
                                offset - cur_res - 1,
                                offset + cur_res - 1))
                    face_number += 1

                    uvs_extend([(prev_a - move_back_x, previous_y),
                                (b - move_back_x, previous_y),
                                (a - move_back_x, current_y)])

            if j == last_node_index:
                if cur_res == 2 and i == 1: # LOD, allow 2 resolution.
                    pass
                else:
                    # Cap the tip.
                    if wind_shape or spring_shape:
                        shape_extend(pos_offset)
                    if not wind_shape:
                        verts_append(pos_offset)
                        v += 1

                        for i in range(cur_res):
                            if i == cur_res - 1:
                                faces_append((v - 2,
                                            v - 2 - i,
                                            v - 1))
                                face_number += 1

                                uvs_extend([(0.5 * circle[0].x + 0.5, 0.5 * circle[0].y + 0.5),
                                            (0.5 * circle[i].x + 0.5, 0.5 * circle[i].y + 0.5),
                                            (0.5, 0.5)])
                            else:
                                faces_append((v - 3 - i,
                                            v - 2 - i,
                                            v - 1))
                                face_number += 1

                                uvs_extend([(0.5 * circle[i + 1].x + 0.5, 0.5 * circle[i + 1].y + 0.5),
                                            (0.5 * circle[i].x + 0.5, 0.5 * circle[i].y + 0.5),
                                            (0.5, 0.5)])
            
            # GARDENER - Moved numbers here as Gardener needs these!
            if j == last_node_index:
                number = cur_res + 1
            else:
                number = cur_res

            if cur_res == 2:
                number = cur_res  # LOD

            if do_layers:
                layers_shade_extend([self.shade] * number)
                layers_thickness_extend([n.thickness] * number)
                layers_age_extend([n.age / tree_age] * number)
                layers_weight_extend([n.weight / base_weight] * number)
                layers_power_extend([self.power] * number)
                layers_health_extend([pow(n.photosynthesis, 0.2)] * number)
                if self.dead:
                    layers_dead_extend([1.0] * number)
                else:
                    layers_dead_extend([0.0] * number)
                layers_pitch_extend([pitch] * number)
                layers_apical_extend([0.0] * number)
                layers_upward_extend([0.0] * number)
                layers_dead_twig_extend([0.0] * number)
                layers_lateral_extend([0.0] * number)
                layers_branch_index_extend([branch_index] * number)
                layers_branch_index_parent_extend([branch_index_parent] * number)

                # GARDENER - Additional layers
                layers_frond_extend([0.0] * number)
                layer_height_extend([n.pos.z] * number)
                if self.is_trunk:
                    layer_trunk_distance_extend([0.0] * number)
                else:
                    layer_trunk_distance_extend([curr_trunk_distance + dist[j]] * number)
                layer_branch_distance_extend([0.0] * number)
                layer_branch_group_extend([branch_group] * number)
            
            # Material indexes for frond meshes are counted differently.
            if gardener_use_fronds:
                for id_list in frond_materials.values():
                    id_list.extend([0.0] * face_number)


            prev_res = cur_res
    
    # TK NOTE - Apical and Lateral Twig distribution.

    # Skip distributing twigs on dead branches.
    # if not self.dead:
    duplicator = [Vector((0.0, -0.001, -0.001)),
                    Vector((0.0, 0.001, -0.001)),
                    Vector((0.0, 0.000, 0.001))]

    last_node = self.nodes[-1]
    if last_node.age < 4 and disable_twigs is False:
        # Add Apical Twig.
        direc = last_node.pos - self.nodes[-2].pos

        branch_mat = two_point_transform(vector_zero, direc)
        twig_matrix = Matrix.Translation(last_node.pos) @ branch_mat

        if spring_shape:
            twig_matrix = Matrix.Translation(last_node.pos_last_year) @ branch_mat

        if wind_shape or spring_shape:
            shape_extend(twig_matrix @ duplicator[0] - origin)
            shape_extend(twig_matrix @ duplicator[1] - origin)
            shape_extend(twig_matrix @ duplicator[2] - origin)
        
        if not wind_shape:
            verts_extend(twig_matrix @ vert - origin for vert in duplicator)
            v += 3

            faces_append((v - 3, v - 2, v - 1))
            uvs_extend([(0.5, 0.5),
                        (0.5, 0.5),
                        (0.5, 0.5)])

            number = 3

            if do_layers:
                
                # Upward twigs, if pointing upward more than a set angle, use an upward twig instead of a regular apical twig.
                if self.dead or last_node.dead:
                    layers_apical_extend([0.0] * number)
                    layers_lateral_extend([0.0] *number)
                    layers_upward_extend([0.0] * number)
                    layers_dead_twig_extend([1.0] * number)
                else:
                    direction_flat = direction.copy()
                    direction_flat.z = 0.0
                    if direction.angle(direction_flat, 3.14159) > 0.8 and direction.z > 0.0:  # 70 degrees is 1.2. 1.0 works well.
                        layers_apical_extend([0.0] * number)
                        layers_upward_extend([1.0] * number)
                    else:
                        layers_apical_extend([1.0] * number)
                        layers_upward_extend([0.0] * number)
                    layers_lateral_extend([0.0] * number)
                    layers_dead_twig_extend([0.0] * number)

                layers_shade_extend([self.shade] * number)
                layers_thickness_extend([last_node.thickness] * number)
                layers_age_extend([last_node.age / tree_age] * number)
                layers_weight_extend([last_node.weight / base_weight] * number)
                layers_power_extend([self.power] * number)
                layers_health_extend([pow(last_node.photosynthesis, 0.2)] * number)
                if self.dead:
                    layers_dead_extend([1.0] * number)
                else:
                    layers_dead_extend([0.0] * number)
                layers_pitch_extend([pitch] * number)
                layers_branch_index_extend([branch_index] * number)
                layers_branch_index_parent_extend([branch_index_parent] * number)

                # Gardener-specific layers
                layers_frond_extend([0.0] * number)
                layer_height_extend([last_node.pos.z] * number)
                if self.is_trunk:
                    layer_trunk_distance_extend([0.0] * number)
                else:
                    layer_trunk_distance_extend([curr_trunk_distance + dist[j]] * number)
                layer_branch_distance_extend([0.0] * number)
                layer_branch_group_extend([branch_group] * number)
            

            if gardener_use_fronds:
                for id_list in frond_materials.values():
                    id_list.extend([0.0])

    
    # Add lateral twigs.
    last_node_index = len(self.nodes) - 1
    if disable_twigs is False:
        for i, n in enumerate(self.nodes):
            if i == 0 or n.age > lateral_twig_age_limit + dead_twig_wither:
                    continue

            if i == last_node_index:
                if not lateral_on_apical:
                    continue

            if len(n.sub_branches):
                # Don't add lateral twigs to nodes with sub branches.
                if len(n.sub_branches[0].nodes) > 2:
                    continue

            direction = n.direction
            if i != last_node_index:
                direction = self.nodes[i + 1].pos - n.pos  # Use bent direction.
                if spring_shape:
                    direction = self.nodes[i + 1].pos_last_year - n.pos_last_year  # Use bent direction.
                    if direction.length == 0.0:
                        direction = n.direction

            current_branching = int(branching * min(1.0, self.power))
            if branching > 1 and current_branching < 2:
                current_branching = 2
            elif branching == 1 and current_branching == 0:
                current_branching = 1
            for b in range(current_branching):

                sub_branch_dir = deviate(branch_angle, current_branching, twist, self.initial_phyllotaxic_angle,
                                            plagiotropism_buds, add_planar, 0.0, direction, i, b)

                branch_mat = two_point_transform(vector_zero, sub_branch_dir)
                twig_matrix = Matrix.Translation(n.pos) @ branch_mat

                if spring_shape:
                    twig_matrix = Matrix.Translation(n.pos_last_year) @ branch_mat

                if wind_shape or spring_shape:
                    shape_extend(twig_matrix @ duplicator[0] - origin)
                    shape_extend(twig_matrix @ duplicator[1] - origin)
                    shape_extend(twig_matrix @ duplicator[2] - origin)

                if not wind_shape:
                    verts_extend(twig_matrix @ vert - origin for vert in duplicator)
                    v += 3

                    faces_append((v - 3, v - 2, v - 1))
                    uvs_extend([(0.5, 0.5),
                                (0.5, 0.5),
                                (0.5, 0.5)])
                    
                    number = 3

                    if do_layers:
                        layers_shade_extend([self.shade] * number)
                        layers_thickness_extend([n.thickness] * number)
                        layers_age_extend([n.age / tree_age] * number)
                        layers_weight_extend([n.weight / base_weight] * number)
                        layers_power_extend([self.power] * number)
                        layers_health_extend([pow(n.photosynthesis, 0.2)] * number)
                        if self.dead:
                            layers_dead_extend([1.0] * number)
                        else:
                            layers_dead_extend([0.0] * number)
                        
                        layers_pitch_extend([pitch] * number)

                        layers_apical_extend([0.0] * number)
                        layers_upward_extend([0.0] * number)

                        if n.age > lateral_twig_age_limit or self.dead:
                            layers_lateral_extend([0.0] * number)
                            layers_dead_twig_extend([1.0] * number)
                        else:
                            layers_lateral_extend([1.0] * number)
                            layers_dead_twig_extend([0.0] * number)
                        
                        layers_branch_index_extend([branch_index] * number)
                        layers_branch_index_parent_extend([branch_index_parent] * number)

                        # GARDENER - Additional layers
                        layers_frond_extend([0.0] * number)
                        layer_height_extend([n.pos.z] * number)
                        if self.is_trunk:
                            layer_trunk_distance_extend([0.0] * number)
                        else:
                            layer_trunk_distance_extend([curr_trunk_distance + dist[j]] * number)
                        layer_branch_distance_extend([0.0] * number)
                        layer_branch_group_extend([branch_group] * number)
            
                    if gardener_use_fronds:
                        for id_list in frond_materials.values():
                            id_list.extend([0.0])
    
    # TK NOTE - Loops through to any sub-branches that may be in this node.

    # Build sub branches.
    next_branch_index = branch_index
    for i, node in enumerate(self.nodes):
        if node.sub_branches:
            for sub_branch in node.sub_branches:
                next_branch_index += 1

                # If the branch is too short or if Grove Gardener has intervened here,
                # we skip sub-branches.
                if len(sub_branch.nodes) < 2 or gardener_intervention is True:
                    continue
                
                next_trunk_distance = curr_trunk_distance + dist[i]
                hierarchy += 1
                
                # If we're in the trunk, increment the index group.
                # We also need to collapse the current set of distances to the trunk.
                if self.is_trunk:
                    branch_group += 1
                    next_trunk_distance = 0
                    hierarchy = 0

                    # Slice the trunk distance data layer and divide it by the highest length.
                    trunk_length = len(layers['layer_trunk_distance'])
                    trunk_indices = arange(trunk_distance_index, trunk_length)
                    trunk_array = array(layers['layer_trunk_distance'])

                    trunk_sliced = layers['layer_trunk_distance'][trunk_distance_index:]
                    trunk_remainder = numpy_delete(trunk_array, trunk_indices)

                    slice_max = amax(trunk_sliced)
                    trunk_sliced = trunk_sliced / slice_max
                    final_list = concatenate((trunk_remainder, trunk_sliced))
                    layers['layer_trunk_distance'] = final_list.tolist()

                    trunk_distance_index = len(layers['layer_trunk_distance']) + 1
                    
                # GARDENER - The distance tallied depends on what the previous node sent will be.
                if i == 0:
                    previous_node, current_node, next_node = None, self.nodes[0], self.nodes[1]
                elif i == 1 and i != len(self.nodes) - 1:
                    # Second node sub branch and not the last node.
                    if len(self.nodes) == len(nodes):
                        # This branch has no additional smoothing.
                        previous_node, current_node, next_node = self.nodes[0], self.nodes[1], self.nodes[2]
                    else:
                        if len(nodes) - len(self.nodes) == 2:
                            # This branch has smoothing at the start.
                            previous_node, current_node, next_node = nodes[2], nodes[3], nodes[4]
                        else:
                            # Only inserted one extra node for smoothing on thick branches.
                            previous_node, current_node, next_node = nodes[1], nodes[2], nodes[3]
                elif i < len(self.nodes) - 1:
                    # Not the last node.
                    previous_node, current_node, next_node = self.nodes[i - 1], self.nodes[i], self.nodes[i + 1]
                else:
                    # Sub branch of the last node.
                    previous_node, current_node, next_node = self.nodes[i - 1], self.nodes[i], None

                v, next_branch_index, hierarchy = sub_branch.build_branches_mesh(
                    lateral_on_apical,
                    profile_resolution, profile_resolution_reduction,
                    twist, u_repeat, texture_aspect_ratio, scale_to_twig,
                    root_distribution, root_shape, root_scale, root_bump,
                    base_weight,
                    previous_node, current_node, next_node, v,
                    verts, faces, uvs, shape, layers, fronds, frond_materials, 
                    next_branch_index, branch_index, branch_group, next_trunk_distance, trunk_distance_index, hierarchy,
                    origin, circles,
                    lateral_twig_age_limit, dead_twig_wither, branch_angle, branching, plagiotropism_buds, add_planar, 
                    wind_force, 
                    tree_age,
                    spring_shape=spring_shape, wind_shape=wind_shape)
    
    hierarchy -= 1
    return v, next_branch_index, hierarchy