# PSM-WMA V3 r2 new Pair — GPT independent static follow-up Fresh Review

Date: 2026-10-10
Reviewer: ChatGPT (independent design/code/Evidence reviewer)
**Formal verdict: `APPROVE` — ONLY the incremental Ruff/fixture remediation review and permission to execute the read-only independent DS_PRO Gate A.**
**NOT `GATE_A_PASS`, NOT MC-01/production or Resume approval.**

## Exact target and predecessor

- Current implementation/design Formal Root: `444c232b976e80ac68cde9e7370e73b9f6410f0e`
- Current Formal Child / Root Gitlink: `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
- Previous Root implementation: `cf0c92731197bfdd0de073a4c07ca93194f58968`
- Previous Child / Gitlink: `d41be4f5485dcd9321318840c8c278c1f7487924`
- Parent of the new Root: `32cc72bf49385904c2e720314ea47f47f492906c`; subsequent Root `24423db2a11fbc30feb43e6c0283e388fffdbe31` is the Codex Fresh Review request/Inbox bookkeeping commit, not a replacement formal implementation SHA.
- Root tree and Child branch were directly re-read and agree on the new Gitlink. New Formal Pair differs; therefore this is a fresh *incremental* review rather than repetition of the old target.

## Independent change review and evidence boundary

1. The previous independent DS_PRO CPU Gate A on `cf0c9273/d41be4f` failed exactly at `ruff_check` with 81 violations. `verify_pair` and 36-file `py_compile` passed; later stages were correctly not run. That failure remains historical evidence and is **not** a new-Pair verdict. The DS operator's single-file H3-F quarantine/restoration witness showed SHA256/mode/status retained after the failure; no DCP/GPU/train touched.
2. The new Child is the direct child of `d41be4f`. Actual Git diff has **19** changed Python paths, predominantly import ordering, unused import removal and formatting. Inspected representative production diffs (dataset/reader, prefetch, grouped trainer, evaluation, cache, training audit and Local intervention) show no change to algorithmic expressions or authority lifecycles. Codex's assertion of full 19-file non-import AST equivalence is *author evidence*, not an independently rerun AST comparison. Import initialization order may still require integrated validation.
3. The new Root changes five Python paths, along with exact Gitlink and append-only status/evidence/design records. Four code paths show formatting/import-only changes. In `tools/v3/remaining_optimizations_test.py`, `test_evaluation_manifest_requires_same_exact_identity` now uses `tmp_path / "evaluation"` instead of the repository `tmp_path` shared with conftest logs; it retains tests for same-identity resume, non-resume overwrite rejection, changed seed/horizon rejection, and separate legacy result rejection. Actual `scripts/v3_evaluation_identity.py::claim_evaluation_run` still refuses nonempty unbound output. No production fail-closed relaxation observed.
4. Author-side *committed* logs/JUnit were read, not accepted merely by assertion: Ruff 0.12.7 `check` PASS; `format --check` reports 28 formatted files; runner tests 8/8; migration list under real repository conftest **328 passed, 3 skipped**, zero failure/error, 113.81 s; launcher bash syntax 3/3. These logs predate the Root implementation commit but bind measured source files by SHA256 and are author checks **only**. The independent runner's pair/source immutability checks were NOT executed as a real DS Gate A.
5. The three explicit asset skips: `test_optional_real_data_debug_smoke` (real debug cache/source unavailable); `test_optional_strict_real_data_grouped_smoke` (strict cache/source unavailable); `test_optional_real_strict_snapshot10_preflight` (real cache/source/Edge/base/VAE unavailable). Those are open real-asset contracts, NOT passing real-data evidence.

**Current code-review finding:** no evidenced new implementation blocker in the scoped static/fixture change. Prior Ruff blocker is author-remediated in the new bytes, pending DS independent verification. The independent Gate A remains **OPEN**. Real data parity, same-job DCP including Local/optimizer/scheduler/RNG, GPU, workers0/2/4 numerical/RSS, two-Replan/48/128 simulator and strict 18-task Evidence remain **OPEN**; frozen config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` is not newly measured.

## Newly scoped H3-F operational authorization for the new Pair

The historical `?? scripts/plot_h3f_monitor.py` is explicitly permitted by the Child Phase5 guard but still rejected by the unchanged Root Gate runner allowlist. Prior disposition `2026-10-10_V3_gateA_h3f_untracked_file_scoped_disposition.md` referred only to the old pair; it is **not automatically inherited**.

**New Pair decision: (a), one-time permission with the same strict preservation safeguards**:
- DS_PRO first confirms exact new Root/Child/Gitlink and preflight porcelain; Child clean. If anything else disallowed is dirty, report BLOCKED; never conceal another file.
- If and only if `scripts/plot_h3f_monitor.py` is still the single historical untracked regular file, not a symlink, capture SHA256/mode/mtime/size and Root status and make/verify independent recovery copy outside worktree.
- With EXIT/INT/TERM restoration handler already installed, relocate *only* this file to a private external location (no overwrite). Verify original path absent and other status unchanged; run unchanged CPU runner with new external Evidence dir. Restore on all exits, recheck exact bytes/mode/mtime/untracked path and Root/Child/Gitlink. If unexpected destination collision or restoration failure, BLOCKED, preserve backup and all logs.
- Previous observed SHA256 `8b53ad9a01ee29d64420ff8995d1d40be57bdf99c45e96636913154715f732e0` is a historical witness only; DS must measure current file independently before moving. If identity differs, stop and request a new disposition.
- This permission does not authorize changes to tracked source, runner whitelist, tests, MM notes, DCP or unrelated files. No reset/clean/force, fresh worktree, installation, training or GPU.

## Read-only DS Gate A — exact next action

Use existing authorized validation worktree, safely pin **exact** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` / Child `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` (not moving V3 HEAD) while preserving all uncommitted notes, unrelated files and previous Evidence. If safe pin impossible, BLOCKED.

```bash
python tools/v3/run_migration_cpu_gate.py \
  --root-worktree "<EXACT_ROOT_WORKTREE>" \
  --expected-root 444c232b976e80ac68cde9e7370e73b9f6410f0e \
  --expected-child e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c \
  --evidence-dir "<NEW_EXTERNAL_EVIDENCE_DIR>"
```

Use existing Python + Ruff 0.12.7. Set writable HF_HOME/HF_DATASETS_CACHE/MPLCONFIGDIR/XDG_CACHE_HOME outside worktree as required; no disabling TLS, no package installation or config mutation. Capture exact commands, versions, `gate.json`, all generated Ruff/pytest/JUnit/bash logs, three skips and first failure without retry; plus historical-helper backup/restore SHA/mode/status witnesses. For this new Pair, Gate A PASS can be reported **only** when the unchanged runner independently reports PASS and post-run restoration, code immutability and formal pair checks are true. On any failure STOP and return Evidence. The existing Gate A review is not reopened for repeated technical evaluation on the same pair; new independent execution evidence should be considered as evidence-only closure.

No next-stage (Gate B-F), production, DCP, GPU, fresh or same-job Resume action is authorized by this verdict. Original job `formal_verified_index_30k` remains **STOPPED**. Never assume the latest complete checkpoint is iter800.
