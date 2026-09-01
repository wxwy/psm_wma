# R09-B2 P4 Launch D005 design review

- Request / design commit: `b546aac0721ff8efa7a3895d878596edd9e989a7`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — `command.cwd` is still not bound to the production framework root

The revised design correctly adds one-process torchrun, backend-specific output roots, resume freshness checks, and explicit `trainer.max_iter=100` / `trainer.save_zero_checkpoint=true` overrides. However the D005 schema still only contains a generic `command.cwd` field; the design never freezes or verifies its exact value.

That is not optional for this production recipe. At the reviewed Gitlink, `EDGE_MODEL_CONFIG` constructs the Nemotron config from the relative path:

`cosmos_framework/model/generator/reasoner/nemotron_3_dense_vl/configs/Nemotron-2B-Dense-VL.json`

This exact class of relative-path failure already blocked P3 until the isolated worker changed cwd to the `cosmos-framework` root. `PYTHONPATH=<canonical cosmos-framework>` does not affect filesystem resolution of `from_json_file()`.

Required change:

1. Freeze `command.cwd` to the canonical absolute realpath of the reviewed `cosmos-framework` root.
2. The verifier must independently require that exact cwd and reject root-repo cwd, arbitrary cwd, symlink aliases, or missing cwd.
3. Bind the `--sft-toml` argv path to that cwd. Either use the exact framework-relative `examples/toml/sft_config/action_policy_libero_edge_all.toml` under framework cwd or another single canonical representation; do not allow a path whose meaning changes with cwd.
4. Add a negative regression where every other D005 field is valid but cwd is the root repository; verifier must FAIL.

### HIGH — the launcher executable is not tied to the recorded canonical Python interpreter

The input contract records a canonical external `Python executable`, but the future command is specified as a bare `torchrun ...`. A bare executable token is resolved through the inherited `PATH`; therefore the D005 can claim one Python asset while actually launching a different torch/venv installation. This violates the purpose of an exact launch D005 and reintroduces an uncontrolled parent-environment dependency.

Required change:

Prefer one exact interpreter-bound launcher form, for example:

`<canonical-python> -m torch.distributed.run --standalone --nnodes=1 --nproc-per-node=1 -m cosmos_framework.scripts.train ...`

Alternatively, an absolute canonical `.../.venv/bin/torchrun` may be frozen and hashed, but it must be explicitly bound to the intended interpreter/toolchain. The verifier must reject bare `torchrun`, PATH-dependent launchers, or any launcher differing from the recorded asset. Add a negative regression for that case.

## Accepted parts of this revision

The following prior blockers are structurally addressed and need not be redesigned again unless implementation diverges:

- backend binding through production `PSM_R09_B1_TTT_ENABLED=0|1`;
- P1 stream manifest / cache / checkpoint / processor / VAE actual env consumers;
- explicit `trainer.max_iter=100` for 100 optimizer updates;
- one-process launch semantics (`nnodes=1`, `nproc_per_node=1`) and `CUDA_VISIBLE_DEVICES=0`;
- rejection of conflicting rank/world-size environment;
- backend-specific `IMAGINAIRE_OUTPUT_ROOT` with production `JobConfig.path_local` derivation;
- fresh job/checkpoint directories and rejection of `latest_checkpoint.txt` / `iter_*` auto-resume state;
- `checkpoint_step0` now tied to an actual `trainer.save_zero_checkpoint=true` override;
- external runtime assets may be canonical absolute realpaths under verifier-owned allowlisted roots.

## Gate decision

Static P4 builder/verifier implementation is **not yet approved**.

This review does not authorize any torchrun execution, B2-T, P5, model/data/VAE/checkpoint I/O, GPU, training, evaluation, inference, multi-GPU work, or backend freeze.
