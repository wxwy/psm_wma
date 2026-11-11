# G2 F24 direct 10 mm color core — staged V3 port

This directory ports the source-verified F21/F22 numerical kernels:
- `fast_surface_cells.cpp` and `fast_surface_cells.py`: C++ bounded surface-cell rasterization and ctypes wrapper. The F21 isolated source passed 9/9 geometry parity cases.
- `fast_static_dynamic_merge.py`: coalescing of an immutable static 10 mm source map and exact changed-dynamic geometry, preserving owner conflicts. The F22 isolated source passed the corresponding regression tests and 25/25 state RGB image parity.

Run `bash g2/offline/build_native_raster.sh` before importing the raster wrapper. The generated shared library stays in the local ignored/build output, not Git.

**Boundaries:** source generation must bind the exact MuJoCo model closure, state row, scene and frame; 10 cm Occupancy/ESDF/Room are independent. These modules alone are not a V3 episode producer. The validated offline producer, state delta encoding, native long-lived worker and H1-accepted View pipeline must be connected and retested on the pinned GitHub PR head before any 9,126-episode production.

Native consumer: nav_sg [F24 Draft PR #10](https://github.com/wxwy/nav_sg/pull/10) (stacked on F3); V3/F3 dependency stack remains Draft. No GT known-free region is certified for real navigation.
