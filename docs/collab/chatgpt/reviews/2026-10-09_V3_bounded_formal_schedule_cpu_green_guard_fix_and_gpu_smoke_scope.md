# Corrected V3 — Bounded Formal Schedule CPU Gate and Controlled GPU Telemetry Smoke

Date: 2026-10-09
Reviewer: ChatGPT
Status: previous bounded-stop CPU Gate PASS; new root-status lock adjustment pending narrow CPU corroboration

## Evidence accepted on exact previous candidate pair

- Root `f99087221d5630db80a8e4e026cc30ed623cd9b8`
- Child/Gitlink `f6b4801c645a78b4ac9dfa0438901d5187747c43`
- DS_PRO real training-runtime evidence: bounded stop tests 12 passed / 28 deselected; full two corrected test files 49 passed / 1 skipped; child clean; root/child/Gitlink identity exact.
- `max_iter=30000`, `warmup=500`, `save_iter=100` retained; bounded stop is a separate execution limiter and does not enter the frozen formal config digest.
- Historical full-corpus, Phase3.5, one-step optimizer, and telemetry-readiness Gates remain CLOSED. No repeat GPU iter1, cache build or 33-minute independent formal preflight is required.

Verdict: `BOUNDED_STOP_TARGETED_CPU_GREEN` on that exact previous candidate.

## Independent source-review finding / narrowly scoped fix

DS deliberately preserves modified root `SESSION.md`, `TODO.md` and 37 untracked `artifacts/g0/*.json` and `docs/collab/chatgpt/DS_PRO_*.md` Evidence in its **single** project directory.

The previous `verify_root_child_lock` unconditionally rejected all non-empty root git status, even if the root tree and child implementation SHAs match and no executable code is dirty. That would block the GPU smoke before model initialization.

This has been corrected in the sole candidate:
- Last reviewed GPU stop's two-loop cap, scheduler, optimizer and DCP semantics are unchanged.
- Child source remains **entirely clean and exact SHA-pinned**.
- Root HEAD and Gitlink remain **exact SHA-pinned**.
- Only tracked root `SESSION.md` / `TODO.md` ordinary modifications and untracked JSON under `artifacts/g0/` or DS markdown reports under `docs/collab/chatgpt/DS_PRO_*.md` are exempted.
- Any other root edit, deletion, renamed file, unrecognized untracked file or code alteration fails closed. The parser uses `git status --porcelain=v1 -z --untracked-files=all` to avoid status whitespace corruption.

Additionally, the bounded 3-step diagnostic samples CUDA Events and slow-parameter norms on its third step; formal long training retains the 100-step cadence.

## New exact code implementation pair (needs narrow test)

- Root: `6f86a5c8a080f0d50df8d75c310982a61da0ea03`
- Child/Gitlink: `18f1a3598b3c89137e15b80fcfaad652628db405`
- Root candidate branch: `v3-bounded-formal-schedule-pair-20261009`
- Child candidate branch: `v3-bounded-formal-schedule-20261009`

Later review/bookkeeping-only root commits may differ in SHA. For execution, always replace `--expected-root` with the actual full candidate root HEAD explicitly handed to DS; never mix formal-pair versions.

## CPU gate for this delta only

DS_PRO on a **single existing** local root+child checkout, preserving MM notes and evidence:
1. Verify exact root/child/Gitlink; child clean and root only the previously disclosed noncode dirt.
2. Run `pytest -q -p no:cacheprovider examples/psm_wma_robocasa_corrected_phase5_test.py -k "root_noncode or root_dirty or bounded_diagnostic_final"`, with targeted test output.
3. Run `ruff check`, `ruff format --check`, `python -m py_compile` on the Phase5 entrypoint and its test only.
4. Call `verify_root_child_lock` directly once with `root_worktree` and the exact pair. This must return the observed count of permitted local noncode changes, without deleting/stashing files.
5. If any unexpected status appears, stop and report the exact path. DS must never edit, reset/clean, create worktrees, or upload code.

No historical rerun, 8xH100 single-step repeat, VAE rebuild or full 30k is authorized.

## Conditional separate GPU Gate (only after the above CPU gate PASS)

`CORRECTED-V3-FORMAL-SCHEDULE-BOUNDED-GPU-TELEMETRY-SMOKE`

**Exactly one fresh 8xH100 diagnostic, at most three completed optimizer steps, and immediate bounded completion.**

Required launcher constraints:
- `--phase fresh`
- `--stop-after-iter 3`
- `--max-iter 30000 --warmup 500 --save-iter 100`
- `--t 16 --b 8 --ga 2 --k 4 --world-size 8`
- isolated new `--job-name bounded_...` namespace and official DROID DCP fresh model initialization, training state disabled
- same corrected exact-window cache and flat source authority
- actual root HEAD, child SHA, root Gitlink strict match
- formal config digest **`70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`**
- correct `PYTHONPATH` resolution to child source
- no fallback and no trainer/optimizer change outside the reviewed scoped diff

Stop and report immediately on any preflight, code, data or runtime error; do not retry with relaxed settings or resume the diagnostic checkpoint.

GPU evidence acceptance:
- exit 0, trainer completed_iteration=3, observer completed=3, exactly three successful optimizer updates, no iter4
- `[CorrectedV3][bounded_stop]` proves max_iter=30000 / warmup500 / formal digest
- all per-step rank0 structured records present, finite outer/action/vision/Local-inner loss, expected gradient groups, step wall and timing breakdown, LR finite
- third-step CUDA event sample and selected slow-parameter norm fields populated or any explicit null/error investigated
- no extra per-consumer synchronization for observer, no DCP ownership/Local frontier error, no OOM
- final checkpoint `iter_000000003` contains model, optimizer, scheduler, trainer and all eight dataloader rank pkl components; classify as **DIAGNOSTIC_ONLY_DO_NOT_RESUME**
- reports include wall duration, peak allocated/reserved GPU memory and `data_prepare_ms` vs model compute/forward/backward to diagnose bottlenecks

This conditional authority **does not** authorize starting or resuming formal30k training.

## No DS code ownership

GPT alone changes GitHub code and configuration. DS only syncs the sole specified version into its existing project directory, runs approved checks and reports raw evidence. No multi-worktree requirement and no destructive cleanup.
