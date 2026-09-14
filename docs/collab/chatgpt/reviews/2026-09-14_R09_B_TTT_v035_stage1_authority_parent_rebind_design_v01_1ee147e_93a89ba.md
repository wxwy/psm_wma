# ChatGPT Independent Review — R09-B TTT v0.3.5 Stage-1 Authority Parent Rebind Design v0.1

**Date:** 2026-09-14  
**Formal root:** `1ee147e5cbee13f447fd4d93ed464d3e5e8136ee`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-PARENT-REBIND-DESIGN`

## 1. Pair / scope lock

- Fresh-locked remote `V2` to `1ee147e5cbee13f447fd4d93ed464d3e5e8136ee` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`.
- The live Codex inbox did not yet contain a same-pair `1ee147e5...` request entry at review time. The user explicitly supplied this exact pair and the design document itself freezes the Gate, scope, requested verdict, and prohibitions; this is recorded as a coordination anomaly, not a technical blocker. Codex should still record the same-pair request in its canonical inbox before acting on the approval.
- Verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Technical delta versus rejected design pair `3e0c1657644b2b3c03f93c25ad910fa5d50a9ebd / 93a89ba...` is the parent-rebind design amendment only; no production or child/runtime change is introduced by this formal root.

## 2. Prior blocker closure

The prior HIGH Design/Authority blocker is closed.

The rejected `3e0c165...` design required the outer payload replay to be re-derived but did not explicitly make the new parent launcher source itself first-class request authority. That left room for a mixed-parent request with `formal_parent=08d...` while replay still started from the old v1.3 launcher base (`base_blob=615d6b117f810c4cb8c9459971caa32589352c93`, `base_sha256=3a5b4cd99730ddb01098ed53d4278f1f7b8ef142bc234405095df54de4ec7ea5`).

`1ee147e5...` now explicitly requires the next Stage-1 request to bind, from the exact rebound parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`:

- the exact launcher `payload.base_path`;
- its new-parent blob OID;
- its raw SHA-256;
- its byte length.

It further freezes that ordered replay may consume only those exact new-parent bytes, and that any path/blob/raw mismatch must fail-close. The old `615d6b... / 3a5b4cd...` base, overlay fallback, and mixed-parent reconstruction are explicitly prohibited.

After that base binding, the request must freshly recompute bootstrap raw/argv/contract, outer payload bytes/SHA, clean-root basename, fixed-ref freshness, selection/config FD/raw identity, Git/Python identity, sanitized environment, metadata, and canonical whole-request SHA. Old v1.1-v1.3 values are historical evidence only and cannot be copied as authority.

## 3. Authority consistency

The rebound design remains internally consistent with the closed CPU/static grammar remediation and the frozen Stage-1 split contract:

1. New Stage-1 parent is exactly `08d5828cdb4c12afa3b798ff01826c91ceb8755a`; old parent `b3595395427114f73ff53a19a0c2b9180e39905f` is forbidden for the next request.
2. Child Gitlink remains exactly `93a89ba61306d840a008813f62f26a34d54850f4`.
3. Formal-tree four-module closure and all parent-dependent module blob/raw identities must be re-resolved from the rebound parent.
4. Fixed ref remains `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`; local and remote ends must be freshly observed absent during construction.
5. Stage-1 PASS remains authority-tuple-only followed by hard stop.
6. Approval of this design authorizes only construction of one new docs-only, fully fresh-bound request instance and its later independent review. It does not authorize execution.

## 4. Formal verdict

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_REBOUND_STAGE1_AUTHORITY_ROOT_REQUEST`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production implementation blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Execution boundary

This approval binds only exact pair `1ee147e5cbee13f447fd4d93ed464d3e5e8136ee / 93a89ba61306d840a008813f62f26a34d54850f4` and this docs-only parent-rebind Design Gate.

It authorizes only construction of a new exact docs-only Stage-1 request instance using the rebound-parent authority above, followed by independent same-pair review.

It does **not** authorize Stage-1 materialization/retry, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
