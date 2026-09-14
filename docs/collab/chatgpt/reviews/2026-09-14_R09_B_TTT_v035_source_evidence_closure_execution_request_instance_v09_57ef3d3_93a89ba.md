# ChatGPT Independent Review — R09-B TTT v0.3.5 Source-Evidence Closure Execution Request Instance v0.9

**Date:** 2026-09-14  
**Formal root:** `57ef3d32452d990af98fda5edfe485376b772723`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `57ef3d32452d990af98fda5edfe485376b772723` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- The formal commit changes only the new v0.9 execution-request document plus `SESSION.md` / `TODO.md`; no project implementation or child change is in formal scope.
- Candidate authority parent `b3595395427114f73ff53a19a0c2b9180e39905f` is the previously closed causal-worktree CPU/static implementation pair. Its four referenced pre-import module blob OIDs and the v0.8 launcher base blob match the request's stated blob identities.
- No real materialization/source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/source-evidence/publication mutation, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Positive observations

The request does preserve several important authority properties:

- it binds the closed `b359...` parent and exact child Gitlink;
- it fixes one authority ref and requires clean root/index/backing/evidence/pending plus local/remote ref freshness before mutation;
- it carries the FD8 child ABI and pre-import four-module closure identities;
- the base launcher blob is exactly the reviewed v0.8 blob and the overlay is protected by a final derived byte length/SHA predicate;
- it explicitly hard-stops downstream collection/receipt/source-evidence/publication/GPU/training activity.

Those points are necessary, but they are not sufficient for the requested real-materialization verdict under the controlling source-evidence closure request authority chain.

## 3. Blocking findings

### HIGH-1 — v0.9 is not an exact instance of the approved source-evidence closure execution-request design; it introduces an unreviewed intermediate execution stage

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.9.md:10`

The controlling approved design is `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_execution_request_design_v0.2.md` at formal root `9a8ef4195ebf3e6a0bf5f1a76f6a8f819e5db546`. It freezes the post-review activation as one ordered transaction:

1. materializer establishes/recomputes execution-authority tuple;
2. collection executor commits artifacts + collection receipt;
3. source-evidence producer creates the formal root and next independent receipt root;
4. root audit recomputes the formal/receipt roots and exact receipt identity;
5. only after step 4 PASS does the activation hard-stop for independent receipt-root review.

The exact-pair ChatGPT approval for that design explicitly states that the next allowed action is construction/review of the **exact source-evidence closure execution request instance**.

v0.9 instead requests only one authority-root materialization, then hard-stops, and explicitly places collection/receipt/source-evidence/publication outside the request. That is a new intermediate execution stage. The live Inbox phrase "two-stage progression" is coordination text, not a formal superseding/refreeze of the approved v0.2 design, and cannot change the authority hierarchy by itself.

Therefore the requested literal `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` is not authorized under this Gate as presently frozen.

**Exact acceptance:** either (a) construct the exact closure request instance that implements the approved v0.2 activation ordering and stop boundary, or (b) first create and independently approve a docs-only design/refreeze that explicitly splits authority-root materialization into a separately reviewed first execution stage, then construct the exact stage-1 instance under that new authority.

### HIGH-2 — the v0.9 document is not a fully fresh-bound exact request instance under the current construction checklist

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.9.md:14`

The current Gate's construction checklist (`PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_request_instance_construction_v0.1.md`) requires same-round binding and canonicalization of, among other fields:

- selection/config FD identity **and raw bytes**;
- bootstrap contract / owner FD;
- formal-root full tool allowlist;
- cwd/remote/index/evidence paths;
- sanitized environment;
- commit metadata;
- complete execution argv;
- local/remote ref dual-end **absent observation**;
- then an exact request SHA for independent review.

v0.9 gives roles, hashes, paths, module identities, a payload-overlay recipe and a final derived payload hash, but it does not carry the required same-round concrete FD identity/raw-byte observations, sanitized environment, commit metadata, literal complete outer launcher argv/transport, or the actual dual-end local/remote ref absence observation. Saying those items "must be absent" at launch is a runtime predicate, not the fresh observation that the instance-construction authority requires reviewers to bind before approving execution.

Likewise, a final payload SHA can protect derived bytes after construction but cannot substitute for the missing reviewed execution-instance fields and complete argv.

**Exact acceptance:** the replacement exact instance must record the required same-round fresh bindings, including the literal launcher argv + sanitized env and dual-end ref absence snapshot, then canonicalize/hash the whole exact request for review. Runtime revalidation may remain as an additional fail-closed barrier, not as a substitute for instance construction.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.9.md:10)`

Current blockers: **2 HIGH Design/Authority**.  
Production implementation blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Scope reminder

This verdict binds only exact pair `57ef3d32452d990af98fda5edfe485376b772723` / `93a89ba61306d840a008813f62f26a34d54850f4` and the Gate above.

No real authority-root materialization is authorized. No source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/publication mutation, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 action is authorized by this review.
