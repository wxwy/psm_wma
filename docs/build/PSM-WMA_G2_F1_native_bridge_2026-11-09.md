# G2-F1 native bridge — fixed-source review candidate

Formal Root `feff0d54b04a4c669198ec48493736bbc5dcaa81`, tree
`91312da9c3971fa70491685a2061f5223a687fa3`; companion native
`e15c4cc28a157526a53827f29aeb70f88c845a66`. Exact GitHub trees/Git objects
and45/45 PSM +175/175 native source/test/build-entry blobs verified. Canonical
Inbox request5e220f0e was committed/read back before Issue26/6734897202 and
nativeIssue8/6734902391 delivery; both full comment bodies matched. Final
publication/handoff receipts are metadata only, not new implementation targets.
Awaiting GPT; no independent verdict or automatic server execution is inferred.

F1-D scope remains fixed6b04/reviewf86ecef5; scene-release implementation54541
and both server-local packages remain frozen, pending GPT verification. This
independent bridge starts at F1-E metadata dc714108. Gitlink remains
`1ca308055fc41fb69efaeb9efaa23808f164a18e`.

Only existing snapshot.py/recorded.py change, with two new focused test files.
The other41 earlier G2 files, including sampler, identity, role evidence,
scene_release and six/Island rendering, are byte-identical. Native normal
structures/relations live in the separate nav_sg branch from2009fae35; G2 does
not reimplement Room segmentation or create patches/Islands.

The receiver checks normal Floor/Wall exact occupied-box proofs, current scene/
source/frame/refresh, raw grid and complete native Room/probe fingerprint. It
reproduces C++ binary hashes and verifies finite mesh/bounds/occupied IDs,
known-free sensor/nine-column probe, whole-Room foundation, boundary continuity,
numeric patch owner/normal and complete-coverage claims. Plural display Room
adjacency/null axis are permitted. Resealing flags cannot fill unknown/hole/
open support. Grid reads are prechecked/bounded to <=10M cells, Room labels
budgeted before materialization, local IDs unique, world extent finite.
Rootless legacy diagnostics retain uncertainty; current model witnesses and
semantic=false are distinct from geometric coverage.

The recorded planner adds explicit native-structure flags. PARTIAL_COLOR needs
both --allow-declared-subset and --allow-partial-color, no COMPLETE/full review,
complete unique compiled geom IDs/names, zero actual UNCLASSIFIED, and original
per-point color/mask/face proof. It preserves genuine model/sidecar and original
model/state/ep_meta bindings. Plans never run models or certify full source,
history or training. Existing COMPLETE/default-off behavior is retained.

Author CPU command, repository root, NumPy/MuJoCo environment only:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  python -m pytest g2/tests -q -rs --junitxml="$NEW_AUTHOR_XML"
```

**446/446 distinct PASS**, zero failure/error/skip; original397 and earlier18
native proof IDs retained. New total33 proof/16 recorded-option cases. Another
Agent independently reread final JUnit/source hashes and closed all concrete
P1/P2. Initial negative-fixture earlier rejection and legacy error-message
matcher failures are preserved separately; checks were not weakened. Raw446
log/XML,45-file source inventory, retention and review live in
`docs/evidence/g2_f1_native_bridge_2026-11-09/`.

Native author evidence: full CPU Noetic build,157 distinct C++ (old129 retained),
53 related Python, official no-extra-XML closed/doorway × ESDFGrid/GVD main runs,
earlier/off/isolation controls. Native152-file build fingerprint:
`a977dcd33eeb77a44acb2f9c6818583ab9a2b3b9d243b79b88b6e7c4398fb07c`.
Eighteen actual C++ snapshots passed this Python raw-grid/proof validation.
Objects/models0; capture correctly blocked all18 and wrote no bundle. These
self-authored CPU scenes are not real Layout1/10 or YOLOE/SigLIP results.

GPT's real workflow remains on-server: verify the immutable role release and
all original inputs, reuse already accepted colors/classifications, retain
partial masks. Do not change originals or repeat pointcloud human acceptance.
For an already valid world-frame frame0 PARTIAL_COLOR manifest/matching grid,
prepare only:

```bash
python -m g2.sim.scene_release verify \
  --profiles g2/config/scene_role_profiles_2026-11-09.json --output "$SERVER_LOCAL_SCENE_RELEASE"
python -m g2.nav_bridge.recorded --prescan-manifest "$SERVER_LOCAL_FRAME0_MANIFEST" \
  --grid "$SERVER_LOCAL_MATCHING_GRID" --nav-repo "$ISOLATED_FIXED_NATIVE_REPO" \
  --dataset-root "$SERVER_LOCAL_REAL_RGBD_ROOT" --episode "$EPISODE" --camera "$CAMERA" \
  --sidecar "$SERVER_LOCAL_GENUINE_MODEL_SIDECAR" --frames 201 \
  --allow-declared-subset --allow-partial-color --native-structures --room-source esdf_grid \
  --output "$NEW_SERVER_LOCAL_PLAN"
```

Variables/plans/packages stay server-local. The planner refuses mismatched
frame/world/source inputs or absent genuine dependencies. Do not edit partial
into COMPLETE. Its argv uses the existing native semantic replay/launch, now
with explicit native opt-in and fixed source/tree provenance. Actual model
execution belongs to GPT/execution-side validation, not this author's work.
Check Layout1/10 frame0/200 native roots, objects, relations and uncertainty
before six+Island/human review. Absent model/ground/boundary evidence is a
specific blocker, never filled by source GT labels or guessed valid colors.

Public artifacts contain own test evidence, repository references, counts/hash
only. Original XML/assets/states/images/clouds, private configurations and
individual role proofs remain data; no new private server paths are published.
No V3/production/Gitlink/cache/GPU/model/train/merge/PR change. Publish fixed
sources/review request, then stop for GPT independent acceptance. Owner's next
human review is native rooms/relations/six+Island, not the accepted pointclouds.
