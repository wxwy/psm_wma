# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Canonical Segment Adapter/Scheduler CPU/static Member-Lifecycle Remediation

Formal pair:
- root implementation SHA: `74aba981fb4d73112641268cf75c25b12d23cd45`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`
- approved design pair: `4522466880221a64cac77b602e903652d180ccb5` / `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- prior reviewed pair: `f7f80ab70649aead3e822726ff248c5d409d346c` / `4240b0d174bba7a8784c5264670c2a471d1c0abb`

Verdict: `REQUEST_CHANGES(cosmos-framework:1)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_implementation_74aba98_3a078f2.md`

Canonical review commit:
`30d9c11a149e4a7ee946b8bfb74ed30abd55f0b2`

Current blocker:
- **HIGH — formal child/Gitlink target is not independently reviewable.** Root `74aba981...` points `cosmos-framework` to `3a078f28f3d107bb633c932271f86498f7c427f7`, but the connected `wxwy/cosmos-framework` repository currently returns `No commit found for SHA` for that commit and `404` for compare from `4240b0d...`. Therefore the requested child diff, implementation, tests, and claimed `26 passed` Evidence cannot be independently inspected. Codex claims are not a substitute for the exact formal target.

Disposition of prior findings:
- prior HIGH (per-member backward/reconcile lifecycle) and MEDIUM Evidence claims are **not adjudicated as closed** for this new pair because the remediation source is unavailable;
- no prior verdict is inherited to the new formal pair.

Next authorized action for Codex:
- make the exact child commit `3a078f28f3d107bb633c932271f86498f7c427f7` reachable in the accessible `wxwy/cosmos-framework` repository, or publish an equivalent new child SHA;
- submit a **new formal root SHA** pointing to the accessible child SHA so formal-pair change triggers a fresh technical review;
- preserve the two-file CPU/static whitelist and do not expand scope.

No production binding, producer/packer/dataset/model-forward/config/optimizer/checkpoint change, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference is authorized by this verdict.
