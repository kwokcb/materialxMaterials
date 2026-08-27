#!/bin/bash
# Copy or remove the optional src_test modules (assetOne / assetOneCmd) from the
# package directory. Run from the project root.
#
# Usage:
#   copy_src_test.sh copy    # copy src_test/*.py into the package
#   copy_src_test.sh remove  # remove previously copied src_test files from the package
set -e

# Resolve the project root relative to this script's location.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

SRC_TEST_DIR="src_test"
PACKAGE_DIR="src/materialxMaterials"

ACTION="${1:-copy}"
if [ "$ACTION" = "copy" ]; then
    if [ ! -d "$SRC_TEST_DIR" ]; then
        echo "ERROR: src_test directory not found at $PROJECT_ROOT/src_test"
        exit 1
    fi
    mkdir -p "$PACKAGE_DIR"
    cp "$SRC_TEST_DIR"/*.py "$PACKAGE_DIR"/
    echo "Copied src_test modules into $PACKAGE_DIR/:"
    ls "$SRC_TEST_DIR"/*.py
elif [ "$ACTION" = "remove" ]; then
    if [ -d "$SRC_TEST_DIR" ]; then
        for f in "$SRC_TEST_DIR"/*.py; do
            [ -e "$f" ] || continue
            base="$(basename "$f")"
            if [ -f "$PACKAGE_DIR/$base" ]; then
                rm -f "$PACKAGE_DIR/$base"
                echo "Removed $PACKAGE_DIR/$base"
            fi
        done
    fi
else
    echo "ERROR: unknown action '$ACTION' (expected 'copy' or 'remove')"
    exit 1
fi
