# Independent Design Review — R09-B TTT v0.3.2 C5A chronology-owner / segment / backward

- Gate: `G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-DESIGN`
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5A_CHRONOLOGY_OWNER_SEGMENT_CPU`
- Formal root design SHA: `b793e391f3e57d0b140e0b6b6e33da08509fd844`
- Child/Gitlink: `6de8f2056c62cb10c89791d70335a44a6ab232fc`
- Request/ledger SHA: `679f615109082c2142d4b28489636f461b43fcd5`
- Remote `V2` HEAD resolved at review start/final pre-write check: `ff59d59c31e280eef290aadb30c80800aa4bf266` (status/ledger only; not the design SHA under verdict)
- Closed predecessor: C5 transition implementation `0c5b3d253a7a06bff804f41fc8915e1063ae5ab3` / child `6de8f2056c62cb10c89791d70335a44a6ab232fc`

## Repository-state / evidence note

A literal shell `git fetch origin V2` was attempted first, but this environment has no usable local checkout and shell network access to GitHub failed. I therefore resolved the remote `V2` branch and all reviewed objects through the connected GitHub API. I do not represent the shell fetch as successful.

The formal target `b793e391...` is docs-only: it adds the 70-line C5A design and updates `SESSION.md` / `TODO.md`; it does not modify the child Gitlink or any runtime code. Current `V2` is two bookkeeping/request commits ahead (`679f615...`, `ff59d59...`), neither of which replaces the formal design target. GitHub exposes no CI status for `b793e391...`; the submitted `git diff --check PASS` is repository-recorded evidence and was not independently rerun here.

## Verdict

`REQUEST_CHANGES`

The direction is appropriate—C5A is the correct place to own chronology, replay, state ownership and segment/backward atomicity—but the current v0.2 design does not yet define a closed state machine that can satisfy its own fail/rollback/replay guarantees. Three design blockers and one gradient-semantics issue remain.

## HIGH-1 — committed owner state and pending segment state are not separated, so strict next-step admission and rollback cannot both hold

**File:** `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.2_2026-09-04.md:16-24,43-45,50-52,56`

### Root cause

The owner record has only one `state`, one `episode_step`, one `segment_id/segment_offset`. A new transition must satisfy `episode_step == last_step + 1`, yet the design also says owner `state/ledger` are submitted only after the *complete segment* has executed its single outer backward successfully.

For `N>1` these rules are mutually incomplete:

- If `last_step`, segment cursor and fast state are advanced in the owner record as each admitted transition calls C5, then an exception or failed backward after transition `k<N` has already partially advanced the authoritative owner, violating the promised abort/no-partial-advance rule.
- If the authoritative owner is not advanced until the final backward succeeds, transition 2 cannot satisfy `last_step + 1` against the still-committed cursor, and there is no defined updated fast state from which transition 2 should continue.
- The replay rule also names only an “already completed key”; it does not distinguish a committed replay from a retry of a transition already materialized in the current uncommitted segment.
- Line 50 says the collecting buffer stores C5 output/state-carry, while line 52 forbids carrying an undetached graph across immediate microbatches. The design does not freeze whether raw transitions are collected first and graph-materialized once, or whether C5 is run incrementally while the segment is still pending.

### Required acceptance fix

Freeze an explicit two-phase/transactional owner state machine before implementation. At minimum define:

1. **Committed record**: committed fast state, committed `last_step`, committed segment cursor/epoch and committed replay ledger/cache.
2. **Pending segment transaction**: base snapshot/reference to the committed record plus its own pending fast state, pending step/offset cursor, pending identity/digest ledger and pending replay cache. C5 may mutate only this pending state before commit.
3. Admission while a segment is open compares against the **pending** cursor; opening a segment starts from the exact committed state/cursor. Define deterministic `segment_id` and `segment_offset` progression.
4. Exact retry of a transition already materialized in the pending segment must hit the pending cache and perform zero additional C5 writes; committed replay and pending replay must be distinguishable.
5. Define one materialization lifecycle. A clean option is `COLLECT_RAW -> MATERIALIZE_PENDING -> BACKWARD_OK -> COMMIT`, with C5/autograd graph creation occurring only in `MATERIALIZE_PENDING`; if incremental graph materialization is intended instead, explicitly prove how it does not cross the forbidden microbatch boundary.
6. Successful outer backward atomically promotes the pending terminal state/cursors/ledger into the committed record exactly once. `abort`, exception, failed backward, duplicate backward or duplicate commit must leave the committed record byte/numerically unchanged and dispose of all pending graph/cache/state.
7. Add future CPU acceptance for `N=3` failures before materialization, during materialization and during/after backward, plus exact pending retry, proving zero partial committed-state/cursor/ledger advancement.

## HIGH-2 — causal/provenance admission is caller-asserted rather than authority-bound, and the digest contract is inconsistent with per-row ownership

**File:** `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.2_2026-09-04.md:27,31-39,62-67`

### Root cause

The design intends C5A to reject future/GT/incomplete evidence, but its envelope contains caller-visible booleans `evidence_complete` and `causal_visible` plus an `evidence_digest`. “Read-only” does not establish provenance authority: a caller can construct a digest over forbidden evidence and set both booleans true unless the design freezes a trusted producer/capability or an independently verifiable source binding.

There is also a concrete schema mismatch: the envelope does not list `source_timestep`, while line 39 says the digest covers source timestep and the acceptance matrix requires missing/mismatched source timestep to be rejected. C5A cannot independently validate a source-timestep claim that is not present/bound by an authority.

Finally, the admission key is explicitly **one row / one logical owner**, but line 39 defines the digest over the complete `[B,256]` batch. That makes a logical owner’s replay identity depend on unrelated rows and batch order, conflicting with row-independent owner identity and the batch-permutation acceptance requirement.

### Required acceptance fix

Freeze the provenance contract, not just boolean fields:

1. Add an explicit immutable `source_timestep` (and any required source transition identity) to the admission schema.
2. Specify the trusted authority that creates/adopts the admission envelope—e.g. an upstream R08 completed-causal-evidence materializer or an opaque capability/token that C5A can verify. External callers must not be able to self-attest `causal_visible=true` / `evidence_complete=true` and thereby gain admission.
3. Either define a canonical verifiable digest algorithm/serialization or freeze an opaque upstream digest authority. State exactly what is bound: owner/epoch/episode step, source timestep, per-owner evidence bytes/shape/dtype and any provenance discriminator required to distinguish allowed causal evidence from history/future/GT inputs.
4. Make the digest **per logical owner row** (`[256]`) or explicitly define an equivalent owner-local canonicalization. Then freeze how owner records are gathered into a batched C5 call and scattered back by identity, not row index.
5. A pure batch-row permutation with the same owner envelopes following their evidence must preserve each owner’s identity/result. A permutation that mismatches owner/envelope/state must fail before C5.
6. Add hostile fixtures that forge booleans/digest/source metadata and prove the untrusted form cannot be admitted.

If C5A cannot itself verify future/GT provenance and must rely on an upstream authority, narrow the C5A claim accordingly and freeze that upstream authority as a hard precondition rather than pretending the bare envelope can prove provenance.

## HIGH-3 — terminal remainder and done/reset ordering are referenced but never defined

**File:** `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.2_2026-09-04.md:46,50-52,65-66`

### Root cause

Line 50 allows the final segment to end under a “design-defined terminal remainder rule”, and the acceptance matrix requires that rule to be tested, but no terminal-remainder rule exists in the document. At the same time line 46 says `done/reset` immediately creates a new epoch, clears the old segment ledger and starts from W0.

For a terminal episode with `0 < remainder < N`, those statements leave ordering undefined: clearing the old epoch/ledger before remainder backward loses the final segment; creating the new epoch before old remainder commit exposes new owner state even if the old remainder backward fails; committing the remainder after the epoch was cleared has no defined target.

### Required acceptance fix

Freeze the exact terminal state machine:

1. What trusted terminal condition may close a short segment; non-terminal short segments must be explicitly allowed or rejected.
2. Whether an empty remainder is legal and whether it causes any backward.
3. The old epoch remains the transaction owner until the terminal remainder is materialized and its one outer backward/commit succeeds (or specify a different, equally atomic ordering).
4. On successful terminal commit, define final state/ledger handling, detach/reset semantics, then the exact point at which `owner_epoch` increments and the new W0/step/segment cursor becomes visible.
5. On terminal materialization/backward failure, define retry/abort semantics and prove no new epoch or partial old-epoch commit becomes visible.
6. Freeze `segment_id/segment_offset` values for the terminal remainder and the first segment of the next epoch.
7. Add `N=1`, exact-N terminal, `<N` terminal remainder, terminal failure/retry and non-terminal-short-segment fixtures.

## MEDIUM-1 — outer `backward(create_graph=True)` unnecessarily conflates inner TTT higher-order differentiation with outer optimizer backward

**File:** `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.2_2026-09-04.md:52,68`

### Root cause

C5 needs higher-order construction **inside the TTT update** so the final task loss can reach the slow Q/K/V/slot/W0 parameters through the fast-weight update. That requirement is already represented by the C5 core/transition `create_graph=True` path. It does not imply that the *outer* task loss must itself call `backward(create_graph=True)`.

Mandating `loss.backward(create_graph=True)` builds a graph of the outer gradients and retains substantially more graph/memory; that is only required if a later derivative of the outer gradients is intentionally taken. No such third-order/differentiable-optimizer objective is frozen here.

### Required acceptance fix

- Separate the two meanings explicitly: inner C5 fast-weight update remains higher-order-capable (`create_graph=True` where the inner `autograd.grad` requires it), while the segment’s outer task loss uses ordinary `backward()` / `create_graph=False` unless a separate reviewed objective demonstrates a need for another derivative.
- Add the CPU acceptance that the complete segment’s outer backward reaches every expected slow parameter with finite/nonzero gradients and that no cross-segment graph remains after commit/abort.

## Accepted direction / unchanged boundary

The following are accepted as design direction and should be retained in the remediation:

- C5A is the mandatory chronology/owner/segment authority before C6/config/GPU/training.
- `owner_key` must be logical and independent of batch row/request timestamp.
- strict monotonic transition admission and exact replay/no-second-write semantics are appropriate.
- direct external `state_in`, cross-owner substitution and admission bypass must fail closed.
- C5 remains an internal single-transition primitive and keeps its already-closed C5 numerical contract.
- no child/runtime/config/GPU/training changes belong in this remediation.

## Allowed remediation only

- root docs-only C5A design/status/ledger updates;
- no child change and no runtime implementation;
- static/diff-check evidence only.

A new/remediated root design SHA requires a fresh same-SHA three-party review. Until that new design is approved, C5A implementation, C6+, Cosmos forward/packer/attention, config/optimizer/checkpoint/trainer/inference/parallelization, native `MemoryState` mixing, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.
