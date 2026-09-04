# Independent Design Review — R09-B TTT v0.3.2 C5 fast-state / chronology

- Gate: `G0-R09-B-TTT-V032-C5-FAST-STATE-CHRONOLOGY-DESIGN`
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5_FAST_STATE_CHRONOLOGY_CPU`
- Design SHA under review: `abf33a4ddbc871bb89b75b761ab57444a91118e6`
- Ledger/request SHA observed at review start: `9e10377008239897b673fe330d53f9390b765956`
- Child/Gitlink: `447f4a61a2205ff6be1788b9903fd7bc83363d53`
- Design: `docs/build/PSM-WMA_R09_B_TTT_v032_c5_fast_state_chronology_design_v0.1_2026-09-03.md`
- Upstream authority: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. Remote `V2` was resolved through the connected GitHub API before and again immediately before verdict formation.

At review time the remote `V2` HEAD remained ledger/request SHA `9e10377008239897b673fe330d53f9390b765956`; its parent is exactly design SHA `abf33a4ddbc871bb89b75b761ab57444a91118e6`. The exact design SHA points to child/Gitlink `447f4a61a2205ff6be1788b9903fd7bc83363d53`. The design commit is docs/status-only. GitHub exposes no status/check evidence for the design SHA.

The declared prerequisites are present in current project state: C2 multi-slot CPU core, C3 source/ABI audit, and C4 Memory Prefix CPU contract are recorded DONE; C4's final same-SHA ChatGPT closure is `a2a1f699... / 447f4a61...`.

## Verdict

`REQUEST_CHANGES`

The low-level direction is correct: explicit `state_in/state_out`, one K/V write per valid call, post-update `K_local` reads, whole-row W0 reset, sparse-row isolation, and row-selective TBPTT detach are the right primitives to add around the already-closed `ContinualTTTLocalMemoryCore`.

However, C5 v0.1 currently overclaims a **chronology authority** while its API only defines a caller-driven step transition. It also leaves the TBPTT counter state machine under-specified. Those gaps must be closed before authorizing the two-file CPU implementation, otherwise tests can prove a locally correct transition while still accepting duplicate/out-of-order evidence and an invalid graph-lifetime counter.

## HIGH-1 — the C5 API cannot enforce the claimed exactly-once / causal chronology contract

**File:** `docs/build/PSM-WMA_R09_B_TTT_v032_c5_fast_state_chronology_design_v0.1_2026-09-03.md:20-35,57-62,68-72`

### Root cause

The public transition input contains only:

```text
state_in
evidence_t
valid_t
done_before_t
step_index_in
```

There is no stable episode/rollout owner identity, transition/control-step identity, segment identity/offset, or last-applied identity stored with the runtime state.

Therefore the proposed implementation cannot distinguish these two sequences:

```text
step(e_t, state) -> state1
step(e_t, state1) -> state2      # duplicate/retry of the same transition
```

from two legitimate consecutive transitions. Refusing `[B,H,256]` only prevents a whole overlapping history tensor from entering the API; it does **not** prevent a caller from presenting the same single `[B,256]` evidence twice or presenting valid-looking evidence out of order.

The same authority gap makes the design's fail-closed statement for `future evidence`, `unfinished observation`, or `GT future action` unenforceable inside this two-file runtime: a numerically valid `[B,256]` tensor carries no provenance telling `local_evidence.py` what source timestep produced it.

This matters because the approved static source audit explicitly found that training needs stable episode/segment authority and exactly one state advance per real transition, and that current production inference has no reusable rollout owner. C5 must not silently replace that authority with caller trust while calling the result chronology closure.

### Required acceptance criteria

Choose one of these two scopes explicitly:

**A. Keep the two-file C5 implementation narrow.**

- Recast C5 as a **per-call fast-state transition CPU contract**, not end-to-end chronology closure.
- State exactly what it proves: for one already-admitted causal transition, one valid invocation performs exactly one K/V write and post-update read.
- Remove claims that this layer can itself reject future/GT provenance or duplicate/reordered invocations.
- Freeze the upstream admission contract: `evidence_t` must already be an R08-admitted completed causal evidence item.
- Add a separately named mandatory chronology-owner/segment/backward Gate before any GPU/training Gate. That later Gate must bind stable episode/rollout identity, transition/segment offset, retry/replay semantics, unique owner, and trainer-backward atomicity.

**or B. Make C5 itself the chronology authority.**

- Add verifier-owned/caller-checked identity fields sufficient to detect duplicate and out-of-order transitions (for example owner identity plus monotonic episode step or `segment_id, offset`).
- Carry the last admitted identity in the runtime state/owner and define reset/epoch/retry semantics.
- Add negative CPU fixtures for same-step replay, backward/out-of-order step, cross-owner state substitution, and owner reset/reuse.
- Define how those identities will later be supplied by the frozen training/inference seams; do not use HTTP request IDs or batch row position as owner identity.

Either route must preserve the current prohibition on trainer/data/inference implementation in this Gate.

## HIGH-2 — `step_index` does not have a closed TBPTT state-machine invariant

**File:** `docs/build/PSM-WMA_R09_B_TTT_v032_c5_fast_state_chronology_design_v0.1_2026-09-03.md:23,51-57,68-71`

### Root cause

The document defines `step_index_in` as the number of updates in the current not-yet-detached segment and says the counter resets when it reaches `ttt_tbptt_steps`, but the fail-closed grammar rejects only **negative** counters. It does not freeze the required upper bound or initialization coherence.

For a TBPTT length `N`, any carried non-reset state must satisfy:

```text
0 <= step_index_in < N
```

A caller-provided value `N` or `N+1` is already outside the legal state machine. If it is admitted, an implementation that only tests equality after increment can proceed to `N+1`/`N+2` and violate the frozen truncation length. Likewise, `state_in=None` denotes episode initialization but the current contract does not require the corresponding counter to be zero.

### Required acceptance criteria

Freeze the exact row-wise transition grammar before implementation:

```text
N = ttt_tbptt_steps > 0
input invariant: 0 <= c < N
state_in is None -> c == 0 for all initialized rows

done_before_t:
    state <- W0
    c <- 0

invalid:
    no write/read
    c_out = c

valid:
    updated_state, token = one_write_then_read(...)
    c1 = c + 1
    if c1 == N:
        token keeps the pre-detach outer-gradient path
        state_out = row-selective detach(updated_state)
        c_out = 0
    else:
        state_out = updated_state
        c_out = c1
```

For `N=1`, every valid step must read from the updated state, return the numerically identical detached state for the next call, and return counter zero.

Require fail-before-projection fixtures for `c < 0`, `c >= N`, wrong dtype/device/shape, and `state_in=None` with nonzero counter. Partial `done_before_t` reset must make only the selected row start from `W0,c=0`.

## Chronology/backward scope note

The prior static source audit established a separate training constraint: a complete TBPTT segment must become the atomic unit that is fully materialized before the trainer's immediate microbatch `backward()`. Carrying an undetached graph across a backward boundary is invalid; forcibly detaching at arbitrary current packing boundaries changes the algorithm.

C5's two-file synthetic transition primitive cannot by itself prove that production segment/backward ownership. If scope A above is chosen, the later mandatory chronology-owner Gate must explicitly retain this source-audit requirement. The current C6=`config/optimizer/checkpoint`, C7=`CPU full review`, C8=`GPU smoke`, C9=`matched smoke` sequence must not be interpreted as permission to skip that integration design.

## Accepted parts to retain

- Fast state remains distinct from Cosmos `MemoryState` / native KV cache.
- One newly admitted causal evidence performs one K/V write, never `K_local` writes.
- `K_local` reads happen from the **updated** `W_t`; `K_local=1` remains compatibility behavior.
- Per-row reset must copy the whole learned W0 pytree and leave other rows unchanged.
- Invalid rows do not mutate state and produce exact-zero/absent output for the current call.
- `ttt_tbptt_steps` is positive/configurable with default 16 and is a graph-truncation length, not a memory horizon/reset period.
- Training meta-update remains `create_graph=True`; no inference/GPU/training authority is granted here.
- Implementation scope should remain `local_evidence.py` + adjacent synthetic CPU test if C5 is narrowed to the per-call transition contract.

## Scope

Do **not** authorize `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5_FAST_STATE_CHRONOLOGY_CPU` at `abf33a4` yet.

Allowed remediation is docs/status only. No child/runtime implementation, config/optimizer/checkpoint/trainer/inference/parallelization change, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1 training is authorized by this review.