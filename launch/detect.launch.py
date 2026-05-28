import os
import sys
from pathlib import Path
import yaml
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, OpaqueFunction,
    SetEnvironmentVariable, TimerAction,
)
from launch.substitutions import LaunchConfiguration, EnvironmentVariable
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

PKG_NAME = 'nit_aprilcube'
PKG_DIR = Path(get_package_share_directory(PKG_NAME))


def _launch_setup(context):
    mode = context.launch_configurations.get('mode', 'sim')
    setup_file = PKG_DIR / 'config' / f'setup_{mode}.yaml'

    with open(setup_file) as f:
        s = yaml.safe_load(f)

    # Push user overrides into the annotator block
    for key in ('image_raw', 'detections', 'image_annotated'):
        val = context.launch_configurations.get(key)
        if val:
            s.setdefault('annotator', {})[key] = val

    val = context.launch_configurations.get('use_sim_time')
    if val:
        s['use_sim_time'] = val

    annotator = s.get('annotator', {})
    a_raw    = annotator.get('image_raw', '/image_raw')
    a_detect = annotator.get('detections', '/detections')
    a_annot  = annotator.get('image_annotated', '/image_annotated')
    sim_time = s.get('use_sim_time', False)

    actions = []

    model_dir = PKG_DIR / 'models'
    if model_dir.is_dir():
        actions.append(SetEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value=[EnvironmentVariable('GAZEBO_MODEL_PATH', default_value=''),
                   os.pathsep, str(model_dir)]))

    if s.get('spawn_cube', False):
        sdf_path = PKG_DIR / 'models' / 'aprilcube' / 'aprilcube.sdf'
        if not sdf_path.exists():
            print(f'[{PKG_NAME}] ERROR: {sdf_path} not found.\n'
                  'Model files are not installed by default. Rebuild with:\n'
                  f'  ROS_SIM=true colcon build --packages-select {PKG_NAME}',
                  file=sys.stderr)
            sys.exit(1)

        tags_dir = PKG_DIR / 'models' / 'aprilcube' / 'meshes' / 'tags_scaled'
        if not tags_dir.is_dir():
            print(f'[{PKG_NAME}] ERROR: Scaled texture directory {tags_dir} not found.\n'
                  'The original 8x8 px textures are too small for Gazebo.\n'
                  'Run the scaling script from your workspace root and rebuild:\n'
                  '  python3 src/nit_aprilcube/scale_up_tags.py\n'
                  f'  ROS_SIM=true colcon build --packages-select {PKG_NAME}',
                  file=sys.stderr)
            sys.exit(1)

        pose = s.get('cube_pose', {})
        actions.append(TimerAction(
            period=LaunchConfiguration('spawn_delay_sec'),
            actions=[Node(
                package='gazebo_ros', executable='spawn_entity.py',
                name='spawn_aprilcube', output='screen',
                arguments=[
                    '-file', str(sdf_path),
                    '-entity', 'aprilcube',
                    '-x', str(pose.get('x', 1.0)),
                    '-y', str(pose.get('y', 0.0)),
                    '-z', str(pose.get('z', 1.0)),
                    '-R', str(pose.get('R', 0.0)),
                    '-P', str(pose.get('P', 0.0)),
                    '-Y', str(pose.get('Y', 0.0)),
                ],
            )],
        ))

    actions.append(Node(
        package='apriltag_ros', executable='apriltag_node',
        name='apriltag', output='screen',
        remappings=[
            ('image_rect', a_raw),
            ('detections', a_detect),
        ],
        parameters=[
            {'apriltag': {'ros__parameters': s['apriltag_params']}},
            {'use_sim_time': sim_time},
        ]))

    if annotator.get('enabled', False):
        actions.append(Node(
            package=PKG_NAME, executable='image_annotator',
            name='image_annotator', output='screen',
            remappings=[
                ('image_raw', a_raw),
                ('detections', a_detect),
                ('image_annotated', a_annot),
            ],
            parameters=[{'use_sim_time': sim_time}]))

    actions.append(Node(
        package=PKG_NAME, executable='aprilcube_detector',
        name='aprilcube_detector', output='screen',
        parameters=[{'use_sim_time': sim_time}]))

    if context.launch_configurations.get('use_tag_printer', 'false').lower() == 'true':
        actions.append(Node(
            package=PKG_NAME, executable='tag_printer',
            name='tag_printer', output='screen',
            remappings=[('detections', a_detect)]))

    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='sim',
                              description='sim | robot | remote'),
        DeclareLaunchArgument('image_raw', default_value='',
                              description='Override image topic from setup YAML'),
        DeclareLaunchArgument('detections', default_value='',
                              description='Override detections topic from setup YAML'),
        DeclareLaunchArgument('image_annotated', default_value='',
                              description='Override annotated image topic from setup YAML'),
        DeclareLaunchArgument('use_sim_time', default_value='',
                              description='Override use_sim_time from setup YAML'),
        DeclareLaunchArgument('spawn_delay_sec', default_value='0.0',
                              description='Delay before spawning cube in Gazebo'),
        DeclareLaunchArgument('use_tag_printer', default_value='false',
                              description='Enable tag_printer debug node'),
        OpaqueFunction(function=_launch_setup),
    ])
