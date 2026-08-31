# R09-B1-G launch evidence re-review — root f52898d / submodule eaa0f97

## Verdict

**APPROVE_TO_RUN_B1_SMOKE**

Scope of approval is only the bounded two-stage single-GPU smoke already frozen in the launcher:
1. Gate-A-compatible replacement warm-start rebuild: 2 optimizer steps;
2. B1 TTT smoke: 5 optimizer steps, model-only warm-start from the exact rebuilt iter2 checkpoint;
3. one A100-80GB, exact-window cache-only path, workers=0, no eval/inference/closed-loop/multi-GPU/long training.

This closes the launch-evidence blockers from review `85cda6e`.

## Review findings

### 1. GPU binding / identity — CLOSED

`tools/g0/launch_r09_b1_smoke.sh` now queries GPU name and total memory with `nvidia-smi`, aborts unless the visible host GPU is A100 with >=80000 MiB, and explicitly executes both phases with `CUDA_VISIBLE_DEVICES=0`.

D005 now records GPU name, total memory and index; verifier hard-gates both sidecars plus runtime probe A100 identity.

### 2. Hermetic command provenance — CLOSED for this bounded smoke

The launcher constructs one argv array, serializes that exact argv into D005, and then executes the same array. D005 stores both shell-rendered command/hash and structured `command_argv`.

Verifier checks structured argv, exact unset-list cardinality/membership, every frozen environment assignment, and `DISABLE_AUTO_RESUME=1`. This is sufficient to close the prior string-substring-only provenance blocker for this smoke.

### 3. Exact model-only Gate-A -> B1 handoff — CLOSED

The B1 sidecar binds its input checkpoint to the Gate-A rebuilt output. Verifier requires the B1 log to report loading that exact checkpoint at iteration 0 and requires `checkpoint.load_training_state=False` in the recorded command.

Together with `DISABLE_AUTO_RESUME=1`, this is sufficient evidence for the intended model-only handoff contract.

### 4. Gate-A checkpoint completeness / manifest — CLOSED for launch

Verifier still checks all four DCP component `.metadata` files and now also builds a recursive file manifest with size and SHA256 for every retained file in the rebuilt checkpoint. The actual runtime review must inspect the resulting manifest and PASS artifact; this no longer blocks launching the bounded smoke.

## Runtime acceptance conditions

Approval to run is **not** approval to close B1-G. After the run, stop at REVIEW and submit the generated evidence. Runtime closure still requires the strict verifier to PASS and independent review of at least:
- exact root/submodule/Gitlink provenance;
- both D005 sidecars and their hashes;
- actual GPU identity and CUDA peak;
- Gate-A 2/2 finite training + complete iter2 checkpoint manifest;
- B1 exact model-only load of that iter2 checkpoint;
- B1 5/5 finite losses;
- frozen-common bitwise unchanged / expected GRU removal only;
- exact optimizer membership and expected gradient behavior;
- exact B0 TTT state schema/reset/detach contract;
- cache-only/no-online-VAE-fallback PASS;
- root/submodule tracked-clean at verification.

## Scope boundary

**Allowed now:** only the launcher-defined 2-step Gate-A-compatible rebuild followed by 5-step B1 TTT single-GPU smoke and verifier.

**Still blocked:** eval/inference/closed-loop, multi-GPU, long training, matched SR, backend freeze, shared-MoT/RoboTTT expansion, Global, Agent, RL, or any additional GPU experiment intended to amplify/repair a failed smoke.

If the smoke/verifier FAILs, stop and return the evidence for review; do not automatically broaden or rerun the experiment except for an obvious infrastructure-only failure that preserves the frozen contract.
