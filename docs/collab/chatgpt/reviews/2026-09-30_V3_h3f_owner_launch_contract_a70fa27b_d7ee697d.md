# PSM-WMA V3 — H3-F owner launch contract

- Date: 2026-09-30
- Formal root: `a70fa27bfc4967462301e3ac13df03e9bb7b5c12`
- Formal child/Gitlink: `d7ee697df5800be3c6fda90de23ea4014ff34a90`
- Status: **H3F_OWNER_LAUNCH_IMPLEMENTED_PENDING_REVALIDATION**
- 30k long-run authorization: **NOT YET AUTHORIZED**

## Owner-facing launch facade

The following executable entry point now exists:

`examples/launch_sft_action_policy_robocasa_edge_all_target_atomic.sh`

It is a facade over the current grouped H3-F implementation, not the historical Local-TTT
launcher. It launches `examples/psm_wma_robocasa_h3f.py` through 8-rank `torchrun`.

The facade auto-detects:

- fresh when no same-job checkpoint exists;
- resume when same-job `latest_checkpoint.txt` exists;
- a new evidence attempt index for every resume.

It refuses an existing job directory that has no latest checkpoint instead of silently treating
it as fresh.

## Owner-specified environment contract

The launcher accepts and H3-F preflight validates:

- `ROBOCASA_ROOT`;
- `ROBOCASA_LATENT_CACHE_ROOT`;
- `BASE_CHECKPOINT_PATH`;
- `EDGE_POLICY_CHECKPOINT`;
- `WAN_VAE_PATH`;
- `OUTPUT_ROOT`;
- `CUDA_VISIBLE_DEVICES`;
- `ROBOCASA_NUM_WORKERS`;
- `SAVE_ITER`;
- `TTT_ACTIVE_GA`.

The existing TTT envs for T/dim/hidden/K/inner-lr/B-stream are also accepted.

Frozen algorithmic values remain fail-closed:

- T=16;
- dim=64;
- fast_hidden=256;
- K_local=4;
- inner_lr=0.1;
- B_stream=8;
- active_GA=2;
- CUDA devices = 0..7.

`ROBOCASA_NUM_WORKERS` is accepted as a positive runtime contract value and recorded in
preflight evidence. The current grouped planner/binder path materializes samples synchronously,
so this value does not create a conventional multi-worker PyTorch DataLoader.

## SAVE_ITER

`SAVE_ITER` is now a real runtime input rather than decorative shell state.

- default = 500;
- must be a positive integer;
- must divide every primary evaluation milestone;
- is written into the H3-F config digest;
- is applied to `config.checkpoint.save_iter`;
- changing it across same-job resume changes the grouped config authority and therefore fails
  resume instead of silently changing checkpoint cadence.

No automatic retention is implemented. Checkpoint cleanup remains owner-managed.

## Path authorities

The supplied dataset/cache/Edge/VAE paths must resolve to the frozen H3-F authorities.

`BASE_CHECKPOINT_PATH` is explicitly validated as the frozen Edge-Policy-DROID DCP lineage
input. The effective H3-F training warm-start remains the already-validated Stage-A H100 iter1
authority; this distinction is recorded in preflight evidence.

The owner-selected output path under the repository's ignored `outputs/` subtree is now
explicitly allowed. Other source-tree output locations remain rejected.

## Readiness timing mode

The H3-F launcher also supports a separate readiness-only path:

`H3F_READINESS_STEPS=<2..100>`

This keeps the formal 30k scheduler horizon and 500-step warmup contract, but stops after the
requested number of optimizer steps and writes to a distinct readiness group.

The formal observer records per-iteration loss/memory/gradient evidence plus step-to-step wall
time and emits an aggregate timing summary at completion.

This mode exists to get a H3-F-native steady-step measurement before deciding whether to run the
full 30k budget.

## Revalidation Gate

Before long-run authorization, ds must validate the exact pair above:

1. grouped trainer tests;
2. H3-E harness tests;
3. H3-F tests;
4. Ruff check;
5. Ruff format --check;
6. `git diff --check`;
7. `bash -n examples/launch_sft_action_policy_robocasa_edge_all_target_atomic.sh`;
8. exact owner-env read-only H3-F preflight;
9. 10-step H3-F readiness smoke using the facade.

The formal 30k run remains blocked until those results are reviewed.
