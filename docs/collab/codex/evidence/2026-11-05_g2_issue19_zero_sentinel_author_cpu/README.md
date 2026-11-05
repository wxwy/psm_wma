# Issue19 — author CPU evidence

Formal implementation Root: `fbe578908a840a5f4e5b351f1c2e8fb019def6e5`.
Child/Gitlink: `1069fe78841228cadbbfbe6afbd767eaed6225da` (unchanged).
PR #20 head branch: `v3-g2-codex-depth-zero-sentinel-20261105`.
PR base: `v3-g2-spatial-policy-20261104`, `9568723fd19d008be180c7b3e4126e1176c07d26`.

`final/gate.json`: PASS, **174 tests, zero failure/error/skip**. Breakdown:
53 Issue19 focused tests + 83 exporter/source/recovery/geometry regressions +
38 spatial/photometric policy regressions. Pytest reported 5.26 seconds; this is
synthetic test duration, not a production throughput measurement.

Ruff 0.12.7 check and format check, AST parsing of all 12 G2 Python files and
diff-whitespace checks passed. Before/after Git snapshots are clean at the exact
Formal Pair; all bound source hashes are unchanged. Source bindings include Git
Blob and SHA256; the full implementation diff is included.

Raw argv/cwd are in `final/commands.json`; effective allowlisted environment and
versions are in `final/runtime.json`. `run_author_cpu.py` is the unchanged runner
executed outside the checkout. Reproduction requires a clean isolated worktree
at the formal implementation SHA and equivalent installed CPU dependencies;
paths are the actual author paths, not a claim that these paths exist elsewhere.
The runner's output directory must not already exist. No dependency was fetched
by these tests. No project-wide conftest, model or source recording was loaded.

`development/dev1` preserves 173 PASS/1 FAIL before the old dry-run capacity
expectation was updated from 3 to 2 bytes/pixel. `development/dev2` preserves
174 PASS after that correction. These dirty-development runs do not replace
the clean final run or establish an old-production RED Gate. No old test was
skipped, deleted or xfailed; format-specific expectations alone changed.

The 736/73/74 fixture is synthetic (25/230 far-floor pixels); actual recorded
CloseFridge global736/local234, the seven real legacy episodes, native
RoboCasa/EGL and production resume were **not executed**. No server file was
accessed or transferred. The historical 24 software-rendering tests were not
repeated: renderer code is unchanged; the 38 spatial-policy tests were rerun.

This directory contains text evidence only. It excludes temporary NPZ/parquet,
images, caches and source recordings. `SHA256SUMS` covers all other files in this
evidence directory, including development logs and this explanation.
