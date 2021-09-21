#!/bin/python3

from .sef_definitions import *
import bpy

def loadSEF(context, keywords):
	with open(keywords['filepath'], 'r') as file:
		try:
			world = SEFWorld.load_data(file)
		except Exception as e:
			print('Error in input file!')
			print(e)
			return {'CANCELLED'}
	draw_world(world)
	return {'FINISHED'}

def add_mesh(name, verts, faces, uv=None, edges=None, material=None, vert_color=(0, 0, 0), col_name="Collection"):	
	if edges is None:
		edges = []
	mesh = bpy.data.meshes.new(name)
	if material != None:
		mesh.materials.append(material)
	mesh.from_pydata(verts, edges, faces)

	if uv is not None:
		uvlayer = mesh.uv_layers.new()
		mesh.uv_layers.active = uvlayer
		for face in mesh.polygons:
			for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
				uvlayer.data[loop_idx].uv = uv[vert_idx] # like `me.vertices[vert_idx]`
	if mesh.vertex_colors:
		vcol_layer = mesh.vertex_colors.active
	else:
		vcol_layer = mesh.vertex_colors.new()
		
	for face in mesh.polygons:
			for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
				color = vert_color[vert_idx]
				r = int((color[4:5]), 16)
				g = int((color[6:7]), 16)
				b = int((color[8:9]), 16)
				a = int((color[2:3]), 16)
				vcol_layer.data[loop_idx].color = (r, g, b, a)

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

def draw_world(world):
	bpy.ops.scene.new(type='EMPTY')	 
	bpy.context.scene.name = 'Stadium-%s' % world.weather
	
	# First load all materials
	loaded_materials = {}
	for material in world.materials:
		loaded_materials[material.name] = load_texture(material.name, material.tex)
	
	# Next, load all objects
	for group in world.groups:
		collection = bpy.data.collections.new(group.name)
		bpy.context.scene.collection.children.link(collection)
		for obj in group.obj_list:
			add_mesh(obj.name, obj.verts, obj.faces, obj.uv, vert_color=obj.vcol, material=loaded_materials[obj.material], col_name=group.name)
	
	
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
		bpy.context.collection.objects.link(light_object)

		# make it active 
		bpy.context.view_layer.objects.active = light_object

		#change location
		light_object.location = (light.x, light.y, light.z)
		
	# Load rebounds
	collection = bpy.data.collections.new("REBOUNDS")
	bpy.context.scene.collection.children.link(collection)
	for rebound in world.rebounds:
		add_mesh(rebound.name, rebound.verts, [], col_name="REBOUNDS")
	
	# Refresh render
	bpy.context.evaluated_depsgraph_get().update()
