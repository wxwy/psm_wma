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

- immediate prior live blob SHA: `25179b75796f440c6ad7d59c080236a742e7c4f2`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Segment Production ABI CPU/static final evidence closure still REQUEST_CHANGES

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `59d0848ff5d77023365a0f540fcdf1f562500583`
- child/Gitlink SHA: `331622d41ac0c76fe2f14479fb67ceb607b8aef9`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:604)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_segment_production_abi_cpu_static_implementation_59d0848_331622d.md`

Canonical review commit:
`47211e150f234ebce01c55cabfdc4abe6b638146`

Current blockers: `1 HIGH`, Evidence-only. Production blockers: `0`.

Closure / remaining work:
- reconstructed-plan zero-core/full-zero-mutation witness is CLOSED;
- exact later frozen-member out-of-order witness is CLOSED;
- post-consume copied retry identity witness is CLOSED and preserves the exact registered retry authority;
- post-consume pre-scan stale retry witness is CLOSED and proves scan-time revalidation before core scan;
- the only remaining gap is the previously frozen full zero-mutation evidence for second-retry and post-backward retry rejection: snapshot/assert scheduler live state, exact frozen transitions, transaction, frontier, `_scan_requests`, `_scan_results`, and retry authority/capability bookkeeping immediately across each rejected call.

Tests-only remediation is sufficient unless those stronger witnesses expose a source defect.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler stepping, runtime sidecar, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
