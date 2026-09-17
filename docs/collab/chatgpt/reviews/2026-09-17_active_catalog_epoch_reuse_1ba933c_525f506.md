# ChatGPT formal review — ACTIVE-CATALOG-EPOCH-REUSE v0.6

Status: **REQUEST_CHANGES**

Formal pair reviewed:
- root: `1ba933c15375f3d77341b69b5c707f81ce5a9904`
- child/Gitlink: `525f5066393cba044f00f1104b83f5eb424a9c49`
- design blob: `6a4c0ac69e89d37fcb718181159a7a366fa68784`
- Gate: `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`

## Project-level judgment

The capacity problem is real: the active catalog supports only 112 full 128-member windows before the remaining 94 blocks cannot fill another optimizer window, while the planned run is 5000 steps. A reuse mechanism is therefore necessary before D8b.

However, v0.6 solves capacity by changing two already-frozen Local-Memory semantics: episode continuity/reset authority and the weighted-deficit exposure authority. Those are not bookkeeping details. They determine the training distribution and the TTT fast-state chronology, so they cannot be changed inside a catalog-capacity Gate without an explicit refreeze.

## Current blockers

### HIGH-1 — Global epoch rollover rewinds a non-terminal episode and discards its fast state

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md:166-170,196-210,216-235`

**Root cause:** v0.6 treats the inability to fill the next 128-member window as authority to globally reset every slot: `_stream_index` goes to zero, `_active_stream` / `_active_cursor` are cleared, `stable_slots` / `terminal_slots` / admission/commit guards are cleared, and every sidecar carry is discarded. The design explicitly acknowledges that the boundary can occur while a slot is mid-episode, and then restarts that episode from cursor 0 in the next catalog epoch.

This is not just a dataset-epoch implementation detail. The frozen Local-Memory chronology says a stable slot keeps the same `category / episode_id`, advances cursor strictly continuously **until `training_stream_end`**, and only then becomes free. The fail-closed contract also requires a continued episode to use `start_step_new == end_step_prev + 1`, keep the same episode/slot ownership, and consume the detached numeric `state_out`; a continued episode must not clone/reset to `W_bar_0`.

Relevant frozen authority: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md:217-231,251-267`.

The v0.6 rationale that a partial episode may be abandoned and then “replayed completely from the beginning” does not satisfy that contract. The prefix already contributed optimizer updates in the previous catalog epoch; restarting the same episode at cursor 0 with sidecar state discarded is a chronology reset without `training_stream_end`.

**Acceptance condition:** redesign the epoch/cycle transition so a non-terminal stable slot is never rewound or reset. At the 112-window boundary, any slot that is still inside an episode must preserve the exact episode identity, next cursor and detached fast state until terminal completion. Add a boundary fixture matching the observed `stable_but_not_terminal` case and prove that the next consumption of that slot is the exact canonical continuation (`cursor + 1`, same episode, same slot, preserved state). If the project intentionally wants catalog-epoch boundaries to become a new legal fast-state reset authority, that is a frozen chronology change and requires a separate explicit refreeze/design Gate before this Gate can proceed.

### HIGH-2 — v0.6 replaces the frozen cumulative-exposure scheduling authority with a per-epoch controller

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md:188-210,330-365`

**Root cause:** v0.6 changes `freeze_window` so `observed` no longer comes from `scheduler.cumulative_valid_consumer_exposure`; instead it comes from a new `_epoch_observed` counter that resets every catalog epoch, while cumulative exposure becomes “report-only”. This was introduced to make later epochs resemble epoch 0.

The frozen scheduler contract says that after an episode ends, weighted-deficit scheduling selects the next category according to **cumulative valid-consumer exposure** and that balance is a long-term soft target. See `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md:217-231`.

Therefore this is a scheduler-authority change, not a neutral catalog-reuse repair. It changes which category is selected for most of the 5000-step run. The fact that the previous cumulative behavior produced an undesirable regime does not authorize silently replacing the frozen controller inside this Gate.

**Acceptance condition:** either keep cumulative valid-consumer exposure as the selection authority while solving reuse/continuity, or open an explicit scheduler-semantics refreeze that justifies the move to per-epoch exposure and defines new matched acceptance/evidence. The current Gate must not claim both that the v0.3.5 cumulative-exposure contract remains frozen and that cumulative exposure is report-only.

## Consequence

Because both blockers affect training semantics, this is not an Evidence-only rejection. The design itself must change before implementation. The existing probes are useful evidence for the capacity/regime problem, but they do not validate the proposed semantic override.

D8b long training remains blocked. Slot Rotation and Resume may proceed independently within their own approved scopes; neither approval closes this Gate.

## Verdict

`REQUEST_CHANGES`

No `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE` token is granted for this formal pair.
