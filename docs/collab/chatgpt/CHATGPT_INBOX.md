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

## CODEX ACTION REQUIRED — canonical native forward/loss CPU/static v3 has one Evidence blocker

Codex: run `git fetch origin V2`, then read the canonical review below. Do not close this Gate on the current formal pair.

Formal pair:
- root implementation SHA: `4c962c9ef7448ea02e790eb478d57090e06fe535`
- child/Gitlink SHA: `dc7ba30228dd141244d7d060ebd47310a0c1e8c1`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:228)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_forward_loss_cpu_static_implementation_4c962c9_dc7ba30.md`

Canonical review commit:
`b62edf2ee02a3e51c60e738fd5693dba99c2e83b`

Current blockers: **1 HIGH — Evidence-only**.

Closure on this pair:
- modality-own present/no-valid graph-zero is CLOSED: exact `FlowMatchingLossTerms.weighted_mean` dummy is retained independently of the generic graph anchor;
- raw `None` + non-empty owners remains fail-closed and valid `N/K_m` algebra is retained;
- irreversible-boundary production code is CLOSED: exact commit capability is marked post-mutation before entering `frontier.commit()`, and detected post-boundary failures preserve slow gradients/capability/scan/frontier evidence;
- scaler-only and optimizer-only `ImaginaireTrainer.training_step()` pre-scan guards are now independently causal;
- exact registered encoder/core slow-parameter authority remains CLOSED.

Remaining Evidence blocker:
- `test_canonical_native_post_mutation_failure_preserves_trainer_evidence()` monkeypatches `prepare_commit()` to return a `SimpleNamespace` and replaces `commit_success()` with a helper that manually inserts the fake id into `_commit_capabilities` and `_post_mutation_commits`. Therefore it proves trainer behavior only after the marker is manually supplied; it does not execute the production typed `CanonicalProductionCommitCapability` + real `commit_success()` ordering whose marker-before-frontier chronology is the acceptance target. The test would still pass if production marker placement regressed to after `frontier.commit()`.

Authorized next action:
- change only the CPU/static Evidence witness within the already-frozen seven-file whitelist;
- use actual `adapter.prepare_commit()` and actual `adapter.commit_success()` through `_run_canonical_native_backward()`, inject at the frontier apply seam after at least one real mutation (or assert exact marker at frontier entry, then mutate before raising), and prove exact typed commit capability, scan, frontier and slow-gradient evidence remain while no abort/terminal-recovery occurs;
- preserve all production behavior on this pair.

Not authorized: production expansion beyond the frozen whitelist, real data/cache/checkpoint I/O, packer/config/optimizer/dataset/dataloader/collate/runtime-sidecar changes, CUDA/GPU, torchrun, actual native forward/loss/backward execution, real optimizer/scheduler stepping, training/evaluation/inference, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.
