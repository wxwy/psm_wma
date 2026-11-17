# Issue63 — G2 final source capsule and safe retirement

2026-11-17 CST. Code/CPU candidate, not a real-server/capacity acceptance.
Base is PR62 latest `d0bb45343a047fdf90d8e376acf4502fdf13fff4`; approved
production source `5e6a2ceb702acd724076692f42ca4fc60380192b`, unchanged
Child/Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2` and nav
`70eb7b447e65d793b0ebe18b258291ce46f057c1`. The new formal Root is assigned
after code/CPU checks and listed in the Draft PR/canonical Inbox.

Owner Issue63 authorizes repository code, CPU evidence and an independent
Draft PR; GPT performs fixed-code real F27/Wan/capacity checks on the server.
No server/private-file access or transfer, new environment/install, real GPU,
full production, old-data deletion, state15, alignment, training or merge here.
Existing GPT501/501,169 real B1 owners and419 pixel pairs are baseline evidence,
not an approval automatically inherited by this new source protocol.

## Actual field-dependency audit

| Working v1 field | Actual consumer | Final representation |
|---|---|---|
| source_id, original source/READY SHA | cache payload headers, source receipt, job scope | exact historical working binding + original readiness JSON in capsule; explicitly retired provenance |
| task/episode/source_fingerprint/profile_id | stage validator, scanner, ledger | capsule + existing episode manifest; exact equality checks |
| source_inputs_sha256, mapping/source versions | original inputs and immutable plan | capsule input identity from full seal and frozen controller policy |
| states incl raw pose, selection, SG/spatial paths | stage validator, Viewer/text references | unchanged episode_manifest.states; numeric ordinal/id/frame table stays in cache manifest |
| files | full product verifier | unchanged episode_manifest.files, fingerprint-bound by capsule; no third copy |
| views.owners, state_records | scanner, per-View cache planning/reading, late-event idempotence | all owners in order + all state mappings in capsule; no task-based filtering |
| owner PNG path/SHA/event, scene geometry state/frame/hash, native projection SHA, marker flags | immutable owner reconciliation and spatial_metadata.image_owner | all non-projection owner fields retained exactly |
| projection axis/reference_frame/right/up/forward/uv/mpp/width/height/bounds/depth | projection_from_renderer + spatial image_projection | canonical-equivalent minimal raw projection table, deduplicated by content hash |
| projection.stage_static/stage_dynamic/alpha and unrelated renderer audit | not used by projection_from_renderer or numeric scanner | removed only after full verification; optional external lossless audit |
| final_pixel_events | seal/refill and late-message identity | complete small final-owner descriptor map retained |
| membership, inverse object/View links, geometry versions, Room/Island, language/task bindings | spatial_metadata, SG, task_entities, language, selection | original files/bytes retained; common stage verifier rechecks them |

`minimum_projection()` derives its whitelist from the existing projection
function's actual input uses and requires exact canonical projection equality.
The common verifier compares it to every independent state spatial metadata
image projection. No coordinates, member sets, Room/Island IDs, SG relations,
task entities, original captions, text or pose are regenerated. Native-only
source audit hashes remain provenance, not a claim that their old files exist.

## Explicit v1/v2 contracts and unchanged PT payloads

Production keeps the full `g2_sealed_spatial_source_v1` and its READY through
rendering, VAE, ACK, post-hoc recovery and original full profile verification.
Legacy OutputProfile semantics/IDs and all v1 scanners remain strict.

Only `final_source_format=capsule_v2` enables retirement, on a **new owned
output/work/spool/run namespace**. The frozen JSON source policy binds its
output guard, config ID, source versions, mapping SHA and protected roots.
One output has one source policy; a different spool/archive policy rejects.
The new official template opts into this mode and uses Issue63 fresh paths.
Omitted selector means working_v1; it never silently migrates old accepted data.

| Artifact | Final v2 contract |
|---|---|
| spatial_source_index.json | g2_spatial_source_index_v2, actual file SHA + capsule_id, below1MiB enforced |
| SPATIAL_SOURCE_FINAL_READY.json | g2_final_spatial_source_v2, actual capsule SHA/ID and attestation |
| vae_cache/manifest.json | g2_spatial_view_vae_index_v2, final source binding + exact historical working_source |
| vae_cache/COMPLETE.json | g2_spatial_view_vae_complete_v2, actual new cache-index SHA and capsule SHA |
| episode_manifest.json / COMPLETE.json | g2_spatial_profile_episode_v2; unchanged products/state/file inventory, new verified VAE receipt |
| SOURCE_RETIREMENT.json | g2_spatial_source_retirement_v2, old verified proof and actual final-file hashes |
| spool completed tombstone | g2_published_episode_tombstone_v2; actual current identity files, capsule SHA and original audit provenance |

Original `source_id` is retained for immutable numeric/source history;
`capsule_id` identifies the new compact content. The v1 payload header's
original source/READY hashes are historical evidence, not hashes recomputed
against deleted files. Explicit v2 dispatch validates the new files and matches
selected PT headers to the authenticated working binding. No original `.pt`
bytes, recipe, B=1/T=1 math, weights, normalization, dimensions, tensor layout,
View storage or selected-only LRU/mmap behavior are changed.

Hash graph avoids cycles: capsule and new READY precede cache index/COMPLETE;
those precede episode manifest and retirement receipt; final episode COMPLETE
binds that receipt. The SQL-bound transaction and final job tombstone anchor
the exact capsule and both generations of identity. No file pretends to hash
itself or a deleted full audit.

## Safe lifecycle and recovery

The existing collector reaches done=2 only after real full source/cache/profile
verification, durable ACK/handoff and private chunk release. It verifies exact
scope/recipe and obtains the existing renderer/work/target locks. Work cleanup
keeps its original working-cache proof even when final indices later change.
Explicitly retained renderer work is not eligible for source retirement.

Retirement additionally holds cache writer and reader leases. Legacy read-only
datasets bootstrap shared leases on the existing manifest inode; retirement
holds it exclusively while installing a permanent lease. This avoids a
lock-file creation race and introduces no legacy write requirement. Live
ViewReader leases defer retirement. A stale pre-swap EpisodeIndex must reopen.
The JSON-only index opener imports neither Torch nor renderer/VAE/ROS modules.

1. Validate every original artifact/PT and source/scope. Build minimal capsule
   and planned small indices; refuse capsule>=1MiB or transaction>8MiB.
2. Commit the exact transaction/capsule hashes to SQLite FULL-sync **before**
   any source mutation. Fsync the bounded transaction journal.
3. Temporarily remove the episode COMPLETE, publish the capsule/new small
   indices, and rehash every unchanged PNG/SG/metadata/task/language/PT plus
   planned new index/receipt. They must still match the verified publication.
4. Only then atomically rename full source/old READY into this episode's owned
   retirement staging, fsync and unlink them. No other input/work is eligible.
5. Publish actual final v2 COMPLETE, run the strict v2 profile/cache verifier,
   record metrics, remove the journal and finally archive the acknowledged SQL
   rows under the new tombstone. Final training_ready remains false.

The journal is bound to SQL job/target/recipe/policy hashes; it cannot substitute
another episode or become an unverified absence waiver. After a hard exit,
new readers reject pending publication. Resume repairs the transaction before
the original planner sees temporarily mixed indices. Known atomic temp names
are reclaimed only with the durable SQL intent; other files and symlinks reject
and remain. Repeated retirement/GC and late final-owner messages are idempotent.
Low disk before publication retains the full working source. No partial VAE or
unacknowledged data can retire. Source recovery never runs a renderer or VAE.
The final capsule must still match the durable SQL intent even after journal
removal and before completed-ledger GC; missing or changed bindings reject.
Both original proof/cleanup fingerprints and both retired-file hashes are
checked against that capsule in the shared lazy-reader verifier. Archive and
disposition fields must agree too; changing a receipt together with its
COMPLETE hash cannot detach its provenance from the original capsule.

Spoolv4 explicitly carries a capsule policy and the durable retirement hash.
Working-v1 spoolv3 still attaches under its original binding; no v3→v4 implicit
migration. Use new staging for this candidate. Default full audit retention is
false, with no permanent original/gzip duplicate inside the final dataset.

## Optional external full audit

`keep_full_audit=true` requires an explicit archive root on another filesystem,
disjoint from output/work/spool/code/raw/flat/Depth/G1/cache/checkpoints, plus
an operator retention policy. Fill `source_protected_roots` with the actual
existing G1/cache/checkpoint roots before enabling it; no guessed server paths.
An unowned nonempty archive root or policy conflict rejects.

The archive preserves **exact complete working source JSON bytes**, losslessly
gzip1 (deterministic header), and original readiness/scope/provenance in a small
external receipt. It verifies decompressed SHA before retirement. Existing raw
private model/state/log assets remain on the server; this is not a copy of the
whole native work directory. Archive bytes are additional disk use, reported
separately. External retention/deletion is operator managed, never automated
by this task; training v2 reads do not depend on archive availability.

## GPT native asset-root verification (2026-11-17)

The old operator template's `robocasa_repo=/mnt/data1/data_v2_0617/robocasa_repo` contains `robocasa/models/assets` as a symlink to `/mnt/data1/data_v2_0617/robocasa_vendor_build_20261023/robocasa/robocasa/models/assets`. The strict source closure validator correctly rejected a file whose resolved path fell outside the declared root (`asset escapes approved roots`). Actual RoboCasa files at both paths are identical through the symlink; the failure was the authorization boundary, not different model bytes.

The template now uses the **canonical already-existing vendor asset repository** `/mnt/data1/data_v2_0617/robocasa_vendor_build_20261023/robocasa`. This explicit authorized root passed official two-real-episode preflight, F27 native generation and B1 Wan parity (81 states, 169 owners, 419 exact image pairs) on isolated fixed implementation `a169fea0`. It does **not** disable symlink containment, hash checks or raw-episode source identity. Frozen private configs on other hosts must use their independently verified canonical asset roots. Do not alter or delete either installed asset tree during production.

## Operator commands (NOT RUN on server here)

Freeze Root from the new PR, original Child/nav and original PSM Python. Copy
the repository template to a **private external** config, fill actual mapping
SHA/paths/Root. Never use the old accepted data root as this staging output.

```bash
G2_CODE=/absolute/clean/checkout/of/reviewed/issue63/sha
G2_PYTHON=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
G2_CONFIG=/absolute/private/frozen/issue63_sample.json
cd "$G2_CODE"
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" preflight
# GPT separately authorized real sample only, not full9126:
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" run --manual-start
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" progress
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" stop
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" resume --manual-start
```

Sample config: sample_mode=true, tasks=[CloseBlenderLid,CloseFridge],
episodes_per_task=1, expected_selected_episodes=2, expected_task_count=2,
expected_episode_ids=[0,502], explicitly approved GPU allocation/resources;
final_source_format=capsule_v2, keep_full_audit=false. Same B1 recipe
`3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1` and original
NumPy2.2.5 consumer, renderer MuJoCo overlay isolated as accepted in PR62.
No environment installation or automatic build is added.

```bash
export PYTHONPATH="$G2_CODE:$G2_CODE/cosmos-framework" PYTHONDONTWRITEBYTECODE=1
export COSMOS_TRAINING=0 COSMOS_INTERNAL=0
# Full CPU audit of one already-retired v2 episode; no encoder:
"$G2_PYTHON" -m tools.g2.verify_spatial_source_index \
  --episode-root "$G2_EPISODE" --recipe-id "$G2_RECIPE" --file-bytes
# Existing shared-core source/cache verification, including new v2:
"$G2_PYTHON" -m tools.g2.verify_spatial_view_vae_cache \
  --dataset-root "$G2_EPISODE" --recipe-id "$G2_RECIPE"
# Owned acknowledged transaction recovery only (no rendering/encoding):
"$G2_PYTHON" -m tools.g2.resume_spatial_source_retirement \
  --spool-root "$G2_SPOOL" --job-id "$G2_JOB" --execute
```

Existing post-hoc build/verify CLI still handles completed v1 and explicit v2;
resuming a complete v2 cache does not rewrite numeric payloads. Interrupted
retirement must recover through its original owned spool before inspection.
0 means fully verified retired data;75 means retained busy/pending work;
2 means rejected/failure. Source-ready75 is never final v2 completion.

## Capacity Gate: measure strata; do not infer from two large episodes

Issue63 comment6948361728 supplies a real old-corpus baseline:9,126 episodes,
18 tasks,638,440 files,68,740,346,457 logical bytes=64.02GiB. Task means range
widely; Blender/Fridge are not representative corpus averages. Prior 500GB
extrapolation is not a measured corpus requirement. Conditional104–126GiB is
also not capacity approval. No old view was deleted by this implementation.

The read-only scanner counts logical/allocated bytes, PNG physical owners,
SG/metadata/latent/index categories and per-task distributions. The sample
projection uses same-task deltas when measured, otherwise explicitly labels
cross-task sensitivity. Missing tasks or inadequate budget yield HOLD_CAPACITY,
even if a two-sample conditional upper estimate fits. Even full strata return
only a candidate requiring GPT approval, never authorize production.

```bash
"$G2_PYTHON" -m tools.g2.audit_spatial_capacity \
  --old-root "$G2_OLD_VIEWS" --output "$G2_PRIVATE_EVIDENCE/old_by_task.json"
"$G2_PYTHON" -m tools.g2.audit_spatial_capacity \
  --old-root "$G2_OLD_VIEWS" --new-root "$G2_V2_SAMPLES" \
  --available-bytes "$G2_VERIFIED_BUDGET_BYTES" --reserve-bytes 8589934592 \
  --expected-episodes 9126 --expected-tasks 18 \
  --output "$G2_PRIVATE_EVIDENCE/stratified_capacity.json"
```

Outputs must be fresh paths outside datasets and Git source; no tracked test
evidence can be overwritten. The tool does not launch GT/F27 or delete files.
Account separately for external archive bytes, native/spool peaks, transient
transactions, failure recovery and the8GiB output reserve. Existing production
disk admission is a runtime reserve, **not** proof that the corpus fits.

## Required independent real Gate and stop condition

GPT uses isolated v2 outputs for Blender000000/Fridge000502, verifies81 spatial
states/12 logical Views/169 physical owners/419 original-vs-new pixel pairs,
all PT file SHAs before/after retirement, B1 independent reencode169/169 exact0,
selected-only reader after full source is gone, v1/v2 read latency and new
finalization overhead. Report per-file bytes, source index well below1MiB,
expected total Blender<=24MiB/Fridge<=28MiB **as targets, not measured facts**.
Keep every private raw source/image/log on the server.

Then perform18-task stratified capacity inference and original32-renderer
resource/A-B gate. Full9,126 remains HOLD until those facts and Owner approval;
the old manual tmux start command is not an approval. No old views/G1/flat/
Depth/cache/checkpoints or environments are removed. No V3/Child/nav merge.

CPU command/raw JUnit/source SHA/fixture protocol and local peer receipt are
under docs/collab/codex/evidence/2026-11-17_issue63/. FakeEncoder exact0 and
synthetic sizes do not replace the above real169/419/capacity Gates.
