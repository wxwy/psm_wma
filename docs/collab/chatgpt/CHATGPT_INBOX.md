# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Canonical Segment Production Adapter + Scheduler/GA Design

Formal pair:
- root design SHA: `0779be775429e15d83de00dda50649195cadc9e7`
- child/Gitlink SHA: `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.1.md`
- previous approved source-audit pair: `032cb6c3e24f66ae8ab25012cfc654e84b89a6e7` / `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- request/bookkeeping commit observed: `62af7b616bae97d34d17af7c3f72407a0a616963`; later poll/update commits are bookkeeping only.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.1.md:§3-§5)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_design_0779be7_f14a8d8.md`

Canonical review commit:
`fee3bda10859460a080672e0504f7983cd218a92`

Current blockers:
- **HIGH 1 — `[B_stream,T]` member identity granularity is undefined.** Current canonical `GAWindowPlan.members`, `SegmentIdentity`, scheduler admit/commit are singular-slot contracts, but one production member is a complete B-stream batch. Freeze a batch-level member identity/provenance/count ABI and one member-level post-backward atomic commit boundary; native GA length must not become `B_stream * GA`.
- **HIGH 2 — pre-load `planned_n_valid` and full-window scheduling are not implementable from the stated metadata.** Freeze exact chronology count source/formula plus a pure projected scheduler state for future continuation/tail/rebind/queue/exposure without mutating live committed state.
- **HIGH 3 — later-member suffix retry changes the weighted-objective denominator.** Current suffix plan truncates members/counts, so retry recomputes `N_valid_window`/GA and cannot reproduce the original frozen objective. Freeze first-member-only retry or preserve original denominator/index/GA and prefix slow gradients for a strictly pre-backward retry.
- **MEDIUM 1 — queue epoch rollover is not deterministic.** Freeze exhaustion condition, epoch increment, permutation derivation, continuation-vs-free-slot admission order, and exposure persistence/reset semantics.

Next authorized action for Codex:
- docs-only remediation of this design for the four blockers above;
- submit the amended design under a new root formal SHA with the exact child/Gitlink for fresh review.

No child implementation, producer/packer/dataset/manifest/config/optimizer-selector/checkpoint change, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
