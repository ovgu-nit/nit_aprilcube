# Aprilcube
by Vincent Rist (vincent.rist@ovgu.de)

![image of printed cube](print3D/printed.png)

The aprilcube is a cube object with [apriltags](https://april.eecs.umich.edu/software/apriltag) on each face. 
It is an "easy-to-detect" object for e.g. a robotic pick and place task. 

## Features

- OpenSCAD file to 3D-print and assemble the cube yourself
- Latex file to render a printout which allows you to craft a paper version of the cube from a A4 sheet of paper
- 3D model files for the Gazebo simulation.
- ROS2 integration:
  - **aprilcube_detector**, a ros2 node that subscribes to the apriltag detections and the camera information, keeps track of the detected aprilcube, and updates Moveits planning scene (adds the cube itself and a pseudo table underneith)
  - a webcam demo to test the apriltag detection with a webcam
  - a launchfile to spawn the aprilcube model in the Gazebo simulation
  
## Design

- cube side lengths are **5 cm** (as previously used by other NIT cube obejcts)
- apriltags are the first 6 tags of the [**tag16h5**-family](https://github.com/AprilRobotics/apriltag-imgs/tree/master/tag16h5)

## Tag Textures

The original tag images (see `meshes/tags_original`) as provided by the apriltag repo have a minimal size of 8 by 8 pixels. Using those directly as textures causes many simulators including Gazebo to blur the images. To overcome this, cd into the package directony and run
```bash
python3 scale_up_tags.py
```
The script creates scaled up version (512 px by default) of the tags and places them in `meshes/tags_scaled`.

## Simulation

- To use the aprilcube in Gazebo (tested with ROS2 Humble), make sure the package and the model file match this structure (default if you install this repo as a ROS2-package in your workspace):
    ```
    ros2_ws/
    └ src/nit_aprilcube/
        ├ ... (other files)
        └ models/
            └ aprilcube/
                ├ meshes/
                │   ├ tags_scaled/
                │   │   └ ...
                │   └ aprilcube.dae
                ├ aprilcube.sdf
                ├ model.config
                └ ...
    ```
- Gazebo needs to know the path to the model file before launch. You have two options:
    1. Add the install path to the environment variable by calling:
        ```bash
        export GAZEBO_MODEL_PATH="$GAZEBO_MODEL_PATH:$(ros2 pkg prefix nit_aprilcube)/share/nit_aprilcube/models"
        ```
    2. or – if you start Gazebo with a launch file – at this in the launch file before Gazebo:
        ```python
        SetEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value=[
                EnvironmentVariable('GAZEBO_MODEL_PATH', default_value=''),
                os.pathsep,
                os.path.join(get_package_share_directory('nit_aprilcube'), 'models'),
            ],
        )
        ```
- Install dependencies with rosdep and build your workspace with colcon.
- Spawn the cube to Gazebo:
    1. either manually through the GUI. You should see the specified path in the Insert-panel.
    2. or automatically in your launch-file by using the launch description of this package:
    ```python
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
            os.path.join(nit_aprilcube_dir, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'image_raw': '/head_front_camera/rgb/image_raw',
            'x': '0.7'
        }.items()
    )
    ```
   Optional launch arguments are:
    - 'image_raw': rgb image input topic for the tag detection
    - 'image_annotated': output image topic with annotated tags
    - 'detections': output topic of tag detections
    - 'spawn_delay_sec': delay of spawn in seconds, default 0
    - 'x': 1.0, 'y': 0.0, 'z': 1.0, 'R': 0.1, 'P': 0.1, 'Y': 0.1 (position and orientation parameters of the cube pose with their respective defaults)

## Printing

The printable STLs are modeled with [OpenSCAD](https://openscad.org/) in `print/aprilcube.scad`.
- `print/svg/`: vectorized versions of black pixels of the tags to be imported in OpenSCAD. 
- (ignored) `print/stl/`: Rendered STL files of the 3D objects. Excluded from Git. If you have OpenSCAD installed you can open the .scad-file and render the STLs yourself.
- (ignored) `print/3mf/`: Compiled gcodes and print settings for the Bamboolab X1.

**Print instructions:**
1. **tagcube**: First print the cube base created by the `tagcube()` module using white color. Can be printed without support. 
2. [Optional] **tolerance test**: The `toltest_plates()`-module renders 6 version of the tag1 plate with tolerances ranging from 0 to 0.25 mm. These plates have a text engraving stating the thier tolerance for reference after printing. Print them, check which of the plates fits best in the corresponding slot on the tagcube. Then set the parameter in the .scad file accordingly: 
    ```openscad
    tol_to_tag = 0.15; // tolerance taken away from the tags (only influences the tags), should be >0 and <tag_shape_offset (see comment at tolerance test below)
    ```
    This parameter modifies the plates and would require rerendering them.
    Tolerance of 0.15 mm formed a tight connection between tag and cube after hammering (no glue necessary) with the Bamboo Lab X1 setup. 
3. **tagplates**: Then print the six black tag plates. The `tagplates_layout()`-module renders them in a "ready-to-print"-orientation.
4. Assemble the aprilcub by inserting the plates into the corrent slot on the cube base. Looser tolerances might require glue while tighter renders form tight connecting after hammering.


## Printout

You have no 3D printer, but want to become an aprilcube owner nonetheless? If you instead have a 2D printer, scissors and glue, referr to `print2D/`. The latex file provides a flattened aprilcube texture with cut, fold, and glue instructions.
