# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with an explicit Codex notice containing the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists, then read the exact review path/commit named below.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.

---

## CODEX NOTICE — canonical production source-ABI audit v0.3 approved

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root audit SHA: `395dadff0b17ed6206887e372718bb166aa63b40`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_IMPLEMENTATION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_integration_source_abi_audit_395dadf_3a078f2.md`

Canonical review commit:
`2e3d88a526e70fcb3c885bfed156489f3dca604f`

Current blockers: none.

Closure:
- prior v0.2 HIGH (`1/GA^2` from duplicate GA normalization) is CLOSED;
- canonical branch must preserve native GA clock/DDP sync/optimizer cadence while applying exactly one scaled backward to the already-window-normalized `L_member`;
- No-Local ordinary path keeps the native `/GA` behavior unchanged.

Authorized next action:
- create only the P1 **docs-only production ABI implementation design** on a new formal root SHA;
- that design must freeze its own exact whitelist and segment-level production seam before any implementation.

Not authorized: child implementation, producer/packer/dataset/model/trainer/config/optimizer/checkpoint modification, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference.

This notice is coordination only and does not replace the formal pair.

---

## CODEX ACTION REQUIRED — canonical production source-ABI audit v0.2 still needs remediation

Codex: run `git fetch origin V2`, then read the canonical review below. Do not enter P1 on this formal pair.

Formal pair:
- root audit SHA: `e0cc97e7178d345c6575bb7f73f540b8ec056f1c`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.2.md:32)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_integration_source_abi_audit_e0cc97e_3a078f2.md`

Canonical review commit:
`e19f34c25d29111121d93b9391e1e074cc15c714`

Current blockers: **1 HIGH**.

- CLOSED: v0.1 native-total-loss weighting blocker.
- CLOSED: v0.1 real packer/loss-mask source-map blocker.
- NEW HIGH: v0.2 correctly defines the already-GA-normalized canonical objective, but then routes that scalar through the ordinary trainer `loss / grad_accum_iter` normalization. Full-valid windows would become `1/GA^2`. P1 must preserve the GA clock/DDP sync/optimizer cadence while backwarding the canonical objective with no second `/GA`; No-Local ordinary behavior remains unchanged.

Authorized next action:
- docs-only remediation of this P0 source audit on a new formal root SHA;
- explicitly freeze exact once-only GA scaling and a full-valid `1/GA` (not `1/GA^2`) algebra witness.

Not authorized: P1 implementation, child modification, producer/packer/dataset/model/trainer/config/optimizer/checkpoint changes, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference.

This Inbox notice is coordination only and does not replace the formal pair.

---

## CODEX ACTION REQUIRED — canonical production source-ABI audit needs remediation

Codex: run `git fetch origin V2`, then read the canonical review below. Do not enter P1 on the current formal pair.

Formal pair:
- root audit SHA: `2d34eedcf30163de9e011bf1c4166199e916a2f6`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.1.md:74)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_integration_source_abi_audit_2d34eed_3a078f2.md`

Canonical review commit:
`d78583e7e15ee807766259cab71d2086b3c417ec`

Current blockers: **1 HIGH, 1 MEDIUM**.

- HIGH: P1 cannot multiply the whole native total loss by `N_valid/N_window`; the frozen objective must keep valid-consumer `consumer_loss` weighting separate from `auxiliary_loss/GA`, with native sample-level/DDP scaling applied exactly once.
- MEDIUM: §20.2-A source map must reach the real `pack_input_sequence` ordering/payload ABI and real flow-loss mask/reduction implementation before P0 can be declared complete.

Authorized next action:
- docs-only remediation of this P0 source audit, producing a new formal root SHA while keeping any unchanged child SHA explicit;
- no implementation is authorized.

Not authorized: child implementation, producer/packer/dataset/model/trainer/config/optimizer/checkpoint modification, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference.

This Inbox notice is coordination only and does not replace the formal pair.

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
