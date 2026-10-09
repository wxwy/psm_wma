# Corrected V3 — Persistent Verified Dataset Index Contract

Date: 2026-10-09
Owner: ChatGPT
Scope: exact-window RoboCasa target-atomic cached source binding, not training numerics

## Why this Gate is ahead of GPU smoke

The previous corrected V3 cold preflight repeatedly traversed 9,126 accepted
episodes / 2,085,331 exact windows. Source binding scans Parquet identities
and calls `read_identity()` on every window, loading episode .pt payloads
containing precomputed VAE tensors. A later second pass over the same windows
reloaded evicted .pt payloads (8-episode LRU) to check up to 17 absolute-row
identities per window. The 8 torchrun ranks repeat these operations independently.

The requested 3-step 8xH100 GPU telemetry diagnostic remains on hold until
this optimization receives its own CPU + actual corpus index evidence.

## One-time single-process cold build

`python -m examples.psm_wma_robocasa_build_verified_index
  --cache-root <accepted exact-window cache>
  --source-root <accepted LeRobot v3 flat source>
  --index-root <new external path>`

- Run once in the already authorized V3 training venv. **Do not** run under torchrun.
- The destination must not already exist. Only the builder creates it via a
  staged directory and final rename; it does not overwrite an index.
- The cold source reader still validates manifest, cache episode identities,
  full source episode Parquet identities, LeRobot row mapping, and full accepted
  per-window cache identity.
- A one-pass cold source-binding fix checks the interval witness on the first
  encounter, then verifies filtered LeRobot membership only once per unique
  source row. Runtime middle-window exact-row validation remains unchanged.
- The data remains immutable; this operation does NOT regenerate any VAE
  tensors, action targets or transformed/prompt/tokenized training samples.

## Indexed output (static only)

`receipt.json`:
- Schema marker: `psm_v3_robocasa_verified_index_v1`
- Accepted episode IDs and their order, window counts, source path, task
  annotations, absolute-row bounds, first/terminal window identity witnesses
- `cache_manifest_sha256`, `cache_corpus_digest`, `source_binding_digest`
- Original accepted cache payload and selected source Parquet file **stat
  identity witnesses** (size / mtime_ns / ctime_ns / device / inode)
- All source `meta/` files including content SHA256
- Absolute-to-filtered-row-map data checksum and row count

`absolute_row_mapping.npy`:
- Sorted pairs `[absolute_index, filtered_relative_index]` as int64
- Loaded read-only with NumPy mmap; lookup uses searchsorted
- Avoids reconstructing a several-million-entry Python dict at every warm
  startup; preserves source's original arbitrary absolute-to-relative mapping

Neither file contains raw RGB/video, 451GB cached latent tensor payloads,
optimizer state, per-rank Slot Frontier, Sidecar Fast Weight, or DCP state.

## Strict warm startup

Launch the corrected Phase5 entrypoint with `--dataset-index-root`. The
trained program opens and validates a **previously built** index. No
implicit index construction or download is permitted on cache miss, version
mismatch, new or removed source metadata, or a changed required file witness.

Warm sequence:
1. Verify schema, row-map checksum, metadata SHA, Cache manifest SHA and
   stat identities of all accepted cache .pt / selected Parquet files.
2. Build the usual CacheCatalog with manifest + declared .pt membership
   audit, but reuse verified `cache_corpus_digest` instead of hashing every
   individual window.
3. Use the same Catalog object for SFT / Local instead of constructing it
   again; use episode offsets plus bisect for flat-window index.
4. Construct official nonvisual LeRobotDataset, restore verified episode
   bindings and memory-mapped absolute-row mapping; compare resulting binding
   digest exactly against the receipt.
5. Build the same ExactWindowLocalCatalog and rank-owned Local planner.

**Expected:** no `torch.load` of VAE cache .pt and no full source Parquet
identity scanner during warm Dataset constructor, until explicitly requested
runtime `__getitem__` / producer. The original runtime per-window
cache/source/action/identity/finite checks remain enforced.

**Bounded GPU 3-step entrypoint requires `--dataset-index-root`**: no flag,
missing file, changed witness or invalid index => fail-closed before training.
An explicit legacy cold path remains for regression tests and for initial
single-process builder; it does not silently activate after index miss.

## Limits of file integrity witness

Metadata uses cryptographic content SHA256. For the very large accepted .pt
and source-data Parquet files, warm verification uses fast stat identities.
This catches ordinary replacement/rewrite/move/mutation, but is **not** a
cryptographic proof that a privileged writer did not replace contents while
spoofing all file identity metadata. The accepted dataset is assumed to live
under a controlled immutable snapshot; runtime read validation remains strict.
Do not claim that warm startup re-verifies 451 GB of content.

Device/inode in the witness means relocating/copying the source or cache
requires an explicit cold index rebuild at the destination. This path is
intentionally not portable, while the semantic training config digest remains
unchanged for equivalent validated corpus contents.

## Invariants

- Original cache episode ordering, window identity and flat indices preserved.
- Native raw15/17-frame Action+State+Latent samples must compare exactly for
  cold and warm on synthetic coverage + real sampled indices.
- `source_binding_digest` and `config_digest` are exactly equal in both
  paths; the index directory is NOT a training configuration field.
- B_stream, active_GA, T=16, K_local and episode-by-episode deterministic
  rank partitioning are unchanged. DCP per-rank Slot Frontier and Fast Weight
  Resume remain wholly independent of this static index.
- Production V3/v3-local-ttt branch tips MUST NOT move before targeted CPU
  + real dataset evidence, and before a new formal pair review.
- No change to optimizer, scheduler, Local scan, fast updates, loss, sample
  payload/transform, DCP ownership or training stop gate.

## Acceptance stages

1. **CPU code Gate**: new verified-index tests, source-cache/Local regression,
   bounded Phase5 tests, syntax/Ruff format. Test invalidation: missing index,
   changed metadata/payload, row-map corruption, unknown schema and strict
   end-to-end cold/warm payload/Source/Local/digest parity.
2. **Real corpus one-time build**: DS runs builder once in the existing
   environment, outside the repo and GPU. Record manifest/digests, output
   receipts, cold staged wall times and errors.
3. **Real warm Gate**: DS executes builder `--verify-existing` plus corrected
   Phase5 `--preflight --dataset-index-root <path>` in one process, with
   formal 30000/500/100, B8/GA2/T16/K4 and official DROID config. Record
   warm startup wall breakdown, digest equal frozen
   `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`,
   absence of .pt loads and no silent cold fallback. Observe multirank
   overhead separately if approved.
4. **GPU Smoke**: only after explicit fresh review/CPU warm Gate closure,
   run the previously bounded 3-step 8xH100 diagnostic with the verified
   index flag. No formal30k training is authorized here.

DS_PRO is only authorized to sync one exact root/child pair, run tests and
produce runtime evidence/index artifacts outside the code worktree. DS must
not modify, upload, clean/reset or commit source.
