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

- immediate prior live blob SHA: `e84f3df7dcab2d105a1770ac7cde5bca79838538`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Single-GPU Smoke Execution Runbook Design REQUEST_CHANGES

Formal pair:
- root design SHA: `5912e7d06c53e8a0cf650d4b2886f10cd72e3311`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-RUNBOOK-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_runbook_design_v0.1.md:127)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_single_gpu_smoke_execution_runbook_design_v01_5912e7d_93a89ba.md`

Canonical review commit:
`c7f928bd57d5b27e58c1325eb4815716ce178d9e`

Current blockers: `1 HIGH` (`1 design/failure-semantics`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

Blocker:
- §6 freezes `failure.json` as allowed only for `FAIL/BLOCKED`, while §7 separately mandates that operator `MANUAL_STOP` writes `failure.json` with `MANUAL_STOP` and the last committed transaction identity. Refreeze one terminal outcome taxonomy before execution-request design: either explicitly permit/require `FAIL | BLOCKED | MANUAL_STOP`, or explicitly classify manual stop as a named FAIL reason and use that consistently in the allowlist and schemas.

Prior blocker disposition:
- single-GPU smoke design `world_size` contradictory FAIL predicate: **CLOSED** and remains closed.

Scope reminder: no execution-request design approval is granted from this pair. This review does not authorize creation/execution of an execution request, real source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, matched smoke, sidecar, checkpoint write, or formal training.

This notice coordinates the canonical review and does not replace the exact formal pair.