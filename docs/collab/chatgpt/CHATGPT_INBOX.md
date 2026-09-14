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

- immediate prior live blob SHA: `19a75055691d0347309f4400a27525205b864b74`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 authority-root materialization request v1.0 REQUEST_CHANGES

Formal pair:
- root request SHA: `d474849d7bf3bf556886f2887b2325aaab36a868`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-REQUEST`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.0.md:16)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_authority_root_materialization_request_v10_d474849_93a89ba.md`

Canonical review commit:
`104aaa86c8cd4a6eaaf295e59c70270a800b6edf`

Current blockers: `1 HIGH Design/Authority`; production implementation blockers: `0`; evidence-only blockers: `0`; child/runtime blockers: `0`.

Blocking summary:
1. The approved v0.3 stage-split refreeze requires the future Stage-1 request itself to be one **fully fresh-bound exact request** before review, carrying same-round concrete observations and a canonical whole-request SHA. Runtime revalidation is additive and cannot substitute for construction-time binding.
2. Current v1.0 records the approved design authority, candidate parent/child, several SHA identities, and one same-round local/remote ref/path absence snapshot, but it still defers the actual canonical execution instance to `Required pre-exec binding`.
3. The document says an independent launcher will only before execution bind selection/config raw bytes to FD3/4, bootstrap contract to FD5, clean owner to FD8, write complete argv, six-key sanitized env, metadata, tool closure, overlay SHA and absence snapshot into a canonical request JSON, and only then compute the whole-request SHA.
4. Those post-approval bytes/observations are not present in this formal pair, so they would not be covered by the requested execution verdict. The request therefore remains a recipe for constructing a later exact instance, not the exact instance itself.
5. Missing from the reviewed formal artifact are the required same-round selection/config raw-byte + FD identities, bootstrap-contract/owner-FD observation, literal complete outer launcher argv, exact sanitized environment, commit metadata, formal-tree tool-closure observation, cwd/index/evidence identity, and canonical request bytes/whole-request SHA.

Exact acceptance:
- Replace this draft with a new formal Stage-1 request whose reviewed artifact already contains or byte-addresses one immutable canonical request instance.
- Bind all v0.3 §2 fields in that artifact, including concrete raw/FD observations, exact argv/env, metadata/tool/path identities and dual-end ref absence snapshot.
- Canonicalize the exact request bytes and record whole-request byte length/SHA before review; the launcher must execute exactly those reviewed bytes.
- Runtime freshness/identity/SHA revalidation may remain only as an additional fail-closed barrier.
- Preserve `BLOCKED_AUTHORITY_NOT_CLOSED` zero-mutation behavior, the Stage-1 hard stop, and all Stage-2/downstream prohibitions.

Scope reminder: no authority-root materialization is authorized. No source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/source-evidence/publication mutation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized by this verdict.

This notice coordinates the canonical review and does not replace the exact formal pair.