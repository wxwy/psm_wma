# DS_PRO Task — RoboCasa365 v3 all-suite support

Date: 2026-09-22

Owner requirement: `--suite` must support the full EMBER RoboCasa365 LeRobot v3 collection, not target-only.

## Required suites

Use these internal suite keys and expected underlying task-class counts:

- `robocasa365_pretrain_atomic` -> 65
- `robocasa365_pretrain_mg` -> 60
- `robocasa365_pretrain_composite` -> 235
- `robocasa365_target_atomic` -> 18
- `robocasa365_target_composite_seen` -> 16
- `robocasa365_target_composite_unseen` -> 16

Corresponding local/HF repo slugs:

- `robocasa365-pretrain-atomic`
- `robocasa365-pretrain-mg`
- `robocasa365-pretrain-composite`
- `robocasa365-target-atomic`
- `robocasa365-target-composite-seen`
- `robocasa365-target-composite-unseen`

## Builder changes required

Current `tools/g0/build_cosmos_robocasa_latent_dataset.py` is target-only via `_TARGET_TASK_COUNTS` and argparse choices.

Generalize this to a single all-suite registry, e.g. `_ROBOCASA365_SUITE_TASK_COUNTS`, containing all six suites above.

Do not change the v3 task identity contract:

- `task_index` remains natural-language phrasing identity only.
- underlying `task_class` remains resolved from `annotation.human.task_name` through `meta/tasks.parquet`.
- `--episode-limit` remains deterministic per underlying `task_class`.
- class-count validation remains fail-closed, using the suite-specific expected count.
- exact-window/cache/camera semantics remain unchanged.

## Download helper changes required

Current `tools/g0/download_robocasa365_v3_target.sh` downloads only the 3 target repos.

Add an all-suite download path or replace/generalize the helper so all 6 official EMBER v3 repos can be downloaded. Preserve the ability to download only target subsets if useful, but target-only must not be the only supported path.

## Acceptance

1. `--help` exposes all six suite choices.
2. Metadata-only/class-catalog smoke for each suite resolves exactly:
   - 65 / 60 / 235 / 18 / 16 / 16 underlying task classes.
3. N=2 smoke remains per underlying task class, not per phrasing.
4. Existing target suite behavior is unchanged.
5. No v2.1/tar hierarchy is reintroduced.
6. Update the current RoboCasa365 v3 build document so it no longer states target-only support.

Do not start large pretrain-mg encoding as part of this change; code/support + bounded smoke only.
