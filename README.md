# x3dexport
Blender 2.49 code to export scenes and animations to X3D format. 

This is a python code to be run inside the Blender python console.

This code exports an entire scene to X3D format, including animations.
Attention to scene space optimization was paid, so referenced meshes are not duplicated in the X3D file and are created as references.

Some sensors export were added and their application are made by setting a named empty object as child of the target of the sensor.

This project was developed in 2004 as the first Blender and Python project I created and was set to solve issues for a virtual reality project.

It needs optimizations and is not being maintened.
