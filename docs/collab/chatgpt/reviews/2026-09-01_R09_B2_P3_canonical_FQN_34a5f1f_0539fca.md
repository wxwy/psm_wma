# R09-B2 P3 canonical FQN / attempt-5 review

- Request: `34a5f1fb9f41c44861d6a2854c8b4bd038dd5e01`
- Implementation: `0539fca076c94573c108a94d7f2cc79941b5728b`
- Submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`

## Findings

No blocking issue found in the canonical-FQN repair.

1. attempt-4 failed closed on a real production flattened optimizer key whose FQN cannot be reconstructed by blindly prefixing raw `model.net.named_parameters()` names with `net.`. The new code removes that assumption.
2. `_canonical_parameter_fqns()` reuses PyTorch DCP's own `torch.distributed.checkpoint.state_dict._get_fqns(model, full_name)` and maps the resulting canonical FQN back to the raw stable name by parameter object identity. It fails closed on multiple FQNs, non-`net.` FQNs, duplicate canonical FQNs, or incomplete coverage.
3. `OmniMoTModel` inherits `ImaginaireModel`, and `ImaginaireModel` inherits `torch.nn.Module`, so calling `model.named_parameters()` is valid for the worker's production model object.
4. Both model-DCP membership and flattened optimizer-DCP ownership now consume the same canonical mapping. Optimizer schema records both `owner` and `owner_fqn`.
5. The verifier requires `owner_fqn` to be a `net.*` FQN, reconstructs `flat_key` exactly from `(namespace, owner_fqn, suffix)`, and includes `owner_fqn` in the recurrent-vs-TTT optimizer-DCP schema identity. This prevents a raw-name-only match from hiding a production FQN drift.
6. attempt-5 uses a fresh output directory and retains the existing 28 GiB fail-closed cap and all prior execution restrictions.

## Authorization

Authorize exactly one attempt-5 execution using the frozen runbook command and token:

`APPROVE_TO_RUN_GPU_ONLY_P3_GATE`

This does not authorize retries, changing GPU/cap/paths/arguments, manual `--worker-backend`, network or remote tokenizer access, data/VAE/weight/checkpoint I/O, forward/backward, optimizer/scheduler step, multi-GPU, B2-T, P4/P5, training, evaluation, inference, closed-loop, Global, Agent, or RL.
