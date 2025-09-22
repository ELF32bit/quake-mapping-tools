#!/usr/bin/python
import os, argparse, math
from PIL import Image

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("input", type=str)
parser.add_argument("--height", type=float, default=256.0, help="|")
parser.add_argument("--unit_size", type=float, default=64.0, help="|")
parser.add_argument("--grid_snap_step", type=float, default=0.125, help="|")
parser.add_argument("--disable_grid_snap", action="store_true", help="|")
parser.add_argument("--classname", type=str, default="func_detail", help="|")
parser.add_argument("--material", type=str, default="__TB_empty", help="|")
parser.add_argument("--skip_material", type=str, default="SKIP", help="|")
parser.add_argument("--offset", type=float, default=32.0, help="|")
parser.add_argument("--chunk_size", type=int, default=0, help="|")
parser.add_argument("--x_offset", type=float, default="0.0", help="|")
parser.add_argument("--y_offset", type=float, default="0.0", help="|")
parser.add_argument("--x_scale", type=float, default="1.0", help="|")
parser.add_argument("--y_scale", type=float, default="1.0", help="|")
parser.add_argument("--phong_disabled", action="store_true", help="|")
parser.add_argument("--phong_angle", type=float, default = "89.0", help="|")
parser.add_argument("--game", type=str, default="Generic", help="|")
parser.add_argument("--output", type=str, help="|")
arguments = parser.parse_args()

# using input file name for the output if not provided
input_basename = os.path.basename(arguments.input)
input_name = os.path.splitext(input_basename)[0]
if arguments.output == None:
	arguments.output = input_name + ".map"

def grid_snap(v, s):
	return math.floor(v / s + 0.5) * s

# shortcuts for easier reading
s = arguments.unit_size
h = arguments.height
o = -arguments.offset
cs = arguments.chunk_size

# trying to open input file
input_file = None
try:
	input_file = Image.open(arguments.input)
except Exception:
	print(f"Failed loading image: {arguments.input}")
	quit()

# loading heightmap pixels
heightmap = input_file.convert("LA")
heightmap = heightmap.transpose(Image.FLIP_TOP_BOTTOM)
pixels = heightmap.load()
iw, ih = heightmap.size
# disabling chunking
cs = min(iw, ih) if cs <= 0 else cs

# sanity checks
if iw > 256 or ih > 256:
	print("Don't use heightmaps larger than 256x256")
	quit()
if iw % 2 != 0 or ih % 2 != 0:
	print("Heightmap dimensions are not divisible by 2")
	quit()
if arguments.chunk_size > 0:
	if iw % cs != 0 or ih % cs != 0:
		print("Heightmap dimensions are not divisible by the chunk size")
		quit()

# trying to open output file
output_file = None
try:
	output_file = open(arguments.output, "w")
except Exception:
	print(f"Failed writing output output_file: {arguments.output}")
	quit()

# checking if grouping is necessary
use_group = False
if arguments.chunk_size > 0:
	if ((iw * ih) // (cs * cs)) > 1:
		use_group = True

# writing output file
output_file.write(f"// Game: {arguments.game}\n")
output_file.write("// Format: Valve\n")

if use_group:
	output_file.write("{\n")
	output_file.write('"classname" "func_group"\n')
	output_file.write('"_tb_type" "_tb_group"\n')
	output_file.write(f'"_tb_name" "{input_name}"\n')
	output_file.write('"_tb_id" "1"\n')
	output_file.write("}\n")

def write_entity_properties():
	output_file.write(f'"classname" "{arguments.classname}"\n')
	output_file.write(f'"_phong" "{int(not arguments.phong_disabled)}"\n')
	if not arguments.phong_disabled:
		output_file.write(f'"_phong_angle" "{arguments.phong_angle}"\n')
	if use_group:
		output_file.write(f'"_tb_group" "1"\n')

def write_brush_at(i, j):
	x, y, ix, iy = (i * s, j * s, i + iw // 2, j + ih // 2)

	# discarding brushes where image pixels are transparent
	a00 = pixels[(ix+0)%iw, (iy+0)%ih][1] / 255.0
	a10 = pixels[(ix+1)%iw, (iy+0)%ih][1] / 255.0
	a01 = pixels[(ix+0)%iw, (iy+1)%ih][1] / 255.0
	a11 = pixels[(ix+1)%iw, (iy+1)%ih][1] / 255.0
	if a00 == 0.0:
		return

	# reading height values from image pixels
	h00 = a00 * h * pixels[(ix+0)%iw, (iy+0)%ih][0] / 255.0
	h10 = a10 * h * pixels[(ix+1)%iw, (iy+0)%ih][0] / 255.0
	h01 = a01 * h * pixels[(ix+0)%iw, (iy+1)%ih][0] / 255.0
	h11 = a11 * h * pixels[(ix+1)%iw, (iy+1)%ih][0] / 255.0

	# snapping height values
	if not arguments.disable_grid_snap:
		h00 = grid_snap(h00, arguments.grid_snap_step)
		h10 = grid_snap(h10, arguments.grid_snap_step)
		h01 = grid_snap(h01, arguments.grid_snap_step)
		h11 = grid_snap(h11, arguments.grid_snap_step)

	output_file.write("{\n")
	output_file.write(f"( {x:g} {y:g} {o:g} ) ( {x:g} {y+s:g} {o:g} ) ( {x:g} {y:g} {h00:g} ) {arguments.skip_material} [ 0 1 0 0 ] [ 0 0 -1 0 ] 0 1 1\n")
	output_file.write(f"( {x:g} {y:g} {o:g} ) ( {x:g} {y:g} {h00:g} ) ( {x+s:g} {y:g} {o:g} ) {arguments.skip_material} [ 1 0 0 0 ] [ 0 0 -1 0 ] 0 1 1\n")
	output_file.write(f"( {x:g} {y:g} {o:g} ) ( {x+s:g} {y:g} {o:g} ) ( {x:g} {y+s:g} {o:g} ) {arguments.skip_material} [ 1 0 0 0 ] [ 0 -1 0 0 ] 0 1 1\n")
	output_file.write(f"( {x:g} {y:g} {h00:g} ) ( {x:g} {y+s:g} {h01:g} ) ( {x+s:g} {y:g} {h10:g} ) {arguments.material} [ 1 0 0 {arguments.x_offset:g} ] [ 0 -1 0 {arguments.y_offset:g} ] 0 {arguments.x_scale:g} {arguments.y_scale:g}\n")
	output_file.write(f"( {x:g} {y+s:g} {o:g} ) ( {x+s:g} {y:g} {o:g} ) ( {x+s:g} {y:g} {h10:g} ) {arguments.skip_material} [ 0 1 0 0 ] [ 0 0 -1 0 ] 0 1 1\n")
	output_file.write("}\n")

	output_file.write("{\n")
	output_file.write(f"( {x:g} {y+s:g} {o:g} ) ( {x+s:g} {y:g} {h10:g} ) ( {x+s:g} {y:g} {o:g} ) {arguments.skip_material} [ 0 1 0 0 ] [ 0 0 -1 0 ] 0 1 1\n")
	output_file.write(f"( {x:g} {y:g} {o:g} ) ( {x+s:g} {y:g} {o:g} ) ( {x:g} {y+s:g} {o:g} ) {arguments.skip_material} [ 1 0 0 0 ] [ 0 -1 0 0 ] 0 1 1\n")
	output_file.write(f"( {x+s:g} {y+s:g} {h11:g} ) ( {x+s:g} {y:g} {h10:g} ) ( {x:g} {y+s:g} {h01:g} ) {arguments.material} [ 1 0 0 {arguments.x_offset:g} ] [ 0 -1 0 {arguments.y_offset:g} ] 0 {arguments.x_scale:g} {arguments.y_scale:g}\n")
	output_file.write(f"( {x:g} {y+s:g} {o:g} ) ( {x+s:g} {y+s:g} {o:g} ) ( {x:g} {y+s:g} {h01:g} ) {arguments.skip_material} [ 1 0 0 0 ] [ 0 0 -1 0 ] 0 1 1\n")
	output_file.write(f"( {x+s:g} {y:g} {o:g} ) ( {x+s:g} {y:g} {h10:g} ) ( {x+s:g} {y+s:g} {o:g} ) {arguments.skip_material} [ 0 1 0 0 ] [ 0 0 -1 0 ] 0 1 1\n")
	output_file.write("}\n")

if arguments.chunk_size > 0:
	for x_chunk in range(iw // cs):
		for y_chunk in range(ih // cs):
			output_file.write("{\n")
			write_entity_properties()
			for i in range(x_chunk * cs - iw // 2, (x_chunk + 1) * cs - iw // 2):
				for j in range(y_chunk * cs - ih // 2, (y_chunk + 1) * cs - ih // 2):
					write_brush_at(i, j)
			output_file.write("}\n")
else:
	output_file.write("{\n")
	write_entity_properties()
	for i in range(-iw // 2, iw // 2):
		for j in range(-ih // 2, ih // 2):
			write_brush_at(i, j)
	output_file.write("}\n")

# closing output file
output_file.close()
