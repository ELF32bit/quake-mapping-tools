#!/usr/bin/python
import os, argparse, math, re

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("input", type=str, help = "|")
parser.add_argument("--scale", type=float, default=1.0, help="|")
parser.add_argument("--unit_size", type=float, default=32.0, help="|")
parser.add_argument("--normal_offset", type=float, default=1.0, help="|")
parser.add_argument("--secondary_normal_offset", type=float, help="|")
parser.add_argument("--secondary_normal_brush", action="store_true", help="|")
parser.add_argument("--grid_snap_step", type=float, default=0.125, help="|")
parser.add_argument("--classname", type=str, default="func_detail", help="|")
parser.add_argument("--material", type=str, default="__TB_empty", help="|")
parser.add_argument("--material_list", type=str, default="", help="|")
parser.add_argument("--skip_material", type=str, default="SKIP", help="|")
parser.add_argument("--skip_material_list", type=str, default="", help="|")
parser.add_argument("--vertex_color_materials", action="store_true", help="|")
parser.add_argument("--phong_angle", type=float, default=89.0, help="|")
parser.add_argument("--uv_valve", action="store_true", help="|")
parser.add_argument("--disable_objects", action="store_true", help="|")
parser.add_argument("--disable_convex_objects", action="store_true", help="|")
parser.add_argument("--disable_sorting_objects", action="store_true", help="|")
parser.add_argument("--disable_sorting_materials", action="store_true", help="|")
parser.add_argument("--disable_smooth_groups", action="store_true", help="|")
parser.add_argument("--disable_grid_snap", action="store_true", help="|")
parser.add_argument("--epsilon", type=float, default=0.001, help="|")
parser.add_argument("--game", type=str, default="Generic", help="|")
parser.add_argument("--info", action="store_true", help="|")
parser.add_argument("--append_to_output", action="store_true", help="|")
parser.add_argument("--output", type=str, help="|")
arguments = parser.parse_args()

# validating input arguments
if not abs(arguments.normal_offset) > 0.0:
	print("Normal offset must be different from zero!")
	quit()
if arguments.secondary_normal_offset != None:
	if not abs(arguments.secondary_normal_offset) > 0.0:
		print("Secondary normal offset must be different from zero!")
		quit()
	if not arguments.secondary_normal_brush:
		if not arguments.secondary_normal_offset * arguments.normal_offset > 0.0:
			print("Normal offset and secondary normal offset must have different direction!")
			quit()
if not abs(arguments.grid_snap_step) > 0.0:
	arguments.disable_grid_snap = True

arguments.squared_epsilon = arguments.epsilon * arguments.epsilon
arguments.material_list = (";" + arguments.material_list).split(";")
arguments.skip_material_list = (";" + arguments.skip_material_list).split(";")

# using input file name for the output if not provided
input_basename = os.path.basename(arguments.input)
input_name = os.path.splitext(input_basename)[0]
if arguments.output == None:
	arguments.output = input_name + ".map"

def sorted_alphanumeric(data):
	convert = lambda text: int(text) if text.isdigit() else text.lower()
	alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
	return sorted(data, key=alphanum_key, reverse=False)

def vector3_substract(a, b):
	return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]

def vector3_multiply_by_scalar(a, s):
	return [a[0] * s, a[1] * s, a[2] * s]

def vector3_cross(a, b):
	return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]

def vector3_length_squared(v):
	return v[0] * v[0] + v[1] * v[1] + v[2] * v[2]

def vector3_length(v):
	return math.sqrt(vector3_length_squared(v))

def vector3_normalize(v):
	length = vector3_length(v)
	if length:
		return [(v[0] / length), (v[1] / length), (v[2] / length)]
	return [0.0, 0.0, 0.0]

def vector3_grid_snap(v, s):
	return [math.floor(v[0] / s + 0.5) * s, math.floor(v[1] / s + 0.5) * s, math.floor(v[2] / s + 0.5) * s]

def triangle_get_center(a, b, c):
	return [(a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0, (a[2] + b[2] + c[2]) / 3.0]

def triangle_get_clockwise_normal(a, b, c):
	return vector3_normalize(vector3_cross(vector3_substract(a, c), vector3_substract(a, b)))

def triangle_get_counterclockwise_normal(a, b, c):
	return vector3_normalize(vector3_cross(vector3_substract(a, b), vector3_substract(a, c)))

def triangle_get_valve_uv(a, b, c):
	normal = triangle_get_clockwise_normal(a, b, c)
	if abs(normal[0]) > abs(normal[1]) and abs(normal[0]) > abs(normal[2]):
		return "[ 0 1 0 0 ] [ 0 0 -1 0 ]"
	elif abs(normal[1]) > abs(normal[0]) and abs(normal[1]) > abs(normal[2]):
		return "[ 1 0 0 0 ] [ 0 0 -1 0 ]"
	else:
		return "[ 1 0 0 0 ] [ 0 -1 0 0 ]"

def triangle_get_standard_uv(a, b, c):
	return "0 0"

# trying to get input file paths
input_file_paths = []
input_is_directory = False
if os.path.isdir(arguments.input):
	for path in os.listdir(arguments.input):
		file_path = os.path.join(arguments.input, path)
		if os.path.isfile(file_path) and file_path.endswith(".obj"):
			input_file_paths.append(file_path)
	input_file_paths = sorted_alphanumeric(input_file_paths)
	input_is_directory = True
else:
	input_file_paths = [arguments.input]

# processing input files
input_data = []
for input_file_path in input_file_paths:
	try:
		input_file = open(input_file_path, 'r')
	except Exception:
		if not input_is_directory:
			print(f"Failed opening input file: {arguments.input}")
			quit()
		else:
			continue
	input_file_basename = os.path.basename(input_file_path)
	input_file_name = os.path.splitext(input_file_basename)[0]

	objects = [""]
	materials = [""]
	vertices = []
	triangles = []
	colors = []
	lines = []

	input_data.append({})
	input_data[-1]["name"] = input_file_name
	input_data[-1]["path"] = input_file_path
	input_data[-1]["objects"] = objects
	input_data[-1]["materials"] = materials
	input_data[-1]["vertices"] = vertices
	input_data[-1]["triangles"] = triangles
	input_data[-1]["lines"] = lines

	current_object = ""
	current_material = ""
	current_smooth_group = 0
	for line in input_file:
		split = line.split()
		if len(split) == 2 and split[0] in ["o", "g"]:
			current_object = split[1]
			if not current_object in objects:
				objects.append(current_object)
		elif len(split) == 2 and split[0] == "usemtl":
			current_material = split[1]
			if not current_material in materials:
				materials.append(current_material)
		elif len(split) == 2 and split[0] == "s":
			if arguments.disable_smooth_groups:
				continue
			if split[1] in ["0", "off"]:
				current_smooth_group = 0
			elif split[1].isdigit():
				current_smooth_group = int(split[1])
		elif len(split) in [4, 7] and split[0] == "v":
			vertices.append([])
			# immediately converting coordinate system
			scale = arguments.scale * arguments.unit_size
			vertices[-1].append(+float(split[1]) * scale)
			vertices[-1].append(-float(split[3]) * scale)
			vertices[-1].append(+float(split[2]) * scale)
			# reading vertex colors for face materials
			if arguments.vertex_color_materials:
				colors.append([255, 255, 255])
				if len(split) == 7:
					colors[-1][0] = int(float(split[4]) * 255.0)
					colors[-1][1] = int(float(split[5]) * 255.0)
					colors[-1][2] = int(float(split[6]) * 255.0)
		elif len(split) >= 4 and split[0] == "f":
			face_vertices, face_colors = [], []
			for index in range(1, len(split)):
				face_data = split[index].split("/")
				vertex_index = int(face_data[0]) - 1
				face_vertices.append(vertices[vertex_index])
				if arguments.vertex_color_materials:
					face_colors.append(colors[vertex_index])
			# converting n-gons to triangles
			for index in range(1, len(face_vertices) - 1):
				triangles.append([])
				triangles[-1].append(face_vertices[0])
				triangles[-1].append(face_vertices[index])
				triangles[-1].append(face_vertices[index + 1])
				triangles[-1].append(current_smooth_group)
				triangles[-1].append(current_material)
				triangles[-1].append(current_object)
				if arguments.vertex_color_materials:
					if face_colors[0] != face_colors[index]:
						triangles[-1].append(None)
					elif face_colors[0] != face_colors[index + 1]:
						triangles[-1].append(None)
					else:
						triangles[-1].append(face_colors[0])
		elif len(split) >= 3 and split[0] == "l":
			lines.append([current_object])
			for index in range(1, len(split)):
				lines[-1].append(int(split[index]) - 1)
	input_file.close()

	# finding vertex color materials
	if arguments.vertex_color_materials:
		materials.clear()
		materials.append("")
		for triangle in triangles:
			triangle[4] = ""
			if triangle[6] == None:
				continue
			r, g, b = tuple(triangle[6])
			material_name = f"#{r:02x}{g:02x}{b:02x}"
			if not material_name in materials:
				materials.append(material_name)
			triangle[4] = material_name

# sorting objects by name
if not arguments.disable_sorting_objects:
	for data in input_data:
		data["objects"] = sorted_alphanumeric(data["objects"])

# collecting map materials
map_materials = []
for data in input_data:
	for material in data["materials"]:
		if not material in map_materials:
			map_materials.append(material)

# sorting materials by name for material lists
if not arguments.disable_sorting_materials:
	for data in input_data:
		data["materials"] = sorted_alphanumeric(data["materials"])
	map_materials = sorted_alphanumeric(map_materials)

if arguments.info:
	gbox = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
	for data_index, data in enumerate(input_data):
		print(f'{data["path"]}:')

		print("\tObjects:")
		if input_is_directory:
			frames = len(str(len(input_data)))
			for object_index in range(1, len(data["objects"])):
				print(f"\t\t [{str(data_index + 1).zfill(frames)}]", end = " ")
				print(data["objects"][object_index])
		else:
			frames = len(str(len(data["objects"]) - 1))
			for object_index in range(1, len(data["objects"])):
				print(f"\t\t [{str(object_index).zfill(frames)}]", end = " ")
				print(data["objects"][object_index])

		print("\tMaterials:")
		for material_index in range(1, len(data["materials"])):
			print("\t\t" + data["materials"][material_index])

		# calculating AABB 
		box = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
		for vertex in data["vertices"]:
			for index in range(3):
				box[index] = min(box[index], vertex[index])
				gbox[index] = min(gbox[index], vertex[index])
			for index in range(3, 6):
				box[index] = max(box[index], vertex[index % 3])
				gbox[index] = max(gbox[index], vertex[index % 3])

		if not arguments.disable_grid_snap:
			box[0], box[1], box[2] = tuple(vector3_grid_snap(box[0:3], arguments.grid_snap_step))
			box[3], box[4], box[5] = tuple(vector3_grid_snap(box[3:6], arguments.grid_snap_step))
		print(f"\tAABB: ({box[0]:g} {box[1]:g} {box[2]:g}, {box[3]:g} {box[4]:g} {box[5]:g})")
		print(f"\tSize: ({(box[3] - box[0]):g}, {(box[4] - box[1]):g}, {(box[5] - box[2]):g})\n")

	print('Material List: "', end = "")
	for material_index in range(1, len(map_materials)):
		print(map_materials[material_index] + ";", end = "")
	print('"')

	if not arguments.disable_grid_snap:
		gbox[0], gbox[1], gbox[2] = tuple(vector3_grid_snap(gbox[0:3], arguments.grid_snap_step))
		gbox[3], gbox[4], gbox[5] = tuple(vector3_grid_snap(gbox[3:6], arguments.grid_snap_step))
	print(f"AABB: ({gbox[0]:g} {gbox[1]:g} {gbox[2]:g}, {gbox[3]:g} {gbox[4]:g} {gbox[5]:g})")
	print(f"Size: ({(gbox[3] - gbox[0]):g}, {(gbox[4] - gbox[1]):g}, {(gbox[5] - gbox[2]):g})")
	quit()

# creating material lists
for index in range(len(map_materials)):
	if index >= len(arguments.material_list):
		arguments.material_list.append(arguments.material)
	elif arguments.material_list[index].strip() == "":
		arguments.material_list[index] = arguments.material
	if index >= len(arguments.skip_material_list):
		arguments.skip_material_list.append(arguments.skip_material)
	elif arguments.skip_material_list[index].strip() == "":
		arguments.skip_material_list[index] = arguments.skip_material

# trying to open output file to read map group count
output_group_count = 0
if arguments.append_to_output:
	try:
		input_file = open(arguments.output, 'r')
	except Exception:
		print(f"Failed opening output file: {arguments.output}")
		quit()

	for line in input_file:
		split = line.strip().replace('"', ' ').split()
		if len(split) >= 2 and split[0] == "_tb_id" and split[-1].isnumeric():
			output_group_count = max(output_group_count, int(split[-1]))
	input_file.close()
map_group_count = output_group_count

# trying to open output file for writing
output_file = None
try:
	if arguments.append_to_output:
		output_file = open(arguments.output, "a")
	else:
		output_file = open(arguments.output, "w")
except Exception:
	print(f"Failed writing output file: {arguments.output}")
	quit()



def write_group_entity(name, parent_group_id = None):
	global map_group_count
	map_group_count += 1
	output_file.write("{\n")
	output_file.write('"classname" "func_group"\n')
	output_file.write('"_tb_type" "_tb_group"\n')
	output_file.write(f'"_tb_name" "{name}"\n')
	output_file.write(f'"_tb_id" "{map_group_count}"\n')
	if parent_group_id != None:
		output_file.write(f'"_tb_group" "{parent_group_id}"\n')
	output_file.write("}\n")
	return map_group_count



def write_brush(triangle, normal_offset, mode = 0):
	a, b, c = triangle[0], triangle[1], triangle[2]
	center = triangle_get_center(a, b, c)
	normal = triangle_get_counterclockwise_normal(a, b, c)
	d_direction = vector3_multiply_by_scalar(normal, normal_offset)
	bv = [a, b, c, vector3_substract(center, d_direction)]

	# snapping brush vertices to grid
	if not arguments.disable_grid_snap:
		for index in range(len(bv)):
			bv[index] = vector3_grid_snap(bv[index], arguments.grid_snap_step)

	# formatting brush vertices for writing
	fbv = []
	for index in range(len(bv)):
		fbv.append(f"( {bv[index][0]:g} {bv[index][1]:g} {bv[index][2]:g} )")

	uv = triangle_get_standard_uv
	if arguments.uv_valve:
		uv = triangle_get_valve_uv

	material_index = map_materials.index(triangle[4])
	material_name = arguments.material_list[material_index]
	skip_material_name = arguments.skip_material_list[material_index]
	if mode == 1:
		skip_material_name = material_name

	# writing brush planes
	if mode == 0:
		output_file.write("{\n")
	if normal_offset > 0.0:
		if mode == 0 or mode == 1:
			output_file.write(f"{fbv[0]} {fbv[3]} {fbv[2]} {skip_material_name} {uv(bv[0], bv[3], bv[2])} 0 1 1\n")
			output_file.write(f"{fbv[1]} {fbv[3]} {fbv[0]} {skip_material_name} {uv(bv[1], bv[3], bv[0])} 0 1 1\n")
			output_file.write(f"{fbv[2]} {fbv[3]} {fbv[1]} {skip_material_name} {uv(bv[2], bv[3], bv[1])} 0 1 1\n")
		if mode == 0 or mode == 2:
			output_file.write(f"{fbv[0]} {fbv[2]} {fbv[1]} {material_name} {uv(bv[0], bv[2], bv[1])} 0 1 1\n")
	else:
		if mode == 0 or mode == 1:
			output_file.write(f"{fbv[0]} {fbv[2]} {fbv[3]} {skip_material_name} {uv(bv[0], bv[2], bv[3])} 0 1 1\n")
			output_file.write(f"{fbv[1]} {fbv[0]} {fbv[3]} {skip_material_name} {uv(bv[1], bv[0], bv[3])} 0 1 1\n")
			output_file.write(f"{fbv[2]} {fbv[1]} {fbv[3]} {skip_material_name} {uv(bv[2], bv[1], bv[3])} 0 1 1\n")
		if mode == 0 or mode == 2:
			output_file.write(f"{fbv[0]} {fbv[1]} {fbv[2]} {material_name} {uv(bv[0], bv[1], bv[2])} 0 1 1\n")
	if mode == 0:
		output_file.write("}\n")



def write_entity(name, smooth_groups, parent_group_id = None, is_convex = False):
	entity_group_id = parent_group_id
	if len(smooth_groups) > 1:
		entity_group_id = write_group_entity(name, parent_group_id)
	for smooth_group in smooth_groups:
		triangles = smooth_groups[smooth_group]

		output_file.write("{\n")
		output_file.write(f'"classname" "{arguments.classname}"\n')
		output_file.write(f'"_phong" "{int(smooth_group != 0)}"\n')
		if arguments.phong_angle != 89.0:
			output_file.write(f'"_phong_angle" "{arguments.phong_angle}"\n')
		if entity_group_id != None:
			output_file.write(f'"_tb_group" "{entity_group_id}"\n')

		if is_convex and len(triangles) > 0:
			output_file.write("{\n")
			for triangle in triangles:
				write_brush(triangle, 1.0, 2)
			output_file.write("}\n")
		elif arguments.secondary_normal_offset != None:
			for triangle in triangles:
				if not arguments.secondary_normal_brush:
					output_file.write("{\n")
					write_brush(triangle, -arguments.secondary_normal_offset, 1)
					write_brush(triangle, arguments.normal_offset, 1)
					output_file.write("}\n")
				else:
					write_brush(triangle, -arguments.secondary_normal_offset, 0)
					write_brush(triangle, arguments.normal_offset, 0)
		else:
			for triangle in triangles:
				write_brush(triangle, arguments.normal_offset, 0)
		output_file.write("}\n")



def convexify_smooth_groups(smooth_groups):
	if not len(smooth_groups) > 0:
		return
	object_smooth_group = 0
	if (not 0 in smooth_groups) or (len(smooth_groups) > 1):
		object_smooth_group = 1
	object_triangles = []
	for smooth_group_triangles in smooth_groups.values():
		object_triangles.extend(smooth_group_triangles)
	object_normals, object_planes = [], []
	for triangle in object_triangles:
		a, b, c = triangle[0], triangle[1], triangle[2]
		if not arguments.disable_grid_snap:
			a = vector3_grid_snap(a, arguments.grid_snap_step)
			b = vector3_grid_snap(b, arguments.grid_snap_step)
			c = vector3_grid_snap(c, arguments.grid_snap_step)
		normal = triangle_get_counterclockwise_normal(a, b, c)
		is_unique_normal = True
		for object_normal in object_normals:
			d = vector3_substract(object_normal, normal)
			if vector3_length_squared(d) < arguments.squared_epsilon:
				is_unique_normal = False
				break
		if is_unique_normal:
			object_normals.append(normal)
			object_planes.append(triangle)
	smooth_groups.clear()
	smooth_groups[object_smooth_group] = object_planes



def write_path_corner_enity(origin, targetname, target, parent_group_id = None, flag = None):
	o = origin
	if not arguments.disable_grid_snap:
		o = vector3_grid_snap(origin, 1.0)
	output_file.write("{\n")
	output_file.write('"classname" "path_corner"\n')
	output_file.write(f'"origin" "{o[0]:g} {o[1]:g} {o[2]:g}"\n')
	output_file.write(f'"targetname" "{targetname}"\n')
	output_file.write(f'"target" "{target}"\n')
	output_file.write(f'"wait" "{0 if flag != None else -1}"\n')
	output_file.write(f'"_tb_group" "{parent_group_id}"\n')
	output_file.write("}\n")



# starting to write output file
if not arguments.append_to_output:
	output_file.write(f"// Game: {arguments.game}\n")
	if arguments.uv_valve:
		output_file.write("// Format: Valve\n")
	else:
		output_file.write("// Format: Standard\n")

# writing entities
if arguments.disable_objects:
	for data_index, data in enumerate(input_data):
		smooth_groups = {}
		for triangle in data["triangles"]:
			if not triangle[3] in smooth_groups:
				smooth_groups[triangle[3]] = []
			smooth_groups[triangle[3]].append(triangle)
		write_entity(data["name"], smooth_groups, None, data_index + 1)
else:
	for data_index, data in enumerate(input_data):
		data_group_id = None
		data_is_convex = ("convex" in data["name"])
		for object_index, object_name in enumerate(data["objects"]):
			smooth_groups = {}
			for triangle in data["triangles"]:
				if triangle[5] == object_name:
					if not triangle[3] in smooth_groups:
						smooth_groups[triangle[3]] = []
					smooth_groups[triangle[3]].append(triangle)

			if input_is_directory and len(smooth_groups) > 0 and data_group_id == None:
				data_group_id = write_group_entity(data["name"], None)

			object_is_convex = False
			if not arguments.disable_convex_objects and len(smooth_groups) > 0:
				if (data_is_convex and not "concave" in object_name):
					if object_name != "":
						object_is_convex = True
				if "convex" in object_name:
					object_is_convex = True
				if object_is_convex:
					convexify_smooth_groups(smooth_groups)

			write_entity(object_name, smooth_groups, data_group_id, object_is_convex)

# writing path corner entities
for data_index, data in enumerate(input_data):
	path_corners = {}
	targeted_path_corners = {}
	for line in data["lines"]:
		line_object = ""
		if not arguments.disable_objects:
			line_object = line[0]
		if not line_object in path_corners:
			path_corners[line_object] = {}
			targeted_path_corners[line_object] = set()
		for index in range(1, len(line)):
			vertex_index = line[index]
			vertex = data["vertices"][vertex_index]
			if not vertex_index in path_corners[line_object]:
				path_corners[line_object][vertex_index] = [vertex, None]
			# some targets have to be skipped for branching paths
			if index < len(line) - 1:
				next_vertex_index = line[index + 1]
				next_vertex = data["vertices"][next_vertex_index]
				path_corners[line_object][vertex_index][1] = next_vertex_index
				targeted_path_corners[line_object].add(next_vertex_index)

	for object_name in path_corners:
		path_group_name = object_name if object_name != "" else "paths"
		adjusted_object_name = object_name if object_name != "" else "unnamed"
		path_group_id = write_group_entity(path_group_name, None)

		path_start_index = -1
		for index in path_corners[object_name]:
			if not index in targeted_path_corners[object_name]:
				path_start_index = index
		if path_start_index == -1 and len(path_corners[object_name].keys()):
			path_start_index = list(path_corners[object_name].keys())[0]

		for index in path_corners[object_name]:
			origin, target_index = tuple(path_corners[object_name][index])
			targetname = f'{data["name"]}/{adjusted_object_name}-{index}'
			target = f'{data["name"]}/{adjusted_object_name}-{target_index}'
			if index == path_start_index:
				targetname = f'{data["name"]}/{adjusted_object_name}'
			if target_index == path_start_index:
				target = f'{data["name"]}/{adjusted_object_name}'
			write_path_corner_enity(origin, targetname, target, path_group_id, target_index)

# closing output file
output_file.close()
