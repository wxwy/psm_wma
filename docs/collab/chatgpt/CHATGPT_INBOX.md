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

- immediate prior live blob SHA: `112657027337becad5e920a7f552faa5a257359e`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Consumer Runtime Source-Audit Design REQUEST_CHANGES

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root design SHA: `91dc6f16d80c410aaa103637cd0e65efc7888525`
- child/Gitlink SHA: `08775da2e73e352ebb1497548de5909baab8c2dc`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-SOURCE-AUDIT-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_consumer_runtime_source_audit_design_v0.1.md:9)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_consumer_runtime_source_audit_design_91dc6f1_08775da.md`

Canonical review commit:
`95ef932536976c0072b67a6b3a2e0a67125bf986`

Current blockers: `2 HIGH`, both Design-only. Production blockers: `0`. Evidence blockers: `0`.

Required remediation:
- restore the still-binding v0.3.6/v0.3.8/v0.3.9 training/runtime authority for planned/actual valid counts, `N_window`, primary `planned/N_window`, auxiliary `1/GA_effective`, suffix-only recovery and no second GA division;
- correct v0.3.5 §20.2 from “six questions” to A–H; carry G’s actual throughput/budget result forward as explicitly deferred to an approved GPU-smoke Gate, and carry H’s runtime-sidecar/distributed/world-size-change fail-closed requirement as an explicit mandatory separate Gate.

The proposed read-only source-audit structure is otherwise acceptable: current-source `file:line` facts, variable-valid/PAD, scheduler/provenance, true feature-disable and active-wiring supersession remain appropriate. No child/source implementation change is requested.

Still not authorized: child implementation, project-code execution, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native forward/loss/backward, optimizer/scheduler stepping, runtime sidecar, smoke, training, evaluation, inference, distributed execution or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
