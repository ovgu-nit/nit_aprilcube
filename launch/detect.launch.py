from pathlib import Path
from ament_index_python.packages import get_package_share_directory
import yaml
import os 

import launch 
import launch.launch_context
import launch.actions
import launch_ros.actions

from launch_ros.actions import Node
from launch.actions import ExecuteProcess, TimerAction, DeclareLaunchArgument, OpaqueFunction

PKG_NAME = 'nit_aprilcube'
PKG_PATH = Path(get_package_share_directory(PKG_NAME))

def load_yaml_configuration(
    mode_or_path: str
) -> dict:
    """
    Attempts to treat the input as a direct path first. 
    Falls back to looking inside the package config directory.
    """
    given_path = Path(mode_or_path)
    
    # Scenario A: User provided a direct absolute or relative file path
    if given_path.exists() and given_path.is_file():
        with open(given_path, 'r') as f:
            return yaml.safe_load(f)
            
    # Scenario B: User provided a keyword mode (e.g., 'webcam' or 'sim')
    default_config_path = PKG_PATH / 'config' / f'{mode_or_path}.yaml'
    if default_config_path.exists():
        with open(default_config_path, 'r') as f:
            return yaml.safe_load(f)
            
    # Scenario C: File wasn't found in either location
    from launch.substitutions import SubstitutionFailure
    raise SubstitutionFailure(
f"""\033[91m
[{PKG_NAME}] Could not find configuration file or profile matching: '{mode_or_path}'
    Looked for file at: {given_path.resolve()}
    Looked for internal profile at: {default_config_path}
\033[0m
"""
    )


def launch_function(
        context: launch.launch_context.LaunchContext
):

    mode = context.launch_configurations.get('mode')

    # Force user specification check
    if mode == 'REQUIRED':
        from launch.substitutions import SubstitutionFailure
        raise SubstitutionFailure(
f"""\033[91m
[{PKG_NAME}] You must specifiy a launch mode. See Readme for more info or try again like this for a webcam-demo:
    ros2 launch nit_aprilcube detect.launch.py mode:=webcam
\033[0m
"""
        )

    config = load_yaml_configuration(mode)

    actions = []

    # Activate webcam with usb_cam module
    if 'usb_cam' in config:
        actions.append(
            launch_ros.actions.Node(
                package='usb_cam',
                executable='usb_cam_node_exe',
                name='usb_cam',
                output='screen',
                parameters=[config['usb_cam']['parameters']]
            )
        )

    if 'tiago_gazebo' in config:

        
        if 'launch_arguments' in config['tiago_gazebo']:

            # Add model path to Gazebos include path
            gazebo_model_path = os.environ.get('GAZEBO_MODEL_PATH', '')
            custom_model_dir = str(PKG_PATH / 'models')
            os.environ['GAZEBO_MODEL_PATH'] = f"{custom_model_dir}{os.pathsep}{gazebo_model_path}"
            print(os.environ.get('GAZEBO_MODEL_PATH', ''))

            # Start the simulation of Tiago in Gazebo
            tiago_gazebo_dir = Path(get_package_share_directory('tiago_gazebo'))
            from launch.launch_description_sources import PythonLaunchDescriptionSource
            actions.append(
                launch.actions.IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        tiago_gazebo_dir / 'launch' / 'tiago_gazebo.launch.py'
                    ),
                    launch_arguments=config['tiago_gazebo']['launch_arguments'].items()
                )
            )

        # Despawn the default arucocube object from gazebo
        if 'despawn_aruco_cube' in config['tiago_gazebo']:
            despawn_action = launch.actions.ExecuteProcess(
                cmd=[
                    'ros2', 'service', 'call', 
                    '/delete_entity', 
                    'gazebo_msgs/srv/DeleteEntity', 
                    '{"name": "aruco_cube"}'
                ],
                output='screen'
            )
            
            despawn_delay_sec = config['tiago_gazebo']['despawn_aruco_cube'].get('despawn_delay_sec', 0.0)
            actions.append(
                launch.actions.TimerAction(
                    period=float(despawn_delay_sec),
                    actions=[despawn_action]
                )
            )


        if 'spawn_aprilcube' in config['tiago_gazebo']:

            model_path = PKG_PATH / 'models' / 'aprilcube'
            model_file = model_path  / 'aprilcube.sdf'
            if not model_file.exists():
                raise FileNotFoundError(
f"""\033[91m
[{PKG_NAME}] Model files of the aprilcube which are necessary for simulation are not installed by default. Rebuild the package with:
    SIM_INSTALL=true colcon build --packages-select {PKG_NAME}
\033[0m
"""
                )
            
            texture_path = model_path / 'meshes' / 'tags_scaled'
            if not texture_path.exists():
                raise FileNotFoundError(
f"""\033[91m
[{PKG_NAME}] Scaled texture directory not found. Run the scaling script from your workspace root and rebuild:
    python3 src/nit_aprilcube/scale_up_tags.py
    SIM_INSTALL=true colcon build --packages-select {PKG_NAME}
\033[0m
"""
                )

            pose = config['tiago_gazebo']['spawn_aprilcube'].get('pose', {})
            spawn_action = launch_ros.actions.Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                name='spawn_aprilcube',
                output='screen',
                arguments=[
                    '-file', str(model_file), 
                    '-entity', 'aprilcube',
                    '-x', f"{pose.get('x', 1.0):.4f}",
                    '-y', f"{pose.get('y', 0.0):.4f}",
                    '-z', f"{pose.get('z', 1.0):.4f}",
                    '-P', f"{pose.get('pitch', 1.0):.4f}",
                    '-R', f"{pose.get('roll', 1.0):.4f}",
                    '-Y', f"{pose.get('yaw', 1.0):.4f}",
                ],
            )
            
            spawn_delay_sec = config['tiago_gazebo']['spawn_aprilcube'].get('spawn_delay_sec', 0.0)
            actions.append(
                launch.actions.TimerAction(
                    period=float(spawn_delay_sec),
                    actions=[spawn_action]
                ),
            )


    if 'apriltag' in config:
        remappings_list = []
        if 'remappings' in config['apriltag']:
            remappings_list = [(k, v) for k, v in config['apriltag']['remappings'].items()]

        actions.append(
            launch_ros.actions.Node(
                package='apriltag_ros',
                executable='apriltag_node',
                name='apriltag',
                output='screen',
                remappings=remappings_list,
                parameters=[config['apriltag']['parameters']]
            )
        )

    if 'rviz' in config:
        launch_delay_sec = config['rviz'].get('launch_delay_sec', 0.0)
        config_file = PKG_PATH / 'config' / config['rviz']['config_file']

        actions.append(
            launch.actions.TimerAction(
                period=float(launch_delay_sec),
                actions=[
                    launch.actions.ExecuteProcess(
                        cmd=['rviz2', '-d', str(config_file)],
                        output='screen'
                    ),
                ]
            )
        )

    if 'image_annotator' in config:
        remappings_list = []
        if 'remappings' in config['image_annotator']:
            remappings_list = [(k, v) for k, v in config['image_annotator']['remappings'].items()]

        params_list = config['image_annotator'].get('parameters', {})

        actions.append(
            launch_ros.actions.Node(
                package='nit_aprilcube',
                executable='image_annotator',
                name='image_annotator',
                output='screen',
                remappings=remappings_list,
                parameters=[params_list]
            )
        )

    if 'head_follower' in config:
        remappings_list = []
        if 'remappings' in config['head_follower']:
            remappings_list = [(k, v) for k, v in config['head_follower']['remappings'].items()]

        params_list = config['head_follower'].get('parameters', {})

        actions.append(
            launch_ros.actions.Node(
                package='nit_aprilcube',
                executable='head_follower',
                name='head_follower',
                output='screen',
                remappings=remappings_list,
                parameters=[params_list]
            )
        )

    return actions


def generate_launch_description():
    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(
            'mode',
            default_value='REQUIRED',
            description='Setup mode / environment profile (REQUIRED)'
        ),

        launch.actions.OpaqueFunction(
            function=launch_function
        )
    ])