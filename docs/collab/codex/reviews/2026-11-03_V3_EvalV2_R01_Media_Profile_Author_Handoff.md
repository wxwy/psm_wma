# R01-MEDIA-PROFILE-01 — minimal Root fix, incremental review request

| Identity | Exact value |
| --- | --- |
| New Formal Root | `2d1ad80f89ab4cc0e275ff4341f064954870abdd` |
| Unchanged Child / Gitlink | `c93f2abf4fb27d36176ff8db094379a853cec796` |
| New isolated Root branch | `v3-eval-v2-media-profile-20261103` |
| Root review/request base | `b19b9edf7f39a83013a853f95c543081e0216b28` |
| Prior Code/CPU approved Root | `e7ce99d7a0bbb7a81ea7afcee7253548687dc223` |
| New author CPU | **42 distinct PASS, 0 failure/error/skip** |
| Old frozen targeted RED | **2 expected failures** |

Only Root `scripts/robocasa_eval_v2/generated_media.py:34` changes production
semantics: compare Manifest `execution.profile` with **phase_b_native_batch_v1**,
the actual output of production `config.execution()` and frozen Child contract,
instead of CLI value phase_b. Format2 insertions/1 deletion, one string constant;
AST equality after substituting exactly this literal is verified. No Child
branch/commit/code/Gitlink change, no other Root production edits or refactor.

The same strict identity/count/ACK bool checks still run, followed by exact MP4
inventory, Episode/Attempt receipt identity and file hash validation. No status
forcing, count inference from filenames alone or Core/SR changes. Encoder, spool,
ACK history, Local/model/action/scheduler/GPU policy/config/training are unchanged.

## Regression and evidence

New `tools/v3/eval_v2_replan_tests/media_profile_test.py` is frozen BEFORE RED.
It constructs a real production native Manifest using `execution()` and Child
`build_manifest`/`validate_manifest`, a valid Store with committed synthetic
32-step Core and2 Replans, fresh CPU-generated MP4/receipts and completion input.
It does not substitute a CLI profile string into the Manifest by hand.

- Old e7ce production source byte-check: native true-ACK positive wrongly fails;
  native false-ACK negative wrongly passes. Both are raw pytest RED, same frozen
  test bytes retained for GREEN.
- New clean exact Pair: **15 new profile tests +10 existing report +17 config =42**
  distinct PASS, Python3.13.5, no skip. Not a rerun of379/122 or independent DS.
- Phase B true, Phase A/absent false pass. Phase B false/None/1/string and Phase A/
  absent true refuse. Existing Child contract still rejects CLI/unknown profiles.
- Positive spies delegate to REAL receipt/file-hash functions and assert both
  video indexes are checked on each repeated publish; no helper bypass. Missing
  MP4/receipt, bad receipt SHA and same-size changed video remain incomplete.
  Core `summary.json`, `result.json`, Manifest bytes and SR authority stay unchanged.
- Ruff0.12.7 check/format, AST/py_compile2, exact production literal-only AST diff,
  source bindings and unchanged Child/config/Vendor/old379/122 evidence pass.

Raw commands/env/versions, RED/GREEN JUnit/stdout/frozen test, source diffs/bindings
and synthetic Phase B manifest/summaries are in
`docs/collab/codex/evidence/2026-11-03_eval_v2_media_profile_author_cpu/`.
SHA256SUMS binds25 artifacts. Synthetic counts are2, not the real19; no old Canary
media/log/result access occurred. Author PASS does not close a hardware Gate.

## Original R01 failure and offline reconciliation

Source request:
`docs/collab/chatgpt/requests/2026-11-03_V3_EvalV2_R01_Media_Summary_Profile_Codex_Narrow_Fix.md`.
The prior source APPROVE_CODE/DS CPU122 stand for their old scoped Pair; the new
hardware report remains **FAIL / REQUEST_CHANGES**, including original exit1.
No historical files or review verdicts are overwritten. Current author tests
prove the corrected profile path, not actual R01 inventory integrity.

**offline_reconciliation: PENDING_DS_ISOLATED_COPY_RECONCILIATION**.
The cloud code workspace has not accessed target R01 outputs. After fresh Code
Gate, DS should recompute with new `publish` against an independent copy while
preserving original Manifest/Core/receipts/videos and original failure evidence.
The new function must reach all19 inventory/receipt/identity/hash checks. If any
remain invalid, record actual offending source/path and retain non-success; do
not manually turn status COMPLETE or assume this literal fix proves all19.
Any new GPU Run still requires separate Owner authorization. No DS dispatch here.

Request GPT **APPROVE_CODE / REQUEST_CHANGES / BLOCKED** on this new Root with
unchanged Child, only the profile correction and related tests. Later evidence/
publication commits are bookkeeping, not another Formal implementation. Publish
candidate, fresh-readback refs/Gitlink/artifacts/source, then STOP. No V3 merge,
GPU/model/RoboCasa/900EP/training/DCP/Job or old out2/No-TTT/H2/H3 operations.
