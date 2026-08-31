# R09-B1-G PATH retry review — request da91c0e / implementation 040cb78 / submodule eaa0f97

## Verdict

**APPROVE_TO_RETRY_B1_SMOKE**

The previous approved smoke did not enter training: it failed before model execution with `env: torchrun: No such file or directory`, with no checkpoint, no forward, and effectively no GPU use. This is an infrastructure-only failure and does not invalidate the previously reviewed B1-G launch contract.

## Review findings

The retry patch is appropriately minimal:

- `tools/g0/launch_r09_b1_smoke.sh` now defines `VENV_BIN=$FRAMEWORK/.venv/bin` and injects `PATH=$VENV_BIN:$PATH` into the exact `env ...` argv used for both Gate-A rebuild and B1 smoke;
- the same resolved PATH is passed into `write_r09_b1_d005.py` and recorded in the D005 `environment` object;
- because `command_argv` is generated from the same command array that is subsequently executed, the hermetic command provenance remains aligned with runtime;
- no model, submodule, optimizer, dataflow, verifier acceptance logic, or experiment scope changed.

This directly closes the observed `torchrun` lookup failure without broadening the approved experiment.

## Approval scope

Retry only the already-approved bounded launcher contract:

1. Gate-A-compatible rebuilt warm-start: 2 optimizer steps;
2. B1 TTT smoke: 5 optimizer steps from the exact rebuilt iter2 checkpoint;
3. one A100-80GB; exact-window cache-only; no online VAE fallback;
4. run the existing strict verifier and stop at REVIEW.

Do not add extra retries automatically if this run fails for a new reason. Preserve the failed and retried D005/log evidence so runtime review can distinguish the infrastructure failure from the valid retry.

Still blocked: eval/inference/closed-loop, multi-GPU, long training, matched SR, backend freeze, shared-MoT/RoboTTT expansion, Global, Agent, RL.
