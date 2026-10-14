# GPT → Codex: V3 Gate B1 exact-SHA tests-only Ruff remediation

**Date:** 2026-10-14
**Role:** Codex/CX = authorized implementation owner; GPT independent reviewer; DS_PRO independent read-only executor.
**Detailed formal GPT verdict:** `docs/collab/chatgpt/reviews/2026-10-14_V3_GateB1_8rank_executable_CPU_independent_review_4ca47102_8f3672d1.md` = **REQUEST_CHANGES**.
**Formal diagnostic implementation CODE SHA:** `4ca4710271936b286643d36ebeb41d0baeff7057`
**Formal diagnostic Gitlink:** `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`
**Current B1 branch:** `wxwy/psm_wma:v3-gateb1-numeric-implementation-20261014`; current tip may have later docs-only commits. Before editing, fetch and explicitly verify that the six+ earlier implementation files still match CODE SHA. Do not reset or force-push branch, do not overwrite any unknown changes.
**Frozen Source Index8:** Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
**Frozen Target Packed128:** Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.

## ONLY authorized change: 5 test files, 15 Ruff findings

- `tools/gates/test_v3_gateb1_compare.py:49` — E702 (1).
- `tools/gates/test_v3_gateb1_fsdp_capture.py:43,98,102` — E702 (3).
- `tools/gates/test_v3_gateb1_metrics.py:55` (two E702), `:67,:125,:135,:142,:149,:156` — E702 (8).
- `tools/gates/test_v3_gateb1_producer_cfg.py:115,116` — E731 (2).
- `tools/gates/test_v3_gateb1_same_job.py:78` — E731 (1).

For E702: split multiple semicolon-separated statements into separate Python statements on separate lines. For E731: replace local `name = lambda ...` with a function `def name(...): ...` maintaining identical captures/return values. Do NOT change assertions, fixtures, test geometry, substantive behavior, data or any other files. Do NOT use a repository-wide formatter. NO production implementation file edits unless a distinct reviewed production blocker is discovered and separately authorized.

## Evidence once fixed

1. Commit a NEW exact Code SHA to the existing isolated B1 implementation branch. Write the five-file diff against old CODE SHA `4ca47102...`, and verify the parent B1 implementation files are byte-identical.
2. CPU-only, no real dataset: `python -m py_compile` on all eleven `v3_gateb1_*.py` implementation + eleven `test_v3_gateb1_*.py` tests; `ruff check --no-cache` on BOTH sets (exit0); `python -m pytest -q tools/gates/test_v3_gateb1_*.py` (prior DS: 138 passed).
3. Negative tests still cover no-Owner-GPU pre-CUDA refusal, absent stochastic/CFG witness, skipped optimizer step, Local sidecar/strict DCP identity and original Root/Child SHA locking.
4. No GPU, torchrun, CUDA, real model/DCP load, checkpoint writes, dataset re-verification, B0 rerun, Gate M, Formal30k or full V3 audit.
5. DS_PRO must independently validate the NEW exact SHA (fresh formal pair) and supply one consolidated CPU evidence report. Then GPT performs a narrow fresh SHA review of just the 5-test-file remediation and executor outputs, not a full re-review of unchanged production code.

**Acceptance verdict request:** only request CPU-Gate closure if all 22 files Ruff exit0, compile exit0, all 138 tests PASS, exact SHA/Gitlink unchanged except new diagnostic Root, no unapproved diff. Failure in any step => BLOCKED with first file:line/error. Neither Codex nor DS_PRO may self-grant Owner GPU authorization or numeric tolerance signoff.
