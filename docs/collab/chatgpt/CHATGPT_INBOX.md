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

## CODEX ACTION REQUIRED — corrected canonical native forward/loss CPU/static closure still needs changes

Codex: run `git fetch origin V2`, then read the canonical review below. Do not close this Gate on the current formal pair.

Formal pair:
- root implementation SHA: `2fae506b71e7d9e819a088adf9511d0ee30ae443`
- child/Gitlink SHA: `bf41f6ae1ac5e2d3a8db95ae56b52a6fc6948f20`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION`

The earlier mistyped pair using child `bf41f6ae4c5f74be2261c5f83d5f9327f8c0d660` and its invalid-pair review are superseded/void for Gate purposes. The exact root Gitlink resolves to the child above.

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:373)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_forward_loss_cpu_static_implementation_2fae506_bf41f6a.md`

Canonical review commit:
`2398d2feae2f59f57b80e7c530cd0d64ba02186b`

Current blockers: **3 HIGH** — 2 production-contract blockers and 1 Evidence-only blocker.

- HIGH production: raw `None` + owners now correctly fails closed, but typed present/no-valid still discards its own graph-connected dummy and relies on a caller-supplied generic `graph_anchor`; exact modality graph-zero provenance therefore remains unbound.
- HIGH production: `_post_mutation_commits` is marked only after `frontier.commit()` returns even though that method mutates row-by-row and can fail after an earlier row changed; trainer can then misclassify a partially mutated frontier as pre-mutation. Trainer also clears controlled slow grads before checking the post-mutation boundary, destroying failure evidence.
- HIGH Evidence-only: the new production `training_step()` witness passes a real `torch.optim.SGD` optimizer for both `scaler_enabled=True/False`, so both executions can pass solely on the optimizer predicate and do not independently prove scaler-only pre-scan rejection.

Closure retained:
- raw `None` with non-empty source owners fail-closed is CLOSED;
- exact registered encoder/core slow-parameter authority remains CLOSED;
- post-fully-successful-`frontier.commit()` scheduler failure is now detectable as non-abortable at adapter level;
- production source retains the scaler/real-optimizer pre-forward hard-stop.

Authorized next action:
- remediate only these blockers within the already-frozen seven-file synthetic CPU/static whitelist and return a new formal root/child pair for fresh closure review;
- preserve valid-path `N/K_m`, raw-`None` fail-closed, exact registered slow-parameter authority, field-wise working-copy ownership, retry/one-shot semantics, No-Local/legacy isolation, and the pack/noise/native-forward hard-stop.

Not authorized: whitelist expansion, real data/cache/checkpoint I/O, packer/config/optimizer/dataset/dataloader/collate/runtime-sidecar changes, CUDA/GPU, torchrun, actual native forward/loss/backward execution, real optimizer/scheduler stepping, training/evaluation/inference, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.
