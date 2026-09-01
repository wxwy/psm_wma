# R09-B2 P3 interpreter launch re-review

- Date: 2026-09-01
- Reviewed root commit: `ac8314aedaa9b415643c44bd13d1abbc26379e3b`
- Submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`

## Scope

Re-review only the terminal launch-error blocker from the prior authorized P3 GPU-only attempt. The prior attempt failed before the recurrent worker started because the parent attempted to execute the non-executable collector `.py` directly. No broader scope is approved.

## Findings

### PASS — child launch now uses the active Python interpreter

The collector now builds child argv via:

```python
def _worker_command_argv(script_path: Path, arguments: list[str]) -> list[str]:
    return [sys.executable, str(script_path.resolve()), *arguments]
```

and the top-level `command_argv` is produced through that helper. Therefore child launches no longer depend on the collector script executable bit. The argv recorded into D005/provenance is also the actual executable argv including the Python interpreter.

### PASS — permanent regression covers the original failure mode

The new regression creates a temporary `collector.py`, explicitly sets mode `0644`, launches it through `_worker_command_argv()`, and asserts successful execution and expected stdout. This directly covers the original `PermissionError` failure mode without using `chmod +x` as a workaround.

### PASS — previous fail-stop controls remain intact

This patch does not weaken the prior machine-enforced fail-stop behavior. Backend launch errors/nonzero exits/non-PASS records still stop orchestration before a later backend is launched.

## Verdict

`APPROVE_TO_RUN_GPU_ONLY_P3_GATE`

This authorizes exactly one new attempt of the previously reviewed P3 GPU-only runbook command after the terminal failed attempt. The authorization is limited to the frozen single-GPU inventory run: 24 GiB hard stop, recurrent then TTT in isolated child processes, local processor exception only, no dataloader, no VAE construction, no checkpoint/weight/data I/O, no forward/backward/optimizer/scheduler step, no automatic retry, no GPU/parameter/path changes, and no `--worker-backend` manual override.

B2-T, P4/P5, training, evaluation, inference, multi-GPU, long-run, backend freeze, Global/Agent/RL remain unauthorized.
