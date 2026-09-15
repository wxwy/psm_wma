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

- immediate prior live blob SHA: `cbacd448d269797b3b6e18fa3e087d9ade654217`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 request-instance construction authority V22 REQUEST_CHANGES

Formal pair:
- root implementation SHA: `36f5216428a28027ac4d33c17ba4456fb93eb359`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AUTHORITY-V22`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_construction_authority_v2.2.md:11)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_request_instance_construction_authority_v22_36f5216_93a89ba.md`

Canonical review commit:
`02a76f87797fdce01f0c38f256d4458cdc0185f1`

Current blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production/implementation: `0`; Evidence/Scope: `0`; child/runtime: `0`.

Positive closure:
- formal root resolves and binds `cosmos-framework` mode `160000` exactly to the declared reachable child;
- V22 is docs-only and has not executed real pre-C/C, request-pair construction, materialization, source-evidence, child/runtime/config mutation, GPU or training;
- previously closed ContractV05/FreshnessGuard CPU-static guarantees remain intact: C01-C15 closure, nine-entry local freshness domain, remote-pre-C-only, same-object patch handoff, exactly-one opaque apply, exact readback, hard stop and terminal no-retry.

HIGH 1 — the real one-shot write is still delegated to future capability identities that are not independently frozen before this construction approval:
- V22 says future real pre-C will seal the unique `PatchConsumerV1`, `FreshnessGuardV1` and post-write verifier identities, but the reviewed V22 authority does not name their exact provider/module/path/blob/callable values and does not require a second independent exact-plan review after real pre-C;
- inherited production validation proves only shape/self-consistency for these host capabilities: non-empty provider/module/path, 64-hex blob text, callable/qualname agreement and fixed ABI/transport; the verifier likewise checks callable/qualname consistency only;
- therefore a future real pre-C could inject a different self-consistent guard/consumer/verifier and proceed to the irreversible one-shot C under an approval issued before those exact code identities existed in the review boundary.

Required remediation — choose one explicit authority model:
1. single-stage: V22 freezes the exact real consumer, freshness guard and readback-verifier provider/module/path/blob/callable identities before approval, and pre-C requires exact equality; or
2. two-stage: this Gate authorizes only one real non-consuming pre-C rehearsal; after it seals exact capability/verifier/plan identities, an independent exact-plan approval is required before the opaque C call.

Preserve the existing nine-entry freshness domain, remote-pre-C-only rule, exact pair bytes/paths, one-call/no-retry semantics and hard stop. No construction approval issued before real pre-C may authorize an arbitrary later self-consistent host capability.

Until this is closed, real pre-C/C, request-pair construction, materialization/source-evidence, real I/O, child mutation, GPU and training remain forbidden.

This notice coordinates the canonical review and does not replace the exact formal pair.
