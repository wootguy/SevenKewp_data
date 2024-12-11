# This script has code for generating a fog model using solid pixel dither patterns in alpha-tested textures.
# It does the job of fog but is extremely distracting and chaotic looking.
# This method doesn't break transparent ents and requires fewer models than the additive method.

import math, colorsys, os, random, numpy
from PIL import Image

# special studiomdl needed to compile the model
# I forget what's changed but it's the same version from the media player plugin.

def normalize_vector(x, y, z):
	x, y, z = float(x), float(y), float(z)
	magnitude = math.sqrt(x**2 + y**2 + z**2)
	
	if magnitude == 0:
		raise ValueError("Cannot normalize a zero vector.")
	
	return x / magnitude, y / magnitude, z / magnitude

def generate_sphere_coordinates(x, y, z):
	x, y, z = normalize_vector(x, y, z)
	r = numpy.sqrt(x**2 + y**2 + z**2)
	phi = numpy.arctan2(y, x)
	theta = numpy.arccos(z / r)
	
	u = (phi + numpy.pi) / (2 * numpy.pi)  # Normalize longitude to [0, 1]
	v = (numpy.pi - theta) / numpy.pi
	#v = (math.asin(phi / 90.0)) / math.pi
	
	if u > 0.5:
		u = 1 - u
	
	return u,v

# create a body which maps to a pixel in the palette texture
def gen_smd(file_path, file_out, u, v):
	vertices = set()
	with open(file_path, 'r') as file:
		lines = file.readlines()
	
	inside_skeleton = False
	inside_triangles = False
	
	with open(file_out, 'w') as outfile:
		for line in lines:
			line = line.strip()
			if line == "triangles":
				inside_triangles = True
				inside_skeleton = False
				outfile.write(line + "\n")
				continue
			elif line == "end" and inside_triangles:
				outfile.write(line + "\n")
				break  # End of triangles section
			
			if inside_triangles and line:
				parts = line.split()
				if len(parts) >= 3:  # A valid vertex definition line
					try:
						x, y, z = map(float, parts[1:4])  # Extract vertex coordinates
						vertices.add((x, y, z))
						
						uScale = 12 / 11
						tiling = 4.0
						u,v = generate_sphere_coordinates(x, y, z)
						u *= tiling * uScale
						v *= tiling
						outfile.write("%s %f %f %f 0.0 0.0 1.0 %f %f\n" % (parts[0], x, y, z, u, v))
					except ValueError as e:
						print (e)
						continue  # Skip lines that don't represent vertices
				else:
					outfile.write(line + "\n")
			else:
				outfile.write(line + "\n")
	
	return vertices

def generate_hue_wheel_palette(num_colors=256):
    palette = []
    for i in range(num_colors):
        hue = i / float(num_colors)  # Evenly spaced hues
        palette.append(hue)
    return palette

dither_patterns = [
	[[0, 1, 0, 1], [1, 0, 1, 0], [0, 1, 0, 1], [1, 0, 1, 0]], # 50%
	[[1, 0, 1, 0], [0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1]], # 40%?
	[[0, 1, 0, 1], [1, 0, 0, 0], [0, 1, 0, 1], [0, 0, 1, 0]],
	[[1, 0, 1, 0], [0, 1, 0, 0], [1, 0, 1, 0], [0, 0, 0, 0]],
	[[1, 0, 1, 0], [0, 0, 0, 0], [1, 0, 1, 0], [0, 0, 0, 0]],
	[[0, 0, 1, 0], [0, 0, 0, 0], [1, 0, 1, 0], [0, 0, 0, 0]],
	[[0, 0, 1, 0], [0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]],
	[[0, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], # idx 7
]

def gen_textures():
	global pad
	global hue_count
	global dither_patterns
	
	hues = generate_hue_wheel_palette(hue_count)
	hues = [0] + hues
	
	palidx = 0
	
	with open('colors.c', 'w') as file:
		file.write("const int g_fog_skins = %d;\n\n" % (hue_count+1))
		file.write("unsigned int g_fog_palette[%d][256] = {\n" % (hue_count+1))
		
		for dither_level in range(len(dither_patterns) + 1):
			for hueidx, hue in enumerate(hues):
				'''
				#img = Image.new('RGB', (16*pad, 16*pad))
				img = Image.new('RGB', (16, 16))
				pixels = img.load()
			
				file.write("\t{")
				#for y in range(0, 16, 1):
				#	for x in range(0, 16, 1):
				#sat = (y / 15.0) * 0.9 + 0.1
				#bright = (x / 15.0) * 0.9 + 0.1
				
				#if hueidx == 0:
				#	sat = 0 # first pal is greyscale
				#	bright = (y*16 + x) / 255
				
				#r, g, b = colorsys.hsv_to_rgb(hue, sat, bright)
				r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
				r = int(r * 255)
				g = int(g * 255)
				b = int(b * 255)
				
				file.write(f"0x{r:02X}{g:02X}{b:02X}")
				#if y!= 15 or x != 15:
				#	file.write(',')
				#	file.write(',')
				
				for px in range(0, 16):
					for py in range(0, 16):
						if dither_level == 0 or dither_patterns[dither_level-1][px % 4][py % 4]:
							#pixels[x*pad + px, y*pad + py] = (r, g, b)
							pixels[px, py] = (64, 0, 0)
						else:
							pixels[px, py] = (0,0,0)
				file.write("},\n")
				'''
				img = Image.open("clouds_0.bmp")
				img = img.quantize()
				print('{ "pal_%d.bmp" }' % palidx)
				
				palette = img.getpalette()
				pal_pixels = img.getdata()
				new_pixels = []
				new_pal = palette[:]
				
				for c in pal_pixels:
					r = palette[c*3 + 0]
					g = palette[c*3 + 1]
					b = palette[c*3 + 2]
					
					if r == 0 and g == 0 and b == 0:
						new_pixels.append(255) # map blak to transparent
					else:
						new_pixels.append(c)
					
				new_pal[255*3] = 0
				new_pal[255*3+1] = 0
				new_pal[255*3+2] = 255
				
				img.putpalette(new_pal)
				img.putdata(new_pixels)
				img.save("pal_%d.bmp" % palidx)
				palidx += 1
			
		file.write("};\n")

def gen_bodies():
	global pad
	
	sz = 16*pad
	
	idx = 0
	for y in range(1, sz, pad):
		for x in range(1, sz, pad):
			print ('studio "./fog_%d"' % idx)
			gen_smd('fog_bones.smd', 'fog_%d.smd' % idx, x / float(sz), 1.0 - y / float(sz))
			idx += 1

def gen_qc(num_bodies, num_pal):
	global sphere_dists
	
	with open('fog.qc', 'w') as file:
		file.write('$modelname "fog.mdl"\n')
		file.write('$cd "."\n')
		file.write('$cdtexture "."\n')
		file.write('$scale 1.0\n\n')
		
		file.write('$bodygroup body\n{\n')
		for i in range(0, num_bodies):
			file.write('studio "./fog_%d"\n' % i)
		file.write('}\n\n')
		
		file.write('$texturegroup "skinfamilies"\n{\n')
		for i in range(0, num_pal):
			file.write('{ "pal_%d.bmp" }\n' % i)
		file.write('}\n\n')
		
		for i in range(0, num_pal):
			file.write('$texrendermode "pal_%d.bmp" masked\n' % i)
		
		file.write('$sequence idle "idle" fps 1 ACT_IDLE 1\n')
		for d in sphere_dists:
			file.write('$sequence dist_%d "dist_%d" fps 1 ACT_IDLE 1\n' % (d,d))

def gen_bones(file_path, file_out):
	vertices = set()
	with open(file_path, 'r') as file:
		lines = file.readlines()
	
	inside_skeleton = False
	inside_triangles = False
	
	for line in lines:
			line = line.strip()
			if line == "triangles":
				inside_triangles = True
				continue
			elif line == "end" and inside_triangles:
				break  # End of triangles section
			
			if inside_triangles and line:
				parts = line.split()
				if len(parts) >= 3:  # A valid vertex definition line
					try:
						x, y, z = map(float, parts[1:4])  # Extract vertex coordinates
						vertices.add((x, y, z))
					except ValueError as e:
						print (e)
						continue  # Skip lines that don't represent vertices
	
	bones = [(0, 0, 0)]
	bones.append((x, y, z))
	for vert in vertices:
		bones.append(vert)
	
	inside_triangles = False
	
	with open(file_out, 'w') as outfile:
		outfile.write("version 1\n")
		outfile.write("nodes\n")
		for idx, bone in enumerate(bones):
			outfile.write('%d "v%d" %s\n' % (idx, idx, 0 if idx else -1))
		outfile.write("end\n")
		
		outfile.write("skeleton\n")
		outfile.write("time 0\n")
		for idx, bone in enumerate(bones):
			outfile.write('%d %f %f %f 0.0 0.0 0.0\n' % (idx, bone[0], bone[1], bone[2]))
		outfile.write("end\n")
		
		outfile.write("triangles\n")
		for line in lines:
			line = line.strip()
			if line == "triangles":
				inside_triangles = True
				continue
			elif line == "end" and inside_triangles:
				outfile.write(line + "\n")
				break  # End of triangles section
			
			if inside_triangles and line:
				parts = line.split()
				if len(parts) >= 3:  # A valid vertex definition line
					try:
						x, y, z = map(float, parts[1:4])
						no_bones_line = parts[1:]
						
						for idx, bone in enumerate(bones):
							if abs(x - bone[0]) < 0.01 and abs(y - bone[1]) < 0.01 and abs(z - bone[2]) < 0.01:
								outfile.write("%d %s\n" % (idx, " ".join(no_bones_line)))
								break
					except ValueError as e:
						print (e)
						continue  # Skip lines that don't represent vertices
				else:
					outfile.write(line + "\n")
		outfile.write("end\n")
	
	return bones

def gen_anim(file_out, bones, scale, offset):
	with open(file_out, 'w') as outfile:
		outfile.write("version 1\n")
		outfile.write("nodes\n")
		for idx, bone in enumerate(bones):
			outfile.write('%d "v%d" %s\n' % (idx, idx, 0 if idx else -1))
		outfile.write("end\n")
		
		outfile.write("skeleton\n")
		outfile.write("time 0\n")
		for idx, bone in enumerate(bones):
			f = offset if idx else 0
			outfile.write('%d %f %f %f 0.0 0.0 0.0\n' % (idx, bone[0], bone[1], bone[2] + f))
			
		outfile.write("time 1\n")
		for idx, bone in enumerate(bones):
			f = offset if idx else 0
			outfile.write('%d %f %f %f 0.0 0.0 0.0\n' % (idx, bone[0]*scale, bone[1]*scale, bone[2]*scale + f))
		outfile.write("end\n")

pad = 4 # size of a color pixel in each palette texture, to prevent color leaking (happens even with tex filtering off)

# up to 255 is possible (save 1 for greyscale), but there are diminishing returns past 32 or so and higher costs:
# longer precache time, file size, possibly client crashes sooner due to texture load leak(?)
# number should divide 360 evenly so that you can get pure green/blue/etc. (green is 120 degrees from red)
#hue_count = 60
hue_count = 0

# skeleton will be scaled by these amounts, with an animation for each scale. Keyframe 0 = scale 1, keyframe 1 = scale
sphere_dists = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

bones = gen_bones('fog.smd', 'fog_bones.smd')
gen_anim('idle.smd', bones, 1.0, 0)
for d in sphere_dists:
	gen_anim('dist_%d.smd' % d, bones, d, 16384)

gen_textures()
gen_bodies()
gen_qc(256, hue_count+1 * 8)
os.system("studiomdl fog.qc")
os.system("xcopy fog.mdl C:\\Games\\Steam\\steamapps\\common\\Half-Life\\valve_downloads\\models\\hlcoop_v2\\weather\\fog.mdl /Y")