# G2-I19-F1 — direct-writer root preflight remediation

State: REVIEW, fresh incremental Code Gate requested; no author self-approval.

| Identity | Value |
| --- | --- |
| New Formal implementation Root | `5e6903b9dd09828f725dc61dcd6e98012fae87b3` |
| Child/Gitlink | `1069fe78841228cadbbfbe6afbd767eaed6225da` (unchanged) |
| Prior implementation | `fbe578908a840a5f4e5b351f1c2e8fb019def6e5` |
| Independent finding | `99ad0de0249a660d46642c3ae849129733b3c503`, G2-I19-F1 |
| PR head branch | `v3-g2-codex-depth-zero-sentinel-20261105` |
| PR base branch | `v3-g2-spatial-policy-20261104` (review99ad0de0 retained) |

## Behavior and scope

When `cache_manifest.json` was missing, direct `export_episode()` could write v2
beside unverified/v1 task data or pending staging/failure artifacts. Both the CLI
manifest publisher and direct writer now use one preflight that rejects this
state before creating a root manifest, lock, staging directory or output file.

Only an absent/new empty direct-library root gets a v2 schema marker through the
existing atomic, fsynced manifest publisher. Subsequent library skip/retry sees
that explicit version. No existing data is automatically adopted or upgraded.
The CLI keeps its full immutable configuration contract and configuration-drift
check. The minimal library schema marker does not silently become a full CLI
configuration contract.

Production delta is **cache.py only**. One new CPU test module covers five refusal
shapes and absent/existing-empty fresh roots. One existing incomplete-target
fixture first declares its valid v2 root so it still tests missing episode
completion; its original exception and preservation assertions are unchanged.
No old test is removed/skipped/xfail or relaxed.

The encoder, renderer/replay, source mapper, geometry thresholds, exporter CLI,
verifier, schema/version constants, nav_sg, training and Child are unchanged.
Original reports/evidence are preserved, including the independent review merged
as a documentation-only parent; no production change was pulled from V3.

## Author CPU evidence

[Raw evidence](../evidence/2026-11-05_g2_issue19_f1_direct_writer_author_cpu/README.md):

- Frozen old-production negative run: **5 expected failures**, 0 error/skip.
  Both the old cache module and new test hash were frozen before execution and
  checked unchanged afterward. Tests failed because old code accepted export.
- Clean new Formal Pair: **181 passed**, 0 failure/error/skip; original174 plus
  new7. Ruff0.12.7/check/format and AST13 PASS. Source bindings, runtime/env,
  exact commands, incremental diff and clean before/after Git snapshots included.
- The new test hash is unchanged RED→GREEN. AST comparison confirms every assert
  in the83-case existing exporter module is unchanged. Old20 evidence artifact
  hashes remain valid.

This is author CPU evidence, not another DS/GPT execution. The 5.65-second suite
time is not a production performance claim. Fresh Code Gate remains the reviewer
decision for this precise new pair.

## Accepted independent evidence and next boundary

The formal report at99ad0de0 already accepts the prior174 independent CPU tests,
real CloseFridge global736/local234 frame73/74 depth exports, zero sentinel,
five-array storage, K/Pose and4/4 geometry groups, plus7/7 old caches and pixelwise
mask equality for308412416 pixels. Preserve these as reviewer-owned native/read-
only evidence on fbe57890; they were not repeated or transferred to the cloud.

Only G2-I19-F1 needs incremental re-review. No old depth/geometry finding is
reopened. The7 actual v1 episodes remain unconverted and all failure/staging data
are untouched. A runnable, separately approved transition/promotion remains
necessary before production resume. This candidate does not perform it.

Deliver via existing Draft PR20 and canonical Inbox, then stop for GPT/Owner.
No V3 merge, server/GPU/RoboCasa execution, source-data transfer, training or
production export/resume is authorized by this handoff.
