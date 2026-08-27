#!/bin/bash
# Build and install materialxMaterials, then refresh packaged material data.
# Usage:
#   bash build.sh             # default: package only the src tree
#   bash build.sh --src-test  # also copy the optional src_test modules (assetOne) into the package

# Optionally include the src_test modules in the build.
INCLUDE_SRC_TEST=0
if [ "$1" = "--src-test" ] || [ "$1" = "-s" ]; then
    INCLUDE_SRC_TEST=1
fi

if [ "$INCLUDE_SRC_TEST" = "1" ]; then
    echo "Copying src_test modules (assetOne) into the package..."
    bash "$(dirname "$0")/copy_src_test.sh" copy
else
    echo "Removing any src_test modules (assetOne) from the package..."
    bash "$(dirname "$0")/copy_src_test.sh" remove
fi

echo "Start Package Install..."
pip install . -q
echo "Finished Package Install"
