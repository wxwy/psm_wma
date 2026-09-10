# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Canonical Segment Adapter/Scheduler CPU/static Implementation

Formal pair:
- root implementation SHA: `61f469b0a142e340becd8038e2be23eca63b73e4`
- child/Gitlink SHA: `355a44087d0149b4875fb37e81d726523af66fdd`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`
- approved design pair: `4522466880221a64cac77b602e903652d180ccb5` / `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- request/bookkeeping SHA: `9425ff8046e44a321ef21074028f79a9ebd1b434`; later poll/review-persistence commits do not replace the formal pair.

Verdict: `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:241)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_implementation_61f469b_355a440.md`

Canonical review commit:
`bca34885ceba7a5ee80f52b5b684831b56731b69`

Current blockers:
- **HIGH 1 — projected scheduler authority incomplete.** `ProjectedSchedulerState.project_commit()` blindly replays externally supplied members and can overwrite a bound slot without enforcing same episode/category/source + cursor+1. The state also lacks the frozen target-distribution/chronology/per-category permutation authority, does not perform weighted-deficit admission, and does not advance queue position/permutation during normal projected planning. It therefore cannot prove the v0.2 §4-§5 cross-tail/rebind/queue planning contract.
- **HIGH 2 — retry is not behaviorally pre-backward.** `CanonicalGAWindowPlan.retry_first_member_pre_backward()` only checks attempt/member index; it has no window lifecycle/backward-started/completed-member state. The original plan can still produce attempt-1 after a successful member-0 reconcile, and later/post-backward failures do not terminalize/clear/suppress the whole window as frozen by v0.2 §6.
- **MEDIUM 1 — Evidence matrix incomplete.** The test named `unequal_count` actually uses 3/3 counts; there is no shared `.backward()` witness, no multi-member tail/rebind projected plan, and the rollover test does not prove two fresh scheduler states yield the same next-epoch sequence/provenance.

Closed / non-blocking:
- child diff is limited to the two approved new CPU/static files;
- S0/native count semantics and stream-major gather are consistent;
- original-window weighted objective formula is correct;
- v0.3 UTF-8/NUL/ASCII SHA preimage implementation is correct;
- no forbidden production binding/real I/O/GPU/training scope was introduced.

Next authorized action for Codex:
- narrow CPU/static remediation only inside the approved adapter/scheduler contract-double scope and adjacent tests;
- implement exact projected continuation/rebind/admission/queue progression and batch-window retry/failure lifecycle;
- close the missing direct Evidence above;
- submit the resulting new root + child formal pair for fresh implementation review.

No production binding, producer/packer/model-forward/dataset/manifest/config/optimizer/checkpoint change, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference is authorized by this verdict.
