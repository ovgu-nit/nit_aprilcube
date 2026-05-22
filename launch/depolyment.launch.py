import os
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

PKG_NAME = 'nit_aprilcube'
PKG_DIR = Path(get_package_share_directory(PKG_NAME))


def generate_launch_description():
    # --- Launch Configuration Toggles ---
    image_raw_topic = LaunchConfiguration('image_raw')
    detections_topic = LaunchConfiguration('detections')

    return LaunchDescription([
        # --- Arguments ---

        DeclareLaunchArgument(
            'image_raw',
            # Using base topic name instead of trailing /compressed
            # because the image_transport plugin appends the transport method automatically
            default_value='/head_front_camera/rgb/image_raw',  
            description='Input RGB image topic from the real robot (base topic)'
        ),

        DeclareLaunchArgument(
            'detections',
            default_value='/detections',
            description='AprilTag detections topic'
        ),

        # --- Onboard Hardware Nodes ---

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
                # Matches the updated configuration file path
                str(PKG_DIR / 'config' / 'apriltag_deployment.yaml'), 
            ]
        ),

        Node(
            package=PKG_NAME,
            executable='aprilcube_detector',
            name='aprilcube_detector',
            output='screen'
        )
    ])