# Aprilcube
by Vincent Rist (vincent.rist@ovgu.de)

![image of printed cube](print3D/printed.png)

The aprilcube is a cube object with [apriltags](https://april.eecs.umich.edu/software/apriltag) on each face. 
It was modeled for as an "easy-to-detect" object for implementing a pick and place task. The [apriltag_ros](https://github.com/christianrauch/apriltag_ros) repo provides a ROS2 integrating that detects tags in a camera image and then estimates the tags pose in 3D space. From this the cube pose can be easily computed. 

This project provides all file necessary to add the aprilcube to a Gazebo simulation. Furthermore, files to 3D-print and deploy in the real world are provided.

## Design

- cube side lengths are **5 cm** (as previously used by other NIT cube obejcts)
- apriltag are the first 6 of the [**tag16h5**-family](https://github.com/AprilRobotics/apriltag-imgs/tree/master/tag16h5)

## Tag Textures

The original tag images (see `meshes/tags_original`) as provided by the apriltag repo have a minimal size of 8 by 8 pixels. Using those directly as textures causes many simulators including Gazebo to blur the images (many use interpolation shading rather then closests). To overcome this the python script `scale_up_tags.py` scales up the images to 512 (default) and places them in `meshes/tags_original`. If these versions are not yet generated, cd into the apriltag directory and call:
```
python3 scale_up_tags.py
```

The scaled up versions are ignored from git if you want to use version control.

## Simulation

- To use in Gazebo (tested with ROS2 Humble), make sure the file correctly are placed in your package:
    ```
    ros2_ws/
    └ src/your_pkg/
        └ models/
            ├ ... (other models)
            └ aprilcube/ (<-- put it here)
                ├ meshes/
                │   ├ tags_XXXpx/
                │   │   └ ...
                │   └ aprilcube.dae
                ├ aprilcube.sdf
                ├ model.config
                └ ...
    ```
- Make sure your symlink install or share the file correctly in your setup.py if you use python
- Either add the cube manually through the GUI of Gazebo or automatically in your launch-file, e.g:
    ```python
    from launch_ros.actions import Node
    from ament_index_python.packages import get_package_share_directory


    # Share the package directoy with gazebo
    gazebo_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=[
            EnvironmentVariable('GAZEBO_MODEL_PATH', default_value=''),
            os.pathsep,
            str(Path(get_package_share_directory('your_pkg')) / 'models'),
        ],
    )

    # Create a spawn action for the cube
    spawn_cube = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name=f"spawn_aprilcube",
        output='screen',
        arguments=[
            '-database', 'aprilcube',
            '-entity', f'aprilcube',
            '-x', f'0.7',
            '-y', f'0',
            '-z', f'1.2',
        ],
        condition=LaunchConfigurationEquals('gazebo_version', 'classic'),
    )

    # and add it to the LaunchDescription
    ```

## Printing

The printable STLs are modeled with [OpenSCAD](https://openscad.org/) in `print/aprilcube.scad`.
- `print/svg/`: vectorized versions of black pixels of the tags to be imported in OpenSCAD. 
- `print/stl/`: Rendered STL files of the 3D objects. Excluded from Git. If you have OpenSCAD installed you can open the .scad-file and render the STLs yourself.
- `print/3mf/`: Compiled gcodes and print settings for the Bamboolab X1.

Here are the print instructions:
1. **tagcube**: First print the cube base created by the `tagcube()` module using white color. Can be printed without support. 
2. [Optional] **tolerance test**: The `toltest_plates()`-module renders 6 time the tag1 plat with tolerances range from 0 to 0.25 mm. Print these plates. These models have a 1 layer text stating the thier tolerance for reference. After printing, check which of the plates fits best in the corresponding slot on the tagcube. Then set the parameter accordingly: 
    ```openscad
    tol_to_tag = 0.15; // toleracne taken away from the tags (only influences the tags), should be >0 and <tag_shape_offset (see comment for tolerance test below)
    ```
    This parameter changes the plate STLs and would require rerendering them.
    Tolerance of 0.15 mm formed a tight connection between tag and cube after hammering (no glue necessary) with the Bamboo Lab X1 setup. 
3. **tagplates**: Then print the six tag plates. The `tagplates_layout()`-module renders them in a "ready-to-print"-orientation.
4. Assemble the aprilcub by inserting the plates into the corrent slot on the cube base. Looser tolerances might require glue while tighter renders form tight connecting after hammering.


## Printout

You have no 3D printer, but want to become an aprilcube owner nonetheless? If you instead a 2D printer, scissors and glue, referr to `printout/`. The latex file provides a flattened texture of the aprilcube with cut, fold, and glue instructions.
