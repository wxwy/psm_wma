# ChatGPT Independent Review — R09-B TTT v0.3.5 Stage-1 Authority-Root Materialization Request v1.0

**Date:** 2026-09-14  
**Formal root:** `d474849d7bf3bf556886f2887b2325aaab36a868`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-REQUEST`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `d474849d7bf3bf556886f2887b2325aaab36a868` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `d474849...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- The formal commit itself changes only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.0.md`; delivery/session bookkeeping is outside the technical formal commit.
- Controlling authority is the approved stage-split design refreeze v0.3, exact pair `5a668ad8871798a0c252ce9c05dbf167c36ba839` / same child, with ChatGPT canonical approval commit `e7480c0eee3cc9012ca2a8ec38b7aa53015b1f5b`.
- That approval allows only construction and independent review of **one fully fresh-bound Stage-1 request**. It explicitly requires the future request itself to carry same-round concrete observations and canonical whole-request SHA; runtime revalidation is additive and cannot substitute for request construction.
- No authority-root materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/publication mutation, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Positive observations

The v1.0 request correctly carries several Stage-1 boundaries:

- exact approved design authority `5a668ad...`;
- exact candidate parent `b359539...` and child `93a89ba...`;
- selection/config SHA identities and Git/Python identities;
- a same-round observation stating the fixed local ref is absent, remote exact `ls-remote` output is empty, and clean/evidence/pending paths are absent;
- inheritance of the previously reviewed FD8/four-module/payload definition from v0.9;
- one-shot Stage-1 scope: PASS produces only the authority tuple and hard-stops; collection/receipt/source-evidence/publication/GPU/training remain prohibited.

These are necessary inputs to the exact request, but they do not yet satisfy the approved v0.3 exact-instance boundary.

## 3. Blocking finding

### HIGH-1 — the artifact calls itself an exact request, but still defers construction of the canonical reviewed execution instance until after approval

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.0.md:16`

The approved v0.3 design and its canonical ChatGPT review freeze the next step as construction and review of a **fully fresh-bound Stage-1 request**. The request itself must carry the same-round concrete observations and canonical whole-request SHA before reviewers can authorize execution.

Current v1.0 instead states under `Required pre-exec binding` that, only **before execution**, an independent launcher must:

- bind canonical selection/config raw bytes to FD3/FD4;
- bind the bootstrap contract to FD5 and clean owner to FD8;
- write complete argv, six-key sanitized env, metadata, tool closure, overlay SHA, and dual-end absent snapshot into a canonical request JSON;
- then compute the whole-request SHA.

That is not a reviewed exact execution instance. It is a recipe for constructing a new execution instance after this formal pair has already been approved. The exact bytes/observations that would control real mutation are therefore not present in the formal artifact under review and would not be bound by this verdict.

Concretely, this formal request does not itself carry/bind all of the v0.3 §2 required fields:

1. selection/config **raw bytes plus concrete FD identities**;
2. bootstrap contract bytes/identity and owner-FD binding;
3. literal complete outer launcher argv;
4. literal six-key sanitized environment;
5. exact commit metadata used by the launcher;
6. formal-tree tool-closure observation/identity as part of this exact request;
7. cwd/index/evidence identity observation as part of this exact request;
8. the canonical request JSON bytes and **whole-request SHA-256** that reviewers are actually approving.

The local/remote ref absence snapshot recorded in the document is useful, but it cannot make the missing canonical execution instance appear later without a new formal pair/review. Runtime freshness checks may remain as a second barrier; they cannot create or replace the reviewed request after approval.

This is the same authority distinction the v0.3 refreeze was created to enforce: design requirements are not themselves execution-instance evidence.

## 4. Exact acceptance

No production redesign is required. Replace this draft with a new exact Stage-1 request pair in which the **formal artifact already contains or byte-addresses one immutable canonical request instance** before review:

- include the same-round concrete selection/config raw-byte identity and FD-binding observations;
- include the bootstrap-contract/owner-FD observation;
- include the exact complete outer launcher argv and exact sanitized environment;
- include commit metadata, formal-tree tool closure, cwd/index/evidence identity, and local/remote ref absence snapshot;
- canonicalize those fields into the exact request bytes and record the whole-request byte length/SHA-256 in the formal artifact;
- make the launcher execute exactly those reviewed bytes, with runtime revalidation only as an additional fail-closed guard;
- any freshness drift, identity drift, missing field, non-absent ref, or request-byte/SHA mismatch must remain `BLOCKED_AUTHORITY_NOT_CLOSED` with zero mutation;
- preserve the Stage-1 hard stop and all Stage-2/downstream prohibitions.

The replacement exact request must receive a new formal pair and independent review before any materialization may occur.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.0.md:16)`

Current blockers: **1 HIGH Design/Authority**.  
Production implementation blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact pair `d474849d7bf3bf556886f2887b2325aaab36a868` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-REQUEST`.

No authority-root materialization is authorized. No source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/source-evidence/publication mutation, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized by this verdict.
