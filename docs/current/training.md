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

## Fresh run

From the project root:

```bash
scripts/train.sh
```

The wrapper refuses to start into an existing non-empty run directory. Override paths or run length through environment variables such as `OUTPUT_ROOT`, `MAX_ITER`, `SAVE_ITER`, `CUDA_VISIBLE_DEVICES`, and the asset variables above.

Current readiness evidence authorizes the canonical 5000-step geometry; it does not mean the wrapper silently starts training.
## Resume

Use:

```bash
scripts/resume.sh
```

The underlying unified launcher scans the run's checkpoint directory and resumes from the largest `iter_*` checkpoint. The Local Memory callback restores its data-progress state from the DCP `dataloader` component and fails closed if a resumed optimizer/model state lacks the required Local runtime frontier.

Exact resume evidence is already included in the canonical delivery verifier.

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