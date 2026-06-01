#!/usr/bin/env bash
set -eu

SCRIPTPATH="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$SCRIPTPATH"/../.. && pwd)"

# Install all dependencies via rosdep
cd "$WORKSPACE"
rosdep install --from-paths src --ignore-src -r -y

# Build the workspace
REMOTE_INSTALL=true colcon build --symlink-install \
  --cmake-args -DCMAKE_POLICY_VERSION_MINIMUM=3.10 -Wno-dev

echo ""
echo "Build complete. Now source the workspace:"
echo "  source $WORKSPACE/install/setup.bash"
