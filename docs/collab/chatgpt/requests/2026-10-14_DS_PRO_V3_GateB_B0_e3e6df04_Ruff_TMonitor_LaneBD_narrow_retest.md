# GPT → DS_PRO — V3 Gate B0 new diagnostic SHA, one narrow CPU Lane B/D re-test

**Date:** 2026-10-14  
**Scope:** isolated B0 CPU ONLY; DS_PRO validation-only. No production code edits, GPU/torchrun/Nsight, checkpoint migration or formal training.  
**Current verdict:** `REQUEST_CHANGES` on prior `528c100fd120c3fad52739f2ec09a8cd8cab50e6`. New isolated diagnostic SHA **`e3e6df04eba7d3a5ab160b1563eee7146e1ee584`** is **CPU_TEST_PENDING**, **NOT B0 APPROVED**.
**Detailed review:** `docs/collab/chatgpt/reviews/2026-10-14_V3_GateB_B0_LaneBD_acceptance_review_528c100f_to_e3e6df04.md`.

## 0. Do NOT repeat completed work

Accepted previous DS Lane A/C evidence: original source Index8 iter1300 4 metadata/32 DCP shards/8rank 17-field Sidecar, matched original source digest, 8rank×two-window plan identities, terminal partial, native Index8 collective call rhythm 16+16 per rank, and original DCP read-only manifest. Prior candidate `528c100f` test `21 passed` and original root/child identities remain historical evidence ONLY. New code changes precisely 2 diagnostic files, no production pair/Gitlink code changed.

## 1. Exact identity and fix boundary

- Diagnostic GitHub branch `v3-gateb-comparator-b0`, pin **`e3e6df04eba7d3a5ab160b1563eee7146e1ee584`**, clean detached checkout; `PYTHONPATH` per leg must resolve to its own frozen Child, not the diagnostic branch's current child.
- SOURCE Index8 frozen Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- TARGET Packed128 frozen Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
- No Full-Segment-Prefetch `8f3672d1` child in either leg. No source `iter1400`.
- Prior failure: `scoped_python_cfg_rng` refused `threading.active_count()==2` because dataset initialization spawned tqdm TMonitor. New isolated Harness `scoped_disable_tqdm_monitor()` disables monitor creation before source catalog load and restores config on exit, while preserving strict main-thread and no-other-background-thread checks. Two obsolete test imports removed; four targeted CPU safety regression tests added.
- GPT local isolated CPU dry-run: **25 passed**, `py_compile` 3 files PASS, real tqdm `thread_map` smoke PASS, illegal `--mode paired-run` exit2 with expected marker; no GPT Ruff or DS actual dataset rerun yet.

## 2. One execution batch — only Lane B and Lane D

**Lane B (can run concurrently with independent read-only checkpoint/dataset metadata validations, but no redundant Lane C sweep):**
```bash
export HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''
# In isolated diagnostic checkout at e3e6df04 (not Formal30k):
"$VENV/bin/python" -m py_compile tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/python" -m pytest -q tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/ruff" check tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/python" tools/gates/v3_packed128_gateb_compare.py --mode paired-run
```
All first 3 commands require exit0; last requires exit2 and `GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED`. Validate actual source `__file__`; enumerate real tqdm/thread_map monitor test and unexpected-background-thread failure/exception-restoration coverage from pytest. Record actual result, do not infer PASS from GPT local counts.

**Lane D (real source and target CPU producer/transforms serially, after identity check):**
- Reuse previously frozen source checkpoint and dataset/catalog paths. Previous DS established physical source path including `outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/iter_000001300`; do not revert to misleading template path. **Do not modify this source path or latest pointer**.
- Reuse complete CLI template `docs/DS_PRO_V3_GATEB_B0_CPU_VALIDATION_2026-10-13.md` from pinned diagnostic branch, using the new SHA and brand-new /tmp output names ending `_e3e6df04`. Run SOURCE Index8 then TARGET Packed128 in separate Python processes with actual pinned Child-specific PYTHONPATH, both with `--mode cpu-plan-only --num-workers 0 --steps 2 --hash-all-shards --verify-payloads`. No `--phase resume`, no GPU.
- For each leg record SHA/Gitlink, source/target digest, eight-rank two-window plan SHA `6a4d9c6a03aedfedd679179d05c6fe59eb7317d4bebf6d6b5d39f9978b6932b5` as *expected previous reference* rather than a substitute for fresh evidence, `tqdm.monitor_interval` behavior, actual CPU Native transformed payload/CFG materialization hash, terminal counts, exit, result JSON path.
- If both leg JSON files exist, run `--mode compare-cpu-reports` with both pinned paths and record exit0 and complete output. **Explicitly assert BOTH `payload_witness` fields non-null**, both status `CPU_TRANSFORM_PAYLOAD_HASHED_NOT_GPU_VALIDATED`, and both `payload_witness.members` cover 8 ranks×2 windows. Compare payload fingerprints/CFG replay; the compare CLI's `CPU_PLAN_PARITY_ONLY` status is NOT itself sufficient to prove real payload parity when both witness fields are absent.
- Confirm same source checkpoint full metadata/sidecar/shard hashes before vs after; if any targeted run fails before its own after-hash, obtain a separate read-only manifest without touching source. Lane C not rerun as a separate test. No output path may exist before execution or overlap Formal/DCP namespace.

## 3. Fail-closed and batch policy

- If Ruff or test fails, record first raw traceback and proceed only with safe independent CPU checks; if Lane D source fails, do not run dependent target/compare unless safe, but preserve independent evidence.
- If original thread blockage reappears, capture `threading.enumerate()`, tqdm instance class/monitor interval and first real traceback. Do not auto-disable safety guard, monkeypatch Python random globally, change production modules or modify candidate in DS worktree.
- If a **new** production payload/CFG failure appears after tqdm fix, provide first failing rank/episode/GA/consumer and source line. **Do not** run repeated ad hoc retries or expand to GPU.
- Keep all existing owner restrictions: no GPU, torchrun, Nsight, Cosmos FSDP8 DCP load, model train, inference, checkpoint writes, migration, iter1301, Original Formal30k worktree or old latest pointer edits.

## 4. One delivery for one GPT independent review

Submit **one** `DS_PRO_V3_PACKED128_GATE_B0_e3e6df04_FINAL_CPU_RETEST_2026-10-14.md` containing:
- exact diagnostic and two comparator pairs, clean SHA/import paths, env and all Lane B exits;
- exact two Leg CPU commands, payload witness and compare JSON, terminal/rhythm continuity and all new failures;
- old Lane A/C evidence links *only*, not retesting;
- source DCP before/after immutable verification and permissions/no GPU log;
- strict `PASS/FAIL/BLOCKED/NOT_RUN` matrix, first root cause per affected lane, and explicit unverified GPU/FSDP8/native gradients/P1 training-distribution/Gate M/formal resume.

Stop after one consolidated report. **DS_PRO does not edit production or test code and does not self-approve B0.** GPT will review the exact new diagnostic SHA once after this full report. B1 GPU and subsequent migration remain separately Owner-gated.
