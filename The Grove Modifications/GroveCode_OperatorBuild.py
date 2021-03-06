# coding=utf-8

# INSTALLATION : Add this to the top of the OperatorBuild file (around line 27)

# GARDENER - Required imports
from numpy import array, arange, random
from .GardenerBuild import load_frond_set, build_normal_reprojection, vertex_colors_layer_from_colors


# -------------------------------------------------------

# The function below is a modified version of build_branches_mesh, inside the OperatorBuild file.
#
# INSTALLATION : Replace the original build_branches_mesh definition inside OperatorBuild with 
# this and ensure the indentation is correct.
#
# This function is located at line at around line 405 (depending on where you add the import
# statement above)

def build_branches_mesh(tree, properties, context):
    """
    Advanced Mesh, Adaptive Mesh. Build branches with adaptive resolution, UV unwrapping, vertex groups and
    vertex colors. """

    print(t('build_branches_advanced_mesh_message'))

    properties.number_of_polygons = 0

    # Load bark texture and calculate UV aspect ratio.
    if exists(properties.textures_menu):
        im = bpy.data.images.load(properties.textures_menu, check_existing=True)
        if im.size[0] == 0 or im.size[1] == 0:
            # Invalid image file.
            texture_aspect_ratio = 0.5
            properties.report_string = 'Selected bark texture is an invalid image file.'
        else:
            texture_aspect_ratio = im.size[0] / im.size[1]
    else:
        im = None
        texture_aspect_ratio = 3.0

    properties.texture_aspect_ratio = texture_aspect_ratio

    # Load frond data if we're replacing branches.
    # Also contains an indexed list of all materials used.
    gardener_use_fronds = bpy.context.scene.gardener_use_fronds
    gardener_reproject_normals = bpy.context.scene.gardener_normal_use_reproject
    frond_data = []
    frond_materials = {}

    if gardener_use_fronds:
        frond_data = load_frond_set(bpy.context.scene.gardener_frond_collection, properties.scale_to_twig)
        for mat_name in frond_data[1]:
            frond_materials[mat_name] = []

    vertices = []
    faces = []
    uvs = []
    shape = []
    

    simulation_data = {'layer_shade': [],
                       'layer_thickness': [],
                       'layer_age': [],
                       'layer_weight': [],
                       'layer_power': [],
                       'layer_health': [],
                       'layer_dead': [],
                       'layer_pitch': [],
                       'layer_apical': [],
                       'layer_lateral': [],
                       'layer_upward': [],
                       'layer_dead_twig': [],
                       'layer_branch_index': [],
                       'layer_branch_index_parent': [],

                       # GARDENER - Extra data sets.
                       'layer_frond': [],
                       'layer_height': [],
                       'layer_trunk_distance': [],
                       'layer_branch_distance': [],
                       'layer_branch_group': [],
                       }

    tree.engulf_branches(None, None)
    tree.build_branches_mesh(properties.lateral_on_apical,
                             properties.profile_resolution, properties.profile_resolution_reduction,
                             properties.twist, properties.u_repeat, texture_aspect_ratio, 
                             properties.scale_to_twig,
                             properties.root_distribution, properties.root_shape,
                             properties.root_scale, properties.root_bump,
                             tree.nodes[0].weight,
                             None, None, None, 0,
                             vertices, faces, uvs, shape, simulation_data, frond_data, frond_materials, 
                             0, 0, 0, 0, 0, 0,
                             tree.nodes[0].pos, pre_compute_circles(properties.profile_resolution),
                             properties.lateral_twig_age_limit, properties.dead_twig_wither,
                             properties.branch_angle, int(properties.branching),
                             properties.plagiotropism_buds, properties.add_planar, 
                             0.0, tree.nodes[0].age + 1)

    # Name branches object after the preset.
    me = bpy.data.meshes.new(str(properties.preset_name))
    me.from_pydata(vertices, [], faces)

    uv_layer = me.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", [uv for pair in uvs for uv in pair])

    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))

    bark_material = None
    try:
        bark_material = create_bark_material(im, properties, context)
    except:
        if not bark_material:
            print("WARNING:")
            print("Something went wrong while creating the bark material.")
            print("You may be using an unofficial release of Blender, an incompatible render engine, ")
            print("or an incompatible OCIO configruation. You will have to create your material manually.")
            bark_material = bpy.data.materials.new("TheGroveBranches")
            bark_material.diffuse_color = Vector((0.12, 0.09, 0.07, 1.0))
            bark_material.metallic = 0.0
            bark_material.roughness = 1.0
    me.materials.append(bark_material)

    properties.number_of_polygons += len(faces)

    ob = bpy.data.objects.new(str(properties.preset_name), me)
    me = ob.data  # Just to be sure. This could fix the unstable behavior.

    # GARDENER - Inserts property booleans to populate our custom vertex layers.
    properties.do_layer_frond = gardener_use_fronds
    properties.do_layer_height = bpy.context.scene.gardener_datalayer_height
    properties.do_layer_trunk_distance = bpy.context.scene.gardener_datalayer_trunktobranch
    properties.do_layer_branch_distance = bpy.context.scene.gardener_datalayer_branchtofrond
    properties.do_layer_branch_group = bpy.context.scene.gardener_datalayer_branchgroup

    # GARDENER - This needs an actual interface, right now though itll force include all
    # gamedev-relevant vertex groups.
    gardener_merge_layers = bpy.context.scene.gardener_merge_layers

    if properties.do_layer_height or gardener_merge_layers:
        max_height = tree.find_highest_point(0.0)
        height_array = array(simulation_data['layer_height'])
        simulation_data['layer_height'] = height_array / max_height

    if properties.do_layer_branch_group or gardener_merge_layers:
        branch_array = array(simulation_data['layer_branch_group'])
        branch_group_value = branch_array[len(branch_array) - 1]

        # make an array with values counting up to the branch group value and SHUFFLE
        randomizer = arange(branch_group_value + 1)
        random.shuffle(randomizer)

        # replace the numbers incrementally
        i = 0
        print(randomizer)
        print(branch_array)
        while i < branch_group_value:
            branch_array[branch_array == i] = randomizer[i]
            i += 1

        simulation_data['layer_branch_group'] = branch_array / branch_group_value
    
    # GARDENER - Merges all active Gardener data layers into a single color group.
    if gardener_merge_layers:
        r_layer = simulation_data['layer_height']
        b_layer = simulation_data['layer_trunk_distance']
        g_layer = simulation_data['layer_branch_distance']
        a_layer = simulation_data['layer_branch_group']
        vertex_colors_layer_from_colors(ob, "Combined Layers", r_layer, b_layer, g_layer, a_layer)

    # Add vertex layers and material groups.
    print(t('build_layers_message'))

    if properties.show_dead_preview:
        properties.do_layer_dead = True

    material_indices = [0] * len(faces)
    for name, data in simulation_data.items():
        if getattr(properties, "do_" + str.lower(name)):

            if name in ['layer_branch_index', 'layer_branch_index_parent']:
                int_layer = me.vertex_layers_int.new(name=name)
                int_layer.data.foreach_set("value", data)
            else:
                vertex_group_layer_from_data(ob, name, data)
                print('  ' + t(name))
                if not vertex_colors_layer_from_data(ob, name, data):
                    properties.display_vertex_colors_warning = True
                    print(t('colors_limit_message').format(name))

            if name == "layer_apical" and properties.do_layer_apical:
                if "TheGroveApicalTwigs" not in bpy.data.materials:
                    ma = bpy.data.materials.new("TheGroveApicalTwigs")
                    ma.diffuse_color = Vector((0.0, 0.0, 0.0, 1.0))
                    bark_material.metallic = 0.0
                    bark_material.roughness = 0.8
                me.materials.append(bpy.data.materials["TheGroveApicalTwigs"])
                index = me.materials.find("TheGroveApicalTwigs")
                material_indices = [material_indices[i] + (index * int(data[face[0]]))
                                    for i, face in enumerate(faces)]
            
            if name == "layer_upward" and properties.do_layer_upward:
                if "TheGroveUpwardTwigs" not in bpy.data.materials:
                    ma = bpy.data.materials.new("TheGroveUpwardTwigs")
                    ma.diffuse_color = Vector((0.0, 0.0, 0.0, 1.0))
                    bark_material.metallic = 0.0
                    bark_material.roughness = 0.8
                me.materials.append(bpy.data.materials["TheGroveUpwardTwigs"])
                index = me.materials.find("TheGroveUpwardTwigs")
                material_indices = [material_indices[i] + (index * int(data[face[0]]))
                                    for i, face in enumerate(faces)]
            
            if name == "layer_dead_twig" and properties.do_layer_dead_twig:
                if "TheGroveDeadTwigs" not in bpy.data.materials:
                    ma = bpy.data.materials.new("TheGroveDeadTwigs")
                    ma.diffuse_color = Vector((0.0, 0.0, 0.0, 1.0))
                    bark_material.metallic = 0.0
                    bark_material.roughness = 0.8
                me.materials.append(bpy.data.materials["TheGroveDeadTwigs"])
                index = me.materials.find("TheGroveDeadTwigs")
                material_indices = [material_indices[i] + (index * int(data[face[0]]))
                                    for i, face in enumerate(faces)]

            if name == "layer_lateral" and properties.do_layer_lateral:
                if "TheGroveLateralTwigs" not in bpy.data.materials:
                    ma = bpy.data.materials.new("TheGroveLateralTwigs")
                    ma.diffuse_color = Vector((0.0, 0.0, 0.0, 1.0))
                    bark_material.metallic = 0.0
                    bark_material.roughness = 0.8
                me.materials.append(bpy.data.materials["TheGroveLateralTwigs"])
                index = me.materials.find("TheGroveLateralTwigs")
                material_indices = [material_indices[i] + (index * int(data[face[0]]))
                                    for i, face in enumerate(faces)]
                # Store to later tweak twig density without needing a full rebuild.
                ob['number_of_lateral_twigs'] = material_indices.count(index)

            # if name == "layer_dead" and properties.do_layer_dead:
            if name == "layer_dead" and properties.show_dead_preview:
                if "TheGroveDeadBranches" not in bpy.data.materials:
                    ma = bpy.data.materials.new("TheGroveDeadBranches")
                    ma.diffuse_color = Vector((1.0, 0.0, 0.0, 1.0))
                    bark_material.metallic = 0.0
                    bark_material.roughness = 0.8
                me.materials.append(bpy.data.materials["TheGroveDeadBranches"])
                index = me.materials.find("TheGroveDeadBranches")
                material_indices = [material_indices[i] + (index * int(data[face[0]]))
                                    for i, face in enumerate(faces)]

    # Assign custom frond materials
    if gardener_use_fronds:
        custom_i = 0
        for mat_name, mat_data in frond_materials.items():
            me.materials.append(bpy.data.materials[mat_name])
            index = me.materials.find(mat_name)

            for i, face in enumerate(faces):
                result = index * int(mat_data[i])
                material_indices[i] = material_indices[i] + result
        
    
    # Needle layer WIP. TODO: Finalize!
    if getattr(properties, 'do_layer_young'):
        data = simulation_data['layer_age']
        name = t('layer_young')

        for i in range(len(data)):
            if data[i] * properties.age < 3:
                data[i] = 1
            else:
                data[i] = 0
        
        vertex_group_layer_from_data(ob, name, data)
        
        if not vertex_colors_layer_from_data(ob, name, data):
            properties.display_vertex_colors_warning = True
            print(t('colors_limit_message').format(name))
    
    # Set material indices for twig duplicator faces.
    me.polygons.foreach_set("material_index", material_indices)

    # GARDENER - Reproject normals using a duplicated hull of the tree.
    if gardener_use_fronds and gardener_reproject_normals:
        hull_res = bpy.context.scene.gardener_normal_hull_res
        hull_expand = bpy.context.scene.gardener_normal_hull_size
        build_normal_reprojection(ob, properties.scale_to_twig, hull_res, hull_expand)

    me['the_grove'] = 'Grown with The Grove.'
    ob.location = tree.nodes[0].pos * properties.scale_to_twig
    ob.scale = Vector((properties.scale_to_twig, properties.scale_to_twig, properties.scale_to_twig))

    if properties.twigs_menu != t('no_twigs'):
        # Build twigs.
        set_viewport_detail(properties)

        # Apical twig particle system.
        modifier = ob.modifiers.new("Apical Twigs", 'PARTICLE_SYSTEM')
        psystem = ob.particle_systems[-1]
        psystem.name = "Apical Twigs"
        ps = psystem.settings
        ps.count = len([selection for selection in simulation_data['layer_apical'] if selection == 1.0]) / 3
        configure_particles(ps, psystem, modifier)
        psystem.vertex_group_density = t('layer_apical')

        # Lateral twig particle system.
        modifier = ob.modifiers.new("Lateral Twigs", 'PARTICLE_SYSTEM')
        psystem = ob.particle_systems[-1]
        psystem.name = "Lateral Twigs"
        ps = psystem.settings
        ps.count = (len([selection for selection in simulation_data['layer_lateral'] if selection == 1.0]) / 3
                    * properties.lateral_twig_chance)
        configure_particles(ps, psystem, modifier)
        psystem.vertex_group_density = t('layer_lateral')

        # Upward twig particle system.
        modifier = ob.modifiers.new("Upward Twigs", 'PARTICLE_SYSTEM')
        psystem = ob.particle_systems[-1]
        psystem.name = "Upward Twigs"
        ps = psystem.settings
        ps.count = (len([selection for selection in simulation_data['layer_upward'] if selection == 1.0]) / 3)
        configure_particles(ps, psystem, modifier)
        psystem.vertex_group_density = t('layer_upward')

        # Dead twig particle system.
        modifier = ob.modifiers.new("Dead Twigs", 'PARTICLE_SYSTEM')
        psystem = ob.particle_systems[-1]
        psystem.name = "Dead Twigs"
        ps = psystem.settings
        ps.count = (len([selection for selection in simulation_data['layer_dead_twig'] if selection == 1.0]) / 3)
        configure_particles(ps, psystem, modifier)
        psystem.vertex_group_density = t('layer_dead_twig')

    return ob