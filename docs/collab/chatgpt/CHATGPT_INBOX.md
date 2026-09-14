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

- immediate prior live blob SHA: `9190aefd85ca9657235331db50768cd62eca3475`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 request-instance design v0.3 REQUEST_CHANGES

Formal pair:
- root design SHA: `0fc7965d9d1b55a99d0b1a384764f68464b02949`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.3.md:20)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_instance_design_v03_0fc7965_93a89ba.md`

Canonical review commit:
`19d75e5cc7afc9a6fe8dc6a0eac68c32950b5631`

Current blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production/Authority: `0`; Evidence/Scope: `0`; child/runtime: `0`.

Closed in v0.3:
1. v0.2's read-only construction I/O allowlist remains explicit and closed.
2. The prior DS remote-ref finding is substantively fixed: exactly two remote queries are allowed, one for advertised `V2` identity and one for fixed authority-ref absence.
3. Local fixed authority-ref absence and remote fixed authority-ref absence are separately bound; the latter is sourced only from the exact fixed-ref remote query.
4. Formal parent/base/replay identities remain frozen; v1.6 remains consumed/non-reusable; the design remains construction-only and requires a new exact request review before any Stage-1 attempt.
5. Formal root Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime production bytes are unchanged.

Remaining HIGH — empty remote stdout is not sufficient absence authority:
- v0.3 line 20 says the exact fixed-ref `git ls-remote` query establishes remote absence when its output is empty, and binds command/output bytes/length/SHA.
- It does not require or bind a successful command return code.
- A transport/DNS/auth/remote-access failure can also leave stdout empty. That is observation failure, not proof that the authority ref is absent.

Exact remediation:
1. Keep the exact two-query network allowlist and all current zero-mutation boundaries.
2. Require both remote queries to complete successfully (`return code == 0`) before their stdout is authority, and bind each return code into the future canonical request.
3. Define fixed authority-ref remote absence as exactly successful exact query + zero stdout bytes/zero result lines. Nonzero exit, timeout, transport/auth error, malformed result, or nonempty stdout must fail `BLOCKED_AUTHORITY_NOT_CLOSED` and must not be interpreted as absence.
4. Prefer binding stderr bytes/length/SHA too, or freeze an equivalent explicit successful-query diagnostic contract.
5. Preserve one-request-only construction, frozen output paths and identities, and independent same-pair request review before any execution authority.

Still NOT authorized:
- request construction under this unresolved design;
- Stage-1 retry/materialization/execution;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O outside the approved construction allowlist;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
