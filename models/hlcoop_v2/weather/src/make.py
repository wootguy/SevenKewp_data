import math, colorsys, os
from PIL import Image

# special studiomdl needed to compile the model
# I forget what's changed but it's the same version from the media player plugin.

def normalize_vector(x, y, z):
	x, y, z = float(x), float(y), float(z)
	magnitude = math.sqrt(x**2 + y**2 + z**2)
	
	if magnitude == 0:
		raise ValueError("Cannot normalize a zero vector.")
	
	return x / magnitude, y / magnitude, z / magnitude

# used to create the skeleton and assign verts to each bone,
# but i kept commenting out stuff, copying output, then re-running instead of doing this properly
def parse_smd_vertices(file_path):
	vertices = set()
	with open(file_path, 'r') as file:
		lines = file.readlines()
	
	inside_skeleton = False
	inside_triangles = False
	bones = []
	
	for line in lines:
		line = line.strip()
		if line == "time 0":
			inside_skeleton = True
			continue
		elif line == "triangles":
			inside_triangles = True
			inside_skeleton = False
			continue
		elif line == "end" and inside_triangles:
			break  # End of triangles section
		
		if inside_skeleton and line:
			parts = line.split()
			if len(parts) >= 3:  # A valid vertex definition line
				try:
					x, y, z = map(float, parts[1:4])  # Extract vertex coordinates
					
					if len(bones) == 0:
						print("%d 0.0 0.0 0.0 0.0 0.0 0.0" % (len(bones)))
					else:
						vec = normalize_vector(x, y, z)
						#print("%d %f %f %f 0.0 0.0 0.0" % (len(bones), vec[0]*32, vec[1]*32, vec[2]*32))
						#print("%d %f %f %f 0.0 0.0 0.0" % (len(bones), vec[0]*8192, vec[1]*8192, vec[2]*8192))
						print("%d %f %f %f 0.0 0.0 0.0" % (len(bones), vec[0], vec[1], vec[2]))
					bones.append((x, y, z))
				except ValueError as e:
					print(e)
					continue  # Skip lines that don't represent vertices
		
		if inside_triangles and line:
			parts = line.split()
			if len(parts) >= 3:  # A valid vertex definition line
				try:
					x, y, z = map(float, parts[1:4])  # Extract vertex coordinates
					vertices.add((x, y, z))
					
					for idx, bone in enumerate(bones):
						vec = normalize_vector(x, y, z)
						
						if abs(vec[0] - bone[0]) < 0.1 and abs(vec[1] - bone[1]) < 0.1 and abs(vec[2] - bone[2]) < 0.1:
							print("%d %f %f %f 0.0 0.0 1.0 0.0 0.0" % (idx, vec[0], vec[1], vec[2]))
							#print("%d %f %f %f 0.0 0.0 1.0 0.0 0.0" % (idx, x, y, z))
							break
				except ValueError as e:
					print (e)
					continue  # Skip lines that don't represent vertices
			else:
				print(line)
	
	return vertices

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

def gen_textures():
	global pad
	global hue_count
	
	colorSz = 3
	width = colorSz*3
	
	hues = generate_hue_wheel_palette(hue_count)
	hues = [0] + hues
	
	palidx = 0
	
	with open('colors.c', 'w') as file:
		file.write("const int g_fog_skins = %d;\n\n" % (hue_count+1))
		file.write("unsigned int g_fog_palette[%d][256] = {\n" % (hue_count+1))
		
		for hueidx, hue in enumerate(hues):
			img = Image.new('RGB', (16*pad, 16*pad))
			pixels = img.load()
		
			file.write("\t{")
			for y in range(0, 16, 1):
				for x in range(0, 16, 1):
					sat = (y / 15.0) * 0.9 + 0.1
					bright = (x / 15.0) * 0.9 + 0.1
					
					if hueidx == 0:
						sat = 0 # first pal is greyscale
						bright = (y*16 + x) / 255
					
					r, g, b = colorsys.hsv_to_rgb(hue, sat, bright)
					r = int(r * 255)
					g = int(g * 255)
					b = int(b * 255)
					
					file.write(f"0x{r:02X}{g:02X}{b:02X}")
					if y!= 15 or x != 15:
						file.write(',')
					
					for px in range(0, pad):
						for py in range(0, pad):
							pixels[x*pad + px, y*pad + py] = (r, g, b)
			file.write("},\n")
				
			img = img.quantize()
			print('{ "pal_%d.bmp" }' % palidx)
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
			gen_smd('fog.smd', 'fog_%d.smd' % idx, x / float(sz), 1.0 - y / float(sz))
			idx += 1

def gen_qc(num_bodies, num_pal):
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
		
		file.write('$sequence idle "idle" fps 1 ACT_IDLE 1\n')
		dists = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]
		for d in dists:
			file.write('$sequence dist_%d "dist_%d" fps 1 ACT_IDLE 1\n' % (d,d))

pad = 3 # size of a color pixel in each palette texture, to prevent color leaking (happens even with tex filtering off)

# up to 255 is possible (save 1 for greyscale), but there are diminishing returns past 32 or so and higher costs:
# longer precache time, file size, possibly client crashes sooner due to texture load leak(?)
# number should divide 360 evenly so that you can get pure green/blue/etc. (green is 120 degrees from red)
hue_count = 60

#parse_smd_vertices('fog.smd')
gen_textures()
gen_bodies()
gen_qc(256, hue_count+1)
os.system("studiomdl fog.qc")