# ChatGPT independent review — R09-B TTT v0.3.2 C5A chronology-owner / segment / backward design v0.3

**Date:** 2026-09-04  
**Gate:** `G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-DESIGN`  
**Verdict:** `REQUEST_CHANGES`

## Formal target

- root design SHA: `4b3a4129aa3d6f1fbf971397c958cb3abfe6652b`
- child/Gitlink: `6de8f2056c62cb10c89791d70335a44a6ab232fc`
- request/ledger SHA: `f647fbd35e46729f5ac296c20ef999d4336bead4`
- routing clarification ledger: `7ca44617ada4d4b9dd5bcc17bfc33192e86ef4a8` (bookkeeping only; not the design target)
- remote `V2` HEAD observed before review write: `7ca44617ada4d4b9dd5bcc17bfc33192e86ef4a8`
- prior blocked design: `b793e391f3e57d0b140e0b6b6e33da08509fd844`
- prior ChatGPT review record: `a7124a7c4ae3e54f419a8df70e8d9f4a55add5ec`

The root target is exactly one docs-only commit ahead of the prior ChatGPT review commit and changes only `SESSION.md`, `TODO.md`, and the new C5A v0.3 design file. The Gitlink at the formal target resolves to the requested child SHA. No child/runtime code is part of this design target.

## Closure of prior findings

The v0.3 remediation materially closes the prior v0.2 findings:

- committed owner state `C` and pending transaction `P` are now explicitly separated; pending chronology advances against `P.pending_cursor`, while only a successful commit promotes state/cursor/ledger into `C`;
- terminal remainder is explicitly frozen for `r=0`, `0<r<N`, and `r=N`, with old-epoch completion/abort before epoch rollover;
- provenance now includes explicit `source_timestep`, owner-local digest, batch-permutation semantics, and a trusted capability object rather than caller-supplied booleans;
- inner TTT higher-order construction (`create_graph=True`) is separated from ordinary outer `backward()`.

Those prior blockers are considered closed for this new SHA. The following are new blockers discovered while checking the remediated design against the still-authoritative R08/R09 training contract.

## Findings

### 1. HIGH — graph-free `COLLECT_RAW` cuts the trainable R08 evidence-encoder path unless evidence rematerialization is explicitly frozen

**Locations:**
- `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.3_2026-09-04.md:35-49`, especially line 46
- upstream authority `docs/build/PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md:779-820`, especially lines 814-820

**Root cause:**
C5A v0.3 says `COLLECT_RAW` stores the already-verified per-owner **evidence** while creating no autograd graph, and only later materializes C5. But R08 explicitly freezes `LocalEvidenceEncoder + readout` as trainable from the native `L_vision + L_action`. An encoded `E_t` produced by that trainable encoder already carries the encoder graph. Making the pending segment graph-free therefore requires detaching `E_t`; using that detached tensor at materialization removes the outer-loss gradient to `LocalEvidenceEncoder`.

Conversely, retaining graph-bearing `E_t` until a segment fills violates the design's graph-free collection goal and defeats the purpose of the two-phase materialization boundary.

**Acceptance condition:** freeze one mathematically explicit training path before implementation. The preferred contract is:
1. `COLLECT_RAW` stores only trusted causal **source payload/provenance** (or a stable immutable source handle) plus identity/digest material; it does not store a graph-bearing encoded `E_t` as the training value.
2. `MATERIALIZE_PENDING` reruns `LocalEvidenceEncoder` under grad from those frozen raw sources, then runs the C5 inner update/readout and outer task path in the segment atomic unit.
3. Freeze slow-parameter stability between source admission and materialization, or define the digest over immutable source bytes/identity rather than a parameter-dependent encoded `E_t`, so rematerialization cannot invalidate admission merely because encoder weights changed.
4. Add CPU acceptance evidence proving nonzero finite outer gradients reach the trainable evidence-encoder parameters as well as Q/K/V/slot/W0, while no autograd graph is retained across committed/aborted segment boundaries.

An alternative is to explicitly freeze/detach the R08 evidence encoder for this route, but that would be a change to the upstream training contract and therefore needs its own authority rather than being implied by C5A.

### 2. MEDIUM — chronology authority is duplicated between the R08 capability and the C5A owner registry

**Locations:**
- `...c5a_chronology_owner_segment_design_v0.3_2026-09-04.md:17-28`
- same file `:35-42,53-55`

**Root cause:**
The trusted R08 `AdmissionCapability` is defined as carrying `owner_epoch`, `segment_id`, and `segment_offset`, while the C5A owner registry separately owns epoch rollover and deterministically derives segment id/offset from committed/pending cursors. The design does not freeze which side is authoritative or the handshake by which R08 can know C5A's pending chronology before signing the capability.

This leaves two plausible implementations with different semantics: R08 independently assigns chronology (duplicated authority), or C5A supplies chronology to R08 before capability issuance (two-way issuance protocol). The design currently approves neither explicitly.

**Acceptance condition:** make chronology ownership singular. Preferably the R08 capability authenticates source/evidence provenance (`owner_key`/source identity, `source_timestep`, source/evidence digest, provenance class), while C5A assigns and binds `owner_epoch`, `episode_step`, `segment_id`, and `segment_offset` from its own registry state. If chronology remains inside the signed capability, freeze the exact C5A→R08 issuance handshake and require stale/mismatched epoch/segment capabilities to fail before C5.

### 3. MEDIUM — committed replay result storage/detach semantics are not defined

**Locations:**
- `...c5a_chronology_owner_segment_design_v0.3_2026-09-04.md:35-39,47,49,74`

**Root cause:**
`P` explicitly has `pending_replay_cache`, but `C` only names `committed_replay_ledger`. The materialization rule nevertheless requires an already-committed retry to return a "committed cached result" without a second C5 write. The commit rule says pending state/cursor/ledger are promoted and `P` is destroyed, while the acceptance matrix separately requires no cross-segment graph after commit/abort.

The design does not say whether the committed ledger contains the numerical replay result, whether it is detached/cloned, or how graph-bearing pending cached outputs are converted at commit. A naive promotion of graph-bearing output references can retain a previous segment graph; omitting the result makes exact committed replay undefined.

**Acceptance condition:** freeze committed replay entries as explicit graph-free numerical cache records (for example identity + digest + detached/cloned result + any required present/shape metadata), define the exact promotion from pending cache to committed cache, and require a fixture proving committed replay is value-equal, causes zero C5 writes, has no `grad_fn`/cross-segment graph, and survives pending transaction destruction.

## Evidence / scope notes

- `a7124a7... -> 4b3a412...` is one docs-only commit; no child/runtime scope drift was found.
- formal target Gitlink resolves to `6de8f2056c62cb10c89791d70335a44a6ab232fc`.
- repository request records `git diff --check` PASS for this docs-only target; it was not independently rerun in this connector-only environment.
- GitHub reports no combined CI statuses for the formal target.
- `7ca4461...` is routing clarification only and does not replace `4b3a412...` as the design under verdict.

## Allowed remediation only

Root docs-only C5A design/status/ledger remediation is allowed. No child/runtime implementation is authorized by this verdict.

## Still prohibited

C5A implementation/runtime wiring; C6/C7/C8/C9; Cosmos forward/packer/attention; config/optimizer/checkpoint/trainer/inference/parallelization; native `MemoryState` mixing; GPU/CUDA/torchrun; real model/data/cache/checkpoint I/O; training/evaluation/inference; P4/P5; B2-T; LIBERO4IN1.

A remediated design is a new implementation/design SHA and requires a fresh same-SHA three-party review.
