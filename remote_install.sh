#!/usr/bin/env bash
set -eu

SCRIPTPATH="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$SCRIPTPATH"/../.. && pwd)"

# Install all dependencies via rosdep
cd "$WORKSPACE"
rosdep install --from-paths src --ignore-src -r -y

# Build the workspace
PYTHONWARNINGS="ignore" REMOTE_INSTALL=true colcon build --symlink-install \
  --allow-overriding nit_aprilcube \
  --cmake-args --no-warn-unused-cli -Wno-dev

echo ""
echo "Build complete. Now source the workspace:"
echo "  source $WORKSPACE/install/setup.bash"
