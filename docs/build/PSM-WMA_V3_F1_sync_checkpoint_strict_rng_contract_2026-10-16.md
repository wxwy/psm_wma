# V3 F1 — synchronous local Checkpoint publication and strict RNG

Date: 2026-10-16. Status: **candidate contract; independent DS/GPT acceptance pending**.
Authority: Owner's explicit F1 instruction after F0 `APPROVE_TO_CLOSE`, bound to Root `9e51c94a6d5dba41bd37423b9db8e634ca433789` / Child `7cae7c3049310ccc3b7e44ce9769534e152d1f26`.
Scope: `docs/collab/chatgpt/requests/2026-10-16_CODEX_V3_Fresh_P0_safe_start_DCP_RNG_execution_budget_staged_remediation.md` §F1.
Candidate Child: `c0fc4cadccedb5838d3f2e512ea96179a3c969e9`. The Root integration commit and author handoff bind the new exact Pair and this file's SHA256. This contract is not GPU/training authorization.

## Profile and compatibility boundary

Corrected Phase5 explicitly selects `SafeLocalDistributedCheckpointer` and disables asynchronous DCP. The new class requires strict Resume, local load/save, and an initialized distributed group; asynchronous/object-store requests fail before initialization of that profile. Other callers continue using the existing `DistributedCheckpointer` and existing async/object-store APIs. No global easy_io, base checkpointer, random-state codec, Local/optimizer/loss or Index8 changes.

The prospective profile/schema is `psm_v3_sync_local_v1`; it enters the semantic config identity. Native Packed128, raw15 contract, T16/B8/GA2/K4 and configured 30000/500/100 schedule remain unchanged. New Root/Child identity and new Checkpoint schema deliberately require a new approved Fresh namespace. No historical DCP/marker/config is upgraded, rewritten or silently migrated. Official DROID **model-only** warm start is still allowed without training RNG. A training-state warm start through load_path is rejected; full Resume must be same-job latest.

All save/load calls on this profile are collective across the full world. A dedicated CPU Gloo group bounds metadata coordination and completion acknowledgements. Default phase timeout is **1800 seconds**, matching the framework's existing foreground budget, with an explicit constructor override in 1..1800. CPU fault tests use 10 seconds. This is not a measured checkpoint throughput promise or a whole-operation wall-clock deadline: local OS I/O and native model-state preparation can block; process-group/launcher failure stops the job and must not become a success verdict. Storage/GPU readiness remains separately gated.

## Synchronous save transaction

1. Each rank prepares the same five components (`model`, `optim`, `scheduler`, `trainer`, `dataloader`) through the existing model/optimizer/scheduler/state APIs and Local callback. RNG is captured per rank. Component inventory, RNG payload and unchanged iteration are validated; errors are acknowledged before writes. All ranks must agree on the requested iteration.
2. Rank0 verifies existing latest is a complete checkpoint, refuses overwrite or iteration regression, and claims a unique hidden `.iter_<N>.inprogress_<uuid>` directory on the output filesystem. Its name is shared after successful acknowledgement. The F0 exclusive job lease remains the single-writer namespace boundary.
3. Each DCP component is synchronously saved using PyTorch FileSystemWriter with `sync_files=True`; DCP coordination uses the bounded Gloo group. Every component is followed by all-rank error acknowledgement, including PyTorch CheckpointException. No model/optimizer numerical algorithm is changed.
4. Every rank writes its Local/dataloader pickle to a unique same-filesystem temporary file, flushes and fsyncs it, atomically replaces `dataloader/rank_<r>.pkl`, and fsyncs its directory. Sidecar object/schema remains the existing Local callback payload. Each rank returns its size/SHA256 only after close/fsync; all ranks acknowledge success and exchange these small witnesses.
5. Rank0 verifies the four DCP metadata files, referenced shard existence/size bounds and every sidecar against the acknowledged witness. Only metadata and Local sidecars are hashed; **large model/optimizer shard bodies are not rehashed**. All expected rank RNG metadata must be present and backed by complete stored chunks.
6. Rank0 writes/fsyncs/atomically replaces `complete.v1.json` inside staging, then renames the complete staging directory to `iter_<N>` and fsyncs its parent. It finally writes/fsyncs/atomically replaces `latest_checkpoint.txt` and fsyncs that parent. All ranks acknowledge the publication outcome before save returns or success callbacks run.

Complete marker fields: profile/schema, complete=true, final checkpoint name, iteration, world_size, per-component metadata SHA256 and referenced shard sizes, per-rank sidecar size/SHA256. Final names and pointer grammar are strict; torn pointers, missing/changed markers/components/sidecars, symlinks and world mismatch fail closed. Resolve results must agree across ranks before loading.

## Failure and commit semantics

| Failure point | Observable outcome |
| --- | --- |
| Preparation, DCP component, Local write or rank acknowledgement failure | Latest remains the previous complete pointer (or absent on first save); no new final checkpoint is advertised. All surviving participating ranks raise or hit bounded collective failure. |
| Partial sidecar/temp file or process death | Incomplete hidden attempt can remain as evidence. It is never a legal latest target. Hard death cannot guarantee a successful collective response from the dead process. |
| Complete-marker or final-directory publication failure | Old pointer remains. A hidden complete attempt or unadvertised final directory may remain, depending on the exact failure point. |
| Latest temp write failure | Old pointer remains; the new complete final directory can be orphaned. No old checkpoint is overwritten. |
| Error after latest rename, e.g. directory fsync | Attempt rollback to the previous pointer (or removal of first pointer) if storage is still writable; one-shot fsync rollback is tested. Permanent storage failure or process death after the rename cannot promise rollback/durability. Any retained new pointer was eligible only after all ranks/components were complete; it never intentionally names a partial checkpoint. The operation reports failure/uncertainty, not training success. |
| Peer/process failure after publication commit | Last complete pointer may already be the new complete checkpoint; no unconditional rollback claim after a completed commit. Job failure is distinct from checkpoint completeness. |

No old Evidence or checkpoint is automatically cleaned. Failed staging directories are retained. A complete orphan at a final iteration name is never overwritten on retry; resolving it requires explicit operational review. Disk sizing/retention must account for staged/orphaned data. B1 native rank capture sizes are not actual DCP sizing evidence.

## Strict same-job RNG restore

Trainer metadata must contain every expected rank's complete `rng_state_<r>` with these nine tensor leaves:
`torch`, `torch_cuda`, `numpy_packed_len`, `numpy_packed_bytes`, `random_packed_len`, `random_packed_bytes`, `rank`, `world_size`, `schema_version`.

The last three int64 scalars bind rank/world/schema=1. Missing/extra rank keys or leaves, wrong tensor metadata/dtype/shape, absent storage/chunks or incomplete chunk coverage are rejected before using an initialized template. Packed buffers retain the existing 4096-byte codec; declared lengths must be valid and consume exactly one decodable state. CPU Torch, Python and NumPy states are checked using independent generators without changing global RNG. CUDA payload type/shape is checked and the native setter validates restore at runtime.

Every rank reads its own stored state through DCP; all ranks acknowledge validation before any global restore. A loaded iteration must match the checkpoint. Grad-scaler and RNG restore errors are shared; global RNG rollback is attempted on failure, and no successful-restore flag or consumer progression follows a failed restore. Device/storage failure can prevent rollback and remains fatal.

`rng_restored_from_same_job` is reset on load entry and set to the literal True only after successful strict all-rank restore. Parent Trainer's deterministic reseed branch respects that explicit flag; it does not infer Resume from iteration>0. Fresh/model-only load retains normal seeding. Legacy checkpointer callers retain their existing RNG loading behavior and a False flag.

## CPU acceptance and remaining boundaries

Use real CPU Torch/DCP, Gloo and NumPy with tiny synthetic model/optimizer/state fixtures only. External Cosmos configuration/log/object-store imports are isolated; CUDA RNG bytes and GPU/model work in the Trainer-entry reseed test are explicit stand-ins. An independent standard-library read-only subprocess checks pointer/marker/files, without calling writer helpers.

Required negative/positive matrix: delayed final rank after Rank0 sidecar completion; actual DCP writer failure; Local/first-save failure; partial temp/hard process death/unresponsive live rank; marker/latest/fsync failures and rollback; successive save and no-overwrite/no-regression; torn pointer/missing marker/truncated shard/changed sidecar; rank source/iteration disagreement; full same-job synthetic component restore; missing whole rank/every leaf/fake tensor/empty chunk; cross-rank payload mismatch and one-rank-only metadata error; next Python/NumPy/Torch samples with deterministic=True and no reseed; Fresh seeding/model-only warm start; legacy async dispatch and unchanged-source comparison.

Author CPU results are not DS acceptance. DS must independently use the exact new Pair, full established dependency environment, target persistent filesystem, CPU Gloo and affected existing regressions/config serialization; keep all commands/RC/JUnit/tracebacks/witnesses externally. No GPU, real DCP/model/data scan, Fresh/Resume or Formal30k is authorized. Real FSDP8/CUDA-state behavior and actual checkpoint capacity/latency still require later separately authorized Gates. No Index8 compatibility, loss, prefetch, telemetry/performance or frozen B1 changes are included.
