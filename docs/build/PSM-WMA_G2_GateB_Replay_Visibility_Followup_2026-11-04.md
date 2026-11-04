# G2 Gate B — renderer/ray visibility follow-up

## Scope and authority

Owner requested the narrow follow-up to server report
`2026-11-04_G2_Stage1_b67bc4ca_1069fe78_Server_GateB_PHYSICAL_REPLAY_NOT_ACCEPTED.md`.
Start from report commit `992cfc2adb3150c573d19206e176bd8a52574949`, preserving
the previously approved source `b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab` and
all failed server evidence. Child/Gitlink stays
`1069fe78841228cadbbfbe6afbd767eaed6225da`. This is an isolated candidate, not
a V3 promotion. The precise new Formal Root is recorded in the author handoff
and machine-readable evidence after freezing the source.

Only production file `tools/g2/rgbd_pose/replay.py` changes. Source-state/Flat
mapping, RGB decoder, depth codec, cache publisher, verifier thresholds, model,
Local-TTT, training and Child are unchanged. Earlier runbook/cache schema and
reports remain immutable. No server files were obtained by this author.

## Reproduced causes versus unresolved server facts

Tiny synthetic MuJoCo 3.3.1 scenes rendered with CPU OSMesa reproduce the old
checker's false failures, independently of RoboCasa or any recorded data:

| Synthetic case | Old checker | Source of non-equivalence |
| --- | --- | --- |
| Semitransparent foreground box | About 0.85 m error, same geom ID | Normal RGB transparent pass does not write depth; segmentation/ray still sees it |
| Inward-facing triangle mesh | About 0.30 m error, same geom ID | OpenGL culls back faces; `mj_rayMesh` intersects both faces |
| Single mesh with two depth layers, MSAA 4 | About 0.85 m at edges | Segmentation disables multisampling; resolved depth can sample another layer |

A sloped face can also have a measurable pixel-center versus resolved MSAA
sample difference without a geom-ID edge. These are demonstrated reachable
validator errors, **not proof of the server's specific root cause**.

Official robosuite rendering uses the same draw path for RGB and RGB-D; `depth`
only selects additional depth-buffer readback. Synthetic RGB versus RGB-D and
RGB before/after segmentation are identical. G3 visual alignment and matching
Depth/K/Pose do not establish G3 original-video MAE <=5. **RGB mismatch remains
unresolved**; do not guess controller, camera or material overrides.

## Minimal correction and diagnostics

- Read actual scene opacity, geom groups, culling and render options. Reject
  unknown/changing options, convex-hull rendering or wireframe as INCONCLUSIVE.
- Exclude transparent/unknown rendered geometry before comparison. Where MSAA
  is enabled, select same-ID interior pixels using fresh-render validity,
  inverse-depth local plane consistency and a bounded local depth variation.
  Plane consistency supports sloped surfaces; the variation bound excludes
  unresolved steep subpixel footprints. Selection never reads cached depth
  values or measured ray/cache error. Coverage counts and selection bounds
  are included in the report. No error-based rejection of an eligible ray.
- Start rays at the optical near plane, then add the offset back before
  converting unit-ray distance to optical Z.
- Keep native `mj_ray` identity checks. For back-face-culled meshes, intersect
  front-facing compiled triangles independently using Möller–Trumbore and the
  live geom transform. Do not reapply compiler mesh position/rotation/scale.
  Cull-off and non-mesh paths retain native ray distances. The new mesh path
  and sampling eligibility require fresh code review.
- Preserve `max_abs_z_error <=0.01m`, at least 16 matching samples and RGB
  MAE <=5. Insufficient comparable samples remain INCONCLUSIVE; eligible
  outliers remain FAIL. The verifier's full-image cached/fresh depth, mask,
  K/Pose, original RGB and identity checks remain unchanged.
- During explicit `ray_check` only, compare same-context RGB/RGB-D and RGB
  before/after segmentation. Return scalar differences, render settings and
  visual-array fingerprints in `rgb_render_diagnostics`. Existing verifier
  persists this under each camera's `independent_geometry`. Ordinary export
  performs no added renders and runtime identity gains no dynamic fields.

## Author CPU acceptance

Run the existing 83 tests separately with `MUJOCO_GL=disable`. The analytic ray
fixture gains explicit fresh RGB/depth/scene metadata required by the real
interface; existing assertions are preserved verbatim at AST level. Run the
new software-render suite separately with `MUJOCO_GL=osmesa`,
`PYOPENGL_PLATFORM=osmesa`, `LIBGL_ALWAYS_SOFTWARE=1`, empty CUDA devices and
process-scoped temporary library/dependency/cache paths. No skip/xfail allowed.

Freeze the first 20 new tests before evaluating old/new source. Retain old
expected RED and current GREEN, not just a written claim. Additional guards
cover unsupported/changing visibility and one erroneous eligible ray; none
of those errors may be removed to manufacture a PASS. Record Ruff 0.12.7,
format, AST/compile, unique JUnit counts, exact source blobs, scope and unchanged
Gitlink. CPU software rendering is not real RoboCasa acceptance.

## Server follow-up after fresh code approval

Gate B remains FAIL until separately re-executed. Use the original Stage-1
runbook's exact CloseFridge local0 / Flat global502 / frames0,214,428 / two
cameras, in a **new** cache/report namespace with the newly accepted Formal
Pair. Read the server Git fetch skill; do not modify existing outputs or active
worktrees. Keep all thresholds and source state-index policy unchanged.

For each frame/camera, inspect `rgb_render_diagnostics` in the physical report:

1. `rgb_vs_rgbd` must explain whether the installed renderer changes RGB when
   reading depth; `segmentation_before_after` detects actual context pollution.
2. Compare actual geom/site groups, scene/vopt flags, material/geom/light scalar
   hashes and effective old/new render construction settings **on the server**.
   Old G3 scripts are unversioned server-only evidence; do not download them.
3. Measure old G3 RGB versus the same original video, not merely visual alignment.
   If both exceed MAE5, investigate source/runtime photometric differences.
   Share only non-sensitive numeric summaries, not images/arrays/scripts.
4. Report eligible/matched counts, opacity/MSAA/culling handling, ray maximum,
   full cache/fresh checks and original RGB metrics separately. Low coverage or
   unresolved RGB mismatch still prevents physical PASS.

Triangle-based mesh checks may be slower than native BVH; measure Gate B wall
time before discussing further optimization. No Gate C, N100 export, V3 merge,
training, GPU job or old-cache migration is authorized by this follow-up.
