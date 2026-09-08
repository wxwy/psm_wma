# ChatGPT independent review — R09-B TTT v0.3.5 canonical CPU/static implementation remediation

**Date:** 2026-09-08

**Gate:** `G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION`

**Formal target:**
- root implementation SHA: `f0d6c69aae38a7d1b06d06bc1f5c7614d7f440db`
- child/Gitlink SHA: `d7eb51af226888d3d1e49b609b2fe187a73e8143`
- prior formal pair: root `c51fcdce1c5b0330d7c93ecb3304eeb6d3c0904d` / child `f14a0185976cc94fde1be73028417893b68d5ae2`
- approved implementation-design baseline: root `1f6c0bad0faa4aabae1c71b01738ad95a4ea902c` / child `80aec090688e3c710c41e1dfd86b6500773db2c7`

## Verdict

`REQUEST_CHANGES`

This is a fresh incremental review because the child formal SHA changed from `f14a018...` to `d7eb51a...`. The prior ChatGPT approval for `c51fcdc/f14a018` is not inherited.

The remediation correctly closes the previously reported global-terminal isolation defect: terminal state is now per-slot, another slot can continue after one slot terminates, slot continuity rejects category/episode/source changes and noncontiguous cursor, and `terminal_slots` participates in snapshot/rebuild. However the new rebind implementation introduces a scheduler-authority violation that prevents Gate closure.

## Blocking finding

### HIGH — `terminal_rebind()` manufactures an admitted `cursor=0` replacement and bypasses weighted-deficit admission / GA admission chronology

**Files:**
- `cosmos_framework/model/generator/mot/local_memory_segment.py:300-310`
- `cosmos_framework/model/generator/mot/local_memory_segment_test.py:130-133`

**Root cause:**

After verifying the old terminal identity and `replacement.cursor == 0`, `terminal_rebind()` deletes the terminal lock, writes the caller-provided replacement directly into `stable_slots`, and appends it directly to `admission_order`. The new test then calls `commit(replacement, 1)` without ever passing that fresh episode through `RankLocalSegmentScheduler.admit()`.

That means an arbitrary configured-category replacement supplied by the caller is treated as scheduler-admitted even though the scheduler's weighted-deficit selection was never run. After rebind, the same `cursor=0` replacement also cannot subsequently pass `admit()`, because `_is_admissible()` sees it as the existing stable identity and only accepts `cursor == previous.cursor + 1`.

This conflicts with the frozen scheduler contract:

- v0.3.5 addendum §3.2 freezes that once a slot becomes free, **before the next segment the WeightedDeficitScheduler chooses the next category from cumulative valid-consumer exposure**, then takes a fresh episode from that category's queue starting at step0;
- v0.3.9 CPU/static implementation design v0.2 §4 makes `RankLocalSegmentScheduler` the unique rank-local scheduling owner and freezes its weighted-deficit admission rule, admission order and exposure state;
- the current review request explicitly asks to verify legal admission/commit GA ordering after terminal rebind.

The current code therefore allows terminal episode boundaries to bypass the configured target distribution and lets a fresh episode become commit-eligible without the canonical admission path.

**Acceptance:**

Preserve the new per-slot terminal isolation, but make the fresh step0 episode pass through the scheduler's canonical weighted-deficit admission authority before it can become commit-eligible. One acceptable shape is:

1. terminal completion marks only that slot terminal/free;
2. rebind clears the terminal slot (or records a free-slot transition) without appending an arbitrary replacement to `admission_order`;
3. the next `admit(candidates)` runs the existing weighted-deficit rule, selects a configured category/episode, requires `cursor=0`, and is the only path that appends the fresh replacement to `admission_order` / binds it as the stable slot;
4. `commit()` still requires that admitted identity and the transaction/GA order after successful backward.

An equivalent implementation is acceptable if `terminal_rebind()` itself becomes the unique weighted-deficit chooser over a candidate set and returns the chosen identity; it must not accept a preselected arbitrary replacement and silently mark it admitted.

Add CPU fixtures that prove:
- one terminal slot does not block another slot;
- after terminal, a caller-provided arbitrary `cursor=0` identity cannot be directly committed merely by rebind;
- the fresh replacement is selected through weighted-deficit admission and starts at cursor0;
- the fresh replacement participates in the frozen GA member order before commit;
- snapshot/rebuild preserves the terminal/free/rebound state without opening a bypass.

## Closed items in this delta

- **CLOSED:** global `stream_closed` no longer freezes unrelated slots.
- **CLOSED:** terminal state is exact per-slot identity and is serialized/rebuilt.
- **CLOSED:** continued slot admission rejects category/episode/source switches and noncontiguous cursors.
- **CLOSED:** terminal rebind requires the exact terminal slot and `cursor=0`.
- **Evidence observed from the request:** related CPU pytest is reported as `50 passed` with existing unknown `L0` marker warnings; related `py_compile` and child/root `git diff --check` are reported PASS. This review did not independently execute those commands, and passing tests do not override the scheduler-authority blocker above.

No production adapter/dataset/trainer/model-forward/`local_memory2llm`/config/optimizer/checkpoint/manifest/`ttt_lifecycle.py` changes, real model/data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, preflight/staging/record/refreeze/export/compose, P4/P5, B2-T, LIBERO4IN1 or later Gate actions are authorized by this verdict.

This verdict binds only formal pair `f0d6c69aae38a7d1b06d06bc1f5c7614d7f440db` + `d7eb51af226888d3d1e49b609b2fe187a73e8143`. Review/bookkeeping commits do not change the formal implementation target.
