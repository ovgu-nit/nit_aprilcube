#!/usr/bin/env bash
set -eu

# ---
# Setup script for nit_aprilcube with TIAGo simulation
# Run this from the root of your colcon workspace after
# cloning nit_aprilcube into src/. For example:
#
#   cd ~/tiago_public_ws
#   bash src/nit_aprilcube/sim_install.sh
#   source install/setup.bash
# ---

SCRIPTPATH="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$SCRIPTPATH"/../../.. && pwd)"

cd "$SCRIPTPATH"

# Scale up tag textures so Gazebo renders them crisply
python3 scale_up_tags.py

# Install all dependencies via rosdep
cd "$WORKSPACE"
rosdep install --from-paths src --ignore-src -r -y

# Build the workspace
SIM_INSTALL=true colcon build --symlink-install \
  --allow-overriding launch_pal pal_urdf_utils play_motion2 play_motion2_msgs nit_messages \
  --cmake-args -DCMAKE_POLICY_VERSION_MINIMUM=3.10 -Wno-dev

echo ""
echo "Build complete. Now source the workspace:"
echo "  source $WORKSPACE/install/setup.bash"
