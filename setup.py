import os
import sys
from glob import glob
from setuptools import find_packages, setup

PKG_NAME = 'nit_aprilcube'
MODEL_NAME = 'aprilcube'

# --- Validation Logic ---
tags_scale_path = os.path.join('models', MODEL_NAME, 'meshes', 'tags_scaled')
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