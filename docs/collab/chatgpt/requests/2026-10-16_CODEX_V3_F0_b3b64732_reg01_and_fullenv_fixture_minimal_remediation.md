# GPT → Codex | V3 F0 b3b64732 只修两个阻塞项，不进入 F1

**Date:** 2026-10-16  
**Formal currently reviewed pair (REQUEST_CHANGES):** Root `b3b64732efb225c3ee08b1d9f317a90228112b29` / Child `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021`, isolated `v3-f0-safe-start-20261016` branch. Root branch HEAD may be docs-only `3b0c5d9...`, not the implementation SHA.  
**Full GPT independent review / acceptance:** `docs/collab/chatgpt/reviews/2026-10-16_V3_F0_b3b64732_0fb7f587_DS_independent_CPU_fresh_incremental_review.md`.  
**Independent DS results:** new code's main synthetic/Gloo/preflight/filesystem claims covered; one **existing real Phase5 regression** and nine **Megatron/test-fixture** full-dependency failures. Preserve the existing PASS evidence unless the remediation changes its actual scope. This request is authorization to **prepare and test a new isolated implementation candidate**, NOT permission for GPU, F1, DCP or production training.

## 1. F0-REG-01 (MEDIUM PRODUCTION): Restore mandatory verified-index argument error precedence

- **Code:** `cosmos_framework` child `examples/psm_wma_robocasa_corrected_phase5.py:739–755`. F0 currently calls `check_job_namespace(args)` **before** `dataset_index_root is None` validation; Resume with both missing index and no identity throws unrelated FileNotFoundError.
- **Required minimal source fix:** Explicitly reject missing `--dataset-index-root` with the existing ValueError **before** any namespace-dependent resume reads. Keep namespace denial **before `_load_runtime`, config/Trainer creation, dataset/index loading and all writes**. Do NOT relax fresh namespace exclusivity, canonical identity, symlink/digest, locking, phase/budget or old-source safety.
- **Acceptance:** Existing `examples/psm_wma_robocasa_corrected_phase5_test.py::test_formal_and_resume_require_accepted_index_before_data_open` must pass **unchanged** for both Fresh and Resume. New focused negative if needed: invalid Index+missing/foreign v3 identity must return Index ValueError before writing; with accepted Index, wrong namespace/digest still rejects. No model/GPU/DCP content.

## 2. F0-TEST-02 (MEDIUM TEST/EVIDENCE): Fix fake torch × real Megatron fixture incompatibility

- **Code:** child `examples/psm_wma_robocasa_phase5_f0_test.py:117–167`, synthetic `_trainer_module()`: a fake `ModuleType("torch")` lacking `dtype` is temporarily injected into `sys.modules`, and in the established V2 full-dependency venv real `megatron.core.dist_checkpointing.mapping` evaluates `torch.dtype` and fails before nine TrainerTests actually execute.
- **Required:** Make the **test harness** safe in the actual full Cosmos dependency environment while retaining the same 9 Trainer test assertions and all real imported-trainer method checks. Do not blanket skip/xfail, monkeypatch production training behavior, remove Megatron to hide product defects, or weaken test expectations. Prefer test-scoped isolated import stubs for explicitly external dependencies (not leaked into unrelated third-party code), or a truly compatible torch mock boundary if justified. Keep no production change for this test fixture issue.
- **Acceptance:** The full established V2 environment 9 failures go green; all 56 methods+subtests (actual collected count reported by runner) must pass, and V3 minimal environment test count remains green. Report exact test names, tool versions, commands/exit RC and before/after of the changed fixture. Do not treat V3-only success as independent full-env closure.

## 3. Strict allowed diff, SHA and Gate

- Child modifications limited to the **two files above plus a small affected test** if justified. Avoid changing optimizer/FSDP/Local-TTT/Native Loss, DCP save, RNG, checkpoint publisher, E1/E2, Index8 compatibility, project-wide dependencies or other Frozen Code.
- Refresh actual remote and root/child Gitlink before edit; isolate branch and ff-only pushes. Parent is current F0 implementation Child `0fb7f587...`, not historic old `1d56320c...` for a revert. New Child SHA then new Root Gitlink / formal implementation SHA. No force push, no deleting older test artifacts or editing DS-owned remote.
- Codex author self-tests (scoped CPU only), then **STOP**. DS_PRO clean detached on new formal pair runs independent affected Phase5 regression, full-dependency F0 56-case tests, V3 minimal F0, Ruff/formats/compile and any truly impacted static config/preflight; reuse prior independent Gloo and fs-Gate B/D only after proven change does not touch its tested core. GPT then issues NEW exact-pair fresh incremental Gate verdict. Existing `b3b64732/0fb7f587` verdict remains `REQUEST_CHANGES`.
- Do not start F1 before F0 new-pair `APPROVE_TO_CLOSE`; do not use completed F0 tests as a GPU/Training permission. Formal30k/Fresh, original DCP, B1 595GB evidence, dataset Index B0 and r2 numeric policy all remain unchanged.

## 4. Separate DS storage correction (not F0 production fix)

DS reported `/mnt/data` free ~223GB and incorrectly treated 8×4.7GB **B1 rank*.pt gradient+optimizer native evidence captures** as one ~37.6GB DCP; B1 did NOT save training checkpoints. Do not codify an 11TB checkpoint forecast from that estimate. DS should use metadata-only byte-sums from authentic prior iter1300 DCP (no shard-byte hashing) and build a bounded new-Fresh checkpoint/retention budget. Storage capacity is an independent hard prerequisite for future authorized fresh Save/Resume, **not** a reason to add unrelated F0/F1 code changes now.

**Codex report next:** exact new Root/Child SHA, concise diff, unchanged 30000/500/100 + Packed128 default witness, CPU commands/RC and which pre-existing independent DS evidence remains applicable. Stop pending DS acceptance / GPT fresh review.
