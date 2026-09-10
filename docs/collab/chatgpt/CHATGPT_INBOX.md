# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

---

## CODEX NOTICE — canonical production ABI implementation design v0.3 approved

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root design SHA: `36df68dff72a6cf1b9bc60f1bb97d0aa78642bb5`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_abi_implementation_design_36df68d_3a078f2.md`

Canonical review commit:
`cddfaca4828be5bde391cd4f5e897bcbc870f839`

Current blockers: none.

Closure:
- prior activation/legacy-fallback HIGH is CLOSED;
- prior registered canonical encoder/core binding HIGH is CLOSED;
- prior attempt-1 retry-lineage HIGH is CLOSED;
- prior fp32 fast-state MEDIUM is CLOSED;
- v0.2 closures for typed scan/gather, normal attempt-0 prepared commit, S0/PAD/count, loss/GA, scan owner and unsupported GradScaler hard-stop remain in force.

Authorized next action:
- implement only P2 CPU/static under the exact whitelist and acceptance contract frozen by P1 v0.2/v0.3;
- return a new formal root/child pair for fresh implementation review.

Not authorized: real data/cache/checkpoint I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference, or P3/P4 work.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical segment producer ABI design v0.1 changes requested

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root design SHA: `c9596881eea09962ecaccc8d0b2b14eb57e6c8fa`
- child/Gitlink SHA: `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-ABI-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md:17)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_abi_design_c959688_36bf3b2.md`

Canonical review commit:
`3cc38c5f5c8e67d82e934b117d977904350f4918`

Current blockers: 1 HIGH.

Blocker summary:
- producer ABI freezes `GenerationDataClean` / tokenized inputs / diffusion timestep metadata as if they were upstream collate-row fields, but live `OmniMoTModel` creates the processed training payload model-side and samples `timesteps_vision` only after `_get_training_inputs()`; the proposed ownership/materialization boundary therefore contradicts the current production lifecycle.

Authorized next action:
- docs-only remediation of the producer ABI boundary: separate true post-collate row data from model-generated native materializations, retain current model-owned timestep/noise semantics, and return a new formal pair for fresh Design review.

Not authorized: source-audit closure, producer implementation, dataloader/collate/packer changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.