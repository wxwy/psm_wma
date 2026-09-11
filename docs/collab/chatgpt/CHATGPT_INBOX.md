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

- immediate prior live blob SHA: `a1535acebeb00ce531139af1beb5d42342982ebf`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Consumer Runtime CPU/static Implementation remediation REQUEST_CHANGES

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `748a6ad4380a2934672c8d261d15f7bddfa0ef62`
- child/Gitlink SHA: `9368b0b5df9ddc76eed237c80ffeff40fe46a3ef`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:624)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_consumer_runtime_cpu_static_implementation_748a6ad_9368b0b.md`

Canonical review commit:
`e9891d9e504bcab83c401fb696f184e97a801a88`

Current blockers: `1 HIGH`, Evidence-only. Production blockers: `0`. Evidence blockers: `1 HIGH`.

Closure status:
- prior Production HIGH is CLOSED: `on_after_forward` exception, canonical `capture_only`, and `on_before_backward` exception now dispose the exact `CanonicalNativeForwardCapability`, abort its pending scan, clear Local slow grads, preserve frontier/scheduler state, and typed-terminalize the exact transaction member; direct witnesses obtain a real capability through the model seam and exercise all three production exits;
- DataParallel, trainer-side initialized process group, explicit world-size>1, distributed config, CP, optimizer, and enabled-scaler rejection coverage is materially improved;
- remaining Evidence HIGH: the previous exact acceptance also required direct production-entry witnesses for the project `distributed.DistributedDataParallel` predicate and FSDP/FSDP2 identity. Current remediation exercises only `torch.nn.DataParallel` and a fake object whose class name is `FullyShardedDataParallel`; it does not exercise project DDP or the repository/PyTorch `FSDPModule`-style FSDP2 identity;
- the wrapper witnesses also need to explicitly prove rejection before `ddp_sync_grad`/callbacks/model-forward/native prepare/core scan with unchanged scheduler/transaction/frontier/scan/retry state and no Local slow-grad side effect.

Required remediation:
1. add a direct `ImaginaireTrainer.training_step()` witness for the actual `isinstance(..., distributed.DistributedDataParallel)` branch; a CPU/static monkeypatched/test-double class is acceptable and no real process group is needed;
2. add a direct FSDP2 identity witness using `FSDPModule`-style topology or an equivalent test double that exercises the real intended predicate. If it shows the current top-level class-name check is insufficient, fix `_canonical_native_cpu_static_topology_error()` within the already-approved `trainer/__init__.py` scope;
3. for both, assert zero entry into `ddp_sync_grad`, callbacks, model-forward/native prepare/core scan, unchanged scheduler/transaction/frontier/scan/retry bookkeeping, and no Local slow-grad side effect.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real workload forward/loss/backward, real optimizer/scheduler stepping, enabled AMP/scaler-skip lifecycle, distributed execution, runtime sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
