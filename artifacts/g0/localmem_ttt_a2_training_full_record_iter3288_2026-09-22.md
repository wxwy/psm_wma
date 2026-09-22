# PSM-WMA E003 — Local Memory A2 Training Full Record (Summary Archive)

Recorded: 2026-09-22  
Evidence source: owner-provided remote-server training summary  
Raw training logs: remain on the remote training server and are not copied into this repository  
Canonical loss figure: `artifacts/g0/localmem_ttt_1x32_training_loss_iter3288.webp`

![Local Memory A2 raw_last_group_loss](./localmem_ttt_1x32_training_loss_iter3288.webp)

## 1. Experiment role

Local Memory A2 is the formal active local-memory TTT route used as an E003 comparison against native recent-history controls such as WINDOW-H16.

Route identity:

```text
member_layout = a2
B_stream      = 8
ttt_tbptt_steps = 16
group_size    = 8
active_groups = 2
```

The A2 implementation includes configurable stream width, exact D025 handling, native weighted-loss correction, atomic multi-row fast state, recovery geometry, and the online transactional API.

## 2. Environment and launch

Hardware:

- single node
- 8 × A100 80GB
- FSDP8
- NCCL timeout 1800s
- seed 42

Launch command reported by the owner:

```bash
python -m cosmos_framework.scripts.train \
  --sft-toml=examples/toml/sft_config/action_policy_libero_edge_all_localmem_active.toml \
  -- trainer.max_iter=5000 checkpoint.save_iter=200 trainer.logging_iter=1 \
     model.config.parallelism.data_parallel_shard_degree=1 \
     model.config.parallelism.data_parallel_replicate_degree=-1
```

Run:

- RUN_NAME: `edge_libero_4in1_localmem_active`
- OUTPUT_ROOT: `outputs/train_local_memory_a2`
- optimizer: FusedAdam / AdamW
- outer lr: `5e-5`
- scheduler: warmup cosine / LambdaLinear
- TTT inner lr: `0.1`
- grad clip norm: `1.0`
- observed clipping values: approximately `2.36–2.375`
- trainer `grad_accum_iter=2`
- `microbatches=2`
- configured `max_iter=5000`
- `save_iter=200`
- `logging_iter=1`

## 3. Data

LIBERO 4-in-1:

- libero_spatial
- libero_object
- libero_goal
- libero_10

Dataset/config summary:

- LeRobot v3
- fps=20
- chunk_length=16
- image_size=256 at dataset configuration
- mode=wam
- camera=concat_view
- action_space=frame_wise_relative
- rotation=6d
- quantile_rot normalization
- val_ratio=0.01
- seed=0
- cfg_dropout=0.1
- episode_shuffle_seed=42
- iterable_shuffle=False
- packing ceiling: `max_num_tokens_after_packing=74000`
- tokenizer: Cosmos3-Edge-Policy-DROID
- latent cache: `/mnt/data1/data_v2_0617/libero4in1_wan2.2vae_latent_cosmos_style/`

## 4. Pre-run validation

A resume smoke was completed before the formal run:

- `max_iter=6`
- `save_iter=3`
- iter1/2/3 loss: `1.611394 / 1.710646 / 1.662216`
- iter3 wrote a complete DCP plus `dataloader/rank_0.pkl`
- after kill, auto-resume loaded `iter_000000003`
- iteration 4 resumed with finite loss

The owner reports that iter1 matched the D8a reference bit-for-bit.

Catalog geometry:

- catalog blocks: 14,430
- one full A2 training window: 128 members
- one catalog pass provides approximately 112.73 optimizer iterations
- long training therefore depends on catalog epoch reuse
- a 45-epoch probe covered 3,704 windows and 12 rebind seams successfully

## 5. Formal training timeline

Early launch attempts included:

- environment failures from using the wrong Python interpreter, producing `ModuleNotFoundError: loguru`
- two early 10-step runs
- one SIGTERM on 2026-09-19 09:49:21

Main run:

```text
start: 2026-09-19 09:24:37   iteration 1
stop : 2026-09-20 01:35:27   iteration 3288
duration: approximately 16 hours
```

The main run had no reported intermediate crash.

A TerminationSignalCheckpoint SIGTERM handler was installed at 2026-09-19 09:54:33.

Training was stopped externally by owner decision at iteration 3288 and did not reach the configured ceiling of 5000.

Last checkpoint:

```text
iter_000003200
```

## 6. Checkpoint / loss timeline

Important metric convention:

> `train/loss` is cumulative and must not be interpreted as the instantaneous training loss. The meaningful training curve is `raw_last_group_loss`.

| Iter | Time | train/loss cumulative | raw_last_group_loss | step wall (s) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 09:24 | 16.55 | **16.35** | 19.2 |
| 200 | 10:48 | 1403.6 | 1.856 | 15.7 |
| 400 | 11:43 | 1705.5 | 1.309 | 15.7 |
| 600 | 12:37 | 1936.9 | 1.399 | 15.2 |
| 800 | 13:31 | 2145.6 | 1.416 | 16.0 |
| 1000 | 14:25 | 2342.3 | 1.064 | 17.1 |
| 1200 | 15:20 | 2529.1 | 1.178 | 19.7 |
| 1400 | 16:27 | 2708.7 | 0.976 | 20.2 |
| 1600 | 17:34 | 2881.0 | 0.964 | 18.9 |
| 1800 | 18:39 | 3049.1 | 0.930 | 19.5 |
| 2000 | 19:42 | 3211.9 | 0.884 | 17.3 |
| 2200 | 20:40 | 3370.5 | 0.895 | 17.3 |
| 2400 | 21:35 | 3525.6 | 0.782 | 16.8 |
| 2600 | 22:29 | 3677.9 | 0.639 | 15.9 |
| 2800 | 23:22 | 3827.1 | 0.851 | 16.3 |
| 3000 | 00:17 | 3973.3 | 0.763 | 16.0 |
| 3200 | 01:11 | 4116.9 | 0.834 | 15.7 |
| 3288 | 01:35 | 4178.7 | **0.790** | 16.7 |

Observed change in `raw_last_group_loss`:

```text
16.35 -> 0.79
approximately -95%
```

The archived figure above should be treated as the canonical visual record of this curve.

## 7. Runtime performance summary

Reported steady-state behavior:

- average step wall: approximately **16.4 s**
- throughput: approximately **220 optimizer iterations/hour**
- model compute: approximately **10.8–14.4 s / step**, about 71%
- non-model/other: approximately **4.5 s / step**, about 28%
- dataloader wait: approximately 1%

The active A2 route therefore has measurable non-model overhead from stream/window/driver/TTT machinery, but no meaningful dataloader bottleneck was reported.

## 8. Evaluation checkpoints

### iter2800

```text
libero_spatial 94
libero_object  97
libero_goal    68
libero_10      72
overall       331/400 = 82.75%
```

### iter3000

```text
libero_spatial 94
libero_object  97
libero_goal    79
libero_10      88
overall       358/400 = 89.5%
```

Change iter2800 -> iter3000:

- overall: +27 successes / +6.75 pp
- goal: +11 pp
- libero_10: +16 pp
- spatial/object unchanged

Canonical evaluation artifacts already archived:

- `artifacts/g0/localmem_ttt_1x32_iter2800_eval_summary.md`
- `artifacts/g0/localmem_ttt_1x32_iter3000_eval_summary.md`
- `artifacts/g0/localmem_ttt_1x32_iter3000_required_init_off_ablation_summary.md`

## 9. Residual weak tasks at iter3000

- libero_goal task 0: open middle drawer — 0/10
- libero_goal task 7: turn on stove — 3/10
- libero_10 task 8: put both moka pots on stove — 4/10

## 10. Evaluation execution

Evaluation used:

- NUM_STEPS=30
- num_envs=4
- 10 trials/task
- 10 tasks/suite
- 100 episodes/suite
- 400 episodes total
- 6D rotation
- frame_wise_relative action space

Parallel evaluation infrastructure used multiple model servers and episode-boundary resume.

The owner reports:

- iter2800 libero_10 missing episodes were completed using 6 GPU-parallel servers
- iter3000 libero_10 missing episodes were completed using 7 parallel clients/ports
- `partial_summary.json` is the episode-completion authority
- errored episodes are rerun
- Local Memory session state is not resumed mid-episode; resumed evaluation starts a fresh episode session

## 11. A2 vs WINDOW-H16 fairness / compute-alignment note

### Primary matching criterion: training sample amount

For E003, the **primary fairness criterion is the amount of training data consumed**, not equality of microbatch count, wall time, or theoretical FLOPs.

The comparison should be read in this order:

1. **effective consumers / optimizer update**
2. **total consumers seen at the compared checkpoint**
3. same source data distribution / task mix as far as the method permits
4. method-specific compute, wall time, and VRAM reported separately as cost

Current recipes are designed around the same effective consumer budget:

```text
A2 Local Memory ~= 2048 consumers / optimizer update
WINDOW-H16      = 2048 consumers / optimizer update
```

Therefore, when comparing both at the same optimizer iteration, the total training exposure is also aligned. For example:

```text
iter3000 × 2048 consumers/update = 6,144,000 consumers
```

This is the main experimental matching condition.

### Microbatch count is an implementation detail, not the fairness target

A2 uses fewer/heavier active-route microbatches, while WINDOW-H16 uses more native microbatches because each WINDOW sample carries a longer Transformer context.

The fact that:

```text
A2 microbatches     = 2
WINDOW microbatches = 16
```

does **not** by itself make the experiment mismatched. The methods realize the same effective sample/update budget through different internal execution structures.

### Compute cost is secondary and should be reported, not matched away

Strict FLOP equivalence is neither established nor required for the primary ablation:

- A2 pays TTT fast-state update, stream/window driver, inner-loss, and state-management overhead
- WINDOW-H16 pays for a substantially longer native Transformer context by exposing up to 16 full-spatial historical vision items

These are intrinsic costs of the methods being compared.

Preferred report wording:

> **A2 and WINDOW-H16 are matched primarily by effective training sample count (consumers per optimizer update and total consumers seen at the compared checkpoint). Method-specific token/FLOP, wall-time, and memory costs are reported separately rather than used as the primary matching criterion.**

Reported wall-time observations remain useful as systems-cost measurements:

- A2: ~16.4 s/update
- WINDOW-H16: ~25 s/update when clean, ~34 s/update under eval-server contention

Do not reinterpret these wall times as the fairness criterion or as pure model FLOPs.

## 12. Artifact locations

Remote-server paths reported by owner:

- training log: `outputs/train_local_memory_a2/logs/action_policy_libero_edge_all_localmem_active_sft.log`
- checkpoints: `outputs/train_local_memory_a2/cosmos3_action_libero/action_sft/edge_libero_4in1_localmem_active/checkpoints/`
- latest checkpoint on remote: `iter_000003200`
- sim_test roots: `iter_000000800`, `iter_000002800`, `iter_000003000`
- aggregated ablation: `results/libero_local_memory/iter_000003000/`

Repository-side archived evidence:

- this summary
- `artifacts/g0/localmem_ttt_1x32_training_loss_iter3288.webp`
- iter2800 evaluation summary
- iter3000 evaluation summary
- iter3000 Required / Init / Off ablation summary

## 13. Evidence limitation

This archive is based on an owner-provided training summary because the full remote training server filesystem is not available in this repository.

The summary should therefore be treated as a canonical experiment record supplied by the experiment owner, not as a fresh raw-log re-audit performed from this repository.
