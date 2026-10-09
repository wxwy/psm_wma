# PSM-WMA V3 — Missing-Gradient Identity Audit Candidate / Formal30k Hold

Date: 2026-10-09
Owner and sole source code editor: GPT/Codex
Status: **CODE SUBMITTED / TARGETED CPU STATIC RETEST PENDING; GPU AUDIT NOT YET RUN**
Current formal30k launch authority: **PAUSED pending missing-gradient identification and code-owner review**. This supersedes the fresh-formal authorization in the earlier 3-step smoke closure but does not invalidate that smoke's PASS.

## Exact candidate and scope

- Before diagnostic: Root `8f6a20d7e44b57ba128fee9c9a29046f8ef186cd` / Child+Gitlink `4923e494a8bb0e1e18d7943ae00bd17f71498d88`.
- New Child candidate branch `v3-persistent-dataset-index-20261009` at **`9656efc4dc7221710f0017bad662430c83893430`** (the preceding child baseline is an ancestor).
- New Root candidate branch `v3-persistent-dataset-index-pair-20261009` is the **commit containing this review and Gitlink update**. DS must obtain / pin that exact Root HEAD from the final owner handoff, verify Root Gitlink = Child `9656efc4dc7221710f0017bad662430c83893430`, Child clean.
- No promotion or edit of production Root `V3` or Child `v3-local-ttt`.
- 4 changed Child files, all in `examples/`: corrected telemetry implementation/test and corrected Phase5 entrypoint/test. Dataset, source, optimizer, loss, Local-TTT core, DCP/resume components and model weights remain unchanged.

## Issue and exact interpretation

DS's successful 8xH100 3-optimizer-step bounded telemetry previously logged `missing_grad_tensors_rank_local=0 / 4 / 4`. This is the number of **selected named rank0 parameter tensors with `parameter.grad is None` at pre-optimizer, after GA accumulation**. It does NOT count all-zero gradient tensors, NaN gradients, nor necessarily unused tensors globally across FSDP ranks. Even 32 native forward/backward calls per step do not guarantee that every conditionally selected tensor was exercised.

Prior code emitted only an aggregate rank0 count, so the four parameter identities, their categories, and whether this is consistent across 8 FSDP ranks remain unknown. The guard enforces finite *present* gradients, not that all 314 selected tensors are non-None.

## Code-owner diagnostic change (opt-in and numerics-passive)

- New CLI `--audit-missing-grads` is **only permitted when fresh bounded `--stop-after-iter 3`**. It is OFF by default and cannot be used with a full 30k or resume.
- New passive `GroupedPlanObserver` audit at each rank's pre-optimizer boundary: record names and `generation/action/local` group, finer Local subgroup, `global_numel` and `local_numel`, whether DTensor, DTensor placements, `requires_grad`, selected/present/missing counts and group totals.
- No tensor values transferred or reduced, no added all-reduce/barrier, no `.item()`, no graph or grad writes in audit, no per-consumer hot-path instrumentation. For nonzero ranks the original rank0-only training summary remains unchanged; **only when opted in** each of 8 ranks emits one `[CorrectedV3][missing_grad_audit]` JSON record per *successfully committed* optimizer step, 3 steps total.
- First rank's audit count is cross-checked against existing rank0 `missing_grad_tensors_rank_local`. Audit status `AUDIT_ERROR`, mismatches, missing rank/step or incomplete records must BLOCK a formal-training decision.
- Frozen model/data/config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` unchanged. New fresh diagnostic job must use the official DROID DCP, Verified Index and existing T16/B8/GA2/K4, 30000/500/100 schedule. Never resume its DCP.
- Added CPU tests for eight distinct mock ranks, deterministic group/name reporting, zero-gradient-vs-None distinction, no per-step all_reduce/synchronize/`.item()`, successful-commit-only output, default-off behavior, and bounded CLI safeguards.

## Gate 1: targeted CPU/static on original DS host (MANDATORY FIRST)

DS_PRO is **only** an executor/evidence supplier: use original sole `psm_wma_v3` worktree, preserve all MM `SESSION.md`, `TODO.md`, existing Evidence/checkpoints. No source edits, extra worktree, commit, reset, clean, format-write, or force checkout. Safe fetch and fast-forward exact Root/Child; if conflict stop.

Before pytest: `export HF_HUB_OFFLINE=1`. Under Child directory run:
```bash
pytest -q -p no:cacheprovider examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_corrected_phase5_test.py
ruff --version   # required 0.12.7
ruff check examples/psm_wma_robocasa_corrected_telemetry.py examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_corrected_phase5.py examples/psm_wma_robocasa_corrected_phase5_test.py
ruff format --check examples/psm_wma_robocasa_corrected_telemetry.py examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_corrected_phase5.py examples/psm_wma_robocasa_corrected_phase5_test.py
python -m py_compile examples/psm_wma_robocasa_corrected_telemetry.py examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_corrected_phase5.py examples/psm_wma_robocasa_corrected_phase5_test.py
```
Capture pytest counts, raw stderr, `ruff format --diff` on failure, Root/Child/Gitlink and Child-clean. Any failure => STOP. **GPT has not independently run Ruff 0.12.7 or these full project imports on the remote training host; do not mark CPU GREEN from GitHub commit.**

## Gate 2: SINGLE bounded 8xH100 diagnostic (conditional upon ALL Gate1 PASS)

Only if CPU/static ALL GREEN, DS may run **one new**, fresh `torchrun --nnodes=1 --nproc-per-node=8 --standalone` with:
- `--phase fresh --stop-after-iter 3 --audit-missing-grads --dataset-index-root <EXISTING_VERIFIED_INDEX>`
- `--job-name bounded_missing_grad_audit_r1` (unique clean namespace; new external output root), no other training.
- `--max-iter 30000 --warmup 500 --save-iter 100 --t 16 --b 8 --ga 2 --k 4 --world-size 8`
- exact new Root+Child/Gitlink, official DROID DCP, existing accepted data/index, `HF_HUB_OFFLINE=1`, Child-first `PYTHONPATH`.
- Capture **separate stdout/stderr per rank**, plus combined log; the expected evidence is 24 audit records: (rank0..7) x (iter1..3), each `AUDIT_OK`. Check 3 ordinary rank0 `optimizer_committed` records, bounded_stop completed_iteration=3, frozen formal digest, no iter4, no error.
- Report, separately for **each iteration and each rank**: `missing_grad_parameter_names`, group/subgroup, shard `local_numel` and global `global_numel`, placements, selected/present/missing group counts; count rank0 equality with ordinary telemetry; compare (a) names common to all ranks vs (b) rank-specific misses vs (c) missing local zero-length shards vs (d) missing nonempty persistent trainable components.
- Report source, action, local group health / NaN, DCP completeness / memory briefly. DCP from this diagnostic is **DIAGNOSTIC_ONLY_DO_NOT_RESUME**.
- Any CPU gate failure, audit-error record, missing logs, SHA/digest mismatch, DCP mismatch, data violation, optimizer numerical failure or unplanned start of iter4: STOP and return full evidence. No alternative configs or self-fixes.

## Final decision after DS diagnostic

Only GPT reviews the 24 rank-wise name records and judges whether `grad=None` corresponds to expected conditional paths, zero-sized FSDP shards or an unintentional disconnect. Formal30k fresh remains **on HOLD** until that review; no DS unilateral formal launch, production merge or resume.
