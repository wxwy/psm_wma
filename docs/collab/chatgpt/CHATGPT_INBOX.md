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

- immediate prior live blob SHA: `abfb33e636dc93f9d3a75d3bd90065f6bc6c1d08`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Single-GPU Smoke Design APPROVED

Formal pair:
- root design SHA: `e75c8c12c8573d445e91f2b9c9b4d95d98b1d5f8`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_single_gpu_smoke_design_remediation_e75c8c1_93a89ba.md`

Canonical review commit:
`ca9e3cb8b5b662142cc84bc93b251c8843c1fbd3`

Current blockers: `0` (`0 design/admission`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

Prior blocker disposition:
- §5 contradictory `非零 world size` immediate-FAIL predicate: **CLOSED**. Formal delta changes it to exact `world_size != 1`, matching the frozen `world_size=1` single-GPU admission and preserving the separate no-`torchrun` rule.

No new findings. The one-line docs-only remediation does not modify the source-evidence post-commit prerequisite, no-resume, `num_workers=0`, bounded `<=100` step scope, chronology/GA-window transaction, artifacts, PASS semantics, or other stop conditions. Child/Gitlink remains unchanged.

Scope reminder: this closes only the exact docs-only single-GPU smoke design Gate. It authorizes only the next docs-only single-GPU smoke execution runbook/command design and review. It does not authorize real source/checkpoint/manifest/data/cache I/O, source-evidence record/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun execution, training, evaluation, inference, LIBERO4IN1, matched smoke, runtime-sidecar work, or formal training.

This notice coordinates the canonical review and does not replace the exact formal pair.