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

- immediate prior live blob SHA: `aaad3818854488701c4af44959dbeb0b2aa478e9`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Single-GPU Smoke Execution Request Design v0.2 REQUEST_CHANGES

Formal pair:
- root design SHA: `0874bb153ba81ee29eee84f0bde311bbf2d1ebe0`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_request_design_v0.2.md:87)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_single_gpu_smoke_execution_request_design_v02_0874bb1_93a89ba.md`

Canonical review commit:
`9cfcccc71fa803bc4f379d31945ffe75ecc9e2d7`

Current blockers: `2 HIGH` (`2 design/authority-review-closure`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

Prior v0.1 blocker disposition:
- runbook §3 / request-v0.1 schema authority conflict: **CLOSED**. v0.2 explicitly version-supersedes only runbook §3 and preserves the other runbook controls.
- current-Gate / next-Gate request creation contradiction: **CLOSED**. v0.2 makes this Gate design-only and moves creation of exactly one instance to a separately reviewed construction Gate after receipt closure.

Current blockers:
- `design:87`: `approvals` is inside the canonical request covered by `request_sha256`, yet must contain this exact instance Gate's formal root/child, same-pair final verdicts, and review evidence locators. Those values exist only after the exact request has been reviewed; adding them changes the request bytes/hash (and, if committed, formal root), invalidating the embedded same-pair verdict. Move same-instance review results outside the hashed request, or bind only already-final prior authority inside it; freeze exact nested schema if `approvals` remains.
- `design:102-104`: §2 requires the future construction Gate to derive `authority_tuple` by read-only Git blob lookup of the closed receipt, but §4 says that Gate may not read real input outside the request itself. Since the request does not yet exist, construction cannot satisfy both. Explicitly authorize only the minimal read-only receipt/root/tree/Gitlink authority lookup (while keeping source/checkpoint/manifest/data/cache payload I/O and GPU/training prohibited), or provide a separately approved immutable authority package as the sole construction input.

Formal-pair verification:
- root formal commit is reachable;
- formal tree contains `cosmos-framework` mode `160000` at exactly `93a89ba61306d840a008813f62f26a34d54850f4`;
- child commit is reachable in `wxwy/cosmos-framework`.

Scope reminder: no request-instance creation or execution is authorized from this pair. This review does not authorize real source/checkpoint/manifest/data/cache I/O, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or formal training.

This notice coordinates the canonical review and does not replace the exact formal pair.
