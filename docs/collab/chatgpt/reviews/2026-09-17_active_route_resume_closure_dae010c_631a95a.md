# ChatGPT independent review — ACTIVE-ROUTE-RESUME closure

## Formal target

- Gate: `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`
- formal root: `dae010c7b51bbc1e42c5e1af188b2cc2ebf66d9b`
- exact child/Gitlink: `631a95af0aff28b03a93df320c179bfb9d10f607`
- prior reviewed pair: `ffeb6aa2bc9ae1f5e5bbf49ae6aa9f909853353c / 7bb507f0ce2a3a89e78c1c10ae465d0e5907e215`
- review type: fresh implementation/evidence closure review; child changed, so prior verdict does not carry.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/active_local_memory_driver.py:350)`

Blockers: **2** — 1 production/atomicity HIGH, 1 Evidence-only HIGH.

## What closed from the prior review

The previous frontier-coherence finding is **CLOSED in substance**. Child `631a95a` adds fail-closed checks for:

- `active_stream` / `active_cursor` key-set equality;
- active stream identity matching its `_by_slot[slot]` position and `stream_index`;
- cursor range against `producer.block_count(active_stream[slot])`;
- idle-slot frontier range;
- mutation fixtures for misaligned stream index and out-of-range cursor.

These are the right invariants and address the previously identified silent skip/replay channel.

## HIGH-1 — restore validation still occurs after live mutation

**Location:** `cosmos_framework/model/generator/mot/active_local_memory_driver.py`, `load_state_dict()` around the call to `_restore_runtime()` and the subsequent frontier checks; `_restore_runtime()` itself.

### Root cause

`load_state_dict()` calls `_restore_runtime(state_dict["runtime"])` **before** validating `stream_index` / `active_cursor` coherence. `_restore_runtime()` immediately mutates live authority:

1. `owner.scheduler = scheduler`;
2. `scheduler._canonical_runtime_owner = owner`;
3. `sidecar._records.clear()`;
4. sidecar records are repopulated;
5. `owner.snapshot()` is then called as another fallible check.

Only after that live mutation does `load_state_dict()` validate the newly added frontier invariants. A malformed checkpoint can therefore fail because of `stream_index`, cursor range, or missing sidecar scheduler counterpart **after live scheduler/sidecar state has already changed**.

This violates the project restore/checkpoint atomicity rule: decode/stage → full validate → runtime admission → first live mutation, with no remaining fallible validation/load after first mutation.

### Why current tests do not close it

The new mutation tests assert that malformed frontier input raises, but they do not assert **zero live mutation** on failure. A raise after replacing `owner.scheduler` or clearing the sidecar is not a valid fail-closed restore.

Likewise `_restore_runtime()` can discover a `runtime.committed` slot with no scheduler counterpart only after swapping the live scheduler and clearing sidecar state.

### Acceptance

Refactor restore into two phases:

1. **pure staging/validation**: rebuild candidate scheduler off to the side; stage candidate sidecar records; validate all runtime committed↔scheduler identity relations; validate all driver frontier fields and block ranges; validate all cross-field/key-set constraints; perform every other fallible check without mutating the live owner/sidecar/driver;
2. **atomic apply**: only after all checks pass, swap/apply scheduler + sidecar + driver frontier with no remaining fallible validation.

Add causal mutation fixtures for at least:

- bad `stream_index`;
- out-of-range cursor;
- bad active-stream key set;
- `runtime.committed` with no candidate scheduler counterpart.

For each, assert the exact pre-load live scheduler object/frontier, sidecar records, driver frontier, and owner phase remain unchanged after rejection.

## HIGH-2 — mandatory real GPU/DCP resume witness is still absent

**Authority:** resume design v0.4 §6 criterion 4.

The design requires a real end-to-end witness:

`save_iter checkpoint → kill process → auto-resume → first resumed SegmentIdentity sequence matches uninterrupted control → cumulative_valid_consumer_exposure continues rather than resetting`.

No new root/child evidence supplied with `dae010c7 / 631a95a` demonstrates this real GPU/DCP path. CPU unit tests and direct `state_dict()` round trips do not substitute for the production checkpointer callback/load ordering and real trainer integration.

This is an **Evidence-only blocker**; it does not by itself claim the implementation is otherwise incorrect.

### Acceptance

After HIGH-1 is fixed on the resulting new pair, run and retain the exact GPU/DCP save→kill→auto-resume witness required by v0.4 §6, including:

- checkpoint/save iteration and resumed iteration;
- uninterrupted-control comparison;
- first resumed window/member identity sequence;
- `_stream_index` / `_active_cursor` / `window_index` continuity;
- `cumulative_valid_consumer_exposure` continuity;
- successful subsequent native forward/backward/commit window;
- no fallback to fresh catalog state.

## Scope conclusion

Production blocker count: **1**.
Evidence-only blocker count: **1**.

No approval to close this Gate, no D8b authorization, and no carry-over approval to any future root/child. A remediation child/root is a new formal pair and requires fresh review.
