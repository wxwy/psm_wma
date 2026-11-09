# G2 F3: measured native color resolution

Implements Owner comments nav_sg#8/6740780287 and PSM#26/6740781122 from
c4c2a364 / c5825589 source, on independent codex/g2-f3-color-ab branches.
Native source is fixed at abcc87ca636c81455f397e8b0813522c70874c00.
This is a candidate for GPT independent repeat and Owner visual review.

The existing native RGB-D ColorCloudMap is compared at 5 / 2 / 1 cm, with
unchanged navigation geometry, Room/SG algorithms and 2 Hz publication.
No second map/cache, asset-texture color, model inference or training is added.
The native driver retains source-time 1 Hz capture ticks, records achieved
wall cadence, and measures fusion separately from publication and conversion.
Rendering is separately measured; this does not certify live 1 Hz six-view output.
0.5 cm and changing the production default require subsequent evidence.

## Receiving actual observed colors

`g2.nav_bridge.observed_color` verifies the original Episode model/state path-only
proof, current GT manifest/geometry and the actual recorded RGB-D/K/pose prefix.
It pins all four native verifier dependencies. It does not execute an interpreter
from an input artifact. Run it in the same Noetic Python/NumPy serialization
environment as the sender, with MuJoCo 3.3.7 available in an isolated overlay.
Cross-runtime quaternion last-bit differences are rejected, not rounded away.
The `--ros-python` path is only a receipt of the producer interpreter, never a
command to execute during bundle loading.

Prepare using:

```
python -m g2.nav_bridge.observed_color prepare \
  --native-manifest GT_MANIFEST --color-manifest OBSERVED_MANIFEST \
  --nav-repo FIXED_NATIVE_REPO --ros-python PRODUCER_PYTHON \
  --model-rebinding-proof REBINDING_PROOF --output NEW_PREPARED
```

Execute its exact `plan.json` argv/environment in the isolated native Catkin
overlay. The existing GT backend receives the observed cloud without another
color fusion or voxel-size change. Then use `observed_color capture` with
`--native-directory`, `--prepared`, `--output` and expected native build SHA.
Render the sealed bundle with `g2.views.render --allow-full-map-mujoco`.
GT structures/object identities stay explicit GT. RGB comes only from the
native depth/depth_sdf_filtered worker, with no precolored initialization.

Geometry and color retain separate source SHAs, linked by exact original model
closure and state archive. Source-state and ROS clocks remain separate and
bound to the same frame. The receiver checks every integrated trace row against
actual recorded bytes, encoding, dimensions/stride/endianness, K and timestamps;
future or duplicate binding identities, incomplete counters, mixed maps and
LiDAR providers are rejected. Bundle capture protects all original input roots.

`model_rebinding` now records inaccessible archived asset paths explicitly,
while verifying current mapped bytes and path-only XML equivalence. Actual
original includes remain mandatory. Neither current asset agreement nor a
path-only proof certifies historical asset/generator versions.

## Views and measured comparison

The existing native connection and Island IDs drive the six directions.
Floor/Wall alone does not justify an image. No projectable object produces
SKIPPED_NO_PROJECTABLE_OBJECT with metadata/missing mask and no PNG. Existing
objects without observed RGB are UNKNOWN_NOT_OBSERVED. Legacy asset-colored
bundles and a semantic model witness do not certify pure observed color.

The renderer uses zero same-owner depth tolerance and no color interpolation
or backside filling. Whole thin objects within voxel quantization uncertainty
stay masked. Voxel centers carry no per-voxel ray certificate: local thin
features and general directional visibility remain unverified and require the
human Gate. Metadata explicitly says directional_ray_certification=false.

`g2.views.color_ab_report` reports CPU/wall fusion/projection/conversion/export/
render percentiles, voxel counts, actual outcomes, peak RSS, source-time and
achieved wall cadence, missing views and source hashes. Same-scene comparisons
require exact common input/base/build fingerprints and equal nonempty capture
frame sets. Navigation/SG byte differences are reported, not silently promoted
to task stability. Normal frontend/structure failures remain recorded failures.

## Author validation and independent handoff

553 PSM Python tests pass with no failure/skip; all original 517 are retained.
The native candidate has 173 C++ and 121 data/GT Python passing tests (all 106 collected baseline IDs retained). Native
own-fixture runs cover all three leaves, four input frames, two color and two
normal snapshots per leaf, and sixteen rejected bindings per leaf. The separate
worker smoke verifies overwrite/clear/stop/reject accounting and independent
fusion/publication. An actual two-frame native RGB-D -> source-GT -> sealed
bundle -> six-view roundtrip passes, producing two observed images per frame.
Raw own-fixture receipts are under docs/evidence/g2_f3_2026-11-09.

These tests do not approve Layout1/10, normal model semantics, historical source,
training data or human visual quality. Real author A/B artifacts and raw private
files remain on data; only aggregates/hashes are handed off. GPT independently
repeats the fixed pair before the Owner reviews images. V3, Gitlink, original
assets/cache, existing PRs, GPU/training and merges are untouched.

For Noetic with modern CMake and cached GTEST imported names, configure with
`-DCMAKE_PROJECT_mapping_INCLUDE=PSM_REPO/g2/nav_bridge/noetic_gtest_import.cmake`.
This loads the installed GTest config as global targets on each configure; it
does not change native sources or test bodies. Preserve any failed build attempt
and the effective build flags in the server evidence.
