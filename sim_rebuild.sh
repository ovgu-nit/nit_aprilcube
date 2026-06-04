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
WORKSPACE="$(cd "$SCRIPTPATH"/../.. && pwd)"

# Install all dependencies via rosdep
cd "$WORKSPACE"

# Clean previous install

echo ""
echo "rm -rf build/nit_aprilcube install/nit_aprilcube"

rm -rf build/nit_aprilcube install/nit_aprilcube

echo ""
echo "Cleaned up previous build and install."

echo ""
echo "SIM_INSTALL=true colcon build --symlink-install \
  --allow-overriding nit_aprilcube --packages-select nit_aprilcube \
  --cmake-args -DCMAKE_POLICY_VERSION_MINIMUM=3.10 -Wno-dev"

# Build the workspace
SIM_INSTALL=true colcon build --symlink-install \
  --allow-overriding nit_aprilcube --packages-select nit_aprilcube \
  --cmake-args -DCMAKE_POLICY_VERSION_MINIMUM=3.10 -Wno-dev

echo ""
echo "Reuild complete."
