#!/usr/bin/env bash
set -eu

SCRIPTPATH="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$SCRIPTPATH"/../.. && pwd)"

cd "$WORKSPACE"

# cbclean
rm -rf build/nit_aprilcube install/nit_aprilcube

# Build the workspace
SIM_INSTALL=true colcon build --symlink-install --packages-select nit_aprilcube \
  --cmake-args -DCMAKE_POLICY_VERSION_MINIMUM=3.10 -Wno-dev

echo ""
echo "Rebuild complete."
