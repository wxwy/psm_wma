# G2 Issue #19 / Draft PR #20 — implementation submitted for review

This is an author handoff, not an independent approval or production Gate.

| Identity | Exact value |
| --- | --- |
| Formal implementation Root | `fbe578908a840a5f4e5b351f1c2e8fb019def6e5` |
| Child / Gitlink | `1069fe78841228cadbbfbe6afbd767eaed6225da` (unchanged) |
| Isolated PR head | `v3-g2-codex-depth-zero-sentinel-20261105` |
| PR base | `v3-g2-spatial-policy-20261104` at `9568723fd19d008be180c7b3e4126e1176c07d26` |
| Initial PR head | `e531af5c1825f7af0bc94ac2010bae2a04ad11ec` |
| Owner contract | Issue #19 and Owner decision at `9568723f` |

## Implemented behavior

- Schema v2 NPZ contains exactly depth/K/GL-CV pose/frame indices. No persisted
  `valid`; readers derive transient validity from positive depth.
- Renderer-invalid and finite uint16 out-of-range Z become 0. In-range values
  retain nearest-mm rounding and <=0.0005001 m error. Values of 591–614 m never
  saturate or wrap into a false near surface. Camera near/far and replay code
  are unchanged; malformed renderer-valid nonfinite data still fails closed.
- Frame/camera source classifications are separate from storage validity.
  JSONL records disjoint invalid/below/above/encoded counts and explicit range
  diagnostics; episode manifest and replay verify them. Float32 retains its
  own positive representability contract, including far depths.
- Root/episode schema mismatch and extra/missing arrays fail closed. The CLI
  refuses unidentified nonempty cache contents; CLI/direct writer refuse a v1
  root before creating locks or new output. Existing completed evidence is never
  automatically relabeled or adopted.
- Spatial verification uses the fresh representability mask and source counts;
  ray/K/Pose/projection requirements and external-human/nonblocking-RGB policy
  stay unchanged. All-zero depth cannot pass spatial validation.

Production edits are limited to five files: exporter, verifier, geometry, cache
and the schema constant module, with current documentation updated alongside.
The precise diff is authoritative. `replay.py`, source mapper, Child, nav_sg,
training, configuration, historical evidence and V3 are unchanged. Current tests
were extended and codec/accounting expectations updated without loosening other
assertions.

## CPU validation

[Raw evidence](../evidence/2026-11-05_g2_issue19_zero_sentinel_author_cpu/README.md)
contains exact argv/environment, source Git Blobs/SHA256, full diff, raw JUnit,
pytest/Ruff/AST logs and clean before/after snapshots. Final result: **174 PASS,
0 failure/error/skip**, with 53 new focused tests, 83 original exporter/source
regressions and 38 spatial-policy regressions. Ruff 0.12.7 check/format and AST
pass. The author executed these on cloud CPU; DS/GPT independent execution is
not claimed.

Development dev1's sole failure was the old dry-run estimate retaining the
removed bool byte; dev2 and clean final are green. Both raw development records
are preserved. No real source scene was accessed. The native tiny analytic
MuJoCo CPU ray test is part of existing regressions, not real RoboCasa replay.

## Seven-episode and native follow-up boundary

[Transition proposal](../../../build/PSM-WMA_G2_Depth_ZeroSentinel_v2_and_SevenEpisode_Transition_2026-11-05.md)
requires a full legacy inventory, pixelwise `valid == depth > 0`, verified strict
producer provenance, staged conversion, complete hash/array checks, coherent v2
identity and atomic promotion with retained rollback generation. No converter,
production root switch or new namespace is executed by this PR. The original
seven episodes and `.failed`/`.staging` remain untouched on the server.

The global736 frame73/74 test uses synthetic data matching reported far counts;
real local234/230-frame acceptance remains pending server authorization and
resources. No server files leave the server. Current runtime exposes no remote
server command tool; available cloud Git/CPU capability was used directly rather
than waiting for the separate GitHub bot's environment binding.

Request GPT/Owner fresh Code Gate for the exact Formal Pair and transition
proposal. Stop after publishing this isolated draft. Separate authorization is
required for native replay, actual legacy migration, Batch000 resume or V3 merge.
