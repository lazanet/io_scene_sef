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

import os, math, traceback

class SEFBase:
	def __repr__(self):
		import json
		return json.dumps(vars(self), default=repr)
		
	def __str__(self):
		import json
		parsed = json.loads(self.__repr__())
		return json.dumps(parsed, indent=4)

class SEFGroup(SEFBase):
	def __init__(self):
		self.name      = ''
		self.obj_count = 0
		self.obj_list  = []

class SEFObject(SEFBase):
	def __init__(self):
		self.name     = ''
		self.material = ''
		self.verts    = []
		self.uv       = []
		self.vcol     = []
		self.faces    = []

class SEFMaterial(SEFBase):
	def __init__(self):
		self.name = ''
		self.texture  = ''

class SEFLight(SEFBase):
	def __init__(self):
		self.energy	= 0
		self.x		= 0
		self.y		= 0
		self.z		= 0

class SEFRebound(SEFBase):
	def __init__(self):
		self.name  = ''
		self.parts = 0
		self.verts = []

class SEFWorld(SEFBase):
	def __init__(self):
		self.groups    = []
		self.materials = []
		self.lights    = []
		self.rebounds  = []
		self.weather   = 'DF'
			
	@staticmethod
	def load_data(file):
		header = file.readline()
		if header != '//Stadium Exchange File (c)2007 warpjavier\n':
			raise Exception("Wrong file header!")

		world = SEFWorld()
		for line in file:
			if line.find('Weather') >= 0:
				world.weather = line.split('=')[1].replace('"','').replace(' ','').strip()
				break

		next(file)
		for line in file:
			if line.find('Materials') >= 0:
				materials = int(line.split('=')[1])
				break

		next(file)
		for mt in range(materials):
			line = next(file)
			m = SEFMaterial()		
			m.name = "%s" % line.split()[0]
			if len(line.split()) == 2:
				m.texture  = line.split()[1]
			elif len(line.split()) > 2:
				m.texture = line.split()[1]
				for n in range(len(line.split())-2):
					m.texture += " " + line.split()[n+2]
			else:
				raise Exception('Error Loading textures.')

			m.texture = m.texture.replace('"','')
			from os import path
			if not path.exists(m.texture):
				# Lets be more inclusive in this rewrite, and search for relative materials path as well
				m.texture = path.join(path.dirname(file.name), path.basename(m.texture.replace('\\', os.sep)))
				if not path.exists(m.texture):
					raise Exception('Error '+ m.texture + ' not found.')
			world.materials.append(m)

		for line in file:
			if line.find('Lights') >= 0:
				l_count = int(line.split('=')[1])
				break

		next(file)
		for lt in range(l_count):
			line = next(file)
			l = SEFLight()		
			l.energy	= float(line.split()[0])
			l.x 		= float(line.split()[1])
			l.y 		= float(line.split()[2])
			l.z 		= float(line.split()[3])
			world.lights.append(l)

		for line in file:
			if line.find('Meshes') >= 0:
				meshes = int(line.split('=')[1]) 
				break

		next(file)
		for objs in range(meshes):
			line = next(file)
			line = line.split('=')[1]
			group = SEFGroup()
			group.name = line.split()[0].replace('"','')
			group.obj_count = int(line.split()[1])
			for gr in range(group.obj_count):
				obj = SEFObject()
				vertex  = 0
				faces   = 0
				line = next(file)
				obj.name       = group.name + '-' + line.split()[0]
				obj.material   = line.split()[1]
				line = next(file)
				vertex = int(line)
				for ver in range(vertex):
					line = next(file)
					try:
						parts = line.split()
						x,y,z,u,v = float(parts[0]),float(parts[1]),float(parts[2]),float(parts[3]),1-float(parts[4])
						obj.verts.append((x,y,z))
						obj.uv.append((u,v))
						color = parts[5][2:]
						r = int((color[2:4]), 16)
						g = int((color[4:6]), 16)
						b = int((color[6:8]), 16)
						a = int((color[0:2]), 16)
						obj.vcol.append((r, g, b, a))
					except Exception as e:
						raise Exception('Error importing Vertex list.\n' + traceback.format_exc())
				
				line  = next(file)
				faces = int(line)
				for fac in range(faces):
					try:
						line = next(file)
						if len(list(map(int, line.split()))) > 3:
							a,b,c,d = map(int,line.split())
							obj.faces.append((a,b,c,d))
						else:
							a,b,c = map(int, line.split())
							obj.faces.append((a,b,c))
					except Exception as e:
						raise Exception('Error importing Faces.\n' + traceback.format_exc())
		
				group.obj_list.append(obj)
			world.groups.append(group)
#		mats.sort()
		try :
			next(file)
			for line in file:
				if line.find('Rebounds') >= 0: 
					break

			for line in file:
				reb = SEFRebound()
				reb.name  = line.split('=')[0].replace('"','').replace(' ','')
				reb.parts = int(line.split('=')[1])
				reb.verts = []
				for v in range(reb.parts * 4):
					line = next(file)
					x,y,z = float(line.split()[0]),float(line.split()[1]),float(line.split()[2])
					reb.verts.append((x,y,z))
				world.rebounds.append(reb)
		except Exception as e:
			raise Exception('Error importing Rebounds.\n' + traceback.format_exc())

		return world

	def store_data(self, file):
		file.write("//Stadium Exchange File (c)2007 warpjavier\n\n")

		file.write("Weather = \"%s\"\n\n" % self.weather)

		file.write("Materials = %d\n\n" % len(self.materials))
		for material in self.materials:
			file.write("%s \"%s\"\n" % (material.name, material.texture))

		file.write("\nLights = %d\n\n"% len(self.lights))
		for l in self.lights:
			file.write("%8f %8f %8f %8f\n" % (l.energy, l.x, l.y, l.z))

		o_count=0
		for gr in self.groups:
			if gr.obj_count > 0:
				o_count += 1
		file.write("\nMeshes = %d\n\n" % o_count)
		
		for group in self.groups:
			if group.obj_count > 0:
				file.write("Name = \"%s\" %d\n" % (group.name, group.obj_count))
				group.obj_list.sort(key=lambda obj:obj.name)
				for o in group.obj_list:
					name = o.name[len(group.name)+1:] # Remove group prefix
					file.write("%s %s\n%d\n" % (name, o.material, len(o.verts)))
					for i in range(len(o.verts)):
						file.write("%8f %8f %8f " % tuple(o.verts[i]))
						u,v = o.uv[i][0], o.uv[i][1]
						file.write("%8f %8f 0x" % (u, 1-v))
						for j in range(len(o.vcol[i])):
							file.write("%02x" % o.vcol[i][j])
						file.write("\n")
					file.write("%d\n" % len(o.faces))
					for f in o.faces:
						file.write("%d %d %d\n" % tuple(f))
		if len(self.rebounds) > 0:
			file.write("\nRebounds\n")
			for r in self.rebounds:
				file.write("\"%s\" = %d\n" % (r.name, r.parts))
				for p in range(len(r.verts)):
					file.write("%8f %8f %8f\n" % tuple(r.verts[p]))
