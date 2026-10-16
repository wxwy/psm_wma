# DS_PRO — F1 independent synchronous-checkpoint / strict-RNG CPU Gate

Date: 2026-10-16. Role: read-only execution and new external Evidence. This request does not authorize GPU, torchrun, production DCP/model/data access, training, source edits or dependency changes.

## Exact authority

- Formal Root implementation: **`6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`**.
- Child / Gitlink: **`2d128ed5a07601cdd424974f99b67832eafeeb41`**.
- Both isolated branches: `v3-f1-checkpoint-rng-20261016`; later documentation HEAD is not the implementation Root. Do not use mainline V3's historical Gitlink.
- Approved F0 ancestor: Root `9e51c94a6d5dba41bd37423b9db8e634ca433789`, Child `7cae7c3049310ccc3b7e44ce9769534e152d1f26`; closure review `2026-10-16_V3_F0_9e51c94a_7cae7c30_DS_CPU_Evidence_closeout.md`.
- Frozen contract: `docs/build/PSM-WMA_V3_F1_sync_checkpoint_strict_rng_contract_2026-10-16.md`; SHA256 **`aa3f7c6db2bdf5a7c193de1398b7ff1aa81b59b08554552f6fa86fc3e2748185`**. Contract names production Child `c0fc4cad`; final Child is its test-only successor with identical production bytes. Preliminary Root `264cff2f` is superseded for acceptance, preserved in history.
- Author report: `docs/collab/codex/reviews/2026-10-16_V3_F1_sync_checkpoint_strict_rng_author_handoff.md`. Final logs: `docs/collab/codex/evidence/2026-10-16_V3_F1_final_author_cpu/`. These live in the documentation successor; read them separately from the clean implementation checkout.

Safely create clean detached Root/Child worktrees at the exact Pair. Never reset/clean/force, replace another worktree or overwrite uncommitted contents. Unsafe version locking => BLOCKED. Preserve all old Evidence and Checkpoints. Use a NEW external Evidence directory and NEW synthetic-fixture TMPDIR on the intended persistent filesystem, outside production Job namespaces. No production DCP is opened; all checkpoint I/O below concerns tiny temporary CPU tensors only.

## A. Version and compatibility scope

Record Root/Child/Gitlink, statuses, full ancestors and source SHA256 before/after. Child diff from approved F0 contains exactly `checkpoint/dcp.py`, new `checkpoint/dcp_local_safety_test.py`, `trainer/__init__.py`, and corrected Phase5. Final Child's diff from `c0fc4cad` is test-only. Compare existing save/async methods and protected base/RNG codec/Local/FSDP/optimizer/loss code and launcher against F0; inspect author's `unchanged_scope.json`, independently verify rather than relabeling old evidence. Root preserves V3 review history through `e2a11445`; frozen B1 Source/Target, old DCP and other branches stay untouched.

## B. Real CPU DCP/Gloo integration and failure witnesses

Use established V3 Python and the established complete V2 dependency Python (execute candidate V3 source, not V2 code). Do not install or remove packages. Record interpreter, Torch/Gloo/NumPy/pytest versions and imported source paths. If required environment is absent, report BLOCKED rather than using author fixtures as full-dependency proof.

In the validation Child, with writable external HF/MPL/pycache dirs, `CUDA_VISIBLE_DEVICES=''`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and TMPDIR on the isolated target-volume fixture directory, create an external `[pytest]`-only ini and run:

```bash
python -m pytest --noconftest -c "$EVIDENCE/pytest.ini" -q -s -p no:cacheprovider \
  cosmos_framework/checkpoint/dcp_local_safety_test.py \
  examples/psm_wma_robocasa_phase5_f0_test.py \
  --junitxml="$EVIDENCE/f1_f0.xml"
```

Preserve full stdout/stderr and return code; no pipe that loses test exit status. Expected source methods: F1 29 + F0 28 = 57. Author pytest9 added 53 subtests /110 JUnit cases; report methods and runner bookkeeping separately. No skip/xfail permitted in these two files. A failure stops acceptance; no code/test/config edits to get GREEN.

Independently inspect all 14 Gloo scenarios and their reader witnesses:

- Delayed Rank1: Rank0's Local sidecar is already durable, independent reader still sees iter1, and iter2 is unavailable until final acknowledgement; then iter2 becomes complete.
- Successful two-rank restore: deliberately mutated model/optimizer/scheduler recover; Local rank binding and distinct per-rank Python/NumPy/Torch next draws match; successful strict-restore flag is True. No optimizer update/training occurs.
- Actual DCP optimizer writer failure, Local/first-save write failure, partial temp file, dead rank, stalled live rank, marker/latest write failure, iteration/source disagreement: both surviving participants fail or reach bounded timeout, previous latest remains complete (first failure: absent), partial staging remains unadvertised. Tests use a 10s control timeout; production default is 1800s, not a measured save-duration guarantee.
- Whole-rank/leaf/chunk/type/length/world/rank/schema RNG negatives, one-rank metadata failure and cross-rank payload mismatch: fail before consumer progression, no successful flag or reseed fallback; pre-restore rejection retains RNG.
- Torn pointer, absent/changed marker, truncated shard, changed sidecar, atomic partial write and one-shot post-rename fsync failure/rollback, no overwrite/regression, model-only Fresh without RNG, rejection of external training-state warm start, actual deterministic Trainer resume with zero reseed calls and Fresh seeding retained.

The standard-library reader is independent of writer helpers. Verify old-pointer bytes and complete inventories, not only log strings. Preserve expected negative tracebacks as evidence; they are not failed tests. Do not claim actual CUDA RNG or GPU FSDP correctness: CUDA state is explicitly a CPU byte stand-in. Legacy async dispatch is mocked at its external launch boundary; actual CUDA async execution remains outside this Gate.

## C. Full-dependency affected regressions and wiring

With the established full dependency environment and repository CPU collection setup, run:

```bash
python -m pytest --num-gpus=0 -q -p no:cacheprovider -o addopts= \
  examples/psm_wma_robocasa_corrected_phase5_test.py \
  cosmos_framework/trainer/local_memory_grouped_test.py \
  cosmos_framework/trainer/local_memory_grouped_resume_test.py \
  cosmos_framework/checkpoint/dcp_distill_test.py \
  --junitxml="$EVIDENCE/affected_fullenv.xml"
```

Do not bypass conftest or change assertions for these existing full-import tests. Retain an existing legitimate optional-asset skip only with its exact name/reason; no new skips. All nine previously problematic F0 TrainerTests must execute in the complete environment via B. Reuse accepted F0 persistent namespace/Gloo witnesses only after proving unchanged code; new F1 publication/storage behavior requires the new synthetic tests on the target filesystem.

Repeat the accepted CPU-only configured preflight/serialization recipe with this exact Pair and new external paths, without opening production DCP, model weights or dataset contents. Check resolved factory is `SafeLocalDistributedCheckpointer`, async=False, strict=True, local mode, profile `psm_v3_sync_local_v1` bound into semantic identity. Fresh100 / Resume500 execution budgets preserve configured 30000/500/100 and the same semantic digest for this Pair; deliberate profile/layout/identity differences reject. Namespace validation still precedes runtime/writes. Do not launch Fresh/Resume training to inspect this.

## D. Static checks and storage boundary

Ruff must be **0.12.7**. Run `ruff check`, `ruff format --check` and `python -m py_compile` on these six files (pycache external):

```text
cosmos_framework/checkpoint/dcp.py
cosmos_framework/checkpoint/dcp_local_safety_test.py
cosmos_framework/trainer/__init__.py
examples/psm_wma_robocasa_corrected_phase5.py
examples/psm_wma_robocasa_corrected_phase5_test.py
examples/psm_wma_robocasa_phase5_f0_test.py
```

Verify fsync/rename/atomic pointer behavior on target persistent storage using synthetic fixtures only. Metadata/Local bodies are hashed; large shard bodies use existence/extent/size checks. Contract distinguishes pre-publication failure from post-commit uncertainty: permanent storage failure or process death cannot promise rollback, and a complete orphan must not be silently reused/deleted. Retain evidence and report uncertainty as failure, never success.

Capacity/retention remains a separate prerequisite for GPU authorization. Do not infer actual DCP capacity from historical B1 native capture sizes; this Gate does not authorize reading real DCP contents or deleting the 595GB old Evidence.

## E. Deliver and stop

Return gate.json with exact Pair/contract, all commands/cwd/environment/RCs, tool versions, before/after clean-source hashes, test/subtest/skip counts, logs/XML/negative tracebacks, rank timing, reader inventories, RNG next-draw witnesses and persistent-volume results. Missing artifact/environment => BLOCKED; test/safety failure => FAIL and preserve everything. Do not change production code to repair a failure.

Stop after CPU Evidence for GPT Fresh Incremental Review on this exact Pair. Author self-test is not F1 acceptance. **No GPU, real DCP, Fresh/Resume/Formal30k, Index8/loss/prefetch or B1 changes.** No mainline merge is requested before independent acceptance.
