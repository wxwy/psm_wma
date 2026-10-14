# V3 Gate B1 — 8-Rank Executable Comparator: independent CPU Evidence/Gate review

**Date:** 2026-10-14
**Reviewer:** GPT — PSM-WMA independent code/Evidence/Gate auditor
**Formal verdict:** **REQUEST_CHANGES**
**Exact formal diagnostic implementation Root:** `4ca4710271936b286643d36ebeb41d0baeff7057` (`wxwy/psm_wma:v3-gateb1-numeric-implementation-20261014` implementation commit)
**Exact diagnostic Child/Gitlink:** `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`. NOTE: this diagnostic root Gitlink is NOT either side of the frozen B1 comparator.
**Frozen production comparisons, unchanged:**
- Source Index8 Root `b159f45906f7261d028aecc226ab7f2bb9807eb9`, Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- Target Packed128 Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85`, Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
**Current live V3 docs Root:** refreshed separately; current live Child/Gitlink `1d56320c08c56b0f8dd248919d152d81ae12ea7b` (PR #3 trusted startup). V3 ledger/docs commits never substitute for implementation SHA.
**Source evidence:** Owner-provided `DS_PRO V3 Gate B1 — 8-Rank End-to-End Comparator: Independent CPU + Ruff Acceptance`, 2026-10-14, 175 lines. DS_PRO verified a clean detached checkout at exact CODE SHA and immutable frozen Child objects. GPT did not execute DS commands or access DS host logs; their outcomes are executor-reported.
**Reference Gate:** B1 Round2 frozen pair and B1 numeric prefreeze r2; the CPU Code/ABI Gate is distinct from 8×H100 B1 GPU Gate, Gate M and Formal30k. B0 CPU `ec9d162b` previously APPROVED/CLOSED.

## A. Incremental review scope

No redundant audit of the earlier B0 implementation or unchanged V3 production Child. GitHub exact comparison of previous B1 candidate `5aa79a73a4c6f1a424fa0a9476e1ce52ae9e9361` against formal `4ca47102...` has 16 changed paths: 14 B1 implementation/test files + two diagnostic docs, not production V3 code. The native GA2, no-rescan, model-site RNG, same-job DCP loader, 8-rank CLI and postprocessor are present at the pinned CODE SHA. Technical assessment here is limited to new executor CPU evidence and direct relevant code/test file/line confirmations.

## B. Contract → evidence → result

| Requirement | Direct corresponding evidence | Result |
|---|---|---|
| Exact SHA / frozen pair / scope | GitHub CODE SHA `4ca471...` with Gitlink `8f3672...`; DS clean detached checkout with exact commit tree `29fddbc74c53298a71b6e47605d124bdafacc134` and B1 Source/Target object identities | PASS (CPU identity only) |
| Sixteen-file increment | `5aa79a73..4ca47102` 14 Python + 2 docs, no production code modifications | PASS |
| Syntax | `python -m py_compile` on 22 B1 implementation+test modules, exit0 | PASS (DS) |
| Implementation static lint | Ruff `--no-cache` on eleven `v3_gateb1_*.py`, exit0 | PASS (DS) |
| **Full scoped Ruff gate, including tests** | Ruff `--no-cache` on eleven `test_v3_gateb1_*.py`: exit1, **15 findings: E702 ×12, E731 ×3** | **FAIL — Gate blocking** |
| Synthetic B1 CPU behavior | `pytest -q tools/gates/test_v3_gateb1_*.py`, **138 passed in 2.33s**, exit0; Owner approval barrier and absent sigma/CFG witness negative cases covered | PASS (synthetic scope only) |
| CLI early fail-closed | Both `--mode prepare` and `--mode execute` reject fabricated Root at `v3_gateb1_run.py:57` BEFORE CUDA; code also contains owner-receipt gate at lines 94–114 | PASS *only* for invalid-Root negative |
| Frozen Child static ABI | DS inspected both `937066ff` Index8 and `c8dabbb3` Packed128 for patched method signatures, same-job no-save scope and reachable sigma/noise/CFG sites | PASS in static scope; does not establish runtime |
| Side effects | DS reports no real DCP/latest-pointer write path in read-only adapter; no real 4B DCP/model load or training performed | PASS in CPU/static scope |
| Actual FSDP8/GPU parity | No GPU, 8-rank native runtime, DCP load, gradient equivalence, full/terminal × P0/P1 or numerical Owner signoff | NOT RUN / NOT AUTHORIZED |

## C. Current active blocker

### B1-CPU-LINT-01 — LOW (style) / CPU acceptance hard blocker — **OPEN**

- **Files/lines:** 
  - `tools/gates/test_v3_gateb1_compare.py:49` — E702 (1).
  - `tools/gates/test_v3_gateb1_fsdp_capture.py:43,98,102` — E702 (3).
  - `tools/gates/test_v3_gateb1_metrics.py:55` (two semicolon separators), `:67,:125,:135,:142,:149,:156` — E702 (8).
  - `tools/gates/test_v3_gateb1_producer_cfg.py:115,116` — E731 (2).
  - `tools/gates/test_v3_gateb1_same_job.py:78` — E731 (1).
- **Root cause:** multiple statements written on one line; assignment of lambda expressions directly to local names in synthetic fixture code. GPT independently inspected these exact code excerpts in the pinned GitHub CODE SHA and confirmed all 15 locations.
- **Frozen acceptance violation:** CPU static Gate requires Ruff exit0 on *all* changed/scoped B1 implementation and test files; the reported test-file Ruff exit1 cannot be described as all-file PASS. 138 pytest PASS does not waive the lint contract.
- **Production semantics:** no active B1 production-implementation bug established **from this finding**. This is strictly **TEST-ONLY / EVIDENCE-ONLY** remediation. This verdict does **not** authorize changing the 11 implementation modules, model/optimizer/DCP semantics, frozen children or data/checkpoints.
- **Acceptance repair:** Codex (not DS_PRO) changes **only these five test files** by splitting semicolon statements onto independent lines and replacing assigned lambdas with equivalent named `def` functions. Preserve all test bodies, assertions, fixture semantics, branch identity and test count. Commit fresh exact implementation SHA; rerun 22-file `py_compile`, Ruff on all 22 with exit0, entire 138-case B1 scoped pytest suite; DS_PRO independently verifies new SHA in one CPU-only report. Any surprising new test failure or production issue must be reported separately rather than silently fixed or widened in scope.

## D. Evidence caveat (not a new code blocker)

The CLI manual invocations were intentionally fed an unrelated fixture Root. Consequently `prepare` and `execute` both failed at the first Root SHA guard (`v3_gateb1_run.py:57`); this proves that invalid-Root fail-fast works **but does not independently test** the eventual authorized owner-receipt denial on a valid pinned Root, nor a successful legal pinned `prepare` mode. The request permitted synthetic tests as a substitute, and DS listed the corresponding mocked Owner-receipt/prepare-negative tests. This is **not** retroactively elevated to a B1 CPU blocker; it remains a clear limitation for the *separate real-run readiness Gate*. Do not infer full runtime readiness from this early rejection.

DS static ABI evidence says sound schedule/dropout disabled on frozen config; runtime resolved enablement must still be checked in actual setup. Any reachable new stochastic site not covered by the scoped hooks is a B1 GPU-readiness blocker, not a reason to redo the closed dataset or B0.

## E. Final scope

**REQUEST_CHANGES** for exact CODE SHA `4ca47102...` / diagnostic Gitlink `8f3672...`, due solely to **B1-CPU-LINT-01 (test-file Ruff evidence)**. Already satisfied parts (syntax, 138 CPU tests, implementation lint, existing frozen Child signatures) are accepted as **evidence for this SHA**, not a formal Gate approval. A **new CODE SHA** from fixture-only modifications must receive focused fresh review; never inherit a previous verdict automatically.

**Never authorized here:** real 8×H100 execution, DCP model restore, numerical threshold freeze, any migration/Gate M, Formal30k iter1301, whole-V3 audit, 451GB full dataset acceptance. B0 CLOSED. Full/Terminal × P0/P1 remain required GPU-side only after separate Owner approval.
