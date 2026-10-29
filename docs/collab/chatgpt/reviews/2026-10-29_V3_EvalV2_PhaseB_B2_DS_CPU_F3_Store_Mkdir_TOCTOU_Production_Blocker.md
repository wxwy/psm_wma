# V3 EvalV2 Phase B B2 — DS Final CPU 426 F3 Production TOCTOU Evidence Gate

**Date:** 2026-10-29

**Current formal source pair (unchanged):** Root `c724cb8b1ac74c8b1748bdaac95450fb0635a095` / Child+Gitlink `774c2edb93ec5a6ba85ba1124757064d7cc779a5`. Branch `v3-eval-v2-cpu-fixture-20261029`.

**Evidence Gate verdict: `REQUEST_CHANGES` — HIGH production blocker, not test-only.** Prior source-only `APPROVE_CODE` records remain historical; they do not override new failing behavioral evidence or authorize GPU/Canary/900. This is a **new runtime Evidence finding**, not a repeated full Code Gate of unchanged Pair.

## 1. DS run and independently confirmed scope

DS_PRO reports fresh isolated clean exact-pair worktrees, source SHA before recorded and no dirty state after, CPU-only. Reported results:

| group | passed | failed | total |
| --- | ---: | ---: | ---: |
| inference | 145 | 0 | 145 |
| phase_a_regression | 255 | 0 | 255 |
| phase_b_runtime | 25 | 1 | 26 |
| **all** | **425** | **1** | **426** |

Shell exit 1, `gate.json.status=FAIL`. `source_unchanged` final property absent because gate short-circuited on FAIL; clean worktrees and before hashes are only supporting evidence. The raw DS files live at `/tmp/ds_pro_v3_evalv2_b2_final_20261029/evidence/` on the DS machine, with full digests in its `evidence_files.sha256`. **GPT independently read the frozen GitHub source paths cited below, but did not independently fetch the DS server's raw log/JUnit/OS artifacts or execute tests.** Counts, histograms and exact failure stack are DS-supplied.

DS reports F1 two alternative-loopback port negative tests PASS and F2 all three actual CPU OS multi-Sim tests PASS, including G1/N2/E2 `native_batch_histogram {1:4,2:2}`, G2/N3/E1 `{1:4,2:1}`, G1/N3/E1 `{1:6,2:0}`. These prior issues are **CLOSED by DS-reported behavior**; no retesting/redo of their static review. F3 real owned Server death under two active Slot Tickets failed with FileExistsError.

## 2. F3-P1 — HIGH, production fault-path TOCTOU

- **Location and confirmed actual code:** Child `cosmos_framework/evaluation/robocasa_v2/store.py:49-57`: `mkdir(path)` does `path = safe(path)`, then `if path.exists(): ... return`, otherwise recursive `mkdir(path.parent)`, then plain `path.mkdir()`, then `sync_dir(path.parent)`. Two threads can both observe absence and then have one fail at `path.mkdir()` after the other creates it.
- **Actual reachable concurrent callers:** Root `scripts/robocasa_eval_v2/runtime.py:618-630` worker exception path calls `Store.finish_invalid()` / `record_process_error()`; same file `844-862` coordinator exception path writes `coordinator_stop` errors. Both converge on Child `store.py:902-927` `_record_fault(...)` → `save(self._internal(task) / "errors" / random_uuid + ".json", ...)` → `_publish():94` → shared directory `mkdir()`.
- **DS original failure witness (not independently replayed by GPT):** F3 CPU fixture injects an actual Server exit code23 after two distinct active Slot Tickets (`GENERATING` + `QUEUED`). One thread/coordination path races to create the same `_internal/tasks/CloseFridge/errors` directory. `FileExistsError` at `store.py:56` surfaces and prevents the planned F3 assertions. Reported persisted faults include `core_invalid` and `process_cleanup`; the attempted `coordinator_stop` fault can be lost.
- **Violation:** Frozen fail-closed fault logging / coherent recovery and owned Server-death cleanup must remain auditable under concurrent in-flight Slots; a benign newly-existing directory cannot abort or overwrite a distinct uniquely named error record. The exception can obscure the initiating Server failure and invalidate the independently required F3 evidence. **No evidence presently establishes Core corruption, irrecoverable production data loss, or compromised process cleanup**; do not claim those without separate witness.
- **Severity:** HIGH because a reachable fault-recovery path in production can fail during a real Server crash. This is a **pre-existing production defect now exposed by stronger test**, not introduced by last test-only Root diff.

## 3. Minimal authorized remediation scope / acceptance

Authorize Codex to **propose** narrow fix under its existing isolated candidate only (not a direct V3 merge). Minimal source target Child `cosmos_framework/evaluation/robocasa_v2/store.py::mkdir`; Root changes should be limited to new Gitlink and a necessary focused regression test (if not placed in an already-included Child test). Do not modify batch generation, Local-TTT, scheduler, runtime fault authority, old F1/F2, training/DCP or benchmark contracts.

Desired semantics: concurrently created **real directory** is treated as success; preexisting ordinary file and symlink paths remain fail-closed; retain `safe()`, recursive parent construction and **parent-directory fsync**; do not suppress arbitrary `OSError`, lose events, truncate `errors`, or turn failure into successful episode. A minimal `try: path.mkdir(); except FileExistsError: ...` with strict revalidation (`safe(path)`, `is_dir`) and unchanged `sync_dir(path.parent)` is a viable direction. Blindly ignoring every existing path without validating directory/symlink status is not acceptable. Avoid new global locks and unrelated Store redesign.

**Focused regression:** deterministic two-thread collision on initially absent same internal directory, or shared task `record_process_error` writing distinct records; verify both succeed, both immutable uniquely keyed error records persist, no unexpected `FileExistsError`, ordinary-file/symlink cases still rejected, and fsync semantics preserved. Show old source RED and fixed source GREEN where practical. **Critical integration regression:** keep the new F3 deterministic Server death test with two live Slots and assert correct Server exit23, both owned Slot invalidations, process-group cleanup/foreign process unaffected. Reuse existing full CPU unified Gate including inference145 + PhaseA255 + PhaseB26, or greater true count if adding regressions. No skip/x-fail/mocking out the fault path, no opportunistic multi-round CPU replays.

**Handoff:** new complete Child SHA, new Root SHA with exact Gitlink, smallest child+root diff, focused raw CPU/JUnit and baseline static checks, one author unified CPU result if feasible, STOP for GPT **narrow fresh incremental Code Gate** on new pair. Only after approval may DS independently run the clean exact-pair complete unified CPU Gate once and supply raw JUnit/logs/OS witnesses. Do not infer independent 426 PASS from author tests.

## 4. Authorization boundary / previous gates

- **Current final DS CPU Evidence Gate: `REQUEST_CHANGES` (HIGH production blocker)**.
- Previously `APPROVE_CODE` for `323f0b2a/774c2edb` Phase B and `c724cb8b/774c2edb` test-only changes are history, **not final independent CPU closure**. F1/F2 have DS-reported PASS; F3 remains OPEN.
- Until a new Formal Pair is audited and independent CPU Evidence reaches PASS: **no V3/Child production merge; no real GPU/Cosmos/RoboCasa Canary, training/checkpoint/900 evaluation or changes to the concurrently running training job**.
- No new design gate, no third architecture increment, no changes to sample/physics/success scientific contracts.

## 5. References

- [Child Store mkdir and symlink safeguards](https://github.com/wxwy/cosmos-framework/blob/774c2edb93ec5a6ba85ba1124757064d7cc779a5/cosmos_framework/evaluation/robocasa_v2/store.py#L34-L57)
- [Child Store `_record_fault`](https://github.com/wxwy/cosmos-framework/blob/774c2edb93ec5a6ba85ba1124757064d7cc779a5/cosmos_framework/evaluation/robocasa_v2/store.py#L902-L927)
- [Root worker error handler](https://github.com/wxwy/psm_wma/blob/c724cb8b1ac74c8b1748bdaac95450fb0635a095/scripts/robocasa_eval_v2/runtime.py#L618-L630)
- [Root coordinator error handler](https://github.com/wxwy/psm_wma/blob/c724cb8b1ac74c8b1748bdaac95450fb0635a095/scripts/robocasa_eval_v2/runtime.py#L844-L862)
- [Root F3 CPU negative test](https://github.com/wxwy/psm_wma/blob/c724cb8b1ac74c8b1748bdaac95450fb0635a095/tools/v3/eval_v2_batch_tests/runtime_test.py#L303-L364)
