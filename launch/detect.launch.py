from pathlib import Path
from ament_index_python.packages import get_package_share_directory

import launch 
import launch.launch_context
import launch.actions
import launch_ros.actions

from launch_ros.actions import Node
from launch.actions import ExecuteProcess, TimerAction, DeclareLaunchArgument, OpaqueFunction

PKG_NAME = 'nit_aprilcube'
PKG_PATH = Path(get_package_share_directory(PKG_NAME))

def parse_yaml_file(mode: str):
    with open(PKG_PATH / 'config' / f'{mode}.yaml') as f:
        import yaml
        return yaml.safe_load(f)


def launch_function(
        context: launch.launch_context.LaunchContext
):
    mode = context.launch_configurations.get('mode')
    config = parse_yaml_file(mode)

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
                period=launch_delay_sec,
                actions=[
                    launch.actions.ExecuteProcess(
                        cmd=['rviz2', '-d', config_file],
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


    return actions


def generate_launch_description():

    print(f""" --- Launching {PKG_NAME} --- """)
    
    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(
            'mode',
            choices=['webcam'],
            description='Setup mode / environment profile (webcam, sim, remote, robot)'
        ),

        launch.actions.OpaqueFunction(
            function=launch_function
        )
    ])