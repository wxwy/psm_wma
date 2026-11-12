# G2 Full Map native-owner Bundle fast transport gate — 2026-11-12

## Scope

**Applies only to RoboCasa/MuJoCo `FULL_MAP_MUJOCO_SOURCE` simulation.** Real RGB-D, native perception, `ColorCloudMap`, segmentation, Room, SG, AABB connectivity and 10mm F27 renderer semantics are unchanged. The optional fast mode is not the default for the generic Bundle API. Only `g2.offline.atomic_6views_run` explicitly passes `trust_native_owner=True`.

## Mechanism

1. Re-run the existing Full Map source identity/geometry/color evidence validator and verify exact 10cm occupancy and all original entity geometry and source file hashes.
2. Validate **every** source `precolored.txt` point against the original native C++ `surfaces.csv` output (coordinates with identical float32/float64 tolerances, RGB, color_valid, recorded/unknown entity IDs, exact row count), using pandas chunked parser and `float_precision="round_trip"`. No downsampling.
3. Reuse the original native C++ triangle-distance owner calculation rather than performing a second Python `SurfaceOwnerVerifier.verify` sweep over 3–4.4 million points.
4. Retain byte-hash sealing and exact copy checks; default `verify_bundle` and external `load_bundle` continue to perform the original independent full deep audit.
5. Without pandas, opt-in mode falls back to the original per-row transport comparison, still avoiding redundant owner computation.

This is a **different trust boundary** from the default independent Full Map spatial ownership verifier: the fast capture trusts the source-proved native C++ attribution, while independently checking transport and source geometry. It must never be claimed to provide the same *independent owner recomputation*. For external/untrusted bundles use deep `verify_bundle`.

## Official RoboCasa real-data A/B receipts

| Episode | Source points | Previously merged Full Map Bundle capture | Candidate capture | Byte-exact parity |
|---|---:|---:|---:|---|
| CloseFridge 503 | 4,436,126 | 242.79 s (isolated prior gate) | 27.14 s | 12/12 files |
| OpenDrawer 3022 | 3,304,169 | Not measured under equal setup | 21.00 s | 12/12 files |
| OpenDrawer 3029 | 3,325,177 | Not measured under equal setup | 20.71 s | 12/12 files |

The OpenDrawer candidate captures were executed concurrently; the ClosedFridge candidate was isolated. Thus no unmeasured 8-worker total pipeline speedup is asserted.

The original generated Bundle manifest, `snapshot.json`, `surfaces.csv`, `grid_states.raw`, source audit/GT/color attachments, and completion markers were byte-exact in each real-data pair. No published training/validation assets were overwritten.

## Tests

- Isolated V3 `g2/tests`: **809 passed, 0 failed**.
- New fail-closed regression: corrupt XYZ/RGB/validity, unknown/mismatched entity labels, source tampering and row counts all refused; type/selection guard rejects non-Full Map mode.
- The original RGB-D pipeline is untouched (no modified `nav_sg` sources or binary).

## Next phase (not yet in this patch)

The simulation-only initial `native_run` still converts MuJoCo 5 cm surface samples into large ASCII precolored clouds and native surfaces. Removing this handoff requires a separate and explicitly gated native Oracle 10cm Room/SG source adapter; preserve legacy RGB-D support, compare Room footprint, entity/connection certificate, 10cm occupancy, 10mm color and F27 view outputs across full episodes before any promotion. No user-visible change to the native hierarchy or optional fourth-level `Subobject` is part of this optimization.
