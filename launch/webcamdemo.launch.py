from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, TimerAction
from ament_index_python.packages import get_package_share_directory
from pathlib import Path

PKG_NAME = 'nit_aprilcube'
PKG_PATH = Path(get_package_share_directory(PKG_NAME))

def generate_launch_description():
    
    return LaunchDescription([
        # USB Camera
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='usb_cam',
            output='screen',
            parameters=[{
                'video_device': '/dev/video0',
                'image_width': 640,
                'image_height': 480,
                'framerate': 30.0,
                'pixel_format': 'yuyv',
            }]
        ),
        
        # AprilTag Detector
        Node(
            package='apriltag_ros',
            executable='apriltag_node',
            name='apriltag',
            output='screen',
            remappings=[
                ('image_rect', '/image_raw'),
            ],
            parameters=[PKG_PATH/'config'/'apriltag_webcamdemo.yaml']
        ),
        
        # --- NIT Nodes ---

        # Image Annotator
        Node(
            package='nit_aprilcube',
            executable='image_annotator',
            name='image_annotator',
            output='screen',
            remappings=[
                ('image_raw', '/image_raw'),
                ('detections', '/detections'),
                ('image_annotated', '/image_annotated'),
            ]
        ),
        
        # Tag Printer
        Node(
            package='nit_aprilcube',
            executable='tag_printer',
            name='tag_printer',
            output='screen',
            remappings=[
                ('detections', '/detections'),
            ]
        ),
        
        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=['rviz2', '-d', PKG_PATH/'config'/'rviz_webcamdemo.rviz'],
                    output='screen'
                )
            ]
        )
    ])