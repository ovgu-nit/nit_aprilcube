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

def _load_yaml(path: Path) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_config_from_predefined_file(mode: str) -> dict:
    config_path = PKG_PATH / 'config' / f'{mode}.yaml'
    if config_path.exists():
        return _load_yaml(config_path)
    from launch.substitutions import SubstitutionFailure
    options = [p.stem for p in (PKG_PATH / 'config').glob('*.yaml')]
    raise SubstitutionFailure(
f"""\033[91m
[{PKG_NAME}] Could not find the predefined mode '{mode}'. Possible options are:
    {', '.join(options)}
\033[0m
"""
    )


def load_config_from_custom_file(file_path: str) -> dict:
    given = Path(file_path)
    if given.exists() and given.is_file():
        return _load_yaml(given)
    from launch.substitutions import SubstitutionFailure
    raise SubstitutionFailure(
f"""\033[91m
[{PKG_NAME}] Could not find custom config file: '{file_path}'
    Looked for: {given.resolve()}
\033[0m
"""
    )


def deep_merge(base: dict, overlay: dict) -> dict:
    merged = base.copy()
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def launch_function(
        context: launch.launch_context.LaunchContext
):
    # Parse launch config
    config = {}

    arg_mode = context.launch_configurations.get('mode', '')
    if arg_mode:
        mode_config = load_config_from_predefined_file(arg_mode)
        config = deep_merge(config, mode_config)
    
    arg_file = context.launch_configurations.get('file', '')
    if arg_file:
        file_config = load_config_from_custom_file(arg_file)
        config = deep_merge(config, file_config)

    arg_override = context.launch_configurations.get('override', '')
    if arg_override:
        try:
            overlay = yaml.safe_load(arg_override)
            if isinstance(overlay, dict):
                config = deep_merge(config, overlay)
        except Exception:
            from launch.substitutions import SubstitutionFailure
            raise SubstitutionFailure(
f"""\033[91m
[{PKG_NAME}] Could not parse 'override' as valid inline YAML.
\033[0m
"""
            )

    # If still empty, nothing was provided
    if not config:
        from launch.substitutions import SubstitutionFailure
        raise SubstitutionFailure(
f"""\033[91m
[{PKG_NAME}] No configuration provided. Use one of:
    ros2 launch nit_aprilcube launch.py mode:=webcam
    ros2 launch nit_aprilcube launch.py file:=/path/to/config.yaml
    ros2 launch nit_aprilcube launch.py mode:=webcam override:="usb_cam: ..."
\033[0m
"""
        )

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

    if 'aprilcube_detector' in config:
        remappings_list = []
        if 'remappings' in config['aprilcube_detector']:
            remappings_list = [(k, v) for k, v in config['aprilcube_detector']['remappings'].items()]

        params_list = config['aprilcube_detector'].get('parameters', {})

        actions.append(
            launch_ros.actions.Node(
                package='nit_aprilcube',
                executable='aprilcube_detector',
                name='aprilcube_detector',
                output='screen',
                remappings=remappings_list,
                parameters=[params_list]
            )
        )

    return actions


def generate_launch_description():
    return launch.LaunchDescription([
        DeclareLaunchArgument(
            'mode',
            default_value='',
            description='Predefined profile name (e.g. webcam, sim)'
        ),
        DeclareLaunchArgument(
            'file',
            default_value='',
            description='Path to a custom YAML config file'
        ),
        DeclareLaunchArgument(
            'override',
            default_value='',
            description='Inline YAML to merge on top of base config'
        ),

        launch.actions.OpaqueFunction(
            function=launch_function
        )
    ])