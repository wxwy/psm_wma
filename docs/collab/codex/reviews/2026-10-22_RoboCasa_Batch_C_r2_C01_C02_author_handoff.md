# RoboCasa Batch C r2 — C01/C02 author handoff

Date: 2026-10-22 (Asia/Shanghai). Status: REVIEW / author CPU only.

## Formal implementation

- New Root implementation: `a4b22b929175e462b6a8db57ad2abee7e220dd37`.
- Child/Gitlink: **`c9f21040f462a114d597fc83773cb9b6a9e96214`**, unchanged. Both fixes are Root-only; no artificial Child commit was made.
- Vendor: **`1ac174585293ed998ffc9cf73e47439798cf6f6c`**, unchanged.
- Development baseline: latest V3 `c2d8359f918e6880a2c67847b817884a726fe4f9`; reviewed production Root `a2f3a6a367395b2f2a6006cfc4e7c9effa606713`.
- Candidate branch: `v3-robocasa-manual-c-r2-20261022`; submitted to V3 non-force. Later evidence/Inbox commits do not replace the implementation Root above.

Authority: GPT exact-pair `REQUEST_CHANGES` review `docs/collab/chatgpt/reviews/2026-10-22_V3_RoboCasa_BatchC_a2f3a6a3_c9f21040_independent_incremental_review.md` and narrow request `docs/collab/chatgpt/requests/2026-10-22_Codex_V3_RoboCasa_BatchC_r2_evidence_integrity_minimal_remediation.md`. Scope is exactly HIGH-C01 and MEDIUM-C02, adjacent test fixtures and runbook clarification. G1, training, DCP/RNG/optimizer, Local-TTT math and Vendor were not edited or accessed.

## HIGH-C01

`validate_attempt()` now requires both missing classes of evidence before initial COMPLETE publication **and again before a resumed skip**:

- `episode_progress.jsonl`: exactly2N newline-terminated JSON records, each ≤4KiB, exact schema, run digest, `Task/Attempt` identity, typed integer Episode index and ordered start/end pairs0…N−1. Missing/empty/truncated/duplicate/jumped/foreign/extra records, ambiguous duplicate keys and malformed/nonfinite JSON reject validation.
- Each `rolloutXX_cleanup.json`: typed object containing all five required witness fields, `reset_ok is True`, explicitly null rollout/media/cleanup errors and a valid session ID matching the actual required-slot0 Client shape `<32lowerhex>:0:<32lowerhex>`. This is checked against the unchanged `RoboCasaLocalMemoryClient.begin()`/`end()` implementation, not guessed from a UUID-only format. Missing fields, None/string"None", invalid session types/format or failed reset reject completion even after process-group cleanup.
- Online `EpisodeProgress` accepts an expected Attempt ID; the formal Queue **always** supplies it and every event must match. Older process-only callers may omit it, preserving Batch A compatibility without weakening the formal path.

The Child already emits the correct progress and Local cleanup witnesses, so it needs no change. Its event/write ordering is preserved: Episode end follows result/media/Local cleanup, and Queue publishes process cleanup before committing COMPLETE. Existing runtime, action, prediction, media decoding, task deadline and owned-process cleanup checks remain enabled. Synthetic success fixtures now produce both real-shaped witness classes instead of succeeding through their omission.

## MEDIUM-C02

A shared actual-file classifier is used by normal task results and failed/partial fallback rows:

- `rollout_mp4s` contains only exact `rollout<digits>.mp4` environment recordings.
- `generated_mp4s` contains only first/per-replan generated filenames. Both lists are independently aggregated into `screening_summary.json`.
- A disabled environment recording with generated first/all leaves environment lists empty in task rows **and** the overall summary. Failed partial attempts retain existing generated/environment paths under their correct category. Unknown `rollout*_other.mp4` files do not masquerade as either category.

No CLI/config defaults, identity exceptions, media requirements, simulation protocol or session lifecycle policy changed. As with other source changes, strict evaluation identity includes the new Root SHA: old cross-source runs are not imported as same-identity resume. This does not change the separately scoped G1 Owner Override.

## Baseline red and final green

Evidence: `docs/collab/codex/evidence/2026-10-22_RoboCasa_Batch_C_r2_evidence_integrity_author_cpu/`.

Baseline was captured **before** each corresponding production fix:

| Baseline probe | Observed old behavior |
| --- | --- |
| Direct missing-witness probe | Old validator publishes COMPLETE and resumes/skips with progress and per-Episode Local cleanup both absent (`baseline_missing_witness_accepted.json`). |
|68 new finish/resume negative cases |68 expected RED failures because corrupt/missing evidence was accepted (`baseline_attempt_red.*`). |
| Online identity | Direct probe confirms old monitor accepts foreign Attempt progress (`baseline_unbound_probe.json`);5 new expected-binding/API tests fail on the old unsupported constructor (`baseline_online_red.*`). |
| Media classification |3 expected RED assertions, including2 first/all subtest failures, demonstrate generated/unrelated files listed as environment MP4 (`baseline_media_red.*`). The accompanying framework pass is not a formal result. |

| Final suite | Result | Raw evidence |
| --- | --- | --- |
| Attempt125 + Config70 + Process23 + Numba3 | **221 passed**,0fail/error/skip | `helpers.log/xml` |
| Unchanged Child media/runtime/lifecycle/contract/Phase6/client/decoder | **58 passed**,0fail/error/skip | `child.log/xml` |
| Queue,46 synthetic subprocess scenarios | **35 passed +72 subtests passed**,0fail/error/skip | `queue.log/xml` |
| Existing identity/episode/media/screening regressions | **20 passed**,50deselected | `regressions.log/xml` |
| Ruff0.12.7 check/format,12 Python AST, bash syntax, source diff | PASS | `ruff_*.log`, `source_checks.json` |

Total **334 top-level cases +72 passed subtests**; JUnit declares406 across the four suites (Queue107 =35 testcase elements +72 subtest events). These are focused suites, not all-repository tests. Baseline and intermediate runs are never added to this total.

Final green evidence includes actual Queue `--resume` after completed-task progress removal, wrong Attempt and failed Local reset: each exits nonzero before starting additional synthetic Server/Simulator processes, and the damaged original files remain byte-identical. Online foreign Attempt progress rejects execution. Generated-only first/all scenarios verify20 generated MP4s and zero environment MP4s in rows and summary; the failed partial path retains generated fragments. Existing safety assertions remain in place.

Tests use real temporary Git/PIDs/socket/process groups, actual tiny MP4/PNG encoding/decoding and real Numba cache behavior, with policy/simulator/import boundaries doubled. They are author CPU results, not independent DS_PRO or real installed-runtime/physics evidence. Full-suite raw XML/logs, exact commands, static source hashes, checksums and source diff are provided. Internal author-team source review is supporting evidence only; it is not GPT's verdict.

## Independent review and stop

Request GPT fresh incremental review of the new formal Root / unchanged Child / unchanged Vendor, only C01/C02 and adjacent source. Then DS_PRO runs the approved focused CPU contract from a clean detached exact pair using new external evidence, without source edits. Reproduction commands and CPU environments are recorded in `commands.json`; Ruff0.12.7 uses `cosmos-framework/.ruff.toml`. Missing CPU dependencies are failures/BLOCKED, never skips.

No GPU, real Action Server/model, Kitchen creation/reset/step, real DCP or training operation occurred. The running G1 worktree and frozen assets are untouched. Real dependency import/physical-environment/benchmark gates remain open; Owner alone authorizes and manually starts real simulation after combined acceptance. Codex stops after remote readback and canonical Inbox review handoff.
