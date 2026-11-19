# G2 formal R1/R2 reproducible launch (30k)

Everything executable is versioned in this Root repository and the Gitlinked
Cosmos Framework Child. Clone with submodules, then install the training venv
under cosmos-framework/.venv or pass G2_PYTHON. No scratch-directory code is used.

From the root checkout run:

    bash scripts/g2/train_formal.sh r1 fresh
    bash scripts/g2/train_formal.sh r2 fresh

A fresh run uses G1 Local-TTT Iter 27700 **model weights only** and starts new
optimizer, scheduler and data-frontier states. R1 performs 30000 GEN+Action
updates. R2 is one continuous 30000-step run: 1000 Global-only iterations then
29000 Global+GEN+Action iterations; no data/Shuffle reset. Both use the certified
DATA_C v3, B8/GA4/T16/world4, no warmup/decay, and DCP every 100 steps.
Target actual effective consumers for each run: 59489136.

To resume the same job, use resume instead of fresh. Trainer uses strict
same-job DCP, including optimizer, scheduler, RNG and all four rank cursors.

The tracked configs/g2/robocasa365_target_atomic.assets.env supplies default
model/data paths for the data server. Override these G2_* environment variables
for a different machine. G2_G1_JOB_ROOT is an external MODEL ARTIFACT with
config.yaml and checkpoints/iter_000027700; it is NOT source code. Default
G2_OUTPUT_ROOT is the ignored repository outputs/g2_formal_20261119 directory.
Training and recipe outputs are artifacts, never executable source.

The launcher automatically prepares a clean ignored Git worktree INSIDE the
checkout at .g2_run_source (with a local clone of the exact Child Gitlink).
This avoids strict Phase5 source-identity failures caused by historical
untracked server evidence. No code is loaded from a scratch folder outside the
repository. This script does not manage GPUs or prune checkpoints.
