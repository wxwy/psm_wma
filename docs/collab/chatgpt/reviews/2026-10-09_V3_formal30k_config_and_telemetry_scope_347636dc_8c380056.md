# V3 Corrected formal30k config freeze and minimal telemetry authorization

Date: 2026-10-09

## Exact authority
- formal root: `347636dce5cd33ad5a538183595e6cda893354aa`
- formal child / Gitlink: `8c3800565f66cfbce2929264f1c2a7854137482e`
- latest V3 bookkeeping root at review: `7aca83426333c0318e4997df8da847a35f2caeab`
- child implementation unchanged since the prior full-corpus readiness Gate.
- root Gitlink at the exact formal root independently resolves to `8c380056...`.

## Verdict

`APPROVE_FORMAL30K_CONFIG_AND_TELEMETRY_READINESS`

**Strict meaning of this authorization:** formal30k config/preflight sub-Gate is CLOSED and cx/Codex may implement **telemetry-only** wiring. The full telemetry readiness Gate is **OPEN** until implementation, relevant tests, and a fresh exact-pair review pass.

`FORMAL30K_TRAINING_NOT_AUTHORIZED`

`NO_GPU_READINESS_RERUN_AUTHORIZED_OR_REQUIRED_AT_THIS_STAGE`

## Config/preflight sub-Gate: accepted

DS_PRO's submitted full-corpus CPU-only preflight on the exact pair reports:
- `config_digest = 70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`
- `max_iter=30000`, `warmup=500`, `save_iter=100`
- `world_size=8`, `T=16`, `B_stream=8`, `GA=2`, `K=4`
- 9126 corrected-cache episodes, matching flat v3 source
- cache manifest SHA256 `8e63c73b4e07cdbebd6427d9efdd3f2d8b293ecd10511cae25a55c6566f6db88`
- cache corpus digest `0e0c05d09722dc7e65da868326ded3cc23a0885e4ed8841e3fbad1ab2e41fac3`
- source binding digest `f91b0b477a048beb439f1d73e7414f6b1d2a0307eee54c858d6cd8503ea19020`
- official DROID DCP fresh warm start (no training state)
- exact root/child/Gitlink lock and clean worktrees

The report is an execution-side assertion; the detailed local JSON is not present in the fetched remote GitHub tree. This review independently verified the corresponding production entrypoint configuration, root Gitlink, and relevant source callback plumbing. No claim is made that the entire 33-minute execution was independently rerun.

This preflight was **not** advertised as `--snapshot10`, so do not silently claim its ten cached-latent hit samples were executed in this exact run. The previous full-corpus one-step and snapshot smoke remain separate completed evidence.

## Current telemetry implementation facts

Exact child `examples/psm_wma_robocasa_corrected_phase5.py`:
- `overlay_config` sets `config.trainer.callbacks = {}`.
- `GroupedPlanObserver` records forward/backward counts and verifies plan valid count, but discards passed metric values and prints none.
- `GroupedLocalMemoryTrainer._observe_grouped` passes detached `loss` and scalar `metrics` to the observer on each `native_forward`, passes **weighted** loss on each `native_backward`, passes optimizer LR range on `pre_optimizer`, and invokes `post_commit` only after successful `window.finish`.
- `ContinualTTTLocalMemoryCore.drain_telemetry` already exposes detached `inner_loss`, `fast_state_norm`, `fast_update_norm` sum/max/count.
- `GroupedLocalMemoryTrainer.bind_grouped_stream` requires exclusive ownership of the DCP dataloader-state callback component.

## Approved code scope

cx may modify **only the corrected Phase5 entrypoint and its dedicated tests**, plus a single explicitly justified observer-only callback helper if absolutely necessary. No changes to `GroupedLocalMemoryTrainer`, `GroupedLocalMemoryWindow`, `OmniMoTModel`, Local core, planner, producer, sampler, cache reader, resume, optimizer or scheduler semantics.

**Do not blindly restore default `config.trainer.callbacks`.** Prefer extending the existing `GroupedPlanObserver` and, only if required for complete step timing, a single passive purpose-built callback with no checkpoint owner and no grad-modifying behavior. Keep the existing grouped DCP callback unique.

Required rank0 per-successful-optimizer-iteration structured telemetry:
- exact completed iteration and member/consumer counts;
- weighted outer loss from the existing detached backward-weighted path (no double weighting);
- action/vision component losses from `native_forward.metrics`, weighted by effective consumer count (never unweighted per-native-call average);
- Local inner/fast-state/fast-update stats via existing detached core telemetry without changing fast weights;
- LR min/max with explicitly stated pre/post-scheduler timing;
- gradient norms and generation/action/Local groups sampled at `pre_optimizer`, after existing unscale and model pre-step hooks, before optimizer step or zero_grad;
- identify norms over **rank0-local DTensor shards** as rank-local, never assert global norm without a correct all-rank reduction;
- meaningful step-wall measurement with honest start/end points; do not label partial native-forward time as full optimizer-iteration time;
- peak allocated/reserved GPU memory; epoch/frontier sourced from successfully published `window.live`;
- log only once after `post_commit` and only from rank0. Failed/aborted/skipped iterations must never be logged as completed successes.

Additional checks:
- no `tensor` references that retain autograd graphs across iterations; use detach/no-grad scalar extraction;
- no changes to loss scaling, gradients, FSDP collectives, optimizer inventory, Local publish and resume/DCP ownership;
- no silent zeros for unavailable optional telemetry; emit an explicit unavailable marker and classify readiness gaps rather than fabricate values;
- in the new exact pair, rerun full-corpus preflight and confirm semantic config digest still equals `70e9867f...` if only telemetry changed;
- enforce `PYTHONPATH=<exact formal child path>` and record resolved `cosmos_framework.__file__` because the training-host installed venv has an editable package pointing to an older workspace.

## Mandatory CPU/static acceptance before review

1. observer enabled/off behavior does not affect outer loss values, selected optimizer parameters or grouped member counts;
2. two GA members and variable valid consumer count yield exactly one correctly weighted completed-iteration record;
3. action and vision losses map to actual model scalar keys; no fabricated values;
4. inner_loss/fast-state/fast-update stats are detached and counted correctly;
5. pre-optimizer gradient instrumentation does not mutate gradients, and FSDP/DTensor rank-local scopes are labeled;
6. rank0 logs one record per successful iteration; other ranks none;
7. failed/aborted/optimizer-skipped window generates no success record;
8. iteration/epoch/frontier labels are post-commit exact and resume-safe;
9. default callback restoration does not introduce duplicate dataloader DCP owners;
10. py_compile, focused pytest, Ruff check/format, diff-check and exact file scope are green.

## Next process

- cx implements and commits child telemetry changes, then updates root Gitlink/authority via a new formal pair.
- GPT fresh incremental review on that exact new pair; historic unchanged model/trainer logic need not be rescanned.
- ds performs only the separately authorized CPU/static corroboration.
- No GPU optimizer step, diagnostic iter1 resume or formal30k run from this authorization.

Only when telemetry implementation + CPU/static Gate is approved may a separate bounded **formal-schedule** burn-in be considered.
