# R09-B1-G bounded smoke-profile implementation review — root 34695a3 / submodule eaa0f97

## Verdict

**APPROVE_TO_RUN_SMOKE_PROFILE**

Approval is strictly for the bounded, noncanonical `smoke_batch1` runtime contract implemented at root `34695a36e1fd72a1c477a41925386d6994f1f716`, submodule/Gitlink `eaa0f97`.

## Findings

### 1. Approved profile is implemented exactly — PASS

`tools/g0/launch_r09_b1_smoke.sh` freezes:
- `dataloader_train.max_samples_per_batch=1`
- `trainer.grad_accum_iter=1`
- Gate-A-compatible rebuild `max_iter=2`
- B1 smoke `max_iter=5`

The profile only changes the bounded smoke execution scale. Existing single-A100, exact-window cache-only, workers=0, history mode, B1 selector, model-only handoff and environment sanitation remain intact.

### 2. D005 binds the profile before launch — PASS

`write_r09_b1_d005.py` rejects any profile other than `smoke_batch1 / 1 / 1`, requires both profile overrides exactly once in structured `command_argv`, and records the profile as `bounded_noncanonical=true` together with launch timestamp and dmesg diagnostics.

### 3. Verifier hard-gates the profile — PASS

`verify_r09_b1_smoke.py` requires the exact profile in both Gate-A and B1 sidecars, checks the two overrides in structured argv, preserves the 2/5-step phase checks, and emits an explicit warning that PASS is not canonical Gate-A, formal-scale training, throughput, convergence, or SR evidence.

The previous provenance, cache-only/no-online-VAE, exact model-only handoff, GPU, state/reset/detach, optimizer/gradient, checkpoint schema and clean-tree gates remain present.

## Authorization

GPU may start **only after ChatGPT, Kimi and MM have all approved this same implementation SHA (`34695a3`) and same submodule/Gitlink (`eaa0f97`)**.

Once the three-way gate is satisfied, the only authorized execution is the frozen launcher-defined sequence:
1. bounded Gate-A-compatible rebuild: batch1 / grad-accum1 / 2 optimizer steps;
2. bounded B1 TTT smoke: batch1 / grad-accum1 / 5 optimizer steps;
3. strict verifier;
4. stop at REVIEW and submit the generated evidence.

Any FAIL, NaN, OOM, new infrastructure/runtime failure, missing checkpoint/probe, verifier FAIL, or command deviation must stop the run and preserve evidence. **No automatic retry or profile expansion.**

Still blocked: canonical/formal-scale training conclusions, eval/inference/closed-loop, multi-GPU, long training, matched SR, backend freeze, shared-MoT/RoboTTT expansion, Global, Agent, RL.
