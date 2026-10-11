# PSM-WMA V3 D1 Round1 — CPU Readiness Incremental Evidence Review

**Date:** 2026-10-11
**Formal verdict:** `REQUEST_CHANGES` (**D1-GPU-HOLD**; experiment-contract defects, not evidenced production bugs).
**Fixed Implementation:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` / Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Previous Gate:** `C1_RESTORE_PASS / C1_CLOSED`; do not rerun Gate A/B/C0/D0/C1.
**Source:** owner-relayed DS_PRO D1-A/B/C report `docs/collab/chatgpt/evidence/2026-10-11_V3_D1_R1/DS_PRO_2026-10-11_D1_R1_CPU_readiness_owner_relay.md`; raw DS `/tmp` docs are not directly inspected by GPT.
**Next scoped authorization:** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_targeted_parallel_CPU_remediation_authorization_444c232b_e9b8a41.md`.

## Frozen authority

`docs/collab/chatgpt/reviews/2026-10-11_V3_D1_round1_parallel_CPU_readiness_authorization_444c232b_e9b8a41.md` approved only CPU/static experiment planning. DS complied with no-GPU boundary, but the proposed GPU design must be independently accepted before running.

Pinned Child files independently checked for this narrow decision:
- `cosmos_framework/checkpoint/dcp.py:758-815`, `cosmos_framework/checkpoint/base.py:161-225` on same-job vs warm start.
- `cosmos_framework/trainer/local_memory_grouped_resume.py:231-253` on strict Local grouped restore.
- `examples/psm_wma_robocasa_corrected_phase5.py:263-310` on job name / checkpoint load-path semantics.
- `cosmos_framework/trainer/local_memory_grouped.py:201-347`, `cosmos_framework/model/generator/mot/local_memory_grouped_window.py:79-191` on the backward/optimizer commit seam.

## Finding D1-R1-F1: restore source identity INVALID for the proposed new job names

**Severity HIGH / BLOCKED (D1-C).**

DS proposes new `job.name=d1_shadow_singlestep_ref/opt` and `config.checkpoint.load_path=<C1 Shadow iter800>` but did not populate `save_dirname/latest_checkpoint.txt` under either new Job. Pinned `DistributedCheckpointer.keys_to_resume_during_load()` checks **own save_dirname/latest first**. When absent, the explicit `load_path` is a **warm-start source (`source.warm_start=True`)**, even with `load_training_state=True`. Pinned `require_dcp_grouped_resume_component` rejects `warm_start and load_training_state`; source classification is not a matter of choosing a different `load_path` string.

**Acceptance:** Design an actual same-job shadow load source for each invocation. Preferred minimal option: **sequential** ref/opt runs reusing the already physically independent C1 `SHADOW_ROOT` plus `job.name=formal_verified_index_30k_shadow`, preserving its own latest→iter800 and unchanged DCP files, with *separate external /tmp evidence/log dirs* per mode, always restarting new processes and reloading exact same iter800. This uses no extra 24GB duplicate and tests `warm_start=False`, but constructor may overwrite shadow config.pkl/yaml (allowed on shadow; preserve mode-specific copies). Alternative: construct two **fully independent** (no hardlink/symlink) same-job shadow checkpoint copies each with its own latest and job.name, if CPU-only capacity/identity proved and separately authorized to copy; no need when sequential same-shadow is safe. Ensure original formal Job and original Checkpoint are NEVER Trainer output paths.

A run under a genuinely new job name without its own same-job latest is **not allowed**. GPU remains HOLD.

## Finding D1-R1-F2: GPU memory budget mixes global used with local model memory and double-counts ranks

**Severity HIGH / REQUEST_CHANGES (D1-B).**

DS calls `Load-only≈53.9GB` **per-rank model stack**, while the matched C1 measurement `52,051–53,819MiB` is **global per-device used**, containing **45,581–47,263MiB** occupied by unrelated robotwin_server. Subtracting unmatched endpoints only yields an approximate own-process increment ~4.8–8.2GiB, not 53.9GB per-rank. Moreover the reported `model` shards are 8×~1.685GB = ~13.48GB *total on disk*; `optim` 8×~1.424GB = ~11.39GB *total on disk*. DS labels nearly these sums as **per-card**. On-disk sharded size cannot be equated with GPU allocation, but the discrepancy is sufficient to invalidate the per-rank formula. The `68–74GiB` predicted peak therefore has no coherent baseline or confidence interval.

**Acceptance:** Separately tabulate (a) device global used/free including robotwin, (b) model/optimizer DCP bytes **per-rank vs aggregate**, (c) actual own-process peak `torch.cuda.max_memory_allocated/reserved` **if existing C1 rank JSON has it**, (d) unknown forward/gradient/Local activation/workspace and adversarial foreign load. Replace hand-added 53.9/68–74 with a measured-based conservative budget and explicitly state unknown bounds. Guard should be based on **available free** and safe headroom against other jobs; cannot rely on 76GiB *own-process reserved* threshold when other jobs already occupy ~46GiB. Drop unsupported `expandable_segments:True` tuning unless existing frozen runtime confirms it; avoid changing recipe to pass resource gate. If sufficient headroom cannot be substantiated, label `D1_RESOURCE_BLOCKED`, not "fit" by guessed arithmetic.

## Finding D1-R1-F3: no-step objective is plausible, but the proposed harness seam is incomplete

**Severity MEDIUM / CONDITIONAL PASS (D1-A).**

Pinned `GroupedLocalMemoryTrainer.training_step` calls `window.run_member` for member0 then member1; at final member it unscales/validates, then calls `window.finish(observed_optimizer_step)`, which executes optimizer+Scheduler and publishes candidate. A full `trainer.training_step(...,grad_accum_iter=1)` **will therefore update weights**. Merely "stop after backward" is not a production entrypoint.

But `GroupedLocalMemoryWindow.begin(); run_member(...native_loss, backward)` is an authentic lower-level seam. `run_member` computes per-index weighted losses and real backward, commits **candidate** sidecar within window; without `finish`, global live/frontier remains unchanged. An external test harness can construct the same closures/functions as production, capture pre-step gradients and candidate fast state, then abort/dispose the window without calling optimizer/scheduler step. This requires precise static call trace, valid FSDP2 scan registration, matching callbacks, loss weighting, GradientScaler state and tensor fingerprint timing; no production source edits or fake loss.

**Acceptance:** Write external CPU-only static/dryrun harness contract referencing exact production `native_loss/backward` callbacks and `window.begin/run_member/abort` path, explicitly prohibit calling `trainer.training_step` for final member and `window.finish`. Ensure P2 iter800 GA identity/validity and w0 Fast State copied from reloaded DCP, not initial. Pre-step parity can be an **input-to-gradient parity gate**; DO NOT claim verified optimizer-step numerical parity or actual full-step throughput without running that step. If a true optimizer-step target is later needed, separately authorize a bounded Shadow-only matched two-mode optimizer step **after** pre-step comparison, not an unpaired optimized-only step. Freeze per-dtype tolerances/metric scales before GPU; blanket bf16 atol=rtol=1e-3 may be inappropriate for fp32 gradients or nearly-zero values.

## Verdict and next action

- `D1-A CONDITIONAL_PASS` (valid objective but no safe precise harness trace/dtype-specific acceptance yet).
- `D1-B REQUEST_CHANGES` (unit/rank-baseline conflation; start threshold unsupported).
- `D1-C BLOCKED` (same-job vs warm-start misclassification).
- **Overall `D1_R1_REQUEST_CHANGES / D1_GPU_HOLD`**. No demonstrated production defect, no C1 reversal, no additional Gate A/B/Dataset or VAE work.

**Only authorize** three parallel, narrow **CPU-only** R1 remediation tasks in `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_targeted_parallel_CPU_remediation_authorization_444c232b_e9b8a41.md`. Do not repeat full D1 design, and do not run model/GPU until GPT re-adjudicates the resulting artifacts. E/F/Original Formal30k Resume and DCP writes remain HOLD. This prevents a predictable strict-resume error or resource collision instead of treating an avoidable failed launch as a GPU experiment.
