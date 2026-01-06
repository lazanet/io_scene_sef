#!/bin/python3
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

import traceback
import bpy

from .sef_definitions import *

def load_sef(filepath):
	with open(filepath, 'r') as file:
		try:
			world = SEFWorld.load_data(file)
		except Exception as e:
			print('Error in input file!')
			print(traceback.format_exc())
			return {'CANCELLED'}
	draw_model(world)
	return {'FINISHED'}

def add_mesh(name, verts, faces, uv=None, edges=None, material=None, vert_color=None, col_name="Collection"):	
	if edges is None:
		edges = []
	mesh = bpy.data.meshes.new(name)
	if material != None:
		mesh.materials.append(material)
	mesh.from_pydata(verts, edges, faces)

	if uv is not None:
		uv_layer = mesh.uv_layers.new()
		mesh.uv_layers.active = uv_layer
		for face in mesh.polygons:
			for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
				uv_layer.data[loop_idx].uv = uv[vert_idx] # like `me.vertices[vert_idx]`
	if mesh.vertex_colors:
		vcol_layer = mesh.vertex_colors.active
	else:
		vcol_layer = mesh.vertex_colors.new()
		
	for face in mesh.polygons:
			for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
				if vert_color is not None:
					vcol_layer.data[vert_idx].color = [i/255 for i in vert_color[vert_idx]]

	obj = bpy.data.objects.new(name, mesh)
	bpy.data.collections[col_name].objects.link(obj)
	bpy.context.view_layer.objects.active = obj

def load_texture(name, location):
	curr = bpy.data.materials.new(name=name)
	curr.use_nodes = True
	bsdf = curr.node_tree.nodes["Principled BSDF"]
	
	texImage = curr.node_tree.nodes.new('ShaderNodeTexImage')
	texImage.image = bpy.data.images.load(location)
	
	curr.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs[0])
	return curr

def create_empty_material(name):
	"""
	Helper method that creates a empty material 
	useful for when the object uses an outside stadium file material 
	which is not included on the material list
	also this way of creating the material wont be exported into the sef (as long as is not changed by the user)
	"""
	return bpy.data.materials.new(name=name)

def recursive_unlink(obj):
	if hasattr(obj, 'children'):
		for child in obj.children:
			recursive_unlink(child)
		obj.unlink(child)

def reset_blend():
	try:
		scene = bpy.context.scene
		recursive_unlink(scene.collection.children)
		 
		for block in bpy.data.meshes:
			bpy.data.meshes.remove(block)

		for block in bpy.data.materials:
			bpy.data.materials.remove(block)

		for block in bpy.data.textures:
			bpy.data.textures.remove(block)

		for block in bpy.data.images:
			bpy.data.images.remove(block)

		# Running this after removes the orphan collection
		for c in bpy.data.collections:
			bpy.data.collections.remove(c)

		bpy.context.evaluated_depsgraph_get().update()
	except:
		print("This truly horrible way to reset blender state crashed with:")
		print(traceback.format_exc())
		print("Let's pretend that never happened")
		pass
		

def draw_model(world):
	reset_blend()
	scene_name = 'Stadium-%s' % world.weather
	if scene_name not in bpy.data.scenes:
		bpy.ops.scene.new(type='EMPTY')	 
		bpy.context.scene.name = scene_name
	
	bpy.context.window.scene = bpy.data.scenes[scene_name]
	
	# First load all materials
	loaded_materials = {}
	for material in world.materials:
		if not material.texture:
			print(f"Material {material.name} has an invalid filepath it wont be loaded")
			continue
		loaded_materials[material.name] = load_texture(material.name, material.texture)
	
	# Next, load all objects
	for group in world.groups:
		collection = bpy.data.collections.new(group.name)
		bpy.context.scene.collection.children.link(collection)
		for obj in group.obj_list:
			material = loaded_materials.get(obj.material, None)
			if material is None:
				material = create_empty_material(obj.material)
			add_mesh(obj.name, obj.verts, obj.faces, obj.uv, vert_color=obj.vcol, material=material, col_name=group.name)


	# Load all lights
	collection = bpy.data.collections.new("LIGHTS")
	bpy.context.scene.collection.children.link(collection)
	light_number = 0
	for light in world.lights:
		light_name = 'Light-%02d' % light_number
		light_number += 1
		# create light datablock, set attributes
		light_data = bpy.data.lights.new(name=light_name, type='POINT')
		light_data.energy = light.energy

		# create new object with our light datablock
		light_object = bpy.data.objects.new(name=light_name, object_data=light_data)

		# link light object
		collection.objects.link(light_object)

		# make it active
		bpy.context.view_layer.objects.active = light_object

		#change location
		light_object.location = (light.x, light.y, light.z)
		
	# Load rebounds
	collection = bpy.data.collections.new("REBOUNDS")
	bpy.context.scene.collection.children.link(collection)
	for rebound in world.rebounds:
		if len(rebound.verts) % 4 != 0:
			print(f"Rebound '{rebound.name}': vertex count must be a multiple of 4 (quads expected), rebound not imported")
			continue
		faces = [(i, i + 1, i + 2, i + 3) for i in range(0, len(rebound.verts), 4)]
		add_mesh(rebound.name, rebound.verts, faces, col_name="REBOUNDS")
	
	# Refresh render
	bpy.context.evaluated_depsgraph_get().update()
