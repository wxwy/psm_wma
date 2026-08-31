# R09-B1-G smoke profile rework plan review — root 9cfcf95 / submodule eaa0f97

## Verdict

**APPROVE_SMOKE_PROFILE_REWORK**

This approval is for the proposed root-only smoke-profile implementation work. It is **not** approval to rerun GPU yet.

## Rationale

The failure evidence now supports treating the previous 24-minute no-log period as an observability/scale mismatch rather than a demonstrated deadlock: the retained config shows `max_samples_per_batch=128` and `grad_accum_iter=16`, so one optimizer step requires 2048 samples, while stdout/runtime-probe evidence appears only after an optimizer step. The CPU measurements also show dataloader init/prewarm and construction of the first packed batch complete in seconds. Therefore reducing only the bounded smoke execution scale is a reasonable way to validate runtime/checkpoint wiring without changing the model algorithm or making a formal training claim.

The proposed profile is acceptable:
- `dataloader_train.max_samples_per_batch=1`
- `trainer.grad_accum_iter=1`
- Gate-A-compatible replacement rebuild remains `max_iter=2`
- B1 remains `max_iter=5`
- same model/checkpoint family, single A100-80GB, exact-window cache-only path, workers=0, history mode and B1 selector unchanged.

## Required implementation contract

Before any GPU rerun, the root-only implementation must make the smoke profile machine-auditable:

1. Launcher must explicitly inject both profile overrides into the exact executed argv for **both** phases. Do not modify the canonical recipe or submodule algorithm.
2. Both D005 sidecars must record the profile values and identify the run as a bounded/noncanonical smoke profile.
3. Verifier must hard-gate exact values `max_samples_per_batch=1`, `grad_accum_iter=1`, Gate-A steps=2 and B1 steps=5 from structured argv/D005; a missing or different value must FAIL.
4. Runtime artifact/report wording must remain `Gate-A-compatible replacement warm-start` / `bounded smoke profile`; it must not be presented as canonical Gate-A, formal-scale training, throughput evidence, convergence evidence, or SR evidence.
5. All prior launch/provenance hard gates remain in force: source/Gitlink equality, hermetic env/PATH, A100-80GB binding, exact checkpoint handoff, cache-only/no-online-VAE, expected optimizer/gradient/state/reset/detach checks, complete checkpoint evidence, and tracked-clean verification.
6. After implementation, stop at REVIEW and request independent approval to run. Do not treat this plan approval as GPU authorization.

## Scope boundary

Allowed now: root launcher/D005/verifier/docs/status edits needed to encode the smoke profile.

Still blocked: GPU retry until the implementation SHA is independently reviewed; submodule/model algorithm edits; formal recipe changes; eval/inference/closed-loop; multi-GPU; long training; matched SR; backend freeze; shared-MoT/RoboTTT expansion; Global/Agent/RL.
