# EvalV2 CLI `--tasks all` parity fix

Base V3 `0ab13951d640d50ea2c9c8812817bf3009eae7b5`, unchanged Child
`6c83596d6a259e89c4cd3e79424024983426ac3d`. Isolated branch
`v3-eval-v2-cli-tasks-all-20261031`; no V3 merge or runtime execution.

Bug: config.resolve converts CLIall to list[all]; identity.discover recognizes
only stringall as the complete18-task wildcard. Preserve exact CLI stringall;
other values keep original comma splitting, order and validation. Production
change is one line in scripts/robocasa_eval_v2/config.py. Discovery, task catalog,
scheduler, sampling, identity, Resume and Child stay unchanged.

New12 CPU cases cover dry-run/fresh/resume config parity with YAMLall, defaultall,
CSV order/override, invalid/mixed/duplicate names, incomplete18-task catalog and
the real public CPU dry-run JSON plan (both model/config files absent, runtime
preparation forbidden). Synthetic metadata only; no model/GPU/real DCP or env.
Run existing17 config/profile regression cases, not full84/GPU/OS suites.

Freeze newRoot/Child and tests before RED: the old config.py exact Git blob is
loaded into the unchanged CLI/discovery call chain with the same new frozen test;
expect one specific wildcard failure. GREEN uses the real new module and all29
cases, scoped Ruff0.12.7/check/format/AST and exact clean source before/after.
Archive commands/rawJUnit/logs/hashes, publish isolated candidate for fresh GPT
incremental review, thenSTOP. No active training/eval worktree,Job,config,outputs
or checkpoint access; current workaround YAMLtasksall without CLI flag remains
valid until code is reviewed/promoted.
