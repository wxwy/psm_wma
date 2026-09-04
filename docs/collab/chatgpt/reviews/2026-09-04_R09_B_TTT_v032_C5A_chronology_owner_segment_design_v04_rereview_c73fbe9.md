# ChatGPT independent re-review — R09-B TTT v0.3.2 C5A chronology-owner / segment / backward design v0.4

**Date:** 2026-09-04  
**Gate:** `G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-DESIGN`  
**Verdict:** `REQUEST_CHANGES`

## Formal target

- root design SHA: `c73fbe90c24f5376f77e1c4109a205a50145c311`
- child/Gitlink: `6de8f2056c62cb10c89791d70335a44a6ab232fc`
- request/bookkeeping SHA: `e85226753b42fedcbff55dee20d433b1465fee0f`
- prior blocked design: `4b3a4129aa3d6f1fbf971397c958cb3abfe6652b`
- prior ChatGPT review: `5754faa90caa85535bc3c96258ccc2b72e774832`
- remote `V2` HEAD at final pre-write check: `568c2bc79e66399c5efaf5d7d6e0617a7920da68`

`568c2bc...` already contains an approval record for the same target, but this re-review was performed independently against the design, upstream R08/R09 authority, and the frozen C5 source ABI. The findings below supersede that approval as the latest ChatGPT verdict for this exact pair.

## Closure retained from v0.3

The v0.4 remediation does close the three v0.3 findings in principle:

- raw immutable source is retained instead of a detached graph-bearing encoded evidence tensor;
- C5A is now the sole chronology authority and R08 capability is provenance-only;
- committed replay is explicitly detached/cloned and graph-free.

The following are new blockers found while checking the remediated wording against the actual R08/R09/C5 data path.

## Findings

### 1. HIGH — v0.4 rematerializes the R08 stateless replay readout before C5, which changes the frozen R09-B topology and C5 input ABI

**Locations:**
- `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.4_2026-09-04.md:29`
- `cosmos_framework/model/generator/mot/local_evidence.py:112-153`
- `cosmos_framework/model/generator/mot/local_evidence.py:520-528`

**Root cause:**
Line 29 says `MATERIALIZE_PENDING` reruns trainable `LocalEvidenceEncoder + readout`, then executes the C5 inner K/V update/readout. In the frozen R08 implementation, that `readout` is `StatelessLocalReplayReadout`, which maps evidence history to one `[B,1,D_local]` token (`D_local=32`) and is only the R08 stateless control path. The closed C5 primitive instead calls `project_evidence()` on a single `[B,256]` causal evidence tensor. Feeding the R08 stateless readout into C5 is therefore dimensionally and architecturally incompatible, and would also duplicate a readout stage before the TTT readout.

The canonical R09-B route must remain:

`immutable causal source -> LocalEvidenceEncoder -> E_t [B,256] -> C5 K/Q/V projection + fast-state update/read_many -> Local tokens`.

The R08 `StatelessLocalReplayReadout` may remain as a separate no-TTT control baseline, but must not sit inside the formal C5A/TTT materialization path.

**Acceptance condition:**
- replace `LocalEvidenceEncoder + readout` with an explicit `LocalEvidenceEncoder -> E_t [B,256]` rematerialization before C5;
- explicitly state that `StatelessLocalReplayReadout` is bypassed/not called in the R09-B C5A path;
- require a synthetic CPU fixture that spies the stateless readout call count (`0`) and proves C5 receives `[B,256]` evidence while outer gradients reach the evidence encoder and C5 slow parameters.

### 2. HIGH — after removing chronology from `AdmissionCapability`, the design does not freeze the source-key replay lookup that must happen before assigning a new chronology slot

**Locations:**
- `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.4_2026-09-04.md:14-16`
- same file `:33,37`

**Root cause:**
The remediation correctly removes `owner_epoch/episode_step/segment_id/segment_offset` from the R08 capability and makes C5A the only chronology allocator. But an incoming retry now carries only provenance/source identity (`owner_key`, `source_timestep`, source identity/digest). Before C5A allocates the next episode-step/segment offset, it must determine whether that source was already pending or committed.

The design only says “pending same identity+digest replays” and defines committed records as `owner/epoch/segment/offset + digest + detached result`. It does not freeze an external source-key index or lookup-before-allocation rule. A conforming implementation could therefore accept the same source capability again, allocate the next chronology slot, and perform a second C5 write before realizing that the source digest already exists under an older assigned chronology.

**Acceptance condition:**
- freeze a canonical external replay/admission key, e.g. `S=(owner_key, source_identity, source_timestep, source_digest)`;
- require lookup of `S` against both pending and committed source ledgers **before** any new `episode_step/segment_id/segment_offset` allocation or C5 call;
- same `S` must replay the already-bound pending/committed numerical result with zero write; same source identity/timestep with a conflicting digest must reject; only a previously unseen `S` may receive the next chronology binding;
- committed records must retain enough source-key metadata (or a reverse `source_key -> chronology/cache` index) to satisfy this lookup after `P` is destroyed;
- add a fixture that replays a committed source capability after later chronology has advanced and proves no new chronology slot and no second C5 write are created.

## Scope / evidence

- target Gitlink resolves exactly to `6de8f2056c62cb10c89791d70335a44a6ab232fc`;
- `4b3a412... -> c73fbe9...` contains only root docs/review/ledger changes plus the new v0.4 design; no child runtime implementation is part of the target;
- repository request records docs-only `git diff --check` PASS; no local pytest/py_compile was independently executed in this connector-only review;
- no GPU/training/runtime scope drift was found.

## Allowed remediation only

Root docs-only C5A v0.4/v0.5 design/status/ledger remediation and static/diff-check evidence.

## Still prohibited

C5A implementation/runtime wiring; C6/C7/C8/C9; Cosmos forward/packer/attention; config/optimizer/checkpoint/trainer/inference/parallelization; native `MemoryState` mixing; GPU/CUDA/torchrun; real model/data/cache/checkpoint I/O; training/evaluation/inference; P4/P5; B2-T; LIBERO4IN1.

A remediated design is a new root SHA and requires fresh same-SHA three-party review.
