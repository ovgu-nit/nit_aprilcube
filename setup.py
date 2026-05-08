import os
import sys
from glob import glob
from setuptools import find_packages, setup

package_name = 'nit_aprilcube'
model_name = 'aprilcube'

# --- Validation Logic ---
tags_scale_path = os.path.join('models', model_name, 'meshes', 'tags_scaled')
if not os.path.exists(tags_scale_path) or not os.listdir(tags_scale_path):
    print(f"ERROR: Texture directory is missing or empty: {tags_scale_path}", file=sys.stderr)
    print("Please run the 'scale_up_tags.py' script first to generate the scaled textures.", file=sys.stderr)
    print("\tpython3 src/nit_aprilcube/scale_up_tags.py", file=sys.stderr)


# --- Resource Collection ---
# This helper collects all files in the models directory recursively
model_data_files = []
for root, _, files in os.walk('models'):
    if files:
        # Construct the installation path: share/nit_aprilcube/models/...
        target_dir = os.path.join('share', package_name, root)
        file_paths = [os.path.join(root, f) for f in files]
        model_data_files.append((target_dir, file_paths))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),

        # config files
        (os.path.join('share', package_name, 'config'), glob('config/*')),

        # Merge the recursively found model files into data_files
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
        ],
    },
)