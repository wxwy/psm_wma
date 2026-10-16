# V3 F0 — safe startup and formal execution budget

Date: 2026-10-16. Status: candidate implementation contract, DS_PRO/GPT review pending.
Authority: Owner's staged F0/F1 decision and
`docs/collab/chatgpt/requests/2026-10-16_CODEX_V3_Fresh_P0_safe_start_DCP_RNG_execution_budget_staged_remediation.md`.
Base Root: `a1a47b36d10f1974ba0fb7cec872b1976c9c6838`; base Child: `1d56320c08c56b0f8dd248919d152d81ae12ea7b`.
F0 Child: `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021`. Root implementation is the commit first integrating this contract, launcher and that Gitlink; later handoff documents identify its exact SHA.

## Lifecycle contract

1. Corrected Phase5 remains Packed128 (`v2_a2_member_packed_slot_major_v1`). There is no Index8 fallback or new Index8 entry in this batch.
2. The read-only CLI preflight rejects every existing Fresh namespace, including empty/partial/evidence-only directories. Job names must be one ordinary component. Output traversal and symlink ancestors/aliases are rejected. A preflight success alone does not reserve a directory.
3. A real launch first initializes the distributed environment, gathers read-only preflight errors and resolved config digests, and requires agreement. No Trainer/job configuration or journal is created before agreement.
4. The optional parent-Trainer config writer is invoked on Rank0 before legacy config dumps, job logging and checkpoint construction. It atomically claims a new Fresh namespace with `mkdir(exist_ok=False)`. Claim or writer errors are broadcast to peers before the next Trainer barrier. Hard process death is handled by the launcher/process-group timeout, not a promise of unconditional collective recovery.
5. Fresh creates `launch.lock` and holds a POSIX advisory exclusive lock. Resume opens the same inode without truncation and must acquire that lock; the inode is never unlinked. After acquisition, latest must still match the checkpoint selected in preflight. Filesystem support for coherent mkdir/flock is an independent DS storage prerequisite.
6. Fresh failures may leave a partial new directory; it is never automatically recycled. Old jobs and old evidence are never cleaned, renamed or rewritten. A new job name is required after an incomplete Fresh claim unless Owner separately approves recovery work.
7. Fresh creates immutable canonical `config.pkl` / `config.yaml`, a `v3_job_identity.json`, and a unique `launches/<uuid>/` resolved config snapshot. Resume validates identity and canonical file SHA256 values before writing only a new launch snapshot. It never overwrites canonical configurations or earlier snapshots. Unknown/missing identity, changed canonical config, diagnostic jobs, wrong SHA/Layout, symlinked checkpoints or missing rank sidecars fail closed. No historical job is silently upgraded.

## Identity contract

The new `corrected_phase5_f0_v1` profile binds exact Root/Child and Layout; complete resolved model, optimizer, scheduler, Trainer, model-parallel and data-setting values; checkpoint save cadence/strictness; raw15/state15/H16/17-frame contract; T/B/GA/K/world; source/cache/index/DROID/Edge/VAE paths; accepted index receipt SHA256; cache/source authority and model metadata witnesses; transform RNG strategy, seed-by-rank and deterministic-algorithm mode.

Complete resolved model/optimizer values include loss/mask/precision settings, parameter-selection FQNs and weight-decay rules. Stable callable FQNs and supported config values are serialized explicitly; unsupported or anonymous values are rejected, never reduced to memory-address representations. Actual production-config serialization still needs DS's configured-environment regression/preflight evidence.

Phase, actual checkpoint load path/load-training-state, execution budget and per-launch logs are not training semantics. Their full configurations remain visible in each launch snapshot. The runtime stream/checkpoint digest is SHA256 of the existing Phase5 digest plus this semantic identity. Therefore the new profile intentionally has a **new config digest**, while Fresh100 and same-job Resume500 have the same digest. The historical digest/function and frozen B1 implementations are not redefined. Exact implementation SHA changes require a newly reviewed identity; docs-only HEADs cannot replace the implementation SHA.

## Execution contract

`--formal-execution-until N` sets the existing Trainer `_execution_max_iter`, with configured `max_iter=30000`, warmup=500 and save_iter=100 unchanged. It accepts 1..30000, rejects a budget at/below the restored iteration, incompatible schedules, and diagnostic-option combinations. The canonical launcher seals T16/B8/GA2/K4/world8, workers0, full-segment-prefetch disabled, and corrected Phase5 entry. No trailing override arguments are accepted.

The Trainer must observe committed optimizer/Local completion on every update before a checkpoint; premature dataloader exhaustion, half-GA completion or a missing Local commit raises. A successful exit occurs only after the requested iteration, final save when needed, callbacks, checkpointer.finalize and the existing all-rank barrier. Save/finalize exceptions propagate and cannot emit `Done with training.`. The parent Trainer's legacy profile retains its existing config-write path; its success message also now follows finalization.

Cadence: Fresh0→100 saves iter100. Resume100→500 saves iter200/300/400/500. Resume100→101 explicitly creates a new off-cadence iter101 checkpoint. Prefer the single Resume→500 route and observe iteration101 internally after separate authorization; do not change max_iter or scheduler to segment execution.

`--stop-after-iter` retains its separate Fresh-only `bounded_` namespace and non-resumable diagnostic contract. Formal budgets cannot reuse that path.

## CPU and independent acceptance

Author command in Child: `python examples/psm_wma_robocasa_phase5_f0_test.py -v`.
Alternative: `python -m pytest --noconftest -c <external-empty-pytest.ini> -q examples/psm_wma_robocasa_phase5_f0_test.py --junitxml=<external-evidence>/pytest.xml`.

Tests execute the real subprocess CLI/preflight rejection paths, concurrent Fresh claims, lifecycle writers, the actual imported parent Trainer constructor/train methods, and Phase5 main wiring. CUDA, model/optimizer and collective dependencies are synthetic stand-ins. This is **not** a real model forward, real DCP save/load, NCCL/Gloo acceptance or all-project CPU regression. Tests create only synthetic checkpoint metadata/sidecar bytes in temporary directories; they do not deserialize them. The launcher test intercepts its Python executable and inspects arguments; it does not execute torchrun.

Required DS evidence: exact clean detached Pair and unchanged V3/frozen refs; scoped Ruff 0.12.7 check/format, syntax, these negative tests plus existing Phase5/Trainer CPU regressions in the established environment; config digest/unchanged canonical SHA+mtime witnesses; read-only configured-config serialization and approved metadata-only preflight; filesystem mkdir/flock behavior and collective-error propagation using CPU-only processes. Preserve commands, return codes, JUnit, tracebacks, per-negative logs and storage observations externally. Missing dependencies/assets or permissions are BLOCKED, never synthetic PASS.

## Explicit stop boundary

F0 does **not** fix DCP all-rank publication, atomic latest or strict RNG/reseed. F1 remains required after F0 independent acceptance and GPT Fresh Review. No GPU, torchrun, real training/checkpoint load, dataset scan, formal evaluation, iter1300 migration, Formal30k resume or new Fresh is authorized by this contract. E1, Index8 compatibility, Local/FSDP/loss/action semantics and storage gates remain separately scoped. No old Evidence or numerical threshold is changed.
