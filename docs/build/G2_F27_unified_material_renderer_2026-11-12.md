# G2 F27 — Unified Material/Surface Rendering (2026-11-12)

Status: **REVIEW — isolated GitHub candidate, NOT V3 default.**  
Pinned V3 source base: `18a6e6636b3b62ebde22b596cbae81c0b37272e6`.  
The F26 source snapshot is overlaid first, followed by the nine F27 changes. The server is read/execute-only as to Git; GitHub plugin publishes source objects.

## Rationale and frozen boundaries

- Render existence is based on Visual Geom/Surface, **never** the Scene Graph semantic Owner. Unbound wall sockets and switches must remain visible with original Geom identity.
- Geometry answers where the surface lies. Materials answer RGB/UV/alpha. Ray depth and stable tolerance answer visibility. Scene Graph can assign meaning, but cannot erase geometry.
- Visual GT source and source material samples remain separate from Collision/10 cm Occupancy/ESDF and original SG; the full native SG is unchanged.
- Transparent material is handled by an ordered **multi-hit K-buffer** (fast K=8, audit K=32), carrying repeated front/rear faces of one Geom. The shader never branches on object names.
- Rendering alpha is source evidence. Fresnel/studio environment only modifies the **display preview**, not numeric RGB, original Alpha, or training labels. No claim of physical refraction, PBR lighting, or sim-to-real optical correctness.
- Different Geoms sharing exactly one depth can have equal RGB yet ambiguous geometry identity. The F27 equal-depth audit checks every available source material candidate before certifying *color*, and retains the identity ambiguity. If source values disagree, color remains UNKNOWN.
- Static geometry is cached at the pose certified by the 1e-10 bound; material and Owner changes invalidate its key; real motion beyond threshold fails closed.

## Source changes

- `g2/views/exact_compute.py`: one dispatch produces ordered intersections and coordinates/Face IDs, K=8/32.
- `g2/views/surface_renderer.py`: source-bound material, static/dynamic layers, explicit unknown, transparent per-face source IDs, K-hit compositor, static canonical-pose cache, equivalent-RGB tied-depth analysis and optional map branch.
- `g2/views/material_appearance.py`: generic dielectric display-only optical approximation.
- `g2/views/gpu_surface_map.py`, `g2/views/native_map_adapter.py`: experimental verified 10 mm native color surface map projection into the same layer/composer interface with namespaced cell identity and explicit unknown original material identity; **not** the production replacement for exact GT Visual Geometry.
- `g2/tests/test_material_appearance.py`, `test_native_map_adapter.py`, `test_static_surface_cache.py`, `test_surface_multilayer.py`: material, source, cache, identity and depth correctness checks.

The previous `gpu_nearest_recovery` path is not the F27 primary path. Old modules are retained for backwards-compatible F24/F26 experiments rather than deleted before production parity and approval.

## Actual RoboCasa evidence (isolated server)

Episode 005077 / Layout1: **47/47** states, **141/141** views, 198,434 fractional-alpha front pixels in the episode. Layout10: **15/15** states, **90/90** views, 218,155 fractional-alpha front pixels. Both together: 62 states, 231 views. Independently audited material/Geom/Owner/Depth/Alpha/Valid/source bindings: **PASS, 0 failures**.

Restored unbound switch/outlet geometry remains visible (without SG Owner). Layout10 equal-depth RGB-certification restored **21,765 cumulative ambiguous-depth pixel colors** without deciding semantic identity. Total visible UNKNOWN color pixels in the two tested episodes: **0**.

CPU suite after cache changes: **736 passed**. Six view directions × K8/K32 CPU/GPU transparent-hit parity: **12 passed**.

F27 state-based full export latency from the earlier candidate before the final cache change: Layout1 P50 **6.80 s**, Layout10 P50 **14.62 s**. In-memory five-state followup with canonical static pose cache: Layout1 warm P50 **5.67 s**, Layout10 warm P50 **4.35 s**. These are not comparable end-to-end latency metrics. **Neither 1 Hz nor 2 Hz certified.**

Native 10 mm map branch: real Layout1 verified color data with 1,623,491 cells, single view GPU projection A/B tested. It does not preserve original per-Geom Material ID from the native map, and its 10 mm quantization differs from Visual Geometry occlusion: **diagnostic only**, not visually equivalent and not production default. Do not interpret map cells as Visual Geoms or relabel map colors as material ground truth.

The human A/B preview is retained **only on the server** at:
`.../episode_005077_full_2hz_20261111/preview_unified_surface_v2_20261112/index.html`.
It includes 62 states / 231 new images and local material closeups. The server-local HTTP path is `http://127.0.0.1:18765/preview_unified_surface_v2_20261112/index.html`. No original images or server assets have been copied to GitHub.

## Open Gates (do not promote blindly)

1. **H1 human visual approval**: specifically the two hollow glass bottles, contents/caps, opacity, Fresnel appearance, wall outlets and switches, and all six directions.
2. **Performance**: static caching reduced redundant rasterization but 1/2 Hz per-state latency remains far away. Reprofile dynamic/Mesh/Material rasterization, re-use shared GPU projectors, reduce repeated material calls, use region invalidation and pre-batched GPU with dedicated latency gate.
3. **True native map pathway**: fix single-source geometry/visibility equivalence or keep source Visual Mesh as Full Map view authority; verify separate honest alpha evidence, 10 mm quantization, and Cold Start/Partial Map before any promotion.
4. **Material generalization**: run at least additional non-RoboCasa scene(s), transparent alpha masks/complex texture/occlusion and reflectance cases; validate overflow, UNKNOWN and optical proxy semantics.
5. **Release**: new independent review, source hash readback, runtime replay parity and explicit Owner approval before switching V3 default. No training or 9,126-episode batch launched.

This is a **candidate architecture and reproducible A/B**, not a claim of complete production readiness.
