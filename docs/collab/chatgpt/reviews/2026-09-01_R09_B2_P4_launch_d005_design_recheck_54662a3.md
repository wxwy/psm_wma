# R09-B2 P4 Launch D005 design re-review

- Design commit: `54662a3b31e19c224bdbee3446e42968d51615fe`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — actual output / resume path is still not bound to the D005 contract

The revised design correctly binds backend selection to `PSM_R09_B1_TTT_ENABLED`, stream/cache/checkpoint inputs to production env variables, and `100` optimizer updates to an explicit `trainer.max_iter=100` override. However, `outputs.run_root/log/checkpoint_*/capture_root` are still parallel metadata rather than values derived from the production job path.

Production `JobConfig.path_local` is computed from `IMAGINAIRE_OUTPUT_ROOT` plus `job.project/group/name`. The current production TOML gives both backends the same job identity (`cosmos3_action_libero/action_sft/edge_libero_4in1`), while the P4 design does not require either `IMAGINAIRE_OUTPUT_ROOT` or a backend-specific job override in `command.argv` / `environment.set`.

This is unsafe because DCP load prioritizes an existing `latest_checkpoint.txt` in the same job save directory over the configured warm-start `load_path`, and in that same-job case resumes the complete checkpoint key set including trainer state. Therefore:

- recurrent and TTT can write to the same real checkpoint directory even though their D005 `outputs.*` metadata claims isolation;
- the second backend can auto-resume the first backend, or either backend can resume stale state from a previous run;
- `trainer.max_iter=100` then no longer proves 100 fresh optimizer updates from iteration 0.

Required change:

1. Freeze the actual production output control surface: either a backend-specific canonical `IMAGINAIRE_OUTPUT_ROOT` or explicit backend-specific effective `job.project/group/name` overrides (or another production-supported equivalent).
2. The verifier must derive the real `JobConfig.path_local` / checkpoint directory from the effective argv+env and require it to equal the claimed `outputs.run_root` hierarchy; do not trust `outputs.*` self-report.
3. Recurrent and TTT real job/checkpoint directories must be distinct, fresh, non-existing before execution, and not Git-tracked.
4. Fail closed if `latest_checkpoint.txt` or any same-job checkpoint exists before launch.
5. Add negative regressions where D005 metadata claims isolated output paths but argv/env resolve both backends to the same production job path, and where a pre-existing `latest_checkpoint.txt` would trigger auto-resume.

### HIGH — `world_size=1` / single-GPU is still metadata, not an exact launcher binding

Production `distributed.init()` unconditionally calls `torch.distributed.init_process_group(..., init_method="env://")`. The revised design records `budget.world_size=1`, but does not freeze how the future command establishes that process group. It neither requires a one-process `torchrun` argv nor requires the plain-Python env contract (`RANK`, `WORLD_SIZE`, `LOCAL_RANK`, `MASTER_ADDR`, `MASTER_PORT`). `CUDA_VISIBLE_DEVICES` is also absent from the required environment.

Required change:

1. Freeze exactly one launch convention for B2-T.
   - If using `torchrun`, bind its exact executable and one-process arguments (for example `--nproc-per-node=1`) and reject any conflicting rank/world-size overrides.
   - If using plain Python, bind the complete `env://` single-process environment including `RANK=0`, `WORLD_SIZE=1`, `LOCAL_RANK=0`, `MASTER_ADDR`, and `MASTER_PORT`.
2. Bind `CUDA_VISIBLE_DEVICES` to exactly one reviewed GPU visibility value for the future run.
3. The verifier must derive world size from the actual launcher/env contract and require it to equal `budget.world_size=1`; the budget field alone is insufficient.
4. Add negative tests for an argv/env that advertises metadata `world_size=1` but actually launches/declares more than one process, and for missing `env://` requirements under a plain-Python launch.

### MEDIUM — `checkpoint_step0` is declared as an output but production does not create it

The production recipe currently has `trainer.save_zero_checkpoint=False`. The D005 schema nevertheless declares `outputs.checkpoint_step0` without binding an effective override that would create it.

Either remove `checkpoint_step0` from required outputs if it is only conceptual, or explicitly bind a production-supported `trainer.save_zero_checkpoint=true` override and verify that this is intended for B2-T. Do not keep a required output path that the frozen command will never produce.

## Gate decision

Static P4 builder/verifier implementation is **not approved yet**.

This review does not authorize P5, B2-T, `torchrun`, model/data/VAE/checkpoint I/O, GPU execution, training, evaluation, inference, multi-GPU, or backend freeze.
