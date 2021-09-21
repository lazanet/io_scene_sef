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

import string, traceback
import bpy

from .sef_definitions import *

def save_sef(filepath):
	with open(filepath, 'w', newline='\r\n') as file:
		try:
			world = save_world()
			world.store_data(file)
		except Exception as e:
			print('Error saving file!')
			print(traceback.format_exc())
			return {'CANCELLED'}
	return {'FINISHED'}

def traverse_tree(t):
	yield t
	for child in t.children:
		yield from traverse_tree(child)
		
group_names = ["SKY","BASE","REFLEX","UNK1","FIELD1","FIELD2","FIELD3","UNK2","RIGHT_TRIBUNE","LEFT_TRIBUNE",\
	"UPPER_TRIBUNE","DOWN_TRIBUNE","SCOREBOARD","ROOF","UNK3","UNK4","UNK5","UNK6","UNK7","UNK8","UNK9","UNK10", \
	"LIGHT_EFFECT","RIGHT_SIDE","LEFT_SIDE","UPPER_SIDE","DOWN_SIDE","UNK11","UNK12","UNK13","ADS_1","ADS_2",\
	"ADS_3","REBOUNDS","LIGHTS"]

def save_world():
	world = SEFWorld()
	
	world.weather = bpy.context.scene.name[len("Stadium-"):]
	
	for mat in bpy.data.materials:
#		if not all(c in string.hexdigits for c in mat.name):
#			continue
		if not mat.use_nodes or not "Image Texture" in mat.node_tree.nodes:
			continue
		sef_material = SEFMaterial()
		sef_material.name = mat.name
		sef_material.texture = mat.node_tree.nodes["Image Texture"].image.filepath
		world.materials.append(sef_material)
			
	for collection in traverse_tree(bpy.context.scene.collection):
		if collection.name not in group_names:
			continue
		group = SEFGroup()
		group.name = collection.name
		for obj in collection.all_objects:
			if collection.name == "LIGHTS":
				light = SEFLight()
				light.energy = obj.data.energy
				light.x = obj.location[0]
				light.y = obj.location[1]
				light.z = obj.location[2]
				world.lights.append(light)
			elif collection.name == "REBOUNDS":
				rebound = SEFRebound()
				rebound.name = obj.name
				rebound.verts = [(obj.matrix_world @ v.co) for v in obj.data.vertices]
				rebound.parts = len(rebound.verts) / 4
				world.rebounds.append(rebound)
			else:
				sef_obj = SEFObject()
				sef_obj.name = obj.name
				if len(obj.data.materials) > 0:
					sef_obj.material = obj.data.materials[0].name
				sef_obj.verts = [(obj.matrix_world @ v.co) for v in obj.data.vertices]
				# vert_color and uv extraction
				mesh = obj.data
				uv_layer = mesh.uv_layers.active
				for face in mesh.polygons:
					sef_obj.faces.append(face.vertices[:])
					for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
						try:
							col = mesh.vertex_colors.active.data[loop_idx].color
							col = [int(i * 255) for i in col]
							col = [col[3], col[0], col[1], col[2]]
							sef_obj.vcol.append(col)
						except:
							sef_obj.vcol.append([255, 255, 255, 255])
						sef_obj.uv.append(None)
					for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
						sef_obj.uv[vert_idx]=uv_layer.data[loop_idx].uv
				group.obj_list.append(sef_obj)

		group.obj_count = len(group.obj_list)
		if group.obj_count > 0:
			world.groups.append(group)			
	return world
