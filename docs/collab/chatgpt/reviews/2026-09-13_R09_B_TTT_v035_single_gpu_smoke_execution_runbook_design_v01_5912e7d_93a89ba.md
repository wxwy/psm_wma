# ChatGPT canonical review — R09-B TTT v0.3.5 single-GPU smoke execution runbook design

Date: 2026-09-13

## Formal target

- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-RUNBOOK-DESIGN`
- Formal root: `5912e7d06c53e8a0cf650d4b2886f10cd72e3311`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Prior approved design pair: `e75c8c12c8573d445e91f2b9c9b4d95d98b1d5f8 / 93a89ba61306d840a008813f62f26a34d54850f4`

Independent Gitlink verification: formal root tree contains `cosmos-framework` as mode `160000` at exactly `93a89ba61306d840a008813f62f26a34d54850f4`; `.gitmodules` maps that path to `wxwy/cosmos-framework`, and the child commit is reachable there.

## Incremental scope reviewed

The formal root adds the docs-only runbook design `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_runbook_design_v0.1.md` plus task records; the child is unchanged. The prior single-GPU smoke design's `world_size != 1` remediation remains closed.

The runbook correctly preserves the receipt-derived authority tuple, fail-closed authority drift, canonical JSON request schema, `world_size=1`, no `torchrun`, `num_workers=0`, no resume/sidecar, bounded `1..100` steps, fresh output root, chronology/GA count checks, no replay/resample after failed partial GA window, and docs-only scope for this Gate.

## Current blocker

### HIGH — terminal outcome / artifact ABI is internally contradictory

- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_runbook_design_v0.1.md:127` (with conflicting requirement at the manual-stop rule in §7, around line 149)
- Root cause: §6 freezes `failure.json` as allowed **only for FAIL/BLOCKED**, while §7 separately requires an operator `MANUAL_STOP` to write `failure.json` containing `MANUAL_STOP` and the last committed transaction identity.
- Violated frozen contract: this Gate is responsible for freezing the execution request/runbook shape, output allowlist, PASS/FAIL/manual-stop semantics, and evidence schema before an execution request may be designed. A terminal outcome cannot simultaneously be outside the allowed `failure.json` cases and be required to emit that file.
- Why current text is insufficient: a later execution-request implementation would have to invent whether `MANUAL_STOP` is a subtype of FAIL, a third terminal status, or an exception to the §6 allowlist. That changes terminal-state and evidence ABI at implementation time rather than following a frozen design.
- Exact acceptance: refreeze one unambiguous taxonomy. Either (a) make `failure.json` explicitly permitted/required for `FAIL | BLOCKED | MANUAL_STOP` and define `MANUAL_STOP` as a distinct non-PASS terminal status with the required schema/transaction identity, or (b) explicitly classify manual stop as a named FAIL reason and use that same classification consistently in §6, §7, summary/failure schema, and the future execution request. No implementation-time interpretation is permitted.

## Blocker lifecycle

- Prior `world_size` contradictory fail predicate: **CLOSED**.
- Current blockers: `1 HIGH` (`1 design/failure-semantics`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_runbook_design_v0.1.md:127)`

This verdict binds only the exact formal pair above. It does not authorize creation/execution of an execution request, real source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, matched smoke, sidecar, checkpoint write, or formal training.