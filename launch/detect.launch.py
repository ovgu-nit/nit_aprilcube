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

    print(f'{config}')

    actions = []

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