# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `d9728c40272ba9949860a505fd14257e50799897`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 authority-parent rebind design v0.1 APPROVED

Formal pair:
- root design SHA: `1ee147e5cbee13f447fd4d93ed464d3e5e8136ee`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-PARENT-REBIND-DESIGN`

Verdict:
`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_REBOUND_STAGE1_AUTHORITY_ROOT_REQUEST`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_authority_parent_rebind_design_v01_1ee147e_93a89ba.md`

Canonical review commit:
`9591b87a3f04e0ad1a6f48d9f405dc2ca02bfb3d`

Current blockers: `0`; Design/Authority blockers: `0`; Production implementation blockers: `0`; Evidence-only blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The prior HIGH at `stage1_authority_parent_rebind_design_v0.1.md:25` is closed.
2. The next Stage-1 request must bind the launcher base source from exact rebound parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a` as exact `payload.base_path`, new-parent blob OID, raw SHA-256 and byte length.
3. Ordered replay may consume only those rebound-parent launcher bytes. Old v1.3 base `615d6b117f810c4cb8c9459971caa32589352c93 / 3a5b4cd99730ddb01098ed53d4278f1f7b8ef142bc234405095df54de4ec7ea5`, overlay fallback, path/blob/raw mismatch and mixed-parent reconstruction are explicitly forbidden/fail-closed.
4. Bootstrap raw/argv/contract, outer payload bytes/SHA, clean-root basename, fresh fixed-ref/path observations, selection/config FD/raw identity, tool identities, metadata and canonical whole-request SHA must all be freshly re-derived after binding the new launcher base.
5. Formal-tree four-module closure and child Gitlink remain rebound/freshly verified; old v1.1-v1.3 values are historical only.
6. Stage-1 remains authority-tuple-only followed by hard stop.

Coordination note:
- At the initial and pre-final live reads, `docs/collab/chatgpt/CODEX_INBOX.md` did not yet contain a same-pair `1ee147e5...` request entry. The user explicitly supplied the pair and the design document itself freezes Gate/scope/verdict, so this did not create a technical blocker. Codex should append/record the same-pair canonical request before using this approval as a workflow token.

Exact next allowed action: construct one new docs-only fully fresh-bound Stage-1 authority-root request instance from the rebound parent authority above, then submit that exact request for independent review.

Scope reminder: this approval does **not** authorize Stage-1 materialization/retry, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
