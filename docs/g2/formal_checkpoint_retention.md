# Formal G2 R1/R2 SafeLocal checkpoint retention

All executable maintenance code is tracked in this repository at
\`scripts/g2/maintain_formal_checkpoints.py\`. No external project scripts or
Python modules are loaded. This is an **independent CPU-only process**; it
does not modify or restart training, touch GPUs, reseed data, or rewrite
\`latest_checkpoint.txt\`.

The permanent keep schedule is **Iter 1000, 5000, 10000, 15000, 20000,
25000, 30000** for **both R1 and R2**. The native Trainer still produces
full 4-rank DCP every **100 optimizer steps**. Additional checkpoints are
eligible for deletion *only after* a newer **complete** DCP becomes the
latest pointer. The current latest is always retained for strict Resume,
regardless of the permanent schedule. A staging/incomplete, missing-sidecar,
unpublished, or very recent checkpoint is never deleted. The script does
not modify any component of a milestone checkpoint.

The watcher is fail-closed: it requires the exact single tagged job path,
valid \`v3_job_identity.json\` with the correct Root/Child and profile,
\`diagnostic_only_do_not_resume=false\`, a regular
\`latest_checkpoint.txt\`, a \`complete.v1.json\` marker, all four model/
optimizer/trainer sidecars and the native 4-rank dataloader sidecars.
It will not clean an unrelated Job, benchmark, or directory symlink.

## Commands

From the repository checkout, use **dry run** before applying:

\`\`\`bash
python3 scripts/g2/maintain_formal_checkpoints.py \
  --profile r1 --job-tag reviewed_spawn8 \
  --output-root "$PWD/outputs/g2_formal_20261119" \
  --once
\`\`\`

One-minute watcher in its own tmux session (only after verifying the
output-root and job tag):

\`\`\`bash
mkdir -p outputs/g2_formal_20261119/logs
tmux new-session -d -s g2_r1_ckpt \
  "python3 scripts/g2/maintain_formal_checkpoints.py \
     --profile r1 --job-tag reviewed_spawn8 \
     --output-root $PWD/outputs/g2_formal_20261119 \
     --interval-seconds 60 --min-age-seconds 30 --apply \
     >> $PWD/outputs/g2_formal_20261119/logs/r1_checkpoint_maintenance.log 2>&1"
\`\`\`

To inspect:

\`\`\`bash
tmux attach -t g2_r1_ckpt
tail -f outputs/g2_formal_20261119/logs/r1_checkpoint_maintenance.log
\`\`\`

An R2 watcher can use the identical script with \`--profile r2\`, an
independent tmux session, and its actual chosen formal job tag; do not
start it until the corresponding R2 formal job is authorized.

## Running a maintenance update while formal R1 has already started

R1's native training source and its checkpoint identity are pinned to its
original Root/Child Gitlink SHAs. **Do not change that source or re-pin
the R1 job identity while training or before strict Resume validation.**

A new maintenance-only Git checkout may be placed **inside the same repository**
as an ignored \`.g2_run_source_<maintenance SHA>_maint\` worktree and run
the watcher from there, passing the original R1 output root explicitly.
This is still checked-in source code, not a temporary script external to
the repository. Updating the checked-out maintenance code does not alter the
original R1 training worktree.

The script's default is **dry run**; only \`--apply\` can delete any DCP.
All deletion is permanent. Retain test evidence, logs, recipe files and Job
identity; only the designated old completed DCP directory is removed.
