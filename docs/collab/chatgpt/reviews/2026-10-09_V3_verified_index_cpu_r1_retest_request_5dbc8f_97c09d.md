# V3 Verified Dataset Index — CPU Round 1 Remediation Retest

Date: 2026-10-09
Status: **CANDIDATE_FIXED / TARGETED_CPU_RETEST_PENDING**
Verdict: **NOT GREEN; Cold Build / Warm Load / GPU NOT AUTHORIZED before the CPU gate**

## Exact implementation pair

- Root implementation: `5dbc8f547fbc3e995995a66037b4b0625d883e39`
- Child / root Gitlink: `97c09d7b31765741d684258385bb9ed9b63ec91c`
- Root candidate branch: `v3-persistent-dataset-index-pair-20261009`
- Child candidate branch: `v3-persistent-dataset-index-20261009`

## Evidence and scoped fixes

DS_PRO verified the earlier exact pair `bb897419/f7d0897e` on the actual CPU runtime and returned **10 index tests passed, 123 regression passed, one regression failed**, plus Ruff I001 and format failures. The one existing regression failure involved the first/terminal cache witness error precedence.

The child candidate has advanced strictly from the rejected SHA. Incremental edits:
1. Preserve `startup first/terminal` precedence in `RoboCasaExactWindowSourceReader._bind_episode`, without bypassing the new out-of-range witness guard for middle windows.
2. Add verified-index invalidation tests (changed source metadata and schema version).
3. Restore Ruff I001 alphabetical import ordering in `robocasa_exact_window_cached_sft.py`.
4. Normalize Ruff formatting in `robocasa_verified_index.py`, its test module, and the one-time builder.
5. Replace the long chained cold/warm `config_digest` equality assertion with separate `cold_digest` and `warm_digest` variables; **test-only**, no training semantic change.

No changes to optimizer, loss, model forward, fast weight, DCP state, dataset payload format, sampler/slot state or formal30k scheduling were made in these remediations.

## Exact targeted CPU gate

Set `HF_HUB_OFFLINE=1` **before pytest process launch**, as the project conftest detects environment modification at teardown.

Run:
- Index tests: `cosmos_framework/data/generator/action/datasets/robocasa_verified_index_test.py`
- Regression: `robocasa_exact_window_source_test.py`, `robocasa_exact_window_cache_test.py`, `robocasa_exact_window_cached_sft_test.py`, plus directly relevant `robocasa_exact_window_local_test.py`
- Bounded Phase5 dataset-index preflight guard test
- Ruff check/format --check and py_compile on eight changed index/entrypoint/test files, with the project's exact Ruff configuration
- SHA/Gitlink/child clean, MM notes and evidence untouched

This candidate has **NOT** yet been independently validated with Ruff 0.12.7 in DS environment. If any check fails, DS_PRO must stop and send raw stderr / full `ruff format --diff` instead of editing code.

Only after CPU GREEN:
- One **single-process, CPU-only, outside-worktree** real 9126-episode index Cold Build to new nonexisting external directory.
- One read-only Warm Load and corrected formal-config `--preflight --dataset-index-root`.
- Collect Cold/Warm timing breakdown, the three digests, representative real source/action/latent sample parity and expected formal digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`.
- Missing/changed index must fail closed; do not silently redo cold verification on an invalid receipt.

**Do NOT launch the 3-step GPU Smoke or the formal30k run** until separate review of the real cold/warm evidence. DS_PRO remains a read-only code validator/executor: no worktrees, source edit, commit, upload, force reset, or clean.
