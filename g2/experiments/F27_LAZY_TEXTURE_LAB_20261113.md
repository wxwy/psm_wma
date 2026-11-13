# G2 F27 lazy-texel decoding — isolated performance lab (2026-11-13)

**Status: EXPERIMENT ONLY. Not integrated into production, not certified for dataset regeneration.**

This branch is forked from PSM-WMA V3 commit 4f97652bca5c4b134789c163bc4a0dcd72ddc561.
The live V3 checkout, nav_sg/G2 checkout, and active 9,126-Episode production remain unchanged.
No GPU experiments or simulator replay were run.

## Read-only evidence from the running production

- 32 workers on GPUs 4/5/6/7. F27 uses EGL/OpenGL FP64 for mesh hit testing but CPU-side material decoding and composition.
- A cold first-state minus_X View took 930.46s, including 911.06s in static hit/material evaluation; GPU geometry kernel took 0.145s. The source tie evidence had zero depth ties.
- Across 328 completed state receipts, view projection consumed nearly the entire F27 view-export wall time: median 13.81s summed projection vs 14.87s whole; median non-projection residual 0.28s.
- Recompressing eight real geometry.npz arrays took 0.08–0.27s each, not a priority.
- The MaterialResolver._texture path eagerly decodes each 2048-by-2048, 12-MiB RGB texture to a 96-MiB float64 array. The example model has 108 compiled textures (459.9 MiB raw). The code also checks constant texture content after full float conversion.

## Experimental candidate

Keep source texture in read-only uint8 form, check uniformity/alpha statistics in raw bytes, and decode only the four texels sampled for each UV. Match the reference FP64/255 conversion, sRGB linearization, neighbor order and multiplication/accumulation order. For Cube textures preserve the reference face ordering, ambiguous tie handling and UV mapping.

This standalone prototype does NOT replace MaterialResolver or touch production. It exposes lazy_bilinear and lazy_cube and compares against historical eager functions.

## Real-asset benchmark

Single low-priority CPU process, original MuJoCo 3.3.7 scene asset, 10000 UVs and 5000 Cube directions.

| Real texture | Compiled type | Eager entire-texture decode | Sparse 10000 UVs | Exact result |
|---|---|---:|---:|---|
| 3 | 2048² RGB sRGB, nonuniform | 27.915s | 0.0044s | array_equal PASS |
| 23 | 2048² RGB sRGB, Cube | 21.999s | 0.0069s | 2D and 5000 Cube array_equal PASS |
| 4 | 2048² RGB linear, uniform | 2.426s | one scalar texel | array_equal PASS |
| 1 | 2048² RGB sRGB, nonuniform | 24.354s | 0.0070s | array_equal PASS |

Combined eager texture decoding: 76.69s; combined sparse lookup: ~0.02s on the nonuniform UV batches.

**These are isolated texture microbenchmark times, not per-View or whole-Episode speedup estimates.**
Model compilation and downstream material/surface composition are excluded.

Additional parity: 40 synthetic cases, including RGB/RGBA, sRGB/linear, repeated/clamped UV, 1x1/2x3/32x64/256x256 textures, six-face Cube, zero/tied ray directions. All matched bit-for-bit with numpy.array_equal.

## Mandatory gates before production

1. Candidate is opt-in, production default remains OFF.
2. Compare entire MaterialResolver output, including alpha, unknown masks, material evidence and UV identities, on real geometry for mesh/primitive/cube and translucent materials.
3. Byte/pixel-compare exported PNG, geometry.npz and the native SG source on multiple real RoboCasa scenes; no tolerance relaxation.
4. Profile steady-state per-View and per-Episode wall time/CPU/peak RSS; the texture microbenchmark does not prove whole-pipeline speedup.
5. Only promote at a user-approved safe Episode boundary. Never edit the currently running V3 or nav_sg working directories, cache receipts, or live scratch files.

## Isolated invocation example

    nice -n 19 ionice -c3 python -m g2.experiments.f27_lazy_texel_lab --model /path/to/copied/scene_rebased.xml --n 10000

This module is an experiment, not a production worker.
