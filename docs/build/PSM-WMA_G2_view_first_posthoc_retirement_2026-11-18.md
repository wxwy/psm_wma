# G2 View-first → posthoc VAE → existing v2 Source Retirement

2026-11-18 CST. Incremental implementation and validation runbook; real Gate
results belong to their actual fixed-source receipts, not this specification.

Base V3 `b6311222c364543787f913215bf584065aa1c275`, Child/Gitlink
`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`, nav G2
`70eb7b447e65d793b0ebe18b258291ce46f057c1`. PR64/65/66 are merged in this
base. Their approvals remain valid for their stated implementations; this
new posthoc lifecycle requires its own code and real-data checks. Formal new
Root is recorded in the Draft PR/canonical Inbox after CPU and local review.

## Scope and production boundary

The existing `view` task continues unchanged. No renderer, scheduling config,
running production output, raw/flat/Depth/G1/checkpoint, model A/B/C/D module,
Child or nav implementation is modified. No server commit/push is permitted.
Use repository code in an isolated fixed checkout for server validation.
Source retirement is never an automatic consequence of merely reading gzip.
All corpus commands below are **drafts**, not an instruction to run9,126 now.

Existing PR66 `package_stage_a(compress_source=False)` remains the legacy
default. Current View-first producer explicitly opts into compression. Its
completed profile remains `view_vae=false`; Stage B does not change it to true,
rewrite its original manifest/COMPLETE or regenerate its data.

## R1 source access and contracts

`offline.view_only_source.working_source_info()` verifies the exact raw bytes,
source ID/fingerprint, original readiness and transport inventory. The old
`load_working_source()` tuple API remains. `final_source.load_source()` uses
the explicit profile schema to distinguish working data from a final capsule;
the working reader refuses a final capsule. No permanent decompressed JSON is
created, including when resuming or building from a compressed episode.

| State | Authoritative declaration | Hash semantics |
|---|---|---|
| Legacy working JSON | working profile v1, sealed source+READY | actual JSON SHA and original READY SHA |
| View-first gzip | working profile v1 with VAE disabled, typed `g2_view_only_source_gzip_v1` receipt+READY | compressed SHA/bytes, exact raw SHA/bytes/source ID, original READY |
| Posthoc working cache | explicit `g2_view_first_working_source_v1` cache source | actual transport/receipt/READY file hashes, separate raw SHA, owner inventory |
| Retired source | final profile/source/index v2 and retirement receipt | new actual capsule hashes; original transport/raw hashes are historical evidence |

Gzip is bounded by256MiB compressed and1GiB declared/raw output. Receipt sizes
are validated before bounded decompression; source/schema/identity, gzip bytes,
raw bytes and both hashes must agree. Ambiguous raw+gzip or missing/damaged
receipt rejects. Unknown/retired formats do not silently fall back to JSON.

Final capsule materializes only verifier-required views/projections plus the
unchanged published state/file indices. It is never presented as the removed
full renderer audit. All spatial projection/membership/Room/Island/geometry
version/pose/task/language files remain original byte-identical products.

## R2 independent VAE lifecycle

Existing build CLI gains explicit `--view-first` and external `--spool-root`.
Without that flag, the old no-VAE rejection is preserved. Shared builder,
preprocessing, B=1/T=1 Encode1, writer, per-View files and selected-only reader
are reused. B>1 is not implemented/frozen by this increment; no old B1 recipe
is relabeled as batch-equivalent. Every valid View/variant is encoded, whether
selected by the current task or not. Absent directions retain null indices.

`posthoc.py` is a lifecycle adapter, not a second producer or ledger. An
explicit posthoc spool uses existing finite PNG/result budgets, actual
per-record numerical fsync/ACK, refill, retry and GC. A fsynced numeric chunk
before ACK is reused on restart; completed records are not re-encoded. Same
target coordinator and existing consumer/cache locks prevent duplicate
writers. Source/recipe/owner mismatch rejects instead of overwriting.

Stage B publishes only `vae_cache/manifest.json`, its cache COMPLETE and
episode/view numeric files. The original View-first COMPLETE still means
exactly its original declared spatial profile; independent cache completion
does not fabricate a full training-ready status.

## R3/R4 explicit retirement and recovery

Stage C reuses `EventSpool.adopt_completed()`'s **fully audited cache handoff**,
tagged `g2_posthoc_completed_cache_handoff_v1`. A C-only handoff has zero
invented stream events/ACKs. It verifies every tensor file, logical owner/index,
recipe and spatial artifact before the existing collector can reach done=2.
Alternatively the same posthoc consumer can finish its own genuine ACKs.

The explicit posthoc retention policy is stored in an external spool. It binds
the original View-only root claim SHA and exact target/profile/recipe. It does
not create or overwrite any producer root marker/policy. Streaming retirement
policies cannot be used as posthoc policies. Optional audit archive constraints
remain separate filesystem/protected roots/explicit retention; default none.

The existing final-v2 SQL intent/journal, locks, reader leases, index
publication and rename/fsync/unlink engine is reused. The retired inventory is
derived from verified actual files: JSON+READY or gzip+compression receipt+
READY. No fake full JSON is used to satisfy old code. The shared reader checks
all historical proof/cleanup/retired hashes against the immutable capsule.

Original profile ID/products/states and all product/PT bytes stay unchanged.
Only Stage C upgrades the small episode/cache indices to final v2 and adds a
separate `posthoc_vae_receipt`; it does not flip original `view_vae=false`.
The final capsule remains below1MiB; exceeding the limit fails with actual
bytes/owner/projection/state counts and retains working recovery data.

If interrupted, use the **same C spool, policy, recipe and fixed code**.
Recovery repairs pending transactions before normal manifest/discovery checks.
Plan/execute without explicit CLI `--resume` reports pending transactions with
exit75. A live reader/writer returns pending; release it and resume. Corruption
rejects with exit2 and preserves diagnostic state. Never manually delete or
fabricate a READY/COMPLETE/journal. No render/VAE is run during C recovery.

After finalization, the former B spool's original-source proof is historical;
the final capsule/C tombstone is current authority. Do not rewrite old B
receipts. Rechecking a retired episode validates final data and performs no
encoding or full-JSON restoration.

```text
View-first published                 after independent B
  episode_manifest.json (v1)          same original View files/manifest/COMPLETE
  COMPLETE.json (View-only)           + vae_cache/manifest.json
  spatial_source.json.gz             + vae_cache/COMPLETE.json
  SPATIAL_SOURCE_GZIP.json            + vae_cache/<each logical View>.pt
  SPATIAL_SOURCE_READY.json
  PNG/SG/spatial/task/language/pose/selection

after explicit C
  original PNG/SG/spatial/task/language/pose/selection, same PT bytes
  episode_manifest.json / COMPLETE.json (final v2, original profile preserved)
  spatial_source_index.json / SPATIAL_SOURCE_FINAL_READY.json
  SOURCE_RETIREMENT.json, cache final-v2 index/COMPLETE
  no full JSON, gzip, old compression receipt or old READY
```

## Exact operator examples (real runs need actual frozen local configuration)

First verify the current `view` task/resource state without changing it. Clone
only fully published validated episodes into a new isolated sample dataset on
the server. Create its own root claim using the existing claim API before
copying episodes. Preserve originals; never use hard links for mutable indices.
Hash originals before/after to prove production files remain unchanged.

```bash
G2_CODE=/absolute/isolated/checkout/of/reviewed/fixed/root
G2_PY=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
G2_DATA=/absolute/isolated/view_first_samples
G2_B_SPOOL=/absolute/private/new/posthoc_b_spool
G2_C_SPOOL=/absolute/private/new/posthoc_c_spool
G2_POLICY=/absolute/private/frozen/posthoc_source_policy.json
G2_WEIGHTS=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
G2_RECIPE=3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1
cd "$G2_CODE"
export PYTHONPATH="$G2_CODE:$G2_CODE/cosmos-framework" PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1 COSMOS_TRAINING=0 COSMOS_INTERNAL=0
# Plan: no model or GPU initialization; reads declared complete Views only.
"$G2_PY" -m tools.g2.build_spatial_view_vae_cache --view-first \
  --dataset-root "$G2_DATA" --weights "$G2_WEIGHTS" --height 256 --width 256 \
  --cosmos-root "$G2_CODE/cosmos-framework" --plan
# Only in an approved small resource window; do not assume a fixed free GPU.
CUDA_VISIBLE_DEVICES="$G2_APPROVED_GPU" COSMOS_DEVICE=cuda \
"$G2_PY" -m tools.g2.build_spatial_view_vae_cache --view-first \
  --dataset-root "$G2_DATA" --weights "$G2_WEIGHTS" --height 256 --width 256 \
  --cosmos-root "$G2_CODE/cosmos-framework" --device cuda:0 \
  --spool-root "$G2_B_SPOOL" --execute --resume
# Full cache/source verification without reencoding:
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu "$G2_PY" -m tools.g2.verify_spatial_view_vae_cache \
  --dataset-root "$G2_DATA" --recipe-id "$G2_RECIPE"
# C plan: CPU tensor/source audit; no cleanup or model load.
"$G2_PY" -m tools.g2.retire_view_first_sources --dataset-root "$G2_DATA" \
  --spool-root "$G2_C_SPOOL" --source-policy "$G2_POLICY" \
  --recipe-id "$G2_RECIPE" --expected-episodes 2 --plan
# Explicit C small sample, only after B verifies:
"$G2_PY" -m tools.g2.retire_view_first_sources --dataset-root "$G2_DATA" \
  --spool-root "$G2_C_SPOOL" --source-policy "$G2_POLICY" \
  --recipe-id "$G2_RECIPE" --expected-episodes 2 --execute --resume
```

Policy fields reuse `g2_source_retention_policy_v1`'s existing format/output/
work/spool/config/mapping/source_versions/protected_roots/archive fields, with
schema **`g2_view_first_retention_policy_v1`** and additional
`view_first_claim_sha256` (actual new sample root claim file SHA). All paths
are canonical/disjoint; protect actual code/raw/flat/Depth/G1/checkpoint roots.
Freeze true Root/Child/nav/mapping and the selected source claim. Do not copy
the producer's original absolute-root claim verbatim into a different root.

Corpus drafts, **NOT RUN / not released by a sample pass**:

```bash
# After the View task finishes and independent small Gates A-D pass:
"$G2_PY" -m tools.g2.build_spatial_view_vae_cache --view-first \
  --dataset-root "$G2_FINAL_VIEW_ROOT" --weights "$G2_WEIGHTS" \
  --spool-root "$G2_CORPUS_B_SPOOL" --device cuda:0 --execute --resume
"$G2_PY" -m tools.g2.retire_view_first_sources --dataset-root "$G2_FINAL_VIEW_ROOT" \
  --spool-root "$G2_CORPUS_C_SPOOL" --source-policy "$G2_CORPUS_POLICY" \
  --recipe-id "$G2_RECIPE" --expected-episodes 9126 --plan
# Owner explicitly releases this only after independent approval:
"$G2_PY" -m tools.g2.retire_view_first_sources --dataset-root "$G2_FINAL_VIEW_ROOT" \
  --spool-root "$G2_CORPUS_C_SPOOL" --source-policy "$G2_CORPUS_POLICY" \
  --recipe-id "$G2_RECIPE" --expected-episodes 9126 --execute --resume
```

## Gate evidence and truthful accounting

CPU replay: `VF_PYTHON=/absolute/existing/python VF_GATE_OUT=/absolute/fresh/logs
bash docs/collab/codex/evidence/2026-11-18_view_first_retirement/commands.sh`.
It checks original560 identities/source files, all new cases, before/after
source hashes, protected numeric AST/producer/model boundaries, Ruff/help and
synthetic per-file bytes. No installation/new environment is part of it.

Real A: validate copied complete source gzip/raw hashes/source identity and all
spatial products. B: actual Wan T1/per-View owners/absent directions/dual top/
Room/Island/new images and reference reuse. C: final-source-absent readers,
complete metadata/tensor/source checks and PT byte preservation. D: interrupted
resume and unchanged legacy mode. Retest existing CPU legacy suites in the
original server environment. Numerical reencode and prior-recipe parity are
reported separately from structural/hash checks.

Report physical pre/post gzip/index/cache bytes, decoded raw bytes separately,
compression ratio, actual VAE throughput/retirement wall time and resources.
Removing gzip does **not** free the larger decoded JSON size that was never
stored. Tiny CPU fixtures can compress below the final index size; their
before/after numbers do not certify real storage or speed benefit. Private
images/models/states stay on the server; only derived summaries/hashes leave.

Independent code approval, actual small sample acceptance and corpus release
are separate facts. No automatic production stop, merge,9,126 VAE/retirement,
data/environment deletion or training follows this implementation.

## Author fixed-source follow-up (2026-11-18 CST)

Implementation `5c7ea400035e2727a2dae1d63dfe7d21b14b9ff2` is published in
[Draft PR67](https://github.com/wxwy/psm_wma/pull/67). Existing-server-environment
CPU612/612, zero skips; independent local peer4probes/noP1/P2; real two-copy
169record strict-zero reencode and source retirement/recovery passed author
Gates A–D. All retained product/PT bytes and production originals stayed
unchanged. No production full-corpus cleanup or merge occurred.

[Actual commands, bytes/times, limits and private evidence bindings](../collab/codex/evidence/2026-11-18_view_first_retirement/SERVER_GATES.md)
remain separate from this protocol. Source-code review authority stays at the
fixed implementation SHA; later documentation commits are bookkeeping.
Independent GPT approval and any full9,126 release remain pending owner gates.
