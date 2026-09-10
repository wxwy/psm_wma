# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Canonical Segment Adapter/Scheduler CPU/static Queue-Authority Remediation

Formal pair:
- root implementation SHA: `6fc0d111756177e60b06325c8d400dc6a25972ef`
- child/Gitlink SHA: `86091472fd9a49e0b5b8a35d7797abb2d70b4fa8`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`
- approved design pair: `4522466880221a64cac77b602e903652d180ccb5` / `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- request/bookkeeping SHA: `c615315c412bd79ac6017518a5f3780cda3106a0`; later handoff/poll/review-persistence commits do not replace the formal pair.

Verdict: `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:367)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_implementation_6fc0d11_8609147.md`

Canonical review commit:
`a76a0e20fc57ab614003e19f826d08150639b8c1`

Current blockers:
- **HIGH 1 — dynamic-slot continuation remains broken.** Fresh queue admission correctly binds a selected episode to the current free slot, but bound continuation lookup still requires the immutable catalog continuation row to already carry that runtime `slot_id`. An episode admitted to a different free slot can therefore fail exact `cursor+1` continuation. Resolve chronology successor by episode/category/source/cursor independently of placeholder slot, then bind it to the current stable slot.
- **HIGH 2 — attempt-1/failure lifecycle is still forgeable.** Removing the plan retry method is insufficient because `CanonicalGAWindowPlan(..., attempt=1)` / `replace(..., attempt=1)` remains externally constructible without transaction-issued authority. `terminalize()` also accepts phantom or skipped future indices because it does not require the exact current in-range member.
- **MEDIUM 1 — Evidence does not expose these two bypasses.** Missing direct test for an episode admitted to a different slot then continued, direct attempt-1 constructor/replace forgery rejection, and `terminalize()` phantom/skip rejection.

Closed / improved this round:
- fresh episode queue is separated from continuation chronology;
- canonical fresh queue ordering and duplicate provenance rejection;
- same-member same-category multi-free-slot projected reservation;
- projected rollover within one frozen multi-member GA plan;
- exact FIFO cached transition reconcile and out-of-order no-mutation;
- public plan-level retry method removed;
- backward/reconcile member bounds and final transaction seal;
- scope remains exactly the two approved CPU/static files; no forbidden production/I/O/GPU/training changes.

Next authorized action for Codex:
- narrow CPU/static remediation only in `canonical_segment_adapter_scheduler.py` and its adjacent test;
- make continuation slot-neutral until bound to the current stable slot;
- make transaction/capability issuance the only valid attempt-1 authority and require exact current in-range member for terminalization;
- add direct public-path Evidence for both fixes;
- submit a new root + child formal pair for fresh review.

No production binding, producer/packer/model-forward/dataset/manifest/config/optimizer/checkpoint change, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference is authorized by this verdict.
