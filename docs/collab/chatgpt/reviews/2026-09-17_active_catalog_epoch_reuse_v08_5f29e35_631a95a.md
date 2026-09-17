# ChatGPT independent review — ACTIVE-CATALOG-EPOCH-REUSE v0.8

## Formal target

- Gate: `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`
- formal root: `5f29e356f5b2b756f035b70433827e307dcc156b`
- exact child/Gitlink: `631a95af0aff28b03a93df320c179bfb9d10f607`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md` v0.8
- prior reviewed pair: `05fbd7780d034eab59a658e313496a0ed104657f / 525f5066393cba044f00f1104b83f5eb424a9c49`
- review type: fresh design/Evidence review; formal root and child changed.

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md:190)`

Blockers: **2 HIGH + 1 MEDIUM**.

## Prior findings lifecycle

- v0.6 chronology reset HIGH: **CLOSED by direction** — non-terminal slots now continue exact episode/cursor/fast-state chronology.
- v0.6 cumulative-exposure authority HIGH: **CLOSED by direction** — `cumulative_valid_consumer_exposure` remains the selection authority.
- v0.7 single global queue identity cannot represent divergent per-slot epochs: **partially addressed, not closed** — v0.8 chooses driver `_slot_epoch` Option B, but the authority relationship conflicts with the still-frozen upstream queue contract.
- v0.7 stale global-reset probe evidence: **CLOSED as a stale-evidence issue** — the probe was rewritten for per-slot rollover. The new probe, however, exposes a separate target-closure failure described below.

## HIGH-1 — Option B bypasses an un-superseded frozen queue authority while simultaneously claiming it remains frozen

**Location:** v0.8 §3.3 / §4.2.

### Root cause

v0.8 states all of the following at once:

1. scheduler `queue_seed` / `queue_epoch` / `queue_permutation` and frozen `QueueEpochSnapshot` remain part of the frozen contract;
2. for active-route per-slot reuse they are declared **non-authoritative**;
3. driver `_slot_epoch[slot]` becomes the real per-slot queue identity authority;
4. driver reorders `_by_slot` by calling `queue_permutation(...)` directly and **bypasses `configure_queue`**.

That is not merely a storage detail. The approved upstream `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md` §5 freezes a global `QueueEpochSnapshot` and a safe rollover rule: epoch advances only after the current catalog is admitted and no bound non-terminal slot remains, specifically to prevent re-admission while an old-epoch active episode still exists.

v0.8 intentionally permits terminal slots to enter later per-slot epochs while other slots continue an older episode/epoch, and intentionally makes the frozen queue snapshot non-authoritative for that behavior. The document says this is a “bypass” while also saying the old queue contract is not abandoned. Those two claims cannot both be true.

### Why current evidence does not close it

The planning probe directly mutates driver/scheduler containers according to the new per-slot reference algorithm. It proves that the proposed algorithm can be simulated; it does not establish that the algorithm is authorized by the still-frozen upstream queue authority.

### Acceptance

Choose one coherent authority path:

**A. Explicit active-route queue refreeze/supersession.** State exactly which clauses of canonical scheduler design v0.2 §5 are superseded for the active route; define driver `_slot_epoch` as the canonical queue-identity authority; define the typed production lifecycle for per-slot release/reuse, persistence, resume, and guard cleanup; update the authority chain and acceptance tests accordingly. Do not simultaneously describe the superseded global queue snapshot as still authoritative for this route.

or

**B. Conform to the existing global QueueEpochSnapshot authority.** Do not re-admit a terminal slot into a new queue epoch while any old-epoch slot remains bound/non-terminal; solve the fixed-window capacity issue without bypassing the global queue authority.

If A is chosen, this Gate must be explicitly framed as the active-route queue-semantics refreeze (or depend on the already-planned scheduler-semantics refreeze) rather than claiming no scheduler authority change.

## HIGH-2 — the Gate's own capacity PASS criterion is currently false, while the probe still reports PASS

**Location:** v0.8 §6 criterion 2 and §10.3; `tools/g0/probe_epoch_reuse_planning.py`; `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json`.

### Direct evidence

The design's §6 criterion 2 still requires continuous planning of **≥5040 windows** (enough to cover the 5000-step target) without raise.

The committed v0.8 artifact reports:

- `criterion2_target_windows = 5040`
- `windows_total = 3704`
- `criterion2_meets_target = false`
- top-level `result = "PASS"`

The probe source explains why: top-level PASS checks only order mismatches, purity, and `window_index == windows_total`; it does **not** include `criterion2_meets_target`, and the program returns exit code 0 unconditionally.

The v0.8 prose nevertheless says “判据 2 成立” and estimates that approximately 61 rollover boundaries should reach 5000 steps. An estimate is not the required direct capacity witness.

### Why this matters

This Gate exists to remove the finite-catalog capacity blocker for a 5000-step run. Demonstrating 3704 windows and extrapolating to ~61 boundaries does not prove the route reaches 5000/5040 without encountering the newly documented all-non-terminal fail-closed boundary or another guard failure.

### Acceptance

- make probe top-level `result` and process exit status fail when any mandatory criterion, including criterion 2, is false;
- run the per-slot state machine until `windows_total >= 5040` (or an explicitly refrozen equivalent ≥5000 target), not merely a fixed 45 boundary count;
- retain direct evidence that no all-non-terminal dead-end/raise occurs before the target;
- update §10.3 only from the new target-reaching run;
- if the route cannot reach the target, mark this Gate BLOCKED rather than PASS.

Do not lower criterion 2 to merely “>112 windows” while the Gate is still claimed to close the 5000-step catalog-capacity blocker.

## MEDIUM-1 — Option B text and resume acceptance criteria remain internally inconsistent

**Location:** v0.8 §5 / §6 criteria 7 and 10.

Option B says scheduler `queue_epoch`/`queue_permutation` are non-authoritative for per-slot reuse and resume consistency is determined by `_slot_epoch` plus deterministic replay. Yet retained text still says `_slot_epoch` and scheduler queue epoch/permutation “都必须” be checkpointed for resume semantics and criterion 7 asks for `_slot_epoch` with `queue_epoch`/`queue_permutation` consistent restoration.

That wording leaves two possible authorities after restore — exactly what Option B was introduced to eliminate.

### Acceptance

After HIGH-1 is resolved, rewrite §5/§6 so there is exactly one queue-identity authority and one resume witness. If Option B is explicitly refrozen, the witness must bind the derived per-slot ordering to persisted/recomputed seed + `_slot_epoch` + catalog identity, while scheduler global queue fields are clearly either compatibility metadata with specified invariant values or removed from the active-route acceptance condition.

## Scope conclusion

v0.8 improves chronology handling and provides a more relevant per-slot planning simulation, but it is not yet an approvable implementation design.

`D8b` remains **BLOCKED** independently by the design's own scheduler-semantics gate and by the unresolved capacity/authority blockers above.

No implementation authorization is granted for this formal pair. Any remediation root and/or child is a new formal pair and requires fresh review.
