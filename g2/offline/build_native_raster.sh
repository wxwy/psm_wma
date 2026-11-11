#!/usr/bin/env bash
# Build the F21 9/9-verified bounded C++ triangle-to-10mm raster kernel.
# No MuJoCo assets or camera data are read; no git commit/push is performed.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$root/bin"
"${CXX:-g++}" -O3 -ffp-contract=off -std=c++17 -fPIC -shared \
  "$root/offline/fast_surface_cells.cpp" \
  -o "$root/bin/libfast_surface_cells.so"
echo "Built: $root/bin/libfast_surface_cells.so"
