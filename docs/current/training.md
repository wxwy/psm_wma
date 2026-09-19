# Training and Resume

## Canonical recipe

The current Local Memory training recipe is:

- Experiment: `action_policy_libero_edge_all`
- TOML: `cosmos-framework/examples/toml/sft_config/action_policy_libero_edge_all_localmem_active.toml`
- Job name: `edge_libero_4in1_localmem_active`
- Base checkpoint: Cosmos3-Edge-Policy-DROID DCP
- Dataset: four LIBERO suites under one parent root
- Exact-window latent cache: required by the accepted run
- Single rank / single GPU

Default active geometry:

```text
PSM_R08_LOCAL_HISTORY_ENABLED=1
PSM_R09_B_TTT_ENABLED=1
PSM_R09_B_TTT_ACTIVE=1
PSM_R09_B_TTT_MEMBER_LAYOUT=a2
PSM_R09_B_TTT_B_STREAM=8
PSM_R09_B_TTT_ACTIVE_GA=16
PSM_R09_B_TTT_TBPTT_STEPS=16
```

The active TOML sets `max_iter=5000` and `checkpoint.save_iter=50`; it deliberately does not set `grad_accum_iter`, because A2 derives that from `PSM_R09_B_TTT_ACTIVE_GA`.
## Required local assets

Default paths used by the facade:

```text
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3
LIBERO_LATENT_CACHE_ROOT=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1
EDGE_POLICY_CHECKPOINT=/disk/rl/models/Cosmos3-Edge-Policy-DROID
BASE_CHECKPOINT_PATH=cosmos-framework/examples/checkpoints/Cosmos3-Edge-Policy-DROID-dcp
WAN_VAE_PATH=cosmos-framework/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth
```

`LIBERO_ROOT` must contain `libero_spatial`, `libero_object`, `libero_goal`, and `libero_10`.

## Train / auto-resume

From the project root, use the single canonical entrypoint:

```bash
scripts/train_local_memory_ttt.sh
```

Default behavior is fail-safe auto-resume: if the run contains one or more `iter_*` checkpoints, the launcher resumes from the largest iteration; if no checkpoint exists, it starts a fresh run. Override paths or run length with `OUTPUT_ROOT`, `MAX_ITER`, `SAVE_ITER`, `CUDA_VISIBLE_DEVICES`, and the asset variables above.

For an explicitly fresh run, use a new output root:

```bash
FRESH_START=1 OUTPUT_ROOT=/path/to/new/output scripts/train_local_memory_ttt.sh
```

`FRESH_START=1` refuses a non-empty existing run directory, so it cannot silently overwrite or mix with an old run.

## Strict resume alias

```bash
scripts/resume.sh
```

This is only a compatibility convenience. It forwards to `train_local_memory_ttt.sh` with `REQUIRE_RESUME=1` and fails if no `iter_*` checkpoint exists. The Local Memory callback restores its data-progress state from the DCP `dataloader` component and fails closed if a resumed optimizer/model state lacks the required Local runtime frontier.

`scripts/train.sh` is also retained as a compatibility alias to the canonical Local Memory + TTT trainer.

Exact resume evidence is included in the canonical delivery verifier.

## Expected resource envelope

From the canonical full-catalog 20-step A2 run:

- average step wall time: `176.059 s`
- peak CUDA allocated: `45.045 GiB`
- base 5000-step projection: `10.1886 days`

The projection excludes evaluation and checkpoint overhead.

## Verification before a long run

```bash
scripts/verify.sh
```

The wrapper checks both the engineering delivery verifier and the 5000-window long-run readiness evidence. It does not rerun the multi-day training.