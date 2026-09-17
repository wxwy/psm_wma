# ChatGPT Independent Review — ACTIVE-ROUTE-RESUME implementation closure

- Gate: `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`
- current formal root reviewed: `ffeb6aa2bc9ae1f5e5bbf49ae6aa9f909853353c`
- actual child/Gitlink: `7bb507f0ce2a3a89e78c1c10ae465d0e5907e215`
- supersedes closure request pair `eb15c3e5 / 7ca3b20` because the current tree contains an additional resume-closure remediation commit
- review type: fresh implementation/evidence closure review
- verdict: **REQUEST_CHANGES / NOT CLOSED**

## What is accepted

The current implementation correctly follows the approved v0.4 design in the major architectural points:

- DCP state is exposed through the launch callback's existing `dataloader` component rather than a new top-level key.
- load-before-`on_train_start` is handled with `_pending_resume_state`.
- source/catalog/plan identities are fail-closed.
- scheduler state is rebuilt and rebound to the existing runtime owner.
- sidecar identities are rebound to scheduler canonical identity objects.
- scheduler snapshot lists are trimmed only in persisted output, not in the live runtime.
- latest child `7bb507f` adds the missing window-index upper-bound check and several CPU fixtures, including ambiguous/unrebuildable slot binding and runtime identity round-trip.

These are meaningful improvements and the implementation is close to closure.

## HIGH-1 — mandatory GPU save → kill → auto-resume continuity evidence is still absent

The approved v0.4 design made the end-to-end GPU resume test an explicit PASS criterion, not an optional follow-up. The current Inbox itself states that criterion 4 has not been run.

CPU round-trip tests cannot prove the actual DCP/trainer ordering, on-disk rank-local dataloader pickle path, callback discovery, process restart, optimizer/trainer iteration alignment, or the first post-resume window sequence.

### Required evidence

Run the frozen short GPU resume scenario and retain reproducible evidence for the current implementation pair:

1. uninterrupted reference run through at least one checkpoint boundary;
2. interrupted run saves at the same boundary;
3. terminate process after checkpoint is complete;
4. auto-resume from that checkpoint;
5. verify the first resumed window `SegmentIdentity` sequence exactly matches the corresponding uninterrupted window;
6. verify `cumulative_valid_consumer_exposure`, driver `_stream_index` / `_active_cursor` / `_window_index`, and optimizer/trainer iteration continue rather than reset;
7. verify the `dataloader/rank_<rank>.pkl` state was actually written and loaded;
8. retain command, checkpoint path, before/after identities and PASS summary.

Until this is executed on the real checkpoint path, `APPROVE_TO_CLOSE` is not justified.

## MEDIUM-1 — restored driver frontier lacks cross-field consistency validation

`load_state_dict()` uniquely rebuilds `active_stream`, but then restores `stream_index` and `active_cursor` as independent dictionaries without checking that they describe the same reconstructed stream frontier.

A state can therefore pass source/catalog/plan identity checks while containing, for a slot:

- an `active_stream` that matches one catalog entry,
- a `stream_index` pointing at another catalog position, or
- an `active_cursor` outside the valid block range for that stream.

`_peek_block()` subsequently trusts those fields. A mismatched `stream_index` can silently skip/replay the successor after the current episode terminates; an invalid cursor can silently alter continuation behavior.

### Required change

Before applying the restored dictionaries, fail closed per slot:

- key sets of `stream_index`, `active_stream`, and `active_cursor` must be valid for the catalog geometry;
- for every active slot, `stream_index[slot]` must equal the unique position of the reconstructed `active_stream` in `_by_slot[slot]`;
- `0 <= active_cursor[slot] < producer.block_count(active_stream[slot])`;
- slots with no active stream must have a defined, valid catalog index/frontier state consistent with `_peek_block` semantics;
- scheduler `stable_slots` / `terminal_slots` latest identity must agree with the restored driver episode/cursor frontier where applicable.

Add mutation fixtures for wrong position and wrong cursor so these fail closed instead of reaching the next training window.

## Closure status

Current implementation is **not rejected wholesale**; its architecture is aligned with the approved design. But this Gate cannot be closed until the cross-field frontier check is added and the mandatory real GPU/DCP resume criterion passes on the resulting exact pair.

Canonical verdict: `REQUEST_CHANGES` / `DO_NOT_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`.