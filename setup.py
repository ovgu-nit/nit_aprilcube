import os
import sys
from glob import glob
from setuptools import find_packages, setup

PKG_NAME = 'nit_aprilcube'

# Only deploy Gazebo models when ROS_SIM=true (build-time choice)
# On the robot, omit this to keep the install lightweight.
model_data_files = []
SIM_INSTALL = os.environ.get('SIM_INSTALL', 'false').lower() == 'true'
if SIM_INSTALL:
    for root, _, files in os.walk('models'):
        if files:
            target_dir = os.path.join('share', PKG_NAME, root)
            file_paths = [os.path.join(root, f) for f in files]
            model_data_files.append((target_dir, file_paths))

setup(
    name=PKG_NAME,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + PKG_NAME]),
        ('share/' + PKG_NAME, ['package.xml']),

        # launch files
        (os.path.join('share', PKG_NAME, 'launch'), glob('launch/*.launch.py')),

        # config files
        (os.path.join('share', PKG_NAME, 'config'), glob('config/*')),
    ] + model_data_files,
    
    install_requires=['setuptools', 'Pillow'],
    zip_safe=True,
    maintainer='vincirist',
    maintainer_email='vincent.rist@ovgu.de',
    description='Aprilcube: a cube with apriltags. An easy to detect object.',
    license='Apache License 2.0',
    extras_require={
        'test': [
            'pytest',
            'ament_copyright',
            'ament_flake8',
            'ament_pep257',
        ],
    },
    entry_points={
        'console_scripts': [
            'tag_printer = nit_aprilcube.tag_printer:main',
            'image_annotator = nit_aprilcube.image_annotator:main',
            'head_follower = nit_aprilcube.head_follower:main',
            'aprilcube_detector = nit_aprilcube.aprilcube_detector:main',
        ],
    },
)