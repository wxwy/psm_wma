# V3 F1 — implementation author handoff / independent review requested

Date: 2026-10-16. This is the author's factual handoff, **not a GPT verdict or independent acceptance**.

| Authority | Exact SHA |
| --- | --- |
| F1 Root implementation | `6ebf8998a7935f2ad690bb547c5db5e5a4322e6d` |
| F1 Child / Gitlink | `2d128ed5a07601cdd424974f99b67832eafeeb41` |
| Approved F0 base Root | `9e51c94a6d5dba41bd37423b9db8e634ca433789` |
| Approved F0 Child ancestor | `7cae7c3049310ccc3b7e44ce9769534e152d1f26` |

Production implementation Child `c0fc4cadccedb5838d3f2e512ea96179a3c969e9` directly follows approved F0. Final Child `2d128ed5` adds only the positive two-rank restore test; production bytes and frozen contract remain identical. Preliminary Root `264cff2f` and its evidence are retained; final exact Pair above governs independent verification.

Both repositories publish isolated `v3-f1-checkpoint-rng-20261016`. Root preserves prior candidate history and V3 F0 closeout documents through `e2a11445bdb5451605a5ef33da312690931845ff`; Inbox merge retained both appended blocks. No V3 merge/force push or frozen B1 update. Later candidate docs commits do not replace the Root implementation SHA.

Frozen F1 contract: `docs/build/PSM-WMA_V3_F1_sync_checkpoint_strict_rng_contract_2026-10-16.md`, SHA256 **`aa3f7c6db2bdf5a7c193de1398b7ff1aa81b59b08554552f6fa86fc3e2748185`**.

## Scoped implementation

Child changes exactly four files:

- `cosmos_framework/checkpoint/dcp.py`: opt-in `SafeLocalDistributedCheckpointer`, synchronous hidden attempts, bounded Gloo coordination, all-rank prepare/iteration/source agreement, synchronous DCP component acknowledgements, atomic/fsynced per-rank Local files, complete marker and atomic latest; strict full-rank RNG metadata/storage/payload validation and explicit successful-restore flag. Legacy loader only gains flag reset and the opt-in strict branch.
- `cosmos_framework/trainer/__init__.py`: deterministic reseed respects the literal successful same-job restore flag. Fresh still seeds; iteration number is not used as the Resume discriminator.
- `examples/psm_wma_robocasa_corrected_phase5.py`: explicitly select the safe local synchronous class; bind `psm_v3_sync_local_v1` into semantic identity. Native Packed128 and formal 30000/500/100 remain.
- `cosmos_framework/checkpoint/dcp_local_safety_test.py`: focused real CPU DCP/Gloo fixtures and failure/restore regressions.

No changes to checkpoint/base.py, global easy_io, existing random-state codec, Local/FSDP/optimizer/loss algorithms, Index8, prefetch or performance defaults. Existing legacy DCP save/async functions, protected Local/RNG/base/tests and Root launcher have unchanged AST/bytes as recorded in `unchanged_scope.json`. The new local class does not accept async/object-store mode; those existing classes keep their original path. Actual async CUDA background execution is not claimed tested.

## Publication and restore contract

All expected ranks complete the same iteration before publication. Rank-owned Local files are temp→flush/fsync→rename→directory-fsync; all-rank witnesses are checked before writing a versioned complete marker. The complete directory is renamed into its final name before atomic latest. Failed attempts remain unadvertised and are not cleaned or reused. Resume validates exact pointer/marker/world/components/sidecars and required RNG metadata. Stored RNG must include CPU/CUDA, NumPy/Python packed lengths/bytes and rank/world/schema binding; missing keys/chunks cannot fall back to current template values.

The dedicated CPU Gloo timeout defaults to the framework's existing 1800-second foreground budget; tests use 10 seconds. This bounds collective waits, not uninterruptible OS I/O or whole-checkpoint duration. Real storage size/latency still needs independent evidence. Metadata and Local sidecars are hashed; large model/optimizer shards are checked for existence/extent/size, not rehashed.

Failure is distinguished from publication commit. Before pointer commit, tested component/sidecar/marker/latest-temp failures preserve old latest or first-pointer absence. Post-rename fsync failure attempts rollback (one-shot rollback tested). Permanent storage failure or hard death after commit cannot guarantee rollback/durability; any retained new pointer was eligible only after a complete checkpoint existed. Complete orphan final directories are retained and never overwritten; operational reconciliation/retention is not automated. See the contract failure table; no unconditional success/rollback claim is made.

The new policy/checkpoint schema and new exact Pair intentionally change config identity. Official DROID model-only Fresh has no RNG prerequisite. Training-state warm-start through an external load_path is rejected. No old job, iter1300 state, checkpoint bytes or historical evidence was migrated or modified.

## Measured author CPU verification

Evidence: `docs/collab/codex/evidence/2026-10-16_V3_F1_final_author_cpu/`.
Python 3.12.14; PyTorch **2.10.0+cpu** (CUDA build=None); NumPy 2.2.6; pytest 9.0.2; Ruff 0.12.7. CPU-only dependencies were installed outside the repository; manifests/lockfiles unchanged.

| Check | Measured result |
| --- | --- |
| Combined F1 + F0 pytest | **57 methods** (29 F1 +28 F0), **53 subtests**, 0 failure/error/skip, 51.88s |
| JUnit | 110 bookkeeping cases = methods + subtests; no cross-run count addition |
| Final raw per-negative tracebacks / positive restore | retained in final pytest.log; both ranks restore all components and distinct RNG |
| Ruff check / format --check / syntax | 4 changed +2 affected existing test files passed |
| Child diff check / CPU dependency check | passed |
| Legacy/protected-source scope comparison | unchanged save/async functions and protected source bytes; only intended load/seed/profile hooks differ |

Real 2-rank Gloo negatives cover delayed rank with Rank0 sidecar already durable; DCP optimizer writer failure; Local and first-save failures; partial temp, process death and live stalled rank; marker/latest failures; iteration/source disagreement; missing per-rank RNG metadata and cross-rank RNG payload binding. An independent standard-library subprocess reads and verifies the pointer/marker/files. The live-rank test observed failure at **10.06s** with old latest retained.

The positive two-rank test restores model, optimizer, scheduler and rank-local callbacks after deliberate in-memory mutation; both ranks reproduce their own distinct RNG next draws exactly. No optimizer update or training is executed.

Single-rank tests use actual DCP save/load of tiny synthetic model/optimizer/scheduler/trainer/Local state, complete-marker/extent/sidecar/pointer negatives, atomic partial-write protection, post-replace fsync rollback, no overwrite/regression, all missing RNG leaves/types/chunks, model-only warm start, legacy async dispatch and safe Phase5 factory selection. The actual imported Trainer loop with synthetic model/device boundaries shows deterministic Resume does not reseed and Fresh still seeds. Next Python/NumPy/Torch draws matched exactly: `[0.34583182333805484, 0.2849059652276268, 0.893419086933136]`.

**Limits:** real Torch/DCP/Gloo/NumPy are exercised; Cosmos configuration/log/S3 imports are scoped stand-ins, and CUDA RNG bytes are a CPU stand-in. Full Cosmos dependency import/config serialization and target persistent filesystem are not independently verified here. Actual CUDA RNG, native model/optimizer/FSDP8 GPU state and hardware throughput are not tested or authorized. No production DCP/model/data, GPU, torchrun or training was used. Four retained warnings are PyTorch storage deprecation/intended no_dist loading warnings, not skipped cases.

## Stop and next action

DS request: `docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_F1_sync_checkpoint_strict_rng_CPU_acceptance_6ebf8998.md`. Independently verify the exact clean detached Pair/contract, real CPU Gloo and full-dependency affected regressions, target-volume behavior and real config factory/serialization. F0 closure remains valid for its old exact Pair; it does not close F1.

**F1 DS/GPT verdicts PENDING.** Stop after evidence delivery for GPT Fresh Incremental Review. No GPU/Fresh/Resume/Formal30k, original DCP migration, Index8/loss/prefetch or frozen B1 changes are authorized.
