# ChatGPT 独立 Canonical Segment Production Adapter + Scheduler/GA Design Review

Formal reviewed pair:
- root design SHA: `0779be775429e15d83de00dda50649195cadc9e7`
- child/Gitlink SHA: `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.1.md`
- upstream source-audit pair: `032cb6c3e24f66ae8ab25012cfc654e84b89a6e7` / `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- request/bookkeeping commit observed: `62af7b616bae97d34d17af7c3f72407a0a616963`; later V2 poll/update commits are bookkeeping only and do not replace the formal pair.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.1.md:§3-§5)`

## Findings

The design correctly preserves the v0.3.5 high-level production direction: one `[B_stream,T]` graph per native microbatch, stream-major valid gather, S0 Local absent, PAD excluded from native loss, valid-count-weighted outer objective, post-backward fast-state commit, old row-wise active wiring excluded from production authority, and CPU/static-only scope. Those parts are not blockers.

However, the current design is not yet implementable against the inherited canonical core without silently changing scheduler/GA semantics. Three correctness blockers and one determinism/provenance blocker remain.

## Current blockers

### 1. HIGH — one `[B_stream,T]` native microbatch has no batch-level identity / atomic transaction ABI

**Location:** design §3 and §5; current child `cosmos_framework/model/generator/mot/local_memory_segment.py::{SegmentBatch,GAWindowPlan,SegmentIdentity,RankLocalSegmentScheduler}`.

**Root cause:** v0.3.5 freezes one production microbatch as a complete `[B_stream,T]` `SegmentBatch`, but the design still declares the adapter input as `SegmentBatch + admitted SegmentIdentity + frozen GAWindowPlan member` and requires that singular identity to equal the current plan member. In the inherited child, `SegmentIdentity` is one stable slot/episode/cursor and `GAWindowPlan.members` is a tuple of singular `(slot_id, episode_id, cursor)` projections. `RankLocalSegmentScheduler.admit()` and `commit()` are likewise singular. By contrast, `SegmentBatch` has B independent `slot_id` / `episode_id` / `category` rows and `gather_consumers()` emits identities from all rows.

If one current GA member is interpreted as one row, `len(plan.members)` becomes `B_stream * native_GA` and the design's auxiliary `/GA` and full-valid `1/GA` degeneracy are wrong. If one current GA member is interpreted as one full microbatch, a single `SegmentIdentity` cannot represent or validate B stable-slot continuities/provenances, per-row terminal/rebind, or post-backward commit authority.

**Violated contract:** one native microbatch owns the complete `[B_stream,T]` graph while GA membership remains native-microbatch-granular; scheduler identity/provenance and commit must cover every stream row exactly.

**Acceptance:** amend the design with an exact batch-level plan member ABI (for example an immutable `MicrobatchPlanMember`) containing the ordered B stream `SegmentIdentity`/provenance records, per-row planned-valid metadata and aggregate `planned_n_valid`. Freeze that `GAWindowPlan.members` length remains the native GA length, not `B_stream * GA`. Define exact batch prepare/validation, one shared backward, and all-row post-backward commit/rebind semantics, including whether per-row scheduler commits are exposed through one atomic member transaction. Existing singular `SegmentIdentity` must not be silently repurposed as the identity of an entire `[B,T]` batch. CPU/static acceptance must include `B>1` with different episodes/categories/tails and prove exact row identities plus one member-level commit boundary.

### 2. HIGH — `planned_n_valid` / full-window pre-load planning is circular and lacks a projected scheduler-state contract

**Location:** design §5.

**Root cause:** §20.2 C specifically leaves open how the GA window's planned valid count is obtained reliably without loading all tensors. The new design states that `planned_n_valid` is computed from “chronology metadata”, but its frozen pre-load metadata merely lists `planned_n_valid` itself plus `SegmentIdentity(..., training_stream_end)`. A terminal boolean does not identify the exact tail length / consumer range needed to derive the count. For B>1 there is also no per-row count authority or aggregate formula tied to immutable chronology source data.

The same problem applies to freezing the *entire* GA window. The current scheduler mutates `stable_slots` at `admit()`, updates cumulative exposure only at `commit()`, and permits terminal rebind only after a terminal identity has committed. Therefore a GA plan that spans a future tail and subsequent free-slot admission cannot be generated from the current live state without either mutating uncommitted runtime authority or introducing an as-yet-undefined projected planning state. Weighted-deficit decisions for later planned admissions likewise need deterministic projected exposure/queue state.

**Violated contract:** all member identities/counts/queue/exposure metadata must be immutable before tensor/latent load, while live chronology/exposure may advance only after successful execution/commit.

**Acceptance:** freeze the exact trustworthy pre-load chronology record and count formula per stream row (e.g. immutable episode consumer length/range/end-step plus digest binding), its aggregation to member `planned_n_valid`, and a pure projected GA-planning state that derives all future continuations, tail terminal transitions, possible next-member rebinds, queue positions and projected exposure without mutating live committed scheduler state. At execution, loaded `SegmentBatch` row identities and `consumer_valid` counts must be checked exactly against that frozen plan; mismatch is terminal/fail-closed. Add CPU/static evidence for a GA window that crosses at least one tail/terminal boundary and proves plan freeze leaves live scheduler state unchanged until post-backward commit.

### 3. HIGH — inherited suffix retry changes the weighted-objective denominator after a later-member failure

**Location:** design §4-§5; current child `GAWindowPlan.objective()`, `GAWindowPlan.suffix_after_failure()`, and `LocalMemoryTransaction.fail_transient()`.

**Root cause:** the design defines each member's weight from `sum(plan.planned_n_valid)` and `len(plan.members)`, while §5 preserves an immutable suffix retry. The inherited `suffix_after_failure(failed_index)` physically truncates both `members` and `planned_n_valid`, so attempt-1 recomputes a smaller `n_window` and `ga_effective`. For a two-member plan with counts `(5,3)`, if member 0 has already backwarded and member 1 then transient-fails, the original member-1 consumer coefficient is `3/8` and auxiliary coefficient is `1/2`; the one-member suffix plan changes those coefficients to `1` and `1`. Prefix gradients plus retry-suffix gradients therefore cannot equal the original frozen-window objective. The current synthetic transaction also marks slow grads cleared on suffix failure, which would additionally remove already accumulated prefix contribution if carried literally into production.

**Violated contract:** a frozen GA window has one immutable valid-count denominator and one native GA scaling; retry must not change the mathematical objective or silently discard already valid prefix gradients.

**Acceptance:** explicitly choose and freeze one mathematically coherent policy. Either (a) retry is allowed only before any successful member (first-member-only), with later-member transient terminalizing the window; or (b) attempt-1 suffix retains the original window denominator, original GA effective value and original member indices, while already accumulated prefix slow gradients are preserved exactly and retry is restricted to failures before the failed member begins backward. Any exception after backward starts must terminalize/zero the whole slow window unless an exact gradient rollback mechanism is separately designed. CPU/static tests must use unequal counts and prove original-plan objective equivalence across the permitted retry path.

### 4. MEDIUM — queue epoch rollover semantics are fields, not a deterministic algorithm

**Location:** design §5.

**Root cause:** the design records `queue seed / epoch / permutation`, but does not define what happens when the seeded episode queue is exhausted: when epoch increments, how the next permutation is derived, whether bound-slot continuations take precedence over queue consumption, and whether cumulative valid-consumer exposure persists across epoch rollover. §20.2 D explicitly requires the exact scheduler state/seed/queue epoch/permutation semantics to be frozen before implementation.

**Violated contract:** deterministic weighted episode-stream scheduling and provenance must be reproducible from the frozen scheduler state rather than implementation choice.

**Acceptance:** define the exact rollover transition: queue exhaustion condition, `epoch -> epoch+1`, deterministic permutation derivation from the frozen seed/epoch (or another exact frozen scheme), ordering between bound-slot continuation and free-slot episode admission, and exposure persistence/reset rule. Add a CPU/static rollover fixture proving identical state produces identical next-epoch sequence and provenance.

## Scope / next authorized action

This verdict authorizes only a docs-only remediation of this design. It does **not** authorize child implementation, producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1.

After the four blockers above are frozen in a new root formal SHA with the exact child/Gitlink, submit that new pair for fresh design review. The reserved success literal remains:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`.
