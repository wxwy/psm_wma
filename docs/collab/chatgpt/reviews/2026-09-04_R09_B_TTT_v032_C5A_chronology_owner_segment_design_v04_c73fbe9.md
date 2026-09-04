# ChatGPT independent review — R09-B TTT v0.3.2 C5A chronology-owner / segment / backward design v0.4

**Date:** 2026-09-04  
**Gate:** `G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-DESIGN`  
**Verdict:** `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5A_CHRONOLOGY_OWNER_SEGMENT_CPU`

## Formal target

- root design SHA: `c73fbe90c24f5376f77e1c4109a205a50145c311`
- child/Gitlink: `6de8f2056c62cb10c89791d70335a44a6ab232fc`
- request/ledger SHA: `e85226753b42fedcbff55dee20d433b1465fee0f`
- prior blocked design: `4b3a4129aa3d6f1fbf971397c958cb3abfe6652b`
- prior ChatGPT review: `5754faa` / `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_C5A_chronology_owner_segment_design_v03_4b3a412.md`

`7ca44617ada4d4b9dd5bcc17bfc33192e86ef4a8` was routing clarification for the superseded v0.3 target and is bookkeeping only; it is not the design under verdict.

## Closure of prior findings

All three blockers from the v0.3 review are closed on this new SHA.

### HIGH-1 — graph-free collection vs trainable evidence encoder: CLOSED

v0.4 no longer stores graph-bearing encoded `E_t` as the pending training value. `COLLECT_RAW` stores only trusted immutable causal source payload/handle, capability, owner identity and source digest. `MATERIALIZE_PENDING` rematerializes `LocalEvidenceEncoder + readout` under grad inside the segment atomic unit, then runs the C5 inner update/readout and outer task path. This preserves outer-gradient reachability to the trainable evidence encoder without retaining an autograd graph during collection.

The admission identity is also moved to immutable source bytes/identity rather than parameter-dependent encoded `E_t`, so rematerialization does not invalidate provenance solely because encoder parameters differ. The implementation Gate explicitly requires finite/nonzero outer gradients to the evidence encoder and Q/K/V/slot/W0 and no cross-segment graph retention.

### MEDIUM-2 — duplicated chronology authority: CLOSED

The R08 `AdmissionCapability` now authenticates provenance only: owner/source identity, source timestep, immutable source payload handle/digest and provenance class. It no longer carries `owner_epoch`, `episode_step`, `segment_id` or `segment_offset`.

C5A owner registry is explicitly the sole chronology authority and assigns/binds epoch/step/segment/offset after admission. This removes the prior circular/duplicated R08-vs-C5A chronology ownership.

### MEDIUM-3 — committed replay cache semantics: CLOSED

v0.4 freezes `C.committed_replay_ledger` as an explicit graph-free numerical record containing chronology identity, digest, detached/cloned numerical result and shape/presence metadata. Pending replay entries are detached/cloned only at atomic commit. Committed replay is required to be value-equal, `grad_fn is None`, survive pending destruction and cause zero additional C5 writes.

## Transaction / terminal / gradient contract

The v0.3 transaction fixes remain intact:

- committed state `C` and one pending transaction `P` remain separate;
- only `P.pending_state/cursor` advances before commit;
- `COLLECT_RAW -> MATERIALIZE_PENDING -> BACKWARD_OK -> COMMIT` is the only success path;
- abort/failure/repeated backward/repeated commit destroys `P` and leaves `C` unchanged;
- terminal `r=0`, `0<r<N`, and `r=N` are explicitly defined, with old-epoch completion/abort before epoch rollover;
- C5 inner higher-order update keeps `create_graph=True`; outer task loss uses ordinary `backward(create_graph=False)`;
- fast state remains runtime state and must not enter `named_parameters()`.

## Scope and evidence

- root remediation is docs-only; no child runtime implementation is part of this design target;
- child Gitlink remains exactly `6de8f2056c62cb10c89791d70335a44a6ab232fc`;
- repository request records `git diff --check` PASS; this connector-only review did not independently execute local pytest/py_compile;
- no runtime/model/config/optimizer/checkpoint/GPU/training/eval/inference scope drift was found.

## Authorized next step

Only after all required same-SHA reviewers approve this exact pair, Codex may implement the C5A owner/segment **synthetic CPU** slice and adjacent tests required by v0.4, including:

- single chronology authority handshake;
- immutable-source admission and rematerialization under grad;
- pending/committed replay exactness and zero-write semantics;
- transaction rollback/commit atomicity;
- `N=1/3/16` and terminal `r=0..N`;
- forged admission / out-of-order / cross-owner / epoch mismatch fail-before-C5;
- batch permutation identity handling;
- evidence-encoder and Q/K/V/slot/W0 gradient reachability;
- fast state excluded from optimizer parameters.

## Still prohibited

This approval does **not** authorize production/runtime wiring, C6/C7/C8/C9, Cosmos forward/packer/attention changes, config/optimizer/checkpoint/trainer/inference/parallelization, native `MemoryState` mixing, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1.

Any implementation/remediation commit is a new implementation SHA and requires a fresh same-SHA three-party review before closure.
