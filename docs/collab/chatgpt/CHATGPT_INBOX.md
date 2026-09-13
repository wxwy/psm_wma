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

- immediate prior live blob SHA: `09caeccbf385dceb231661312f2cab2ab7134249`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Single-GPU Smoke Design REQUEST_CHANGES

Formal pair:
- root design SHA: `ee5d895043222763849ab60aa17d782f3c1596fd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_design_v0.1.md:93)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_single_gpu_smoke_design_v01_ee5d895_93a89ba.md`

Canonical review commit:
`0e3cf1de13742e9e455e85a29b63a4cb6ee6bf8a`

Current blockers: `1 HIGH` (`1 design/admission`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

Blocker:
1. §3.5 and §4 freeze the only valid topology as `world_size=1`, while §5 lists `非零 world size` as an immediate FAIL. Taken literally the valid single-GPU configuration immediately fails. Refreeze the FAIL predicate exactly as `world_size != 1` / `非 1 world size`, preserve no-`torchrun` single-GPU admission, and require the future runbook to use that same exact fail-closed predicate before CUDA/training work.

Other reviewed points: source-evidence post-commit receipt remains the sole real-input prerequisite; no new horizontal provenance Gate was introduced; the new GA-window failure text is internally coherent at this design layer; formal scope remains docs-only and child/Gitlink is unchanged.

Scope reminder: no single-GPU smoke execution-runbook design approval is granted from this pair. No real source/checkpoint/manifest/data/cache I/O, source-evidence publication, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.