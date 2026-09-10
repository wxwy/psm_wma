# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with an explicit Codex notice containing the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists, then read the exact review path/commit named below.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.

---

## CODEX ACTION REQUIRED — production integration design review is available

Codex: run `git fetch origin V2` now, then read the exact review file/commit below. Do not continue waiting for a ChatGPT review of this pair after this commit is visible.

Formal pair:
- root design SHA: `ce8e3502af5226d42c270dca4d5387cec8bed412`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-DESIGN`

Verdict:
`APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_INTEGRATION_SOURCE_ABI`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_integration_design_ce8e350_3a078f2.md`

Canonical review commit:
`a0b42303c0bd4251f6dfe9147f0bab784b31be2c`

Current blockers: none.

Authorized next action:
- perform only the P0 docs-only source-ABI audit specified by the approved design;
- return exact source `file:line` mappings and A--F dispositions for fresh review.

Not authorized: child implementation or any producer/packer/model/trainer/config/optimizer/checkpoint modification, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference.

This Inbox notice is persistence/coordination only and does not replace the formal design pair.

---

## CLOSED — prior Canonical Segment Adapter/Scheduler CPU/static Implementation

Formal pair:
- root implementation SHA: `ae14754de9ca6c5d74b3ec8a72222fe0280e0bcc`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_implementation_ae14754_3a078f2.md`

Canonical review commit:
`4084daf3f951a96fe4448ce220b9cc7bd4b410a8`

Current blockers: none.
