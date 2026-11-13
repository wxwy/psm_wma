# G2 F27 Lazy-Texel MaterialResolver — independent candidate (2026-11-13)

**Experimental only. No production promotion, no ongoing-run modification.**

Base: `wxwy/psm_wma` V3 `4f97652bca5c4b134789c163bc4a0dcd72ddc561`.
Candidate: the separate `g2-f27-lazy-texel-lab-20261113` branch.

## Motivation and evidence

F27 1 cm/pixel projection is not the same as GPU mesh raster kernel time. Read-only inspection of 328 complete F27 state reports found almost the entire per-state View-export wall time in direction projection. A complex initial side view took 930 s, of which 911 s were inside the static hit/material stage and less than 0.2 s in the GPU geometry kernel. Rendering several other Views in the same episode was considerably faster due to verified static layer caching. Original F27 retains GPU EGL/FP64 mesh hit tests and CPU material decoding, source appearance and transparency composition.

The original `MaterialResolver._texture()` eagerly converts a complete 2048² RGB `uint8` source texture (12 MiB) into a 96 MiB `float64` array and decodes every pixel. The same material may be sampled at only a small number of actual visible pixels per projection.

## Candidate implementation

**Default OFF:** `MaterialResolver(model, lazy_texel_decode=False)` preserves the old eager implementation; `SurfaceRenderer(..., lazy_texel_decode=False)` also defaults to the old path. No production CLI flag or global environment override was added. The 9,126-running-job source and nav_sg are untouched.

Opt-in:

- Cache immutable, source-bound `uint8` texture bytes, not the entire decoded float64 plane.
- Check whole-texture uniformity and the RGBA alpha range once on bytes, equivalent to the previously decoded values (sRGB transfer is monotonic and does not affect alpha).
- For actual UV queries, fetch exactly four neighboring source texels, normalize to float64, decode RGB sRGB as necessary, and accumulate in the original order. Cube maps preserve original OpenGL six-face direction, tie and per-face UV logic.
- Keep compiled texture metadata, source SHA, alpha behavior, unknown/reject reasons, surface/face identities and material appearance outputs unchanged.
- Maintain distinct `raw_texture_load_count` / `raw_texture_cache_hits` counters so `texture_decode_count` continues to mean eager full-array decoding.
- Respect `invalidate(texture_id)`, repeated calls and original material and geom overrides.
- No nav_sg, RGB-D, Scene Graph, occupancy, replay, provenance or view geometry edits.

Touched files on **candidate branch only**:

- `g2/sim/material_resolver.py` (opt-in and sparse texel helpers)
- `g2/views/surface_renderer.py` (optional constructor forwarding)
- `g2/tests/test_lazy_material_optin.py` (full field/evidence comparisons)
- `g2/tests/test_lazy_surface_view.py` (full CPU View and per-pixel evidence comparisons)
- `g2/experiments/f27_lazy_texel_lab.py` (standalone microbenchmark from Phase 0)

## Tested evidence

1. **Existing 844 G2 Python tests** using opt-in candidate modules and the unchanged default eager path: PASS.
2. **29 small source-MaterialResolver opt-in A/B tests**, including sRGB and linear, meshes and primitive geometries, Cube directions, varying RGBA alpha, opacity, source validity, per-geom overrides and cache invalidation: PASS.
3. **One actual RoboCasa scene source** (NavigateKitchen Episode 2022): exact sample/evidence parity, PASS.
4. **Four complete small-scene CPU Views** including opaque and translucent source material: RGB pixels, depth, source geom/surface identity, material evidence and alpha mask arrays are identical.
5. **One actual RoboCasa compiled geometry small CPU View**: exact RGB, geometry, and all pixel evidence arrays, PASS.
6. Combined independent gate: **879/879 PASS**, 0 failed, 0 skipped, with the real-scene source explicitly supplied.
7. Phase 0: synthetic 40 cases of RGB/RGBA, sRGB/linear, UV repeat/clamp, Cube faces and tied directions: bit-exact PASS.

Real-asset 12000-sample end-to-end `descriptor()+sample()` (texture 3, 2048² RGB sRGB):

| Metric | Default eager | Opt-in lazy |
|---|---:|---:|
| Full MaterialResolver descriptor + sample | 0.1265 s | 0.0291 s |
| Cached source texture bytes | 96 MiB | 12 MiB |
| Output fields and evidence | baseline | **bit-exact** |

This single local run observed ~4.35x speedup and 87.5% smaller per-texture CPU cache. Under severe contention, the earlier Phase 0 *isolated texture decode* microbenchmark produced much larger full-texture decoding times (e.g. 27.915 s vs 0.0044 s for 10000 UV queries); timings vary materially with competing server load and cache warmth. **Do not infer whole-View or whole-episode speedup from either comparison.**

## How to repeat opt-in tests

Check out the experimental branch into a separate scratch checkout; never replace files in a running worker's checkout.

Use a Python environment with MuJoCo 3.3.7, and optionally set:

```bash
export G2_F27_REAL_SOURCE_MJCF=/path/to/independently_copied/scene_rebased.xml
python -m pytest -q g2/tests/test_lazy_material_optin.py g2/tests/test_lazy_surface_view.py
```

If the real-scene variable is unset, the two optional real-scene cases skip; small-scene and synthetic cases still run.

## Remaining gates before any safe production switch

- GPU EGL full F27 View A/B: compare every final room/island PNG byte or pixel, all geometry + transparent layers, and SG receipts across multiple complex real layouts; validate original-state SHA provenance. The CPU small-View gate does NOT replace the GPU gate.
- Profile whole Episode / actual F27 under controlled GPU contention and 32-Worker pressure, including peak RSS and aggregate throughput rather than only the texture microbenchmark.
- Demonstrate no first-frame or per-state cache-ID regression and no invalid texture/material evidence in RGB-D and original nav_sg paths.
- Keep current 9,126-production running until user explicitly approves switching at a safe Episode boundary; **not approved yet**.

**Status: CANDIDATE PASS for CPU numerical/field/real-small-View gates. GPU full-view and production promotion still pending.**
