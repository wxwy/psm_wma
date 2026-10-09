# V3 Verified Dataset Index — CPU Round 1 Blocker Remediation

Date: 2026-10-09
Reviewer/code owner: ChatGPT
State: `CANDIDATE_FIX_SUBMITTED / TARGETED_CPU_RETEST_PENDING`

## Exact fixed implementation pair

- Root: `65a6503667eeb7f36974422a0ca890e0745c02fc`
- Child / Gitlink: `751b129bfb62ee1f61b34fd4d67278094bd9f7cf`
- Candidate root branch: `v3-persistent-dataset-index-pair-20261009`
- Candidate child branch: `v3-persistent-dataset-index-20261009`
- DS_PRO tested earlier, rejected implementation pair: root `bb89741916ff13b934c437a5213837256daa568a`, child `f7d0897e9c801c044c52dd70f4d8a7ae4663d579`.

## DS_PRO CPU Round 1 evidence

Source of evidence is DS_PRO's report; code owner did not independently rerun pytest/Ruff on the DS training host.

- New verified-index CPU tests: **10 passed**, with `HF_HUB_OFFLINE=1` set before pytest.
- Existing source/cache/SFT regression: **123 passed, 1 failed**; failing terminal window source/cache witness precedence test.
- Ruff check: **FAIL**, I001 on `robocasa_exact_window_cached_sft.py`.
- Ruff format --check: **FAIL**, three files require formatting (index implementation, index tests, index builder).
- Python py_compile: **PASS**.
- DS did not build the real index, warm load it, alter code, or start GPU.
- DS confirmed SHA identity and clean child tree; MM and old Evidence files retained.

## Code-owner remediation

The upstream candidate branch already contained a two-commit fix before this report was processed:
1. Restore terminal-window error precedence in `robocasa_exact_window_source.py`: a corrupt first/last window must produce the existing `startup first/terminal` failure before the new out-of-range check. Production runtime middle-window validation remains intact.
2. Add a test for source metadata mutation and index schema mismatch.

These existing fixes are preserved in the new child SHA.

Additional corrections made by ChatGPT from that branch tip:
- Correct lexicographic import ordering (`robocasa_lerobot_dataset` before `robocasa_verified_index`) in `robocasa_exact_window_cached_sft.py`.
- Flatten the verified-index sorted row guard, fold applicable test tuple/function calls, and fold `VerifiedExactWindowIndex.open` invocation in the cold-build script to match the repository Ruff 0.12.7 formatter's 120-character limit.
- No model loss, Optimizer, Local-TTT scan, fast-weight update, original dataset sample math, checkpoint/DCP, or formal 30k schedule has changed in these formatting-only commits.

No independent Ruff binary is available in the code-owner runtime, so a Ruff formatting PASS **must not** be assumed until DS runs the exact new pair. If format fails, DS should report complete `ruff format --diff`, not edit code.

## Next gate — narrowly scoped CPU retest

Set `HF_HUB_OFFLINE=1` in environment **before starting pytest**, because the project's `conftest.py` rejects import-time changes to that environment variable.

On the sole existing DS working directory with new exact pair:

- `pytest -q -p no:cacheprovider cosmos_framework/data/generator/action/datasets/robocasa_verified_index_test.py cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source_test.py cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py`
- `ruff check` on the eight verified-index implementation/test files
- `ruff format --check` on the same eight files
- Python `py_compile` only if a code/format issue warrants it; prior result already passed
- Check root/child/Gitlink, child clean, root existing MM/Evidence untouched.

If all checks pass, DS is authorized to perform the previously scoped **single-process CPU** index Cold Build, then read-only Warm Load with formal Phase5 `--preflight --dataset-index-root`, record cold/warm init stage timings and digests, and return evidence. Do not run GPU until reviewed.

## Restrictions

- No destructive reset/clean, no new worktree, no DS code edits/commits/uploads.
- Cold build writes one new indexed receipt under a distinct external output directory, never overwrites source/cache.
- Any cold/warm failure is fail-closed: stop and return actual traceback, do not switch to legacy cold startup.
- Previously closed GPU prep and telemetry readiness remain closed, but **3-step GPU smoke is PAUSED** until real index checks and the new warm preflight pass. Formal 30k is not authorized.
