# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Canonical Segment Supersession Source Audit

Formal pair:
- root source-audit SHA: `032cb6c3e24f66ae8ab25012cfc654e84b89a6e7`
- child/Gitlink SHA: `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-SUPERSESSION-SOURCE-AUDIT`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_supersession_source_audit_v0.1.md`
- previous formal pair: `5e4fbd3cf0542fa6df9b1f08eb9ea1736792033d` / `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- request/bookkeeping V2 HEAD observed during review: `50171c503285657fba515573636c572ce6a40a6c`

Verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_SUPERSESSION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_supersession_source_audit_032cb6c_f14a8d8.md`

Canonical review commit:
`1beb1808aa96b2fe819819320eaee6500333cbe7`

Closure:
- CLOSED: previous MEDIUM provenance blocker. §1 now freezes the exact canonical formal chain `e4b2d2f/80aec09` → `1f6c0ba/80aec09` → `d1f155d/333792e` and names `docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.3.md`.
- CLOSED: `ee07ca0/f14a8d8` is explicitly source-snapshot-only and cannot substitute for canonical formal authority.
- A–H source routing and Gate sequencing remain acceptable; no second implementation authority was found.

Current blockers: none.

Next authorized action for Codex:
- create the next canonical segment supersession production-design Gate only;
- submit that design under a new formal root/child pair for independent review before implementation.

No child implementation, producer/packer/dataset/manifest/config/optimizer-selector/checkpoint change, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this approval.
