#!/usr/bin/env bash
set -eu

# ---
# Setup script for nit_pick_place with TIAGo simulation
# Run this from the root of your colcon workspace after
# cloning nit_pick_place into src/.
# ---

# Assumes that this script is run from within the workspace folder
cd src

# The demo uses the aprilcube as a demo object to pick and place.
# Scale up the tag textures so the model loads correctly in simulation.
cd nit_aprilcube
python3 scale_up_tags.py
cd .. # back to src

# Install all other dependencies via rosdep
cd .. # back to workspace
rosdep install --from-paths src --ignore-src -r -y

# Build the workspace, suppressing deprecation errors and override warnings
SIM_INSTALL=true colcon build --symlink-install \
  --allow-overriding launch_pal pal_urdf_utils play_motion2 play_motion2_msgs nit_messages \
  --cmake-args -DCMAKE_POLICY_VERSION_MINIMUM=3.10 -Wno-dev

# Source workspace
source install/setup.bash