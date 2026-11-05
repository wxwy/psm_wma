# Issue18 author targeted CPU evidence — 2026-11-05

Formal Root `f4871059cf28a7e2142325738decbf1d53c3148b`; Child/Gitlink `b3098008375c275a36dd2f50cbaf757bedf493ea`.

- `final_summary.json`: bound results, stage identities, long-run and Inductor counts, explicit unrun gates.
- `formal-targeted/`: original 77-case JUnit, logs, command/environment, long-sequence witnesses, Inductor witnesses. Eight GPU/L1 cases are deselected, not reported as passed/skipped.
- `old-red/`: same new test bytes against unchanged baseline production; four expected compile-limit failures. The old tree includes an untracked new test.
- `new-green/`: development pass, counted separately from the final clean-Pair run.
- `old-eager/`, `new-eager/`, `formal-eager/`: 96 generated-reference comparisons and original output. Record mode alone is not a parity check; final verify mode is.
- `formal-static/`: exact Child delta, AST scope verification, Ruff/format logs.
- `environment.json`: CPU runtime versions. `author_peer_review.json`: author-side read-only inspection, not external acceptance.
- `cpu_evidence.tar.gz`: original recorder outputs including before/after source fingerprints, generated tiny tensor reference and collector/test-support scripts. Caches, bytecode and symlinks are excluded. No real server/DCP/results files are included.

Reproduce against clean frozen Pair using `run_cpu.py` from the archive and a fresh external evidence output directory. `formal-targeted/command.json` contains the exact pytest command, six input files and CPU environment. The recorder refuses an existing output directory. `capture_numerics.py` record mode uses baseline 4e9; verify mode compares the new model with that generated reference. `finalize_evidence.py` verifies the clean Pair before creating output; run only in a clean disposable checkout without an existing evidence output.

Existing runtime Python3.12.14 / Torch2.10.0+cpu. `--noconftest -c /dev/null` avoids unrelated global/GPU conftest dependencies. Tests import actual production classes and installer; the test compiler chooser counts/selects CPU backends with original options. No model method is replaced in recorder execution. Preserve cap8. GPU/FSDP/full Local-TTT performance acceptance remains pending.
