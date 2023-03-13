import bpy
import os
import math

filepath = "path/to/file.fbx"
fbx_export_mode = {
    "ALL",
    "INDIVIDUAL",
    "PARENT"
}

# Export Model for Unity
def export_model(path, name, fbx_scale_mode):
    bpy.ops.export_scene.fbx(
                filepath=str(path + name + '.fbx'), use_selection=True,
                apply_scale_options='FBX_SCALE_ALL')


def ExportSelectedMeshes(
    apply_loc = True,
    apply_rot = True,
    apply_scale = True,
    delete_mats_before_export = False,
    triangulate_before_export = False,
    fbx_export_mode = "INDIVIDUAL",
    export_combine_meshes = False,
    
    
    ):

    # settings
    fbx_scale_mode = 'FBX_SCALE_ALL'
    
    # get the active object (the one currently selected)
    obj = bpy.context.active_object
    
    # Check saved blend file
    if len(bpy.data.filepath) == 0:
        self.report({'INFO'}, 'Blend file is not saved.')
        return {'CANCELLED'}

    if len(bpy.data.filepath) > 0:
        path = ""

        # Check export path
        if len(bpy.data.filepath) > 0:
            path = bpy.path.abspath('//FBXs/')

        # Create export folder (if this need)
        if not os.path.exists(path):
            os.makedirs(path)

        # Save selected objects and active object
        start_selected_obj = bpy.context.selected_objects
        start_active_obj = bpy.context.active_object
        current_selected_obj = bpy.context.selected_objects
        
        # Name for FBX is active object name (by default)
        name = bpy.context.active_object.name
        
        # Filtering selected objects. Exclude all not meshes, empties, armatures, curves and text
        bpy.ops.object.select_all(action='DESELECT')
        for x in current_selected_obj:
            if x.type == 'MESH' or x.type == 'EMPTY' or x.type == 'ARMATURE' or x.type == 'CURVE' or x.type == 'FONT':
                x.select_set(True)
        current_selected_obj = bpy.context.selected_objects

        # Added suffix _ex to all selected objects. Also add _ex to mesh data and armature name
        for obj in current_selected_obj:
            obj.name += "_ex"
            if obj.type == 'MESH' or obj.type == 'ARMATURE':
                obj.data.name += "_ex"

        # Make copies. These copies will be exported
        bpy.ops.object.duplicate()
        exp_objects = bpy.context.selected_objects
        
        bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True)
        
        # Convert all non-mesh objects to mesh (except empties)
        for obj in exp_objects:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Remove disabled modifiers
            if obj.type != 'EMPTY':
                for modifier in reversed(obj.modifiers):
                    if not (modifier.show_viewport and modifier.show_render):
                        obj.modifiers.remove(modifier)

            # Apply modifiers (except Armature)
            if obj.type == 'MESH':
                for modifier in obj.modifiers:
                    if modifier.type != 'ARMATURE':
                        try:
                            bpy.ops.object.modifier_apply(modifier=modifier.name)
                        except:
                            bpy.ops.object.modifier_remove(modifier=modifier.name)
            elif obj.type != 'EMPTY':
                bpy.ops.object.convert(target='MESH')

        # Delete _ex.001 suffix from object names.
        # Mesh name and armature name is object name
        for obj in exp_objects:
            obj.name = obj.name[:-7]
            if obj.type == 'MESH' or obj.type == 'ARMATURE':
                obj.data.name = obj.name
                
        # Delete all materials (Optional)
        if delete_mats_before_export:
            for o in exp_objects:
                if o.type == 'MESH' and len(o.data.materials) > 0:
                    for q in reversed(range(len(o.data.materials))):
                        bpy.context.object.active_material_index = q
                        o.data.materials.pop(index=q)
                        
        # Triangulate meshes (Optional)
        if triangulate_before_export:
            for o in exp_objects:
                if o.type == 'MESH':
                    bpy.ops.object.select_all(action='DESELECT')
                    o.select_set(True)
                    bpy.context.view_layer.objects.active = o
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.reveal()
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    
        # Select all exported objects
        for obj in exp_objects:
            obj.select_set(True)

        # Apply scale
        if apply_scale:
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
        # Rotation Fix. Rotate X -90, Apply, Rotate X 90
        #if apply_rot:
        if apply_rot:
            bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'

            # Operate only with higher level parents
            for x in exp_objects:
                bpy.ops.object.select_all(action='DESELECT')

                if x.parent is None:
                    x.select_set(True)
                    bpy.context.view_layer.objects.active = x

                    # Check object has any rotation
                    # for option "Apply for Rotated Objects"
                    child_rotated = False
                    bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
                    for y in bpy.context.selected_objects:
                        if abs(y.rotation_euler.x) + abs(y.rotation_euler.y) + abs(y.rotation_euler.z) > 0.017:
                            child_rotated = True

                    bpy.ops.object.select_all(action='DESELECT')
                    x.select_set(True)

                    # X-rotation fix
                    if apply_rot:
                        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                        bpy.ops.transform.rotate(
                            value=(math.pi * -90 / 180), orient_axis='X',
                            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                            orient_type='GLOBAL', constraint_axis=(True, False, False),
                            orient_matrix_type='GLOBAL', mirror=False,
                            use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
                            proportional_size=1)
                        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
                        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                        bpy.ops.object.select_all(action='DESELECT')
                        x.select_set(True)
                        bpy.ops.transform.rotate(
                            value=(math.pi * 90 / 180), orient_axis='X',
                            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                            orient_type='GLOBAL', constraint_axis=(True, False, False),
                            orient_matrix_type='GLOBAL', mirror=False,
                            use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
                            proportional_size=1)

        bpy.ops.object.select_all(action='DESELECT')
        
        # Select exported objects
        for x in exp_objects:
            if x.type == 'MESH' or x.type == 'EMPTY' or x.type == 'ARMATURE':
                x.select_set(True)
                
        # Export all as one fbx
        if fbx_export_mode == 'ALL':
            # Combine All Meshes (Optional)
            if export_combine_meshes:
                # If parent object is mesh
                # combine all children to parent object
                if bpy.data.objects[name].type == 'MESH':
                    bpy.context.view_layer.objects.active = bpy.data.objects[name]
                    bpy.ops.object.join()
                # If  parent is empty
                else:
                    current_active = bpy.context.view_layer.objects.active
                    # Combine all child meshes to first in list
                    for obj in exp_objects:
                        if obj.type == 'MESH':
                            bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.join()
                    bpy.context.view_layer.objects.active = current_active

                exp_objects = bpy.context.selected_objects

            # Export FBX/OBJ
            export_model(path, name, fbx_scale_mode)
                
        # Individual Export
        if fbx_export_mode == 'INDIVIDUAL':
            for x in exp_objects:
                object_loc = (0.0, 0.0, 0.0)
                bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
                # Select only current object
                bpy.ops.object.select_all(action='DESELECT')
                x.select_set(True)
                bpy.context.view_layer.objects.active = x

                # Apply Location - Center of fbx is origin of object (Optional)
                if apply_loc:
                    # Copy object location
                    bpy.context.area.type = "VIEW_3D"
                    bpy.ops.view3d.snap_cursor_to_selected()
                    object_loc = bpy.context.scene.cursor.location.copy()
                    # Move object to center of world
                    bpy.ops.object.location_clear(clear_delta=False)
                # Center of fbx is center of the world
                else:
                    bpy.ops.view3d.snap_cursor_to_center()
                    bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'
                name = x.name

                # Export FBX/OBJ
                export_model(path, name, fbx_scale_mode)

                # Restore object location
                if apply_loc:
                    bpy.context.scene.cursor.location = object_loc
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)

        ##skipped other code to here
        bpy.ops.object.select_all(action='DESELECT')

        for obj in exp_objects:
            obj.select_set(True)

        # Delete duplicates
        bpy.ops.object.delete()

        # Select again original objects and set active object
        bpy.ops.object.select_all(action='DESELECT')

        # Restore names of objects (remove "_ex" from name)
        for j in current_selected_obj:
            j.name = j.name[:-3]
            if j.type == 'MESH' or j.type == 'ARMATURE':
                j.data.name = j.data.name[:-3]

        for i in start_selected_obj:
            i.select_set(True)

        bpy.context.view_layer.objects.active = start_active_obj

        # Restore "Pivot point align" option
        #bpy.context.scene.tool_settings.use_transform_pivot_point_align = current_pivot_point_align

        # Restore cursor location and pivot point mode
        #bpy.context.scene.cursor.location = saved_cursor_loc
        #bpy.context.scene.tool_settings.transform_pivot_point = current_pivot_point
        
    bpy.context.area.type = "TEXT_EDITOR"
    print("DONE")
    return {'FINISHED'}
                        
            
    """
    # duplicate the object
    new_obj = obj.copy()
    new_obj.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(new_obj)

    # set the origin of the new object to the center of its bounding box
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

    # move the object to the world origin
    new_obj.location = (0, 0, 0)

    # apply all transformations to the object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # get the absolute file path of the current Blender file
    blend_file_path = bpy.path.abspath(bpy.context.blend_data.filepath)

    # create the output file path for the exported FBX file
    output_file_path = blend_file_path[:-6] + ".fbx"

    #rename the file without .001 suffix
    new_obj.name = obj.name
    
    # export the object as an FBX file
    bpy.ops.export_scene.fbx(filepath=output_file_path, use_selection=True)
    
    # delete the duplicated mesh
    bpy.data.objects.remove(new_obj, do_unlink=True)
    
    #rename original mesh to original name
    """
    

print("RunningExportSelectedMeshes")

ExportSelectedMeshes()
