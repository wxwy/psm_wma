# ChatGPT independent review — C6 runtime integration implementation @ 0437429

**Gate**: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-IMPLEMENTATION`  
**Formal target**: root implementation `0437429344f4c80f7ffea5621fb1cdcd23b4c235`; child/Gitlink `f0cb6451ed7772ffb7aa0dfe9f024a0fb1aaa63e`  
**Observed V2 request/bookkeeping HEAD at review start**: `74bbc1e87df35bc607334a29b9639d326ca2e963`  
**Frozen C6 design authority**: `574d28750883d9e69bd03aa39cc3640646190dfa` + child `0e904111c189bba46105cfe79c61301f4759c796`

## Verdict

`REQUEST_CHANGES`

## Scope accepted

- Child delta `0e904111... -> f0cb645...` is exactly one commit adding only `c6_runtime_adapter.py` and `c6_runtime_adapter_test.py`; no active Cosmos runtime file changed.
- Root formal delta only carries status/Gitlink/review-bookkeeping plus an unrelated collaboration pacing doc change; no config/optimizer/checkpoint/attention/packing/GPU/training scope drift was found.
- Submitted repository evidence is C5A+C6 CPU `41 passed`, `py_compile`, and child/root `git diff --check` PASS; those commands were not independently rerun in this review.

## Blocking findings

1. **HIGH — C6 exposes direct `commit()` and therefore bypasses the frozen C5A segment-length / terminal closure grammar.**
   - Implementation: `cosmos_framework/model/generator/mot/c6_runtime_adapter.py:40-41` delegates public `commit()` straight to `C5AOwnerSegmentCPU.commit()` and exposes no `finish(owner, terminal=...)` equivalent.
   - Delegated authority: `c5a_owner_segment.py:243-259` `commit()` checks only `BACKWARD_OK`; the actual `N` / terminal-remainder grammar lives in `c5a_owner_segment.py:316-336` `finish()`, which enforces full non-terminal `N`, terminal `r=0`, `0<r<=N`, and terminal reset.
   - Frozen contract: C6 v0.2 §3 requires the full segment transaction and `N∈{1,3,16}` / terminal matrix and explicitly forbids degeneration to per-timestep N=1 commits; v0.4 inherits that clause unchanged.
   - **Root cause**: the adapter delegates the lower-level commit primitive instead of the C5A segment-closing authority, so a caller can commit a short non-terminal segment after one backward without ever passing the frozen length/terminal checks.
   - **Acceptance**: make the public C6 closure path delegate the C5A `finish(owner, terminal)` grammar (or an exactly equivalent single authority path) and ensure raw `commit()` cannot bypass it; add public-adapter fixtures for N=1/3/16, non-terminal short rejection, terminal `r=0`, `0<r<N`, `r=N`, exactly one backward/commit, and terminal epoch reset.

2. **HIGH — frozen `source_identity` ↔ segment coordinate mapping is not implemented; C6 accepts contradictory segment metadata and discards it.**
   - Implementation: `c6_runtime_adapter.py:23-26` checks only non-empty `segment_id` / non-negative `row_index`, then discards both and forwards the capability unchanged to C5A.
   - Tests: `c6_runtime_adapter_test.py:20-22,31-32,45-47,63-66` repeatedly issue `source_identity="seg"` while passing different `segment_id` values such as `s0` / `s1`; those mismatches are accepted.
   - Frozen contract: C6 v0.2 §2 freezes `source_identity = segment_id + ":" + timestep`; v0.4 changes only the `source_timestep` coordinate and explicitly keeps `segment_id` / segment-local row index as separate grouping/logging coordinates.
   - **Root cause**: the new adapter API adds segment coordinates but never binds them to the trusted capability identity, so the frozen production-boundary mapping is unenforced at the seam.
   - **Acceptance**: enforce the exact frozen mapping between the trusted capability `source_identity` and the supplied segment coordinate, while keeping owner-epoch `source_timestep` solely under C5A chronology authority; add positive/mismatch fixtures and prove segment-local row indexing can restart at 0 without resetting owner chronology.

3. **HIGH — the 5 C6 fixtures do not satisfy the frozen adapter-level acceptance matrix, and the batch witness test uses private state instead of the public adapter output.**
   - Evidence: `c6_runtime_adapter_test.py:20-70` covers only basic shape, two N=1 segments, one pending-reset path, no-pending done/reset, and a batch shape smoke.
   - The batch test at `c6_runtime_adapter_test.py:67-70` only asserts output shape, then constructs the loss through private `adapter._c5a._pending_by_owner[...]` witnesses instead of the public `materialize_many()` output. This does not prove owner-row permutation equivalence or the public output→outer-loss graph path.
   - Missing C6-seam evidence includes: N=3/N=16 and terminal matrix; cross-owner/skip/duplicate/changed-byte/row-mismatch fail-closed; successful fresh-epoch same owner/identity/timestep=0 re-admission after reset; pending `done` rejection and snapshot invariance; unrelated/grad-free/partial-owner loss rejection; abort/backward-failure rollback; Local-disabled parity; and public N>1 shape/gradient behavior.
   - Frozen contract: v0.2 §4/§6 requires segment-loss witness coverage and the full synthetic matrix at the adapter seam; v0.4 additionally requires two consecutive segments, reset/new-epoch retry, and cross-owner/skip/duplicate/changed-byte/permutation/row-mismatch fail-closed behavior.
   - **Acceptance**: add direct public-API C6 fixtures for the frozen matrix, without private `_c5a` witness access; prove actual owner-keyed values under both permutations, row mismatch rejection, public output graph reachability to every required owner, and exact rollback/snapshot semantics. Re-run the C5A regression plus the expanded C6 selector and report exact counts.

## Governance / authority note

At review start, the detailed ChatGPT v0.4 design approval exists, but the live canonical `CODEX_INBOX.md` still shows the v0.4 design section as `Awaiting review` rather than carrying the ChatGPT approval handoff. Under the project rule, that means the earlier ChatGPT design verdict was technical-but-not-formal at the moment implementation began. This review bookkeeping will append the missing v0.4 ChatGPT approval entry before/with this implementation verdict so the canonical record is repaired; the bookkeeping SHA does not replace either formal target.

## Scope after this verdict

Allowed remediation is limited to the C6 test-only synthetic adapter + adjacent CPU tests and root status/ledger/review bookkeeping. Do not modify active Cosmos runtime, config/optimizer/checkpoint schema or identity, attention/packing, trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1.

A new root implementation SHA and/or child Gitlink SHA requires fresh same-SHA implementation review. Until then, C6 is not closed and no later runtime/GPU/training Gate is authorized.
