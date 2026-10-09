# V3 corrected Phase5 telemetry — implementation candidate / CPU gate

Date: 2026-10-09

## Exact pair

Candidate root (Gitlink-only implementation commit):
`604191f7458effbc4443a0102d72c00c86fadbce`

Candidate child:
`1a7689a31ab1a672a8431f40681464d6d25729e1`

Candidate root branch: `v3-corrected-telemetry-pair-20261009`
Candidate child branch: `v3-corrected-telemetry-20261009`
Child PR: `https://github.com/wxwy/cosmos-framework/pull/3`

Production root/child is **not** moved by this candidate.

## Code implementation

Diff from the last reviewed child `8c380056...`:
- `examples/psm_wma_robocasa_corrected_phase5.py` — replace internal observer with the passive observer import; add a no-payload-change trigger start observer; provide parameter class labels using the existing optimizer allowlist.
- `examples/psm_wma_robocasa_corrected_telemetry.py` — new observational rank0-only logger.
- `examples/psm_wma_robocasa_corrected_telemetry_test.py` — focused CPU tests.
- `examples/psm_wma_robocasa_corrected_phase5_test.py` — trigger/resume and selected-parameter grouping tests.

No changes to:
- model/trainer numerical path;
- grouped producer/window implementation;
- optimizer/scheduler;
- DCP/dataloader callback ownership;
- sample ordering;
- cache/latent pipeline.

`config.trainer.callbacks={}` is preserved.

## Telemetry semantics

- `native_backward`: report the actual already-weighted outer loss (no double weighting).
- `native_forward`: action/vision scalar metrics weighted by valid consumers / `plan.n_window`.
- `pre_optimizer`: read-only gradient norm over rank0-local gradient shards after unscale; action subset is included in generation norm; no all-rank/global claim.
- `post_commit`: read detached Local-TTT core summaries and committed epoch/frontier, then log one rank0 success record.
- first grouped trigger: start a per-iteration wall timer without changing yielded empty trigger batches.
- no logging on skipped/aborted windows; any post-commit logger error cannot retroactively abort an already-committed optimizer transaction.
- unavailable optional metrics are emitted as null, never silently fabricated as zero.

## Available local CPU evidence

The exact helper source body matches the candidate Git blob (`2a6f1d8851286d1009ec209e840b1e9f71e66a36` before adding standard SPDX header; only the header changed afterward).

Local isolated test harness:
- helper pytest: 4 passed;
- trigger callback semantics: 2 passed;
- total: 6 passed, 0 failed;
- helper `py_compile`: PASS.

These tests do not constitute the full project runtime test suite.

## CI infrastructure blocker (not a code test failure)

GitHub Actions Pre-commit on PR #3:
- base pre-commit hooks (size, secrets) PASS;
- full pre-commit fails to install pinned `rumdl==0.1.62` because that exact distribution is unavailable on the CI package index.
- The CI run does not reach a comprehensive Python code check. Do not label all lint/tests PASS from this CI result.

No unrelated global CI dependency change is authorized by this telemetry Gate.

## Verdict / next action

`CANDIDATE_TELEMETRY_IMPLEMENTED`

`ISOLATED_CPU_TESTS_PASS`

`PRODUCTION_PROMOTION_PENDING_TARGET_RUNTIME_CPU_STATIC_EVIDENCE`

Before promoting child/Gitlink, DS_PRO must run from this exact candidate pair on the training server:
1. `python -m pytest -q examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_corrected_phase5_test.py`;
2. `python -m py_compile` both production candidate Python files and the two test files;
3. targeted Ruff check + Ruff format --check;
4. `git diff --check 8c380056...HEAD`;
5. actual root/child/Gitlink clean lock;
6. config digest equivalence to formal30k `70e9867f...` (when exercising the final promoted pair, the immutable training configuration must remain unchanged).

No GPU optimizer step or formal30k authorized by this candidate.
