# Independent Design Re-Review — R09-B TTT v0.3.2 C5 fast-state transition v0.2

- Gate: `G0-R09-B-TTT-V032-C5-FAST-STATE-TRANSITION-DESIGN`
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5_FAST_STATE_TRANSITION_CPU`
- Remediation/design SHA under review: `d0f29f31cc223284769d726239e0ec71a59a484c`
- Request/ledger SHA: `86a65d59dfbb48ed86aeba498eb7c22cfa1c8e8c`
- Latest status/ledger SHA observed before verdict: `a857baa35c76842d218884fba42777141d1d057b`
- Child/Gitlink: `447f4a61a2205ff6be1788b9903fd7bc83363d53`
- Prior blocked design: `abf33a4ddbc871bb89b75b761ab57444a91118e6`
- Prior ChatGPT review-file commit: `611d462cc1d8a23c111876c0e634ef200a2878c6`
- Canonical remediation: `docs/build/PSM-WMA_R09_B_TTT_v032_c5_fast_state_chronology_design_v0.2_2026-09-04.md`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. Remote `V2` was resolved through the connected GitHub API.

The previous C5 v0.1 detailed review was persisted at `611d462...`; its live-Inbox append raced with concurrent project updates and was rejected by GitHub's stale blob-SHA protection, so no concurrent Inbox content was overwritten. The remediation commit `d0f29f3...` is exactly one docs/status-only commit after that review: only `SESSION.md`, `TODO.md`, and the new v0.2 design were changed. No child/runtime code changed. At the exact remediation SHA, the Gitlink remains `447f4a61a2205ff6be1788b9903fd7bc83363d53`.

GitHub exposes no status/check evidence for the design SHA; this is a design re-review, not runtime evidence.

## Verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5_FAST_STATE_TRANSITION_CPU`

This approval is narrow. It authorizes only the two-file synthetic CPU transition implementation frozen by v0.2. It does **not** close chronology ownership, trainer segmentation/backward semantics, config/optimizer/checkpoint, runtime wiring, GPU, training, evaluation, or inference.

## Closure of prior HIGH-1 — chronology authority overclaim is removed

The prior design called C5 a chronology owner while exposing only `state/evidence/valid/done/counter`, which could not prove duplicate/reordered/future provenance.

v0.2 now explicitly states that C5 receives an **already-admitted single causal transition** and is only a per-call state transform. It no longer claims that a bare `[B,256]` tensor can prove future/GT provenance, duplicate/replay status, ordering, or cross-owner identity.

The contract is now precise:

```text
one upstream-admitted transition invocation
  -> at most one valid K/V write
  -> updated fast state
  -> K_local reads from that updated state
```

End-to-end exactly-once chronology is explicitly deferred to a mandatory `C5A-CHRONOLOGY-OWNER-SEGMENT-DESIGN`, which must close **before C6, GPU, or training** and must freeze episode/rollout identity, transition/segment offset, retry/replay, unique state owner, training segment materialization, and trainer `backward()` atomicity.

This preserves the approved source-audit finding instead of pretending the two-file Local core can solve production ownership.

**Prior HIGH-1: CLOSED.**

## Closure of prior HIGH-2 — TBPTT counter state machine is closed

v0.2 freezes the exact input invariant:

```text
N = ttt_tbptt_steps > 0
0 <= counter_in < N
state_in is None -> counter_in == 0
```

and requires negative, `counter>=N`, init-nonzero, shape/dtype/device/nonfinite errors to fail before projection/update.

The row-wise transition is now complete:

```text
done_before_t:
    whole-row state <- learned W0
    counter <- 0

invalid:
    no write/read
    exact-zero token, present=false
    preserve post-reset counter/state

valid:
    one K/V write
    K_local reads from updated state
    c1 = c + 1
    if c1 == N:
        token retains current pre-detach outer-gradient path
        returned state is detached for this row only
        counter_out = 0
    else:
        returned state remains connected
        counter_out = c1
```

`N=1` is also explicitly frozen: every valid call reads the updated state, returns the numerically identical detached carry state, and returns zero counter.

**Prior HIGH-2: CLOSED.**

## Implementation scope accepted

If the required same-SHA three-party design approvals are all present, the next implementation may touch only:

- `cosmos_framework/model/generator/mot/local_evidence.py`
- adjacent `local_evidence_test.py`
- root status/ledger docs

and may use only synthetic CPU tensors.

Required CPU evidence includes:

- consecutive transition carry;
- exactly one write followed by post-update `K_local` read;
- `K_local=1` compatibility;
- whole-row W0 reset and invalid-row isolation;
- `N=1`, default `N=16`, and non-default positive N;
- row-selective detach with numerical invariance and correct graph boundary;
- all counter grammar failures before projection/update;
- slow-gradient reachability to Q/slot/K/V/W0 where expected;
- fast runtime state absent from `named_parameters()`.

## Mandatory authority boundary retained

This verdict does **not** authorize or imply closure of:

- stable episode/rollout/transition identity;
- duplicate/reorder/retry handling;
- unique state-owner registry;
- training segment materialization;
- native loss/noise integration;
- trainer microbatch/backward boundary;
- production inference state ownership.

Those remain mandatory C5A/later-Gate work. C5A is a hard predecessor of C6/config/checkpoint and of any GPU/training request.

## Still prohibited

- Cosmos forward/packer/attention changes;
- config/optimizer/checkpoint/trainer/inference/parallelization changes;
- native `MemoryState` mixing;
- GPU/CUDA/torchrun;
- real model/data/cache/checkpoint I/O;
- training, evaluation, inference;
- P4/P5 real operations;
- B2-T or LIBERO4IN1 training.