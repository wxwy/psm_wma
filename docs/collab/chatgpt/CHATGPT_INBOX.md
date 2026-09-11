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

- immediate prior live blob SHA: `414ee94baec14a11a0353f950190278f9847e170`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Consumer Runtime Implementation Design APPROVED

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root design SHA: `86b321aaf3a4f96afbd427060bcceb5f39a0dc98`
- child/Gitlink SHA: `08775da2e73e352ebb1497548de5909baab8c2dc`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_consumer_runtime_implementation_design_86b321a_08775da.md`

Canonical review commit:
`00aae3a047fb04d7b689aecf28260e64646ddb5e`

Current blockers: `0`. Production blockers: `0`. Evidence blockers: `0`.

Closure:
- prior HIGH-1 is CLOSED: this CPU/static Gate preserves pre-scan rejection for any real `torch.optim.Optimizer` and any enabled GradScaler; only a non-Optimizer test double plus disabled scaler may enter, and disabled `scale()` proves only one-scale/one-backward structure, not AMP/unscale/step/skip/zero-grad/LR semantics;
- direct witnesses must prove real-optimizer and enabled-scaler rejection occurs before callback/model-forward/native prepare/core scan with scheduler/transaction/frontier/scan/retry bookkeeping and Local slow gradients unchanged;
- prior HIGH-2 is CLOSED: until a dedicated distributed Gate, only single-process/world-size-1 CPU/static is admitted; DDP, FSDP, initialized process groups, world-size != 1, data-parallel configuration and CP must fail closed before scan/native work;
- distributed rejection witnesses must prove zero callback/model-forward/core-scan entry and zero scheduler/transaction/frontier/scan-bookkeeping mutation;
- global `N_window`, distributed gradient averaging, `_sample_level_loss_scale`/all-reduce ownership, rank-local fast state, sidecar/resume and world-size-change semantics remain deferred to a later distributed Gate;
- the v0.1 six-file whitelist, stream-major/PAD identity, sparse Prefix, typed native per-instance split, normal/suffix objective, one-backward/no-second-GA scaling, legacy isolation and existing pre/post-mutation commit semantics remain binding;
- no new Design blocker was found.

Authorized next action:
- implement only the composite v0.1 + v0.2 contract in the six listed child files;
- execution scope is restricted to single-process/world-size-1 synthetic CPU/static witnesses.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real workload forward/loss/backward, real optimizer/scheduler stepping, enabled AMP/scaler skip lifecycle, distributed execution, runtime sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
