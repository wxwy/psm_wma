# Corrected V3 — Verified Dataset Index implementation / targeted CPU handoff

Date: 2026-10-09
Reviewer / code owner: ChatGPT
Status: CANDIDATE_IMPLEMENTED / TARGETED_CPU_AND_REAL_COLD_WARM_PENDING

## Frozen exact implementation pair

Root implementation / design: `7afeba0232bb50995f27ebd2b22f5741c6e79d96`
Child / Gitlink: `bd2fa59ca5b6f1a0b846e8effa5c7c2efcbed8d8`

Branches:
- Root: `v3-persistent-dataset-index-pair-20261009`
- Child: `v3-persistent-dataset-index-20261009`

Parent corrected bounded-GPU pair: root `0c84c9393fc3a24e713b47b1567bbee9258bd862` / child `3641e8e6114b893e3b088a4e5623306875a5cccd`.
This is a NEW implementation pair and previous CPU/GPU-smoke authority cannot be silently inherited.

Frozen design: `docs/build/PSM-WMA_V3_verified_dataset_index_contract_2026-10-09.md`.

## Actual code delta

Child only, relative to accepted bounded GPU preflight child:
1. `robocasa_verified_index.py` (new): one-time atomic receipt + mmap int64 source absolute-row mapping. Stat witnesses on 9k cached .pt and selected nonvisual Parquet, cryptographic digest of source metadata and index-row file. Warm missing/stale/corrupt file => reject, no fallback.
2. `robocasa_exact_window_cache.py`: Catalog reuses already verified static corpus digest rather than recomputing every window, still audits manifest and cache file membership.
3. `robocasa_exact_window_source.py`: use 9k episode offset index instead of materializing 2M Python tuples; cold binds source/cache and validates membership in one pass; warm restores checked static episode binding and mapping, skipping cold parquet identity scanner and .pt payload walks. Runtime read_window strict identities preserved.
4. `robocasa_exact_window_cached_sft.py`: optional shared Catalog/verified index, eliminating the repeated cache catalog construction in Phase5 preflight.
5. `examples/psm_wma_robocasa_build_verified_index.py` (new): standalone single-process CPU index builder / read-only verifier.
6. `examples/psm_wma_robocasa_corrected_phase5.py`: `--dataset-index-root` warm loading, timing report and strict bounded GPU preflight requirement. No changes to frozen `config_digest` authority fields.
7. New `robocasa_verified_index_test.py` plus a single bounded smoke fail-closed regression in `corrected_phase5_test.py`.

No code in model forward, generation/action/Local optimizer, fast weights, TTT temporal scan, data content conversion, DCP Slot-state save/restore, or step-cap Trainer is intentionally modified.

## Source-level reviewer observations

- Cold source identity is no longer redundantly scanned after LeRobot init. Original `_bind_episode` still validates each source row and each cache identity; any cache row witness outside the episode's contiguous absolute range is rejected. Missing/duplicate row checks remain before any training.
- Warm path uses an already accepted immutable file snapshot; large payload file **stat fingerprints are not cryptographic content SHA**. Runtime strict sample checks stay active.
- Source data LeRobotDataset factory still executes per-rank. Actual remaining cost and startup improvement require measurement; DO NOT promise sub-second startup without DS evidence.
- The static index does not store actual cached VAE latent tensors, formatted prompts or action batch, and is independent of per-rank DCP Frontier/fast-state Resume.
- The accepted exact corpus digests and formal 30000/500/100 schedule remain frozen. `--dataset-index-root` is not included in training config digest.
- Previous bounded GPU authorization is paused pending the new index candidate Gate.

## Required DS_PRO scoped CPU evidence

All code verification is on the exact pair in the existing single `psm_wma_v3` project directory. No extra worktree; preserve MM `SESSION.md` / `TODO.md`, historical `scripts/plot_h3f_monitor.py`, and DS reports.

1. Run targeted tests:
```bash
python -m pytest -q -p no:cacheprovider \
  cosmos_framework/data/generator/action/datasets/robocasa_verified_index_test.py \
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source_test.py \
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py \
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py \
  cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py \
  examples/psm_wma_robocasa_corrected_phase5_test.py
```
2. `python -m py_compile`, `ruff check`, `ruff format --check` on the eight changed/new Python files.
3. Verify root/child/Gitlink SHA exact, child clean, root historical MM/Evidence unchanged.
4. Verify the strict fallback and warm-constructor no-.pt access tests are actually executed (not skipped).

Any failure is BLOCKED, and DS does not modify code. Return raw logs/format diff to GPT.

## Real-data index Gate (only after scoped CPU acceptance)

One-time single-process CPU cold build on the previously accepted cache/source, writing to a NEW external directory:
```bash
python -m examples.psm_wma_robocasa_build_verified_index \
  --cache-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window \
  --source-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic \
  --index-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-verified-index-v1
```
Run `--verify-existing` with the same roots immediately after, then run corrected Phase5 `--preflight --dataset-index-root <same path>` with the exact formal config, root/child lock and model assets. Do not pass `--snapshot10` when measuring zero .pt reads during warm constructor.

Record:
- cold builder wall seconds and source_reader phase timing;
- warm verifier and preflight phase timing, LeRobot factory residual time;
- Episode/window totals, cache_corpus/source_binding/formal config digests, 451GB cache not rewritten;
- independent count of .pt torch.load before any requested training __getitem__ (expected zero for warm preflight);
- identical selected window Action/State/Latent and planned Segment identity vs cold path;
- saved index receipt size and row-mapping file size; no output under the repository;
- CPU memory peak and any regression on 8-rank startup if a separate multirank observation is authorized.

No 8xH100 GPU execution until actual cold build and warm preflight Gate is reviewed. No formal30k authority.

## Verdict

`PENDING_VERIFICATION` — implementation is pushed, exact Gitlink checked; no actual DS CPU pass or real corpus timing is yet claimed.
