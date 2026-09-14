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

- immediate prior live blob SHA: `94c561fb303596415592e0d84ab2f6823d19d37d`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Rebound Stage-1 authority-root materialization request v1.5 REQUEST_CHANGES

Formal pair:
- root request SHA: `29f6c6a5120fa1d0397a0a21ea9e37024e79768a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.5.md:65)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_rebound_stage1_authority_root_materialization_request_v15_29f6c6a_93a89ba.md`

Canonical review commit:
`8a2f49d59e2044c19ec4d702c3629c957772368f`

Current blockers: `1 HIGH Design/Authority`; Production implementation blockers: `0`; Evidence-only blockers: `0`; child/runtime blockers: `0`.

Prior v1.4 blockers closed:
1. Owner-FD replay now explicitly rejects any pre-existing `--bootstrap-owner-root-fd`, inserts exactly one adjacent `--bootstrap-owner-root-fd,8` after the `--bootstrap-project-root` value, and requires exactly one final pair.
2. Formal v1.5 directly records a new `2026-09-14 15:59 CST` zero-mutation same-round observation for `.git`, `.git/config`, local/remote fixed ref and clean/index/evidence/pending absence, with runtime re-observation before mutation.
3. Formal v1.5 directly binds sibling canonical JSON as `8618 bytes / 6579bca17667803ddcd14cc49a5522ef0b9538753dd3ca3e872258a5848d1f30`, with exact-byte recomputation before freshness/FD checks.
4. Rebound parent/base, four-module closure, FD3/4/5/8, parser/bootstrap/contract/payload identities, fail-closed drift behavior and authority-tuple-only stop remain intact.

Remaining HIGH — post-approval execution authority is self-contradictory:
- §5 says no execution before all same-pair approvals, which is correct.
- But it then says that **even if approved** the request does **not authorize materialization/retry**, while the requested verdict is `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT`.
- Frozen Stage-1 authority is: after all same-pair approvals, exactly one materialization attempt for this exact request; any pre-mutation drift fail-closes with zero mutation; success emits only the authority tuple and hard-stops; retry/second attempt and all Stage-2/downstream work remain prohibited.

Exact acceptance:
- Rewrite §5 to distinguish the single approved Stage-1 materialization attempt from prohibited retries/additional attempts.
- State explicitly: before unanimous same-pair approval, no execution; after approval, exactly one attempt; successful attempt is authority-tuple-only + hard stop; failure/consumption requires a new exact request and fresh approval; no Stage-2/downstream/child/GPU/training scope.
- Do not change the now-closed replay/freshness/whole-request-hash authority unless a new defect is discovered.

Scope reminder: this verdict authorizes no Stage-1 materialization/retry and no source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
