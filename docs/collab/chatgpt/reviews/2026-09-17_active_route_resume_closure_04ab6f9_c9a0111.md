# ChatGPT independent review — ACTIVE-ROUTE-RESUME closure

Date: 2026-09-17
Gate: `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`
Formal pair reviewed:
- root: `04ab6f9adf6ef023c3b6f15d361a0b8f3824aa8f`
- exact child/Gitlink: `c9a01116e8d48a13d1f38fffafcf72461c2352c3`

Later root `463d649e` changes Gate-3 design/evidence text only; it does not change this Gate-2 implementation child. The latest explicit Gate-2 closure request in `CODEX_INBOX.md` is `04ab6f9a / c9a0111`.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/active_local_memory_driver.py:407-418)`

The previous restore-atomicity blocker is closed in direction: child `c9a0111` now stages active stream/frontier/runtime off to the side, validates them first, then applies live state. The new zero-live-mutation rejection fixtures are the correct shape.

Closure is still blocked by two implementation defects and one evidence gap.

## HIGH-1 — legitimate terminal-frontier snapshots are rejected

Location: `active_local_memory_driver.py`, `_stage_runtime`, terminal-sidecar check around lines 416-418.

Current code builds:

```python
by_slot = {identity.slot_id: identity for identity in scheduler.committed_identities}
...
if any(slot in by_slot for slot in scheduler.terminal_slots):
    raise RuntimeError("... terminal slot retains sidecar state")
```

This does **not** mirror `CanonicalSegmentRuntimeOwner.snapshot()`.

The owner invariant checks whether a terminal slot still has a **sidecar committed record**:

```python
if any(slot in {identity.slot_id for identity, _ in committed}
       for slot in self.scheduler.terminal_slots):
    raise ...
```

A terminal identity is expected to remain in `scheduler.committed_identities` until terminal rebind, while `LocalMemorySegmentSidecar.commit()` removes the sidecar record at `training_stream_end`. Therefore a completely valid IDLE checkpoint can have:

- `terminal_slots[slot]` populated;
- latest `committed_identities` for that slot populated;
- no `runtime.committed` sidecar record for that slot.

`owner.snapshot()` accepts that state, but `_stage_runtime()` rejects it because the slot necessarily exists in `by_slot`.

This is a production resume blocker because checkpoints can be taken at an IDLE window boundary where one or more slots have just terminalized and have not yet rebound.

### Acceptance condition

Validate terminal carry against the staged sidecar-record slots, not against all scheduler committed identities (semantically `terminal_slots ∩ records == ∅`). Add a round-trip fixture that:

1. commits a terminal identity;
2. resolves the window to IDLE;
3. confirms `owner.snapshot()` succeeds with terminal slot present and sidecar record absent;
4. loads that snapshot into a fresh driver successfully;
5. re-snapshots successfully and confirms the terminal slot still has no carry.

## HIGH-2 — sidecar fast state can be silently re-tagged to the wrong identity

Location: `_stage_runtime`, loop over `runtime.committed` around lines 407-415.

Current code looks up the latest scheduler identity by `slot_id` and then stores the checkpoint fast state under that canonical identity, but it never verifies that the serialized sidecar identity is **value-equal** to that canonical scheduler identity.

A malformed or internally inconsistent checkpoint can therefore contain:

- scheduler latest identity = `(slot=4, episode=A, cursor=7, ...)`;
- `runtime.committed` identity = `(slot=4, episode=B, cursor=2, ...)` with B's fast state.

The current staging path takes B's `fast_state`, re-tags it as A's canonical identity, and can pass subsequent object-identity checks. That is exactly the kind of silent half-right restore the v0.4 design says must fail closed.

### Acceptance condition

Before canonicalizing the sidecar record, require the checkpoint sidecar identity to match the scheduler canonical identity by value (all `SegmentIdentity` fields), then use the scheduler object for the stored identity so the downstream `is` invariant also holds. Add a mutation fixture that changes episode/cursor/category/source/end on `runtime.committed` while leaving scheduler state unchanged and asserts rejection with zero live mutation.

## EVIDENCE-1 — retained GPU witness does not yet prove all frozen criterion-4 assertions

The repository records a useful real witness: save at iter 3, kill, auto-resume at iter 3, continue from iter 4 to iter 6, save a complete DCP including `dataloader/rank_0.pkl`. This closes the old question of whether the DCP dataloader seam actually participates in a real resume.

However resume-design §6 criterion 4 requires all of:

1. no `cannot resume` failure;
2. resumed first-window `SegmentIdentity` sequence equals the uninterrupted-control corresponding window;
3. `cumulative_valid_consumer_exposure` is continuous and not reset.

The retained repository evidence I can verify records the iteration/checkpoint continuation and finite losses, but not the exact uninterrupted-control identity-sequence comparison or before/after exposure values. Those must be retained as a machine-checkable or explicit logged witness before closure.

## Accepted parts

- DCP callback/dataloader seam and pre-attach pending state;
- source/catalog/plan identity checks;
- frontier cross-field validation;
- two-phase staging-before-apply architecture;
- zero-live-mutation rejection fixtures already added;
- scheduler rebuild and canonical identity rebinding direction;
- real save/kill/auto-resume path is demonstrably exercised.

## Scope

No `APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME` token is issued on this pair.
Gate 3 design approval is independent and may proceed to implementation, but any Gate-3 implementation that depends on resume across terminal/reuse boundaries must incorporate the Gate-2 fixes above before claiming resume closure.
