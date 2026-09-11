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

- immediate prior live blob SHA: `7778d78e21db6170017562d570fb099e79fede7f`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Consumer Runtime CPU/static Implementation REQUEST_CHANGES

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `64858d3bc76f3d0a8d755a02bd1dd7ab213499ae`
- child/Gitlink SHA: `4dd2eed00a1d9d6e2b28716c106fd9edfe940fcc`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/trainer/__init__.py:553)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_consumer_runtime_cpu_static_implementation_64858d3_4dd2eed.md`

Canonical review commit:
`8b04008f14cb9851104d5c463f38e49932e74e30`

Current blockers: `2 HIGH`. Production blockers: `1 HIGH`. Evidence blockers: `1 HIGH`.

Required remediation:

1. **Production lifecycle HIGH** — once model-forward returns a registered `psm_canonical_native_forward` capability, trainer exits before `_run_canonical_native_backward()` are not disposition-safe. `callbacks.on_after_forward`, canonical `capture_only` early return, and `callbacks.on_before_backward` can currently leave native-forward + pending-scan authority live. Wrap/dispose the exact canonical capability so each pre-backward exception/return either rejects before scan or aborts the exact capability/scan with no frontier commit, no retained Local slow grad, unchanged scheduler state, and typed fail-closed transaction disposition. Add direct production-endpoint witnesses for all three seams.

2. **Evidence HIGH** — approved v0.2 required direct pre-entry witnesses for each unapproved topology. Current implementation directly witnesses CP, model-side initialized process group, and trainer non-`none` distributed config, while prior tests cover optimizer/enabled scaler; it does not directly witness DataParallel, project DDP wrapper, FSDP/FSDP2 wrapper, trainer-side initialized group, and the stronger world-size admission contract. Add direct `ImaginaireTrainer.training_step()` witnesses proving rejection before `ddp_sync_grad`/callbacks/model-forward/core scan with zero scheduler/transaction/frontier/scan/retry mutation and no Local slow-grad side effects. If the FSDP2 witness exposes the current top-level class-name predicate as insufficient, fix it inside the approved `trainer/__init__.py` whitelist.

Positive findings retained:
- formal pair/Gitlink is valid;
- child delta is exactly three files, all within the approved six-file whitelist;
- model pre-scan CP/process-group guards and trainer real-optimizer/enabled-scaler/topology admission exist before `ddp_sync_grad`;
- absent injected CPU/static loss seam aborts the pending scan;
- injected typed split is checked by `bind_native_forward()` for exact pending scan, consumer identities, actual count and planned count;
- canonical dispatcher still owns one plan objective / one scale / one backward / typed commit and avoids ordinary second `/grad_accum_iter` scaling;
- reported 41-pass suite is supporting evidence but does not close the two gaps above.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real workload forward/loss/backward, real optimizer/scheduler stepping, enabled AMP/scaler-skip lifecycle, distributed execution, runtime sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
