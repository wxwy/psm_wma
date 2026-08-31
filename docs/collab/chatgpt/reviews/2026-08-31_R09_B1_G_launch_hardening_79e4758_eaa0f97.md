# R09-B1-G launch hardening re-review

Target request: root `79e4758` (implementation parent `9dc7dd3`), submodule/Gitlink `eaa0f97`.

## Verdict: REQUEST_CHANGES

The previous three broad blockers are materially improved: the launcher now records and executes the same argv, D005 binds explicit output checkpoints, and the verifier consumes both Gate-A and B1 sidecars. However, the launch contract is still not sufficiently self-validating to authorize GPU.

### HIGH-1 — GPU identity/cap is declared, not enforced or verified

`tools/g0/write_r09_b1_d005.py` hard-codes `gpu={index:0, cap:"A100-80GB"}`. The actual launcher command does not set `CUDA_VISIBLE_DEVICES=0`, and `verify_r09_b1_smoke.py` does not validate the D005 `gpu` field or query/record the actual CUDA device/capacity. `NPROC_PER_NODE=1` only constrains process count; it does not prove which GPU was selected or that it is the approved A100-80GB.

Required before launch:
- bind the approved device explicitly (e.g. `CUDA_VISIBLE_DEVICES=0`, or an equivalent frozen device contract);
- record actual runtime device name/index/total memory from the evaluation/training process or a pre-launch machine-readable probe;
- make PASS require the approved single-device identity/capacity rather than trusting the hard-coded D005 claim.

### HIGH-2 — command hermeticity check is substring-based and does not prove D005 == executed environment

`_sidecar_matches_command()` only checks that a handful of substrings occur somewhere in the serialized command. It does not parse argv, does not require the full `UNSET_ENV` set, does not prove each recorded `environment` key/value is present exactly once in the command, and does not reject conflicting duplicate assignments. Consequently a sidecar can satisfy the verifier while the actual argv differs materially from the recorded environment contract.

Required:
- persist structured argv (not only shell-escaped text) in D005;
- verify exact argv hash/structure;
- require every frozen environment assignment and every required unset exactly as specified;
- reject duplicate/conflicting assignments;
- verify phase-specific values (`PSM_R09_B1_TTT_ENABLED`, probe path, checkpoint, output root, expected-step overrides) from structured argv.

### HIGH-3 — B1 model-only handoff is proven only by checkpoint-path substring

`b1_model_only_loads_exact_rebuilt_checkpoint` is currently `str(initial_checkpoint) in log`. This does not prove that the B1 process actually loaded the checkpoint model-only, that training-state restore was disabled, or that the logged path is the successful load marker rather than configuration/echo text.

Required:
- hard-gate an unambiguous successful model-load marker for the exact rebuilt checkpoint;
- hard-gate `checkpoint.load_training_state=False` / no optimizer-scheduler-trainer resume for B1;
- preferably record the loaded checkpoint identity/manifest/hash in machine-readable runtime evidence and bind it to Gate-A output.

### MEDIUM — Gate-A checkpoint completeness is only metadata-presence

`_complete_dcp()` only checks `.metadata` under model/optim/scheduler/trainer. This is better than the prior version but can accept incomplete/truncated storage files. Reuse the stronger completeness/manifest logic already established in R08 Gate A: enumerate required DCP files/storage entries and retain a manifest/hash/size evidence sufficient to reject partial saves.

## Scope

CPU/static-only fixes. Do not run Gate-A rebuild or B1 GPU smoke yet. No eval/inference/closed-loop, multi-GPU, long training, matched SR, backend freeze, RoboTTT/shared-MoT, Global/Agent/RL.

After fixing, submit a new root SHA with unchanged reviewed submodule/Gitlink unless model code truly needs modification, and request re-review.
