# PSM-WMA RoboCasa Local-TTT Rolling Status

Date: 2026-09-24

## Formal training

Current formal run reported by ds_pro:

- tmux: `robo`
- start: 2026-09-24 01:55 CST
- job: `local_ttt_robocasa365_target_atomic_n100_fsdp8_t16_d64_h256_k4`
- TOML: `action_policy_robocasa_edge_all_target_atomic_localmem_active.toml`
- topology: 8-GPU FSDP
- effective consumers/update: `B_stream=8 × TBPTT=16 × active_GA=2 × 8 ranks = 2048`
- warm start: `Cosmos3-Edge-Policy-DROID` DCP
- max_iter: 5000
- save_iter: 100 (command-line override)

Latest reported progress at 2026-09-24 10:54 CST:

- iter ≈ 1983
- train/loss ≈ 3000
- raw_last_group_loss ≈ 0.7–1.2
- active_groups = 2
- step ≈ 16 s
- latest reported checkpoint: `iter_000001900`

Output root:

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/outputs/local_ttt_robocasa365targetAtomicN100_fsdp8/`

Training log:

`logs/action_policy_robocasa_edge_all_target_atomic_localmem_active_sft.log`

Monitor log:

`local_ttt_monitor.log`

## Disk warning

Reported free space:

- `/mnt/data1`: ~124 GB free, filesystem ~99% used
- `/mnt/data`: ~190 GB free

Checkpoint accumulation remains a real operational risk. Do not delete or prune checkpoints implicitly; owner action is required for retention policy changes.

## Branch / repository identity correction

Important correction to the rolling handoff:

- root repository `wxwy/psm_wma` remote branch is still **`V2`**
- child repository `wxwy/cosmos-framework` remote branch is **`v2`**

Therefore:

- root governance commands in `AGENTS.md` and `.codex/skills/psm-execution-governance/SKILL.md` must continue to use `git fetch origin V2`
- child-specific synchronization must use `git fetch origin v2`

Do not globally replace root `V2` with lowercase `v2`.

Current implementation identities at the time this status was recorded:

- root V2 includes the RoboCasa evaluation work
- child gitlink points to the corresponding lowercase-v2 child implementation

## Launcher environment correction

The previously reported "launcher venv torchrun PATH hint pending" is already implemented in current child:

`examples/_sft_launcher_common.sh` checks for:

```bash
$WORKDIR/.venv/bin/torchrun
```

and prepends:

```bash
$WORKDIR/.venv/bin
```

to `PATH` before constructing the torchrun command.

This prevents a system/conda `torchrun` from silently selecting the wrong Python environment when the repository venv provides torchrun.

This item is therefore **CLOSED**, not pending.

## RoboCasa closed-loop evaluation

The closed-loop Local-TTT evaluation implementation is present in current V2 / child gitlink.

Main entry:

`scripts/eval_robocasa.sh`

Implemented path includes:

- RoboCasa Gym rollout
- left_wrist observation contract
- state16 construction
- Local-TTT episode session / acknowledgement / reset
- canonical 20-D action handling
- env action decoding
- completed evidence reconstruction from actual environment transitions
- per-episode actions / predictions / video
- per-task and aggregate SR

Current validation status:

- offline / code-level implementation: complete
- Local-TTT-disabled smoke reported SR 0/1: not evidence of Local-TTT runtime correctness
- real GPU + MuJoCo + `LOCAL_MEMORY_MODE=required` smoke: **pending**

Do not describe RoboCasa closed-loop evaluation as runtime-validated until the required Local-TTT smoke passes.

## Next execution steps

1. Continue monitoring the existing training run; do not alter its namespace or config while it is healthy.
2. Run one bounded Local-TTT closed-loop smoke against an existing checkpoint:
   `MAX_TASKS=1 NUM_TRIALS=1 REPLAN_STEPS=1 SAVE_VIDEOS=1 LOCAL_MEMORY_MODE=required scripts/eval_robocasa.sh <checkpoint>`
3. Record the ten runtime evidence items defined in:
   `docs/build/PSM-WMA_RoboCasa_Local_TTT_closed_loop_eval_implementation_2026-09-24.md`
4. Keep monitoring disk capacity and checkpoint growth; any checkpoint pruning policy requires owner decision.
