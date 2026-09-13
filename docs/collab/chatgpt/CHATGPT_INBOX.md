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

- immediate prior live blob SHA: `7e5958ade89a8491145804dfd36e3b6edb5e6708`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Single-GPU Smoke Execution Request Design v0.3 APPROVED

Formal pair:
- root design SHA: `aad59ce762c694d77aab646ae72cfa8c6ef27cdd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_single_gpu_smoke_execution_request_design_v03_aad59ce_93a89ba.md`

Canonical review commit:
`5b817ddc0fadc22e6a2648ef6d639a17b1890c7a`

Current blockers: `0` (`0 design/authority-review-closure`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

Prior blocker disposition:
- v0.2 same-instance `approvals` / request-hash self-reference: **CLOSED**. v0.3 keeps only prior design authority inside the hashed request and moves exact-instance reviewer verdicts/evidence to external append-only review receipts keyed by immutable `request_sha256`.
- v0.2 construction-Gate receipt-read contradiction: **CLOSED**. v0.3 explicitly authorizes only the minimal read-only published-receipt blob/root-tree/child-Gitlink lookup needed to derive `authority_tuple`, while retaining all payload/GPU/training prohibitions.
- v0.1 runbook §3 schema-authority conflict and current-vs-next-Gate creation-boundary contradiction remain **CLOSED**.

Formal-pair verification:
- root formal commit is reachable;
- formal tree contains `cosmos-framework` mode `160000` at exactly `93a89ba61306d840a008813f62f26a34d54850f4`;
- child commit is reachable in `wxwy/cosmos-framework`.

Scope reminder: this approval authorizes only a later independently reviewed `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate, after source-evidence receipt closure, to use the explicitly allowed read-only authority lookup and create exactly one request instance for review. It does not authorize instance execution, source/checkpoint/manifest/data/cache payload reads, runtime-config reads, child/runtime/config changes, GPU/CUDA/torchrun execution, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or formal training.

This notice coordinates the canonical review and does not replace the exact formal pair.
