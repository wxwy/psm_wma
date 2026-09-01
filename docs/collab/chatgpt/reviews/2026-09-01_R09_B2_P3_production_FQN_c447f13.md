# R09-B2 P3 production FQN re-review

- Request/anchor: `75362b131fcedd82b73bb234d3489863b202fb8c`
- Reviewed implementation target: `c447f13395cc2b1c3ea6806be678bb90b616a7db`
- Submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`

## Independent findings

1. The new implementation no longer assumes production DCP parameter ownership can be reconstructed by prepending `net.` to `model.net.named_parameters()` names. `_canonical_parameter_fqns()` now uses PyTorch DCP's own `state_dict._get_fqns(model, full_name)` and binds the resulting canonical FQN back to the raw stable name by parameter object identity.
2. The root model passed to `_get_fqns()` is the same outer model object that `OptimizersContainer.state_dict()` passes to `get_optimizer_state_dict(model=self.model, ...)`, so the canonicalization root is consistent with production optimizer serialization.
3. The mapping is fail-closed for multi-FQN results, non-`net.` canonical names, duplicate canonical names, and incomplete coverage of `model.net.named_parameters()`.
4. `optimizer_state_schema` records both raw `owner` and canonical `owner_fqn`. The verifier reconstructs each flattened key exactly as `<namespace>.<owner_fqn>.<suffix>` and includes `owner_fqn` in recurrent-vs-TTT schema identity, preventing canonical-name drift from being hidden.
5. The final regression at `c447f133` exercises the exact attempt-4 flattened-key shape `param_groups.net.language_model.model.layers.0.input_layernorm_moe_gen.weight.betas`, verifies raw/canonical ownership mismatch handling, and keeps unknown FQNs fail-closed.
6. No new GPU/resource/scope expansion is introduced after the previously reviewed attempt-5 plan: cap remains 28 GiB, output remains fresh attempt-5, backend ordering/fail-stop and all no-data/no-VAE/no-weight/no-checkpoint/no-forward/backward/step restrictions remain unchanged.

## Authorization

`APPROVE_TO_RUN_GPU_ONLY_P3_GATE`

This authorizes exactly one frozen attempt-5 GPU-only P3 inventory run under the existing runbook. It does not authorize retries, manual `--worker-backend`, parameter/path/GPU changes, B2-T, P4/P5, training, evaluation, inference, closed-loop, Global/Agent/RL, forward/backward, optimizer/scheduler step, or checkpoint/data/VAE/weight I/O.
