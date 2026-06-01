# Aprilcube
by Vincent Rist (vincent.rist@ovgu.de)

![image of printed cube](print3D/printed.png)

The aprilcube is a cube object with [apriltags](https://april.eecs.umich.edu/software/apriltag) on each face. 
It is an "easy-to-detect" object for e.g. a robotic pick and place task (see [nit_pick_place](https://github.com/ovgu-nit/nit_pick_place/tree/humble-devel)). 

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

## Print in 3D

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


## Print in 2D

You have no 3D printer, but want to become an aprilcube owner nonetheless? If you instead have a 2D printer, scissors and glue, referr to `print2D/`. The latex file provides a flattened aprilcube texture with cut, fold, and glue instructions.

## Launch Configurations

Depending on the setup, there are a view different launch configuration modes available. Each modes configurations and parameters are kept in their respective yaml file in the config folder. 

### Webcam-Demo
To launch a webcam demo of the tag detection (e.g. to verify the installation worked) run the following command. You need an aprilcube, to test this (see print2d or print3D). 
```bash
ros2 launch nit_aprilcube detect.launch.py mode:=webcam
```

### Simulation


Set up the [tiago simulation workspace](https://github.com/pal-robotics/tiago_simulation):
```bash
sudo apt-get update; sudo apt-get install git python3-vcstool python3-rosdep python3-colcon-common-extensions
mkdir -p ~/tiago_public_ws/src; cd ~/tiago_public_ws
vcs import --input https://raw.githubusercontent.com/pal-robotics/tiago_tutorials/humble-devel/tiago_public.repos src
sudo rosdep init; rosdep update
```

Clone this package into the workspace:
```bash
cd ~/tiago_public_ws/src
git clone git@github.com:ovgu-nit/nit_aprilcube.git
```

(if not on `humble-devel`, checkout the correct branch)
```bash
cd ~/tiago_public_ws/src/nit_aprilcube
git checkout deploy_on_real
```

Then run the install script from the workspace root:
```bash
cd ~/tiago_public_ws
bash src/nit_aprilcube/sim_install.sh
source install/setup.bash
```

Launch the simulation:
```bash
ros2 launch nit_aprilcube detect.launch.py mode:=sim
```
- This launches the Gazebo simulator from PAL Robotics with Tiago in a tabletop scene. The default aruco cube gets replaced by the aprilcube. 
- Rviz will open with panels showing the annotated camera image, a view port with the TIAGo model and the planning scene objects (april cube and a pseudo box representing the table).
- The demo starts a "tuck arm"-movement. Sometimes this causes problems in the simulation. In that case just relaunch the demo.
- The head_follower node will follow the cube.


### Remotely on real TIAGo


Set up a new testing workspace if necessary:
```bash
mkdir -p ~/nit_test_ws/src; cd ~/nit_test_ws
sudo rosdep init; rosdep update
```

Clone this package into the workspace:
```bash
cd src
git clone git@github.com:ovgu-nit/nit_aprilcube.git
```

(if not on `humble-devel`, checkout the correct branch)
```bash
cd nit_aprilcube
git checkout 4-test-aprilcube-detection-in-real-deployment-on-tiago
```

Then run the install script from the workspace root:
```bash
cd ../.. # back to nit_test_ws
bash src/nit_aprilcube/remote_install.sh
source install/setup.bash
```

Launch the deploy script with remote-configurations:
```bash
ros2 launch nit_aprilcube detect.launch.py mode:=remote
```
- Rviz will open with panels showing the camera image, a view port with the TIAGo model and the planning scene objects (april cube and a pseudo box representing the table). No image annotation as it is an unecessary overhead.
- The head_follower node will follow the cube.


----
# Old stuff

## Launch Configurations

The package ships with three pre-configured setups selected by the `mode` argument:

| Mode | Use case | Transport | Annotator | Spawn cube |
|------|----------|-----------|-----------|------------|
| `sim` | Gazebo simulation | raw | yes | yes |
| `robot` | On-robot deployment | compressed | no | no |
| `remote` | Remote PC visualization | compressed | yes | no |

Each mode is defined by a YAML file in `config/setup_<mode>.yaml` — the single source of truth for that setup. To change behavior, edit the YAML, not the launch file.

### Usage

```bash
# Simulation
ros2 launch nit_aprilcube detect.launch.py mode:=sim

# On robot (CPU-efficient, no GUI overhead)
ros2 launch nit_aprilcube detect.launch.py mode:=robot

# Remote PC (receive compressed stream, annotate, visualize)
ros2 launch nit_aprilcube detect.launch.py mode:=remote
```

Optional overrides:
```bash
# Custom image topic
ros2 launch nit_aprilcube detect.launch.py mode:=robot image_raw:=/my/camera/image

# Enable debug printer
ros2 launch nit_aprilcube detect.launch.py mode:=sim use_tag_printer:=true

# Delay cube spawn (sim only)
ros2 launch nit_aprilcube detect.launch.py mode:=sim spawn_delay_sec:=2.0
```

To add a new mode, create `config/setup_<name>.yaml` and launch with `mode:=<name>` — no code changes.

### Include in another launch file

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

nit_aprilcube_dir = get_package_share_directory('nit_aprilcube')

IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        os.path.join(nit_aprilcube_dir, 'launch', 'detect.launch.py')
    ),
    launch_arguments={'mode': 'sim', 'x': '0.7'}.items()
)
```

### Gazebo prerequisites

- The original tag images (`models/aprilcube/meshes/tags_original/`) provided by the apriltag repo have a minimal size of 8×8 pixels. Using those directly causes Gazebo to blur the images. To fix this:
    ```bash
    python3 scale_up_tags.py
    ```
    This creates scaled-up versions (512 px by default) in `models/aprilcube/meshes/tags_scaled/`.

- The model directory structure (automatic when installed as a ROS2 package):
    ```
    ros2_ws/
    └ src/nit_aprilcube/
        ├ ...
        └ models/
            └ aprilcube/
                ├ meshes/
                │   ├ tags_scaled/
                │   └ aprilcube.dae
                ├ aprilcube.sdf
                └ model.config
    ```
- The launch file automatically sets `GAZEBO_MODEL_PATH` in `sim` mode. If you start Gazebo separately, export the path manually:
    ```bash
    export GAZEBO_MODEL_PATH="$GAZEBO_MODEL_PATH:$(ros2 pkg prefix nit_aprilcube)/share/nit_aprilcube/models"
    ```
- Install dependencies with rosdep and build your workspace with colcon.


---

# Copy & Paste Area

SIM_INSTALL=true colcon build --symlink-install \
  --allow-overriding launch_pal pal_urdf_utils play_motion2 play_motion2_msgs nit_messages \
  --cmake-args -DCMAKE_POLICY_VERSION_MINIMUM=3.10 -Wno-dev

SIM_INSTALL=true cbps nit_aprilcube

cbps nit_aprilcube

rm -rf build/nit_aprilcube/ install/nit_aprilcube/

