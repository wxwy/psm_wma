# Evaluation V2 D5 — Owner Episode-major Round-Robin + Resume Skip-by-Valid-Core (2026-10-28)

## Owner decision / precedence

Latest Owner instruction following earlier query about order `Task1 ep1 → Task2 ep1 → ... → Task18 ep1 → Task1 ep2 → ... → Task18 ep50`:

> “而且，reusme时，从这个排序中，如果测试过了，就跳过”

**D5 NEW HIGH DESIGN REQUIREMENT**: The next fresh 18×50 Evaluation V2 must use a stable global Episode-major **round scheduler**, and Resume must walk **the same plan** while skipping already-valid logical slots. The earlier actual V3 task-major queue is explicitly not the desired scheduler. Current V2 r1 formal design Root `dc750f8e258d10a33e7a195cf907926b1c98bd7f` / Child+Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5` has not been changed/approved and remains `REQUEST_CHANGES`. This is a new Owner design contract; not a new implementation code review or a real run authorization.

## 1. Frozen global ordering

Freeze exactly 18 Task IDs in `manifest.json` with immutable stable `task_order` (not arbitrary Dict/OS/GPU scheduling order). Logical slot key `(task_index, episode_index)` where `episode_index = 0..49`.

Round-major list creation / dispatch priorities:

```python
for ep in range(50):
    for task in frozen_task_order:
        slot = (task, ep)
        disposition = read_authoritative_slot_status(slot)
        if disposition == "VALID_CORE_COMMITTED":
            continue  # BOTH success AND normal behavioral_failure
        if disposition in {"SKIPPED_INIT_ERROR_OWNER_PENDING", "SCENE_ADMISSION_EXHAUSTED_OWNER_PENDING"}:
            continue  # unresolved slot; requires explicit Owner release before retry
        dispatch_only_unresolved_and_authorized_slot(slot)
    wait_for_current_round_dispositions_or_enter_explicit_global_cancel()
```

- **Round barrier**: no new Episode `ep+1` is dispatched until every Task's slot in round `ep` has a final disposition for this invocation: valid Core completion, explicitly deferred Owner-Pending skip, or an explicit stop/cancel (which halts the round; Resume revisits the round). There is no silent promotion of a `RUNNING` or uncommitted `INVALID` file to `DONE`.
- Within the same round, multiple GPU workers may **execute concurrently** in the frozen Task dispatch order; task completion timestamps are allowed to differ. Do not serialize all 18 Tasks onto one GPU just to force identical end timestamps. Preserve a bounded number of live processes and ownership.
- The logical authoritative index and source/output identity are per Task+Episode, never physical worker ID, scheduling order, output filename or task restart counter. Can reschedule to a different free GPU without altering the logical slot.

## 2. Exact Resume admission / skip

- Every new Invocation or owner-authorized Resume builds the **same sorted logical 900-slot plan** from the original frozen task order; check authoritative **Core Result Commit**, not file existence, video, old `RUNNING`, catalog convenience view, success label or `latest_summary`.
- `VALID_CORE_COMMITTED` covers `success` and `behavioral_failure`: **always skip** and preserve source result/action/Local evidence bytes, hash, identity; do not query policy or re-run simulator, even if user later changes GPU allocation.
- `PENDING`, `INTERRUPTED`, or truly `INVALID` without a valid Core commit: eligible for controlled logical-slot retry, under original infrastructure safety, session cleanup and attempt owner constraints. Preserve previous failed attempts in diagnostic namespace. No scene replay/precise RNG state recovery needed per latest Owner statement.
- `SKIPPED_INIT_ERROR` after **4 consecutive reset/precheck errors**: record skipped slot and all exceptions, **skip on ordinary Resume**; do not automatically retry until Owner explicitly authorizes this exact slot. Likewise bounded initial-degenerate admission exhausted is an explicit Owner-Pending hole, not policy failure.
- `DEGENERATE_INITIAL_SUCCESS` alone is a **rejected scene attempt, not a tested logical Episode**; bounded scene-admission resamples the same logical slot until admitted or until its admission limit is hit. Do not advance the episode index just because reset succeeded or a media file exists.
- If some later Episode (e.g. TaskX ep38) already has a valid Core commit but earlier TaskX ep37 is Owner-skipped, **do not re-run ep38**; skip it when the planner reaches that slot. The storage index must support noncontiguous valid slots and explicit pending holes.
- Owner-authorized targeted re-test of previously `SKIPPED_INIT_ERROR` holes must use the same logical Plan order among only released slots, preserve all other valid results, maintain unchanged original slot identity plus separate retry Attempt/stream IDs, and never turn a normal behavioral failure into a repeated trial.
- The formal 900-episode SR is `null` until exactly one valid Core success/failure result exists for every one of 900 logical slots. Report `partial_sr_valid_only` with a labeled denominator and list of skipped/pending/error slots. Any `SKIPPED_INIT_ERROR` or unsafe infrastructure fault prevents Clean Qualification.

## 3. Example: round restart from a partially completed Run

Example frozen Task1..Task18; `Task1/ep0` and `Task2/ep0` valid, `Task3/ep0` interrupted, `Task4/ep0` has `SKIPPED_INIT_ERROR`, Task5..18 ep0 valid. On Resume:

- Task1 ep0: **skip**; Task2 ep0: **skip**; Task3 ep0: **execute**; Task4 ep0: **skip owner-pending**; Task5..18 ep0: **skip**.
- Round0 disposition reached (Task3 valid or in controlled blocked/stop state, Task4 explicitly owner-pending). Then round1 Task1 ep1, Task2 ep1, ... Task18 ep1; skip any that have already valid Core result, dispatch the rest. No wholesale Task restart, no forced original scene reproduction, no automatic owner-skipped-slot retrial.

If a run is stopped while some Task's round0 slot is in-flight, resume rechecks the current round and all existing valid slots; an attempt that committed atomically before the crash is skipped on Resume.

## 4. Production technical risk, not an excuse to relax D5

The old queue does one Task Batch of 50 continuous Episode resets on one Worker. This **cannot meet D5** without a new scheduler/runtime coordination design. With only 3 GPUs and 18 Tasks, a naive one-Episode-per-Batch restart could reload the ~13GB model/Server and recreate EGL contexts up to900 times and be prohibitively slow or unstable. **Codex must propose a resource-bounded implementation** (e.g. reusable checked model server per worker with clean Local session reset and Task environment ownership/pause or re-init as required), while preserving exact post-action `env._check_success`, core action/Local ABI, task scene admissibility, per-Episode output identity and session safety. The Owner does **not** require old scene replay when a stream is reconstructed; record actual seed/stream and distinguish resumed/new scenes. Do not silently claim one uninterrupted Task-level 50-reset RNG stream if the scheduler interleaves or reconstructs Task environments.

The scheduling contract is about **dispatch order + round barriers**, not identical wall-clock completion order under parallel GPUs. Codex's Stage2 proposal must explicitly state process/model/scene lifetime and test stable RNG/Local-TTT session isolation across task switches; actual RoboCasa performance/stability only in separately authorized Canary.

## 5. Required next r2 isolated CPU tests

1. 18 tasks × 50 episodes: planner produces 900 unique indices ordered by `(episode_index, task_order_index)`, round 0 all Tasks precedes round 1; no attempt ordering by GPU completion.
2. 3 simulated asynchronous GPU workers: concurrent same-round tasks allowed, **no ep+1 dispatched before prior round terminal dispositions**.
3. At different crash points (before/after slot atomic Commit, in-flight worker, between two Task slots, after round barrier), re-plan from original order: all valid Core committed success and behavioral_failure bytes unchanged and **zero duplicate execution**, only missing slots dispatched.
4. Initial-degenerate candidate is resampled **within** the same logical slot; 4 consecutive reset/precheck errors skip ep37; ep38..49 still can execute and remain valid; later ordinary Resume must not re-run ep37 until **Owner authorization**, nor re-run already-committed ep38.
5. Error/infrastructure cancellation and resume never conflates `RUNNING`, corrupted evidence, `INVALID`, `SKIPPED_INIT_ERROR`, `PENDING`, and `VALID`; same task/ep attempted by two GPUs must fail closed.
6. Tests cannot count old431 or synthetic900 as real runtime proof. Include focused scheduling performance lifecycle proposal for reviewer (not a GPU execution).

## 6. Scope and history

D1 scoped process-fault cleanup, D2 crash-safe Task/Episode claims, D3 Episode-only Resume/no scene reproduction, D4 degenerate scene admission + 4-consecutive-init-error skip remain required, **D5 added**. No actual runtime, production launcher, Child, model, training, old431, or V3 eval branch was edited by this document. No GPU/DCP/900 real evaluation or merge authorized.

Canonical latest Owner contract (to be updated with D5): `docs/collab/chatgpt/requests/2026-10-28_V3_RoboCasa_EvalV2_r2_CANONICAL_LATEST_OWNER_CONTRACT.md`. Tracking [Issue #7](https://github.com/wxwy/psm_wma/issues/7). Codex must acknowledge this new addition after reading the *latest remote V3* before producing a new formal r2 source SHA.
