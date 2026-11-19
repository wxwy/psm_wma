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

## New G2 async B8 loader (both R1 and R2)

Both launch commands now set `--num-workers 8` for the native
`AsyncExactWindowRawPrefetcher` (eight CPU threads per rank). This runs
immutable Source/Cache and G2 DATA_C State15/initial-language reads in
the background, one GA member ahead of the current GPU computation. Tokenizer
transforms and legacy-global CFG random draws remain on the trainer thread,
preserving the original per-consumer order, model semantics and Local-TTT/DCP
state; this is deliberately **not** the No-TTT-only multiprocessing loader
or an unvalidated change to `consumer_keyed_v1`.

G2 `CandidateAlignedG2Provider` uses a B8-aware 16-episode LRU rather
than the former four-episode cache. Each async worker forks an independent
runtime DATA_C provider so its mutable episode/language/ViewReader caches
are not shared across workers or with the trainer. Read-only certified
metadata may be shared. These changes affect both R1 and R2, including
R2's selected real Sixview Latents.

The asynchronous run has a **new job namespace**
(`r1_g2_formal_async8_30000_20261119` /
`r2_g2_formal_async8_30000_20261119`); do not resume the older, interrupted
synchronous R1 job (which stopped before its first checkpoint). New model
weights still warm-start from the original G1 Iter 27700 artifact.

The clean in-repository source worktree is suffixed by the pinned Root
commit SHA so that a newer R2 or R1 launch does not modify a checkout
used by an already-running job.

CPU tests cover B8 LRU behavior, raw-prefetch ABI/RNG ordering, provider
isolation and real DATA_C R1/R2 threaded-read parity. Real 4-GPU
throughput must be measured when the Owner manually launches training;
the No-TTT process-worker 9–10s/step speed is a reference, not a
guarantee for Local-TTT or Global Memory training.
