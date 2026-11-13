# G2 P0+P1+P2 — independent full-chain integration gate, 2026-11-13

**Status: isolated end-to-end tests and user H1 visual-acceptance gate PASS. Formal V3 promotion and additional full-Worker paired throughput tests remain OPEN. The 9,126-Episode producer was NOT restarted.**

Experiment source base: formal PSM-WMA V3 commit f29b01d3235a7fbfd8e17727b8edaf2155957b35, nav_sg native source 9734d2e0e261a47efbd00f5de78ec6c1a983557b. This experimental branch introduces only opt-in switches. Default v1 producer, default native ROS RGB-D source, and original nav_sg are unmodified.

## Agreed scene-update policy

At each 2 Hz View state:
- If any non-robot Visual Geom moved >= 1 mm in 3D Euclidean translation, or rotated >= 1 degree as an SO(3) geodesic relative rotation, render all scene Views.
- Compare against the LAST ACTUALLY RENDERED scene keyframe; do not allow many subthreshold updates to accumulate invisibly.
- When nonrobot scene is stable and robot base x/y/yaw changed, reuse all other Views and redraw only the existing floor_top game_arrow onto the original unmarked cached floor background.
- When both are stable, reuse every View including floor_top.
- Preserve frame-specific real source GT, every Scene Graph, and source/provenance identifiers.
- Existing robot exclusion and arrow-overlay implementation are reused, not reimplemented.

The user has accepted 1 mm / 1 degree as the physical View cache motion threshold, and had previously inspected sample 1-pixel and 57-pixel differences with H1 visual acceptance. The separate CloseFridge H1 human gate has now PASSED: the user inspected the largest differences and reported no visible distinction.

## P0: opt-in Lazy Texture

MaterialResolver keeps the original eager implementation by default. Opt-in reads original uint8 source texture and decodes only the four referenced Texels per UV with original sRGB/FP64/alpha interpolation order; source provenance and material identity remain unmodified. F27 SourceRenderer accepts lazy_texel_decode=True. Previous full real GPU 19/19 original-view A/B gate PASS with zero numeric or per-pixel differences when motion indexing is disabled.

## P1: real runtime event skip + compact indexed v2

The original F27 episode runner now supports explicit scene_event_index=True. For a skipped frame it:
- Verifies source snapshot identity and the source-bound native color receipt (unless P2 direct material removes that stage with explicit replacement proof).
- Reconstructs the exact current robot marker on a cached raw/unmarked scene background, only when the base moved.
- Does NOT re-rasterize F27 scene objects, re-evaluate every material, or re-read native 10 mm voxel payload for skipped scene frames.
- Copies SG source for every real frame, and records direct physical-View/ref ownership.
- Emits an event receipt for every state.

The v2 compact packer saves only materialized PNGs, and writes direct one-hop view_refs with explicit ref_state for reused views. These refs are bounded to the same Episode, refer to a previous actual physical owner, do not chain, are validated at pack time and at resume. Each state retains its own gzip Scene Graph. The opt-in planner accepts both old completed v1 outputs and new v2 outputs; the default original plan continues to accept v1 only, preventing accidental v2 promotion.

The latest formal Viewer capabilities (including local folder mode) were preserved while adding v2 index-aware Room/Island view resolution. Four JS smoke tests PASS.

## P2: source-bound simulation direct material — NO colored voxels

A new explicit sim_direct_material=True mode uses verified original MuJoCo compiled Visual Mesh, material/UV/alpha and exact FULLPHYSICS GT states, independently generated Full Map Room/SG snapshots, source_model_sha256 and per-frame GT row SHA256. It consumes no native RGB-D or native 10 mm color payload and makes no native-color exactness claim. The original ROS1 native geometry/Room initialization stays in place; original nav_sg native RGB-D and dual-map pipeline are not changed. Source color voxels/Color stage and native_color_only stage are omitted at the actual Worker pipeline stage.

The direct material renderer adds an explicitly source-proved material-only branch; existing normal RGB-D/native behavior is unchanged. Full-scene Image/Mask/Geometry evidence and per-pixel material identity remain bound to compiled MuJoCo source assets.

## Real sequential matched F27 speed A/B (same GPU7, same priority and input)

| Task / episode | Old full F27 | P0+P1 F27 | F27 speedup | Source states | Scene FULL | Arrow-only |
|---|---:|---:|---:|---:|---:|---:|
| NavigateKitchen/002022 | 269.855083 s | 52.824066 s | 5.1086x | 19 | 1 | 18 |
| OpenDrawer/003029 | 200.132471 s | 74.830234 s | 2.6745x | 36 | 10 | 26 |

A/B 002022: 19 source/frame SG byte-content equal, 152 final views compared, 131 PNG exact, 21 differed by one pixel each, 192 cached keyframe NPZ numeric arrays exact, 26 physical PNGs + 126 references.

A/B 003029: 36 frame-specific SG equal, 144 final views compared, 90 PNG exact, 54 different, 1,245 pixels total differing, worst one view 57 pixels; 960 keyframe NPZ arrays exact; 66 physical PNGs + 78 direct refs.

## P2 real source Worker A/B (historical old run vs new independent run)

CloseFridge/episode_000569, source-bound real RoboCasa data and actual nav_sg native Room/SG via ROS Noetic, not a pre-materialized F27-only test:

- Old full Episode historical run: 511.41 seconds; F27 309.64 seconds; Color 92.47 seconds; native_color_only 5.04 seconds.
- New fully independent Worker: 256.86 seconds; F27 116.22 seconds; **0 Color or native_color_only stage starts**; material-direct source proof bound to original model+GT.
- Full Episode indicative speedup ~1.99x, **NOT a same-load paired full Worker benchmark**.
- New v2 package: 17 source states, **17/17 Scene Graphs equal to the old published v1**, 136 old View comparisons, 52 physical PNGs and 84 indexed image refs. 93 PNGs exactly equal; 43 differed by a total 2,710 pixels, worst single side View 468 pixels out of 178,974 (0.2615%).
- New published v2 Episode size around 11 MiB vs old v1 around 19 MiB, using the same broad du units (not a calibrated compression benchmark).
- No original production output was changed or replaced. Independent output path: /tmp/g2_p012_fullworker_20261113/output/tasks/CloseFridge/episodes/episode_000569.
- Human quality preview: /tmp/g2_p012_fullworker_20261113/human_gate/index.html, server localhost:18770. **Human H1 PASS: user explicitly reported no visible difference after inspecting the CloseFridge preview.**

## Tests and strict boundaries

- G2 Python full regression: **916/916 passed** when G2_F27_REAL_SOURCE_MJCF points to the real, read-only NavigateKitchen scene_rebased.xml; this includes both P0 real-texture tests that previously skipped without an explicit source asset.
- G2 Viewer Node smoke: **4/4 passed** (Island, no flicker, native local directory source, v2 indexing).
- Additional opt-in tests verify v2 full/arrow/reuse cases, direct indexes, per-frame SG, changed View inventory at FULL states, mismatched source fingerprint and wrong references, and malformed mode flags.
- P1 refs cannot claim motion above 1mm/1degree; native byte evidence is never forged. P2 direct mode refuses original color payload flags and source snapshots without correct GT provenance.
- Existing v1 202 completed Episodes remain retained and valid; no G2 full production process is running.

## Remaining promotion gates

1. **H1 visual acceptance CLOSED — PASS.** The user examined the CloseFridge preview, including the worst 468-pixel side-view difference, and reported no visible distinction. Keep exact pixel mismatch counts in the audit (visual PASS is not bit-exact parity).
2. Re-run full code on a second complete direct-material Worker task class and confirm Room/Island/ceiling/translucent cases are not regressed.
3. Complete a strict side-by-side or interleaved **full Worker throughput comparison** under the same machine contention if claiming global speedup (current 1.99x is a historical cross-run reference).
4. Promote code only after explicit approval; do not mutate formal V3 or the running/stopped producer in-place, never touch existing 202 v1 completed Episodes. The default original v1 and native RGB-D path must remain unchanged.

## Formal code and output isolation verified after GitHub experiment commit

The experimental branch was created from the pinned V3 commit f29b01d3235a7fbfd8e17727b8edaf2155957b35 and does not update V3. Full worker output was written only into an independent /tmp output root; pre-existing 202 completed formal v1 RoboCasa Episode directories remain untouched. G2 full production was not restarted. The latest CloseFridge H1 review has been explicitly accepted by the user.

## H1 accepted — 2026-11-13

The user reviewed the real complete CloseFridge/episode_000569 side-by-side comparison at the fixed localhost:18770 preview and explicitly stated **“没有区别的”** (no visible difference). The previous 1 mm translation / 1 degree rotation tolerance remains the agreed image-update policy. Mark visual quality gate H1 PASS for this candidate and treat the remaining 468-pixel maximum and aggregate 2,710 different pixels as audited, intentionally accepted visual approximations. This does NOT mean bit-exact PNG equivalence; 17/17 per-frame Scene Graphs were content-equal, and source identity was checked independently.

Promotion remains blocked on finishing remaining required tests (including a second complete original-source direct-material Worker task/layout and source-v1/v2 mixed Resume validation) and an explicit production merge decision. Do not restart full production automatically.
