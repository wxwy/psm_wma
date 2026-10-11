# DS_PRO — V3 D1 Final CPU Prelaunch: two minimal parallel corrections
**Date:** 2026-10-11. Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Status:** `C1_CLOSED / D1_GPU_HOLD / FORMAL30K_STOPPED`. Detailed Review: `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_prelaunch_H1_H2_H3_review_444c232b_e9b8a41.md`.

**Only two CPU-only tasks in parallel. Do not restart full prelaunch tests or use GPU.**

### J1 — Fix and prove final torchrun argv + launcher guard
Correct `/tmp/ds_pro_v3_d1_r1/h3/launcher.py` (external harness only) to launch using the venv `torchrun --standalone --nnodes=1 --nproc-per-node=8 --max-restarts=0 /tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py ...`. Do not insert `/.venv/bin/python` between torchrun flags and script. If using `python -m torch.distributed.run`, document and verify exact equivalence; do not use both Python executable and script as positionals. Validate via CPU-only argv construction/static parse which is positional training_script, executable resolved to correct venv, options parse without firing workers, modes ordered ref→opt, and first error stops ALL further launches. Persist per-rank stdout/stderr for each before-start attempt and forbid overwriting.

Use shared-GPU guard fail-closed at **free <25,000 MiB**; <20,000 is not a separate permission to continue at 20–25GiB. External robotwin_server stability and user/owner GPU-sharing approval required, do not kill it. Do not inject/remove CUDA runtime env vars unless their frozen formal values are known; record resolved environment and reject mismatches. No optimizer/scheduler step or DCP save.

### J2 — Full-gradient parity comparator evidence contract
Keep the already frozen fp32/bf16 tolerances and existing CPU 14 cases. For every selected FSDP2 local shard, freeze how two **sequential** 8-rank modes record and compare **full values**, by rank, FQN, shard shape/dtype and identity; SHA256 full bit-match => `BIT_EXACT`; different SHA requires all-element streaming/chunked comparison for `WITHIN_TOLERANCE` or explicit `UNVERIFIED/BLOCKED`, **never sampled-256 PASS**. Require an additional CPU negative test with a sole difference past sample index256. Show disk/memory budget for per-rank full gradient evidence and time/cleanup plans (do not claim a full-gradient value comparison without data). Special case w0_fast_* must capture **actual grad** not just parameter state; candidate fast-state tensor comparator scope must be clear; loss fields must be native scalars and denominators correct. No relaxation of thresholds after GPU.

### Handoff / boundaries
Independent /tmp J1/J2 outputs and SHA256 of amended launcher, harness/comparator if amended; one merged report `DS_PRO_V3_D1_PRELAUNCH_J1_J2_FINAL_2026-10-11.md` with CPU-only results + corrected ready-to-launch CLI **without executing it**. No code in tracked worktree; no new GPU, torchrun worker process, DCP load/forward/backward, original Formal30k mutation, Fresh/Resume. Original C1 Shadow assets unchanged; `FORMAL30K_STOPPED`.

Once J1/J2 are presented and reviewed, GPT decides paired no-step D1 GPU authorization; no more repeated C1/Index/VAE/prelaunch scope beyond these blockers.