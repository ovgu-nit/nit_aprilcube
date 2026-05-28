import os
from pathlib import Path

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
)
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

# --- User Instructions ---
# Gazebo can only spawn the cube if it has acces to the model file at startup!
# Make sure to export the model path to the evironment variable before starting gazebo:

    # export GAZEBO_MODEL_PATH="$GAZEBO_MODEL_PATH:$(ros2 pkg prefix nit_aprilcube)/share/nit_aprilcube/models"

# or and this to your launchfile before launching gazebo:

    # SetEnvironmentVariable(
    #     name='GAZEBO_MODEL_PATH',
    #     value=[
    #         EnvironmentVariable('GAZEBO_MODEL_PATH', default_value=''),
    #         os.pathsep,
    #         os.path.join(get_package_share_directory('nit_aprilcube'), 'models'),
    #     ],
    # )

# ---


# Pose argument keys used by gazebo spawn_entity.py
PKG_NAME = 'nit_aprilcube'
PKG_DIR = Path(get_package_share_directory(PKG_NAME))
POSE_PARAM_DEFAULTS = {
    'x': 1.0, 'y': 0.0, 'z': 1.0, 
    'R': 0.1, 'P': 0.1, 'Y': 0.1,
}


def generate_launch_description():

    # Launch configurations
    image_raw_topic = LaunchConfiguration(
        'image_raw'
    )

    detections_topic = LaunchConfiguration(
        'detections'
    )

    image_annotated_topic = LaunchConfiguration(
        'image_annotated', 
    )

    gazebo_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=[
            EnvironmentVariable(
                'GAZEBO_MODEL_PATH',
                default_value=''
            ),
            os.pathsep,
            str(PKG_DIR / 'models'),
        ],
    )

    return LaunchDescription(

        # --- Environment ---
        [
            gazebo_model_path,
        ]

        # --- Cube Pose ---
        + [
            DeclareLaunchArgument(
                key,
                default_value=str(value),
                description=f'Optional cube pose argument: {key}'
            )
            for key, value in POSE_PARAM_DEFAULTS.items()
        ]

        # --- Topic Configurations ---
        + [
            DeclareLaunchArgument(
                'image_raw',
                default_value='/image_raw',
                description='Input RGB image topic'
            ),

            DeclareLaunchArgument(
                'detections',
                default_value='/detections',
                description='AprilTag detections topic'
            ),

            DeclareLaunchArgument(
                'image_annotated',
                default_value='/image_annotated',
                description='Annotated output image topic'
            ),
        ]

        # --- Nodes ---
        + [


            DeclareLaunchArgument(
                'spawn_delay_sec',
                default_value='0.0',
                description='Time to delay the object spawn in gazebo in seconds. (default no delay)'
            ),

            # Spawn cube
            TimerAction(
                period=LaunchConfiguration('spawn_delay_sec'),
                actions=[Node(
                    package='gazebo_ros',
                    executable='spawn_entity.py',
                    name='spawn_aprilcube',
                    output='screen',
                    arguments=[
                        '-file', str(PKG_DIR / 'models' / 'aprilcube' / 'aprilcube.sdf'), 
                        '-entity', 'aprilcube',
                        '-x', LaunchConfiguration('x'),
                        '-y', LaunchConfiguration('y'),
                        '-z', LaunchConfiguration('z'),

                        '-R', LaunchConfiguration('R'),
                        '-P', LaunchConfiguration('P'),
                        '-Y', LaunchConfiguration('Y'),
                    ],
                )]
            ),

            # AprilTag detector
            Node(
                package='apriltag_ros',
                executable='apriltag_node',
                name='apriltag',
                output='screen',
                remappings=[
                    ('image_rect', image_raw_topic),
                    ('detections', detections_topic),
                ],
                parameters=[
                    str(PKG_DIR / 'config' / 'apriltag_gazebo.yaml')
                ]
            ),

            # Image annotator
            Node(
                package=PKG_NAME,
                executable='image_annotator',
                name='image_annotator',
                output='screen',
                remappings=[
                    ('image_raw', image_raw_topic),
                    ('detections', detections_topic),
                    ('image_annotated', image_annotated_topic),
                ]
            ),

            # Aprilcube pose detection and application to planning/collision scene
            Node(
                package=PKG_NAME,
                executable='aprilcube_detector',
                name='aprilcube_detector',
                output='screen',
                parameters=[{
                    'use_sim_time': True
                }],
            ),
        ]
    )