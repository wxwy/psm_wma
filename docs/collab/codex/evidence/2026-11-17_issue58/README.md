# Issue58 author evidence (CPU only)

Current product gate is **revision1/gate.json**: 487 PASS /13 inherited
dependency SKIP /0 failure/error, 500 collected. 478 previous test identities
retained, 22 new all execute. 222 product/test/config source hashes stable;
protected B1 encoding/recipe/core, build/verify CLIs and Child unchanged.
No real F27/Wan/GPU/private server/full production/old deletion/train/merge.

`commands.sh` records exact environment, separate JUnit/raw logs, selected
static/format/bash/help checks, 478-ID comparison, synthetic supervisor output
and completed tombstone, and SQLite stress. Override existing ISSUE58_PYTHON
and use a fresh ISSUE58_OUT; never overwrite previous evidence. The stress is
explicitly simulated ACK rows:101101 over1001 jobs, max_records128,
peak active101/1, final DB1159168 bytes. This is not render/VAE performance.

`development/` contains overlapping focused runs, not extra test counts:
old47 pass; first new8fail/12pass from missing config whitelist; corrected
supervisor10pass; protocol11pass before the final late-producer case. `final/`
is the first whole-suite attempt:283pass, then139pass/10skip/1fail because an
old negative test expected the literal words 'ledger budget'. The compatible
error phrase was restored; its test was not weakened/deleted.

Revision1 full invocation:

```bash
ISSUE58_PYTHON=/workspace/.venvs/g2-view-vae-52/bin/python \
ISSUE58_OUT=docs/collab/codex/evidence/2026-11-17_issue58/revision1 \
bash docs/collab/codex/evidence/2026-11-17_issue58/commands.sh
```

All four pytest groups and static checks passed, then the evidence collector
failed because pytest's `current` symlink duplicated the same test result
directory. Only cpu_audit.py was corrected to ignore that directory alias;
no product/test source changed. Original observed collector exception was
AssertionError at `assert len(run)==1`, not a candidate runtime failure.
Collector was rerun alone with the same preserved JUnit/temp inputs:

```bash
ISSUE58_AUDIT_OUT=docs/collab/codex/evidence/2026-11-17_issue58/revision1 \
ISSUE58_TEST_TEMP=/tmp/issue58-cpu-7SxozlHn \
/workspace/.venvs/g2-view-vae-52/bin/python \
docs/collab/codex/evidence/2026-11-17_issue58/cpu_audit.py after
```

It returned0, verified stable222 source hashes and all478 IDs, and generated
gate/synthetic summaries. Temp input paths in receipts are CPU fixtures only;
replay creates a new tmp root. Raw pytest traces are preserved verbatim,
including whitespace; they are excluded from source whitespace lint.

Original three A1 reviewer probes remain byte-identical at SHA256
860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0.
They were NOT_RUN locally without native PyArrow; no install/stub/new env.
Prior GPT478+3 approval is retained, not attributed to this author run.
Fixed commit/source scope and later local read-only peer receipt are separate
publication facts. Only GPT can close the real-sample/resource/full-start gate.
