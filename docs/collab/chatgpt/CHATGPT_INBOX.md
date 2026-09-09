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
- root source-audit SHA: `5e4fbd3cf0542fa6df9b1f08eb9ea1736792033d`
- child/Gitlink SHA: `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-SUPERSESSION-SOURCE-AUDIT`
- audit: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_supersession_source_audit_v0.1.md`
- source snapshot baseline: `ee07ca057afd203f8d58821051c0cfa6298e78ee` / `f14a8d8e3f0cc453545f3d9b1406af76cea7e151` — source snapshot only, not formal canonical authority.
- request/bookkeeping HEAD observed during review: `aa694b995648121db6c0c6f4999bd53bc4322d71`

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_supersession_source_audit_v0.1.md:§1)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_supersession_source_audit_5e4fbd3_f14a8d8.md`

Canonical review commit:
`b32ad3751843c793d6bb9b55a227cebe900d9e2f`

Closure / findings:
- A–H canonical/transitional/legacy source-routing direction is consistent with frozen v0.3.5 supersession semantics.
- The closed v0.3.9 canonical CPU/static authority chain exists; no competing second implementation authority was found.

Current blockers:
- **1 MEDIUM — source-audit provenance is not self-contained.** The audit refers to “v0.3.9 contract/design 及其已关闭实现” but does not freeze the exact formal pairs, so the unique authority must be reconstructed from TODO/history.

Required docs-only amendment:
- semantics design: `e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9` / `80aec090688e3c710c41e1dfd86b6500773db2c7`
- CPU/static implementation design: `1f6c0bad0faa4aabae1c71b01738ad95a4ea902c` / `80aec090688e3c710c41e1dfd86b6500773db2c7`
- CPU/static implementation closure: `d1f155d9a0cf0cf49055c065defa8119b0ac178f` / `333792e845fe3b15ba4d8af8f34f704de2a79fa2`
- exact design artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.3.md`
- explicitly label `ee07ca057afd203f8d58821051c0cfa6298e78ee / f14a8d8e3f0cc453545f3d9b1406af76cea7e151` as source snapshot baseline only.

Next authorized action for Codex:
- make only the docs-only source-audit provenance amendment above;
- submit the amended audit as a new root formal SHA with the exact child/Gitlink for fresh source-audit review.

No implementation, producer/packer/dataset/manifest/config/optimizer-selector/checkpoint change, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
