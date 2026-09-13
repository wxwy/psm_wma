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

- immediate prior live blob SHA: `f108b860abdad02b20095431fa9b1bcd6b5efc0a`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Single-GPU Smoke Execution Runbook Terminal-Status Remediation APPROVED

Formal pair:
- root design SHA: `5053ed40065bfa0b8e1d755756b0565bd2d5ef31`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-RUNBOOK-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_single_gpu_smoke_execution_runbook_design_terminal_status_remediation_5053ed4_93a89ba.md`

Canonical review commit:
`36a9e46e64cdd02763e0c8f6bcf79e81a8451aaf`

Current blockers: `0` (`0 design/admission`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

Prior blocker disposition:
- prior `failure.json` / `MANUAL_STOP` terminal-status ABI contradiction: **CLOSED**. The formal remediation freezes terminal statuses `PASS | FAIL | BLOCKED | MANUAL_STOP`, makes `MANUAL_STOP` a distinct non-PASS terminal, requires `failure.json` for `FAIL | BLOCKED | MANUAL_STOP`, freezes its key set, requires terminal-status equality with `smoke_summary.json.status`, and requires the last committed transaction identity for manual stop.
- prior single-GPU smoke design `world_size` contradictory FAIL predicate remains **CLOSED**.

No new findings. The remediation is docs-only and does not weaken receipt-derived authority binding, non-overridable request schema, no-shell command grammar, exactly-one-GPU/no-`torchrun` admission, no-resume/sidecar/checkpoint-write/eval/inference restrictions, `num_workers=0`, bounded `1..100` steps, canonical chronology/GA-window failure transaction, write allowlist, or no-real-execution scope.

Scope reminder: this approval closes only the exact docs-only runbook-design Gate. It authorizes only preparation and review of a later receipt-bound execution-request design. It does not authorize creation/execution of an execution request, real source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/publication, child/runtime/config changes, GPU/CUDA/torchrun execution, training, evaluation, inference, LIBERO4IN1, matched smoke, sidecar work, checkpoint write, or formal training.

This notice coordinates the canonical review and does not replace the exact formal pair.
