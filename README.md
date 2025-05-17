# Quake mapping tools

## Convert .obj scenes to maps
![obj2map.py](screenshots/obj2map.png)

#### ```obj2map.py --info examples/scene.obj```
```
examples/scene.obj:
	Objects:
		 [01] BezierCircle
		 [02] BezierCurve
		 [03] Cube-convex
		 [04] Cube.001-convex
		 [05] Cube.002-convex
		 [06] Cube.003-convex
		 [07] Cube.004
		 [08] Cylinder-convex
		 [09] Grid-convex
		 [10] Icosphere-convex
		 [11] Plane
		 [12] Suzanne
		 [13] Torus
	Materials:
		BLUE
		GREEN
		MONKEY
		RED
		WHITE
	AABB: (-640 -640 -128, 640 640 435.25)
	Size: (1280, 1280, 563.25)

Material List: "BLUE;GREEN;MONKEY;RED;WHITE;"
AABB: (-640 -640 -128, 640 640 435.25)
Size: (1280, 1280, 563.25)
```

## Convert heightmaps to maps
![height2map.py](screenshots/height2map.png)

#### ```height2map.py --material GRASS --chunk_size 16 examples/height.png```