# Issue63 author CPU evidence

This directory contains only synthetic local fixtures, source identities and
author/peer CPU checks. It does not contain server assets or independent GPT
approval. No GPU, real Wan/F27, private dataset, full production, old-data
deletion, dependency installation, training or merge was run here.

Base: PR62 `d0bb45343a047fdf90d8e376acf4502fdf13fff4` (approved production
source `5e6a2ceb702acd724076692f42ca4fc60380192b`). Unchanged Child/Gitlink:
`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`; nav:
`70eb7b447e65d793b0ebe18b258291ce46f057c1`. The fixed implementation SHA
is recorded by `source_commit_bind.py`, the PR and canonical Inbox, rather
than inferred from a later documentation-only HEAD.

**Final corrected implementation:** `a169fea07016b80b3639646cc9925ac70b6525a8`.
[DraftPR64](https://github.com/wxwy/psm_wma/pull/64), stacked on unchanged PR62.
`revision2/implementation_scope.json` binds all235 tested files to that exact
Git commit. `peer_closure/REPORT.md` records same-pair LOCAL_CODE_REVIEW_PASS,
original5 probes independently PASS; P2-63-PEER-1 closed. Both were added in a
following evidence-only bookkeeping commit, which is not the formal Root.
Original rejected98172110 evidence remains unchanged. GPT/server/capacity
acceptance is still pending, not implied by local peer closure.

## Reproduce

Use an **existing** interpreter. No install/new environment is part of this
command; missing native dependencies remain explicit skips. Every replay
requires a fresh output path outside tracked historical evidence.

```bash
cd /absolute/clean/checkout/of/fixed/issue63/sha
ISSUE63_PYTHON=/absolute/existing/python \
ISSUE63_OUT=/absolute/fresh/private/evidence \
bash docs/collab/codex/evidence/2026-11-17_issue63/commands.sh
```

The script fixes CPU-only/no-user-site/PYTHONPATH environment, executes all
five test groups, writes raw logs/JUnit, runs Ruff checks, inert CLI help,
the synthetic before/after protocol and a source/identity audit. Any failure
stops the command. `gate.json` distinguishes skips and NOT_RUN from PASS.

## Current and historical runs

- `revision2/` is the corrected author gate after P2-63-PEER-1: shared lazy
  verification binds receipt proof/cleanup fingerprints and both retired-file
  hashes to the immutable capsule, plus archive/disposition consistency.
  **542 PASS /13 inherited dependency skips /0failures/errors; original501
  identities retained plus54 new cases,235 stable sources.** Ruff22files,
  CLI helps/protocol/source audit PASS. The final results are in its `gate.json`;
  the final fixed-source binding is
  recorded after committing the correction. No PT/product/recipe was changed.
- `peer/REPORT.md` records the initial fixed98172110 LOCAL_REQUEST_CHANGES,
  exactly one P2. Unchanged independent probe SHA256
  `cbc86a7b29e529fd5ace678fe5a10a78303aaefe25d71e470c23df2959883a1f`
  produced2 PASS /3 RED. `peer_replay/green.log/xml` replays that original file
  unchanged:5 PASS after correction. These overlap and are counted separately.
  `fixed_source_binding.json` binds only the initial rejected98172110; it is
  historical and does not identify the final corrected review target.
- `revision1/` is the preceding author gate after adding persistent SQL/capsule
  binding checks at the post-journal boundary and refusing retirement when
  renderer work was explicitly kept. **536 PASS /13 inherited dependency skips,
  zero failures/errors;501 original identities plus48 new cases.235 tested
  source hashes stable; Ruff22files, CLI helps and protocol checks PASS.**
  The test results are in its `gate.json`;
  the fixed commit binding is generated only after the implementation commit.
- `final/` is the preceding successful gate: 533 PASS, 13 inherited dependency
  skips, zero failures/errors, 501 old identities plus45 new tests; all235
  source hashes stable. It predates those final narrow safety checks and is
  retained as historical evidence, not the final target.
- `development/issue63_first.*`: initial capsule3 PASS.
- `development/issue63_existing.*`: 349 PASS /4 FAIL. A changed generic source
  loader incorrectly required episode_manifest in SQL-only legacy fixtures;
  the v1 late-message path was restored to its original direct full-source
  access. No old assertion or source test was altered to remove the failures.
- `development/issue63_faults.*`:43 PASS, overlapping prior/final suites,
  including22 hard exits and the original101101-event/1001-job SQL stress.
- `development/issue63_entries.*`:11 PASS, overlapping prior/final suites,
  including actual supervisor stop/consumer exit/resume, atomic temp-fsync
  exits, selected-only reads, optional archive and capacity HOLD behavior.

Development, protocol and peer tests overlap the final gate: do **not** sum
them into a larger unique test total. Raw failure logs/JUnit are preserved
verbatim, including traceback whitespace. Prior GPT evidence is untouched.

## What the gate proves

- Original501 testcase identities retained; all old test source files are
  byte-for-byte unchanged against the base. Original #53 suite remains283.
- Numeric `encode_record` AST, encoding.py, contract.py, old build/verify CLI,
  original producer/renderer/task/language/spatial logic and Child unchanged.
- Capsule/profile/cache v2 strictly dispatched; old v1 still requires its
  full source. All product/PT bytes match before/after synthetic retirement.
- Reader source leases, stale index refusal, JSON-only opening, selected3
  numeric files only; no hidden rendering/encoding on a training read.
- Pending/partial work retained, concurrent reader/writer isolation, hash/
  scope rejection, journal/SQL intent integrity, hard process exits, original
  supervisor pre-plan recovery, idempotent completed ledger and late events.
- Optional archive tested losslessly on the existing distinct `/dev/shm`
  filesystem; no new mount/environment. Default leaves no full audit copy.
- Capacity counts remain observational; incomplete task strata return HOLD
  even when the conditional estimate fits an arbitrary test budget.

`synthetic_protocol.json` provides per-file logical/allocated bytes, retained
product/PT SHAs and a FakeEncoder exact0 check. Its deliberately enlarged
audit is **synthetic**, not a measured real F27 size or performance result.

## Still required independently

GPT must validate fixed-code Blender000000/Fridge000502 on the existing
server environment:81 states,12 Views,169 B1 owners exact0,419 pixel pairs,
all PT byte identities, actual v2 source/episode sizes, finalization overhead,
v1/v2 reader latency and stop/crash recovery. Then18-task stratified capacity
and32-worker resource/A-B gates are required. Neither author CPU checks nor
two samples authorize full9126 production, old-view deletion or training.

See `docs/build/PSM-WMA_G2_source_capsule_issue63_2026-11-17.md` for the
field dependency audit, hash graph, exact operator recovery/verification/
capacity commands and stop conditions.
