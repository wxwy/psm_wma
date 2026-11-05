# G2 Issue #19 F1 — Incremental Code Gate APPROVE_CODE

Date: 2026-11-05 (Asia/Shanghai). Independent reviewer: GPT, connected authorized server + GitHub. **Decision: APPROVE_CODE for exact formal implementation Root `5e6903b9dd09828f725dc61dcd6e98012fae87b3` and Child/Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`.** This is a **code** decision, not approval to migrate seven old caches, merge V3, or restart Depth generation.

## Prior accepted results and exact delta

- Previous verified implementation: Root `fbe578908a840a5f4e5b351f1c2e8fb019def6e5` / same Child. Prior independent review: `docs/collab/chatgpt/reviews/2026-11-05_G2_Issue19_CodeGate_independent_CPU_native_PASS_direct_writer_v1_mixing_REQUEST_CHANGES.md`.
- Prior accepted facts: 174 independent CPU tests PASS, real RoboCasa CloseFridge global736/local234 f73/f74, GPU4 EGL, uint16 zero sentinel 25/230 far wrist pixels, v2 five-array NPZ, independent ray geometry 4/4 PASS and native replay `SPATIAL_REPLAY_CHECKS_PASS`. The prior readonly check established 7/7 legacy v1 caches, 2353 frames and 308412416 pixelwise `legacy_valid == (legacy_depth > 0)`, all without changing actual cache.
- GitHub exact implementation incremental diff vs `fbe57890`: production code changed **only** `tools/g2/rgbd_pose/cache.py`; new `tools/g2/test_cache_root_preflight.py`; one setup statement added to a preserved original assertion in `tools/g2/test_rgbd_pose_export.py`. Other additions are review/author-evidence/docs. Encoder, renderer, near/far, policy and thresholds, v2 five-array format, caller/CLI and Child unchanged. No need to rerun native render to re-approve an unchanged renderer/codec path.

## F1 closeout / source inspection

Old code `export_episode()` consulted `_check_root_schema` but accepted a manifest-less root with `tasks/`, `.staging/` or `.failed/` and wrote a v2 episode in it. The fix makes `_check_root_schema(root)` shared across both `ensure_cache_manifest()` and direct `export_episode()`: it refuses unversioned nonempty roots **before** any manifest/lock/staging/episode writes; if truly fresh, the direct writer atomically publishes a minimal v2 schema marker using existing manifest logic. CLI still uses its full immutable configuration and config-drift checks; version bootstrap does not adopt legacy data.

Seven new parameterized cases in `test_cache_root_preflight.py`: 5 categories of unversioned root rejection and preservation (legacy episode, unversioned v2 episode, unknown episode, `.staging`, `.failed`) plus 2 fresh-root/bootstrap/verified-skip cases (nonexistent root vs already empty directory). Old export test for incomplete target now explicitly declares a valid v2 root before constructing the incomplete episode; no old assertion removed.

## Independent connected-server checks

Reviewer fetched **exact commit** into a clean isolated checkout `/tmp/g2_issue19_f1_independent_5e6903_20261105`, with Gitlink exactly unchanged. No existing G2 production checkout edited.

1. **Independent GREEN:** 181/181 CPU pytest PASS (0 failed/error/skipped) using server RoboCasa simulator Python, `--noconftest -c /dev/null -p no:cacheprovider`, all four test modules including the new preflight module. JUnit artifact SHA256 `d546490a1ddf316765472b8d223c176e1f0171e53937a119f98513b4794348e5`. Log SHA256 `9f410654f041a6ba1194dbe3a4f33e36d97a85beb1bca99a36b399aff660852e`. Server-only evidence dir `/tmp/g2_issue19_f1_independent_evidence_20261105`; time ~6.67s.
2. **Independent RED reproduction:** executed new five rejection cases against unmodified `fbe57890` code with `--import-mode=importlib` and explicit legacy code PYTHONPATH. Exactly 5 expected failures, 0 error/skip (2 unrelated fresh-root cases deselected). Verified as genuine missing exception failures. Red JUnit SHA256 `459380f6f2dd4b4e31b04cc91b373163680ea3f47cc9a1fa7ebc6d420ca0cdd5`. Red log SHA256 `cae3a50c8b07f313c4680efcc4d3d7ae7c3f67a412dec1bbd093e27d1d8fffb9`.
3. **Independent lint and diff:** Ruff 0.12.7 `check tools/g2` PASS, `format --check tools/g2` PASS (13 files), Python AST for 13 G2 modules PASS. `git diff --check` scoped to `tools/g2` between old and new implementation PASS; exact implementation commit diff `8d3a5b2..5e6903b9` PASS. A broad `fbe57890..5e6903b9` check shows whitespace within **historical raw JUnit/log/diff evidence** added as documentary data; those artifacts are intentionally preserved verbatim and are outside production-source checks, not a code formatting regression.
4. Reviewer rechecked production cache root: `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth/cache_manifest.json` remains `psm_wma_robocasa_rgbd_pose_v1`, seven `COMPLETE.json` episodes remain. No migration, output cleanup or renderer run.

## Outcome and remaining separation

**G2-I19-F1 is CLOSED / APPROVE_CODE for exact `5e6903b9..1069fe78`.** No additional algorithm or source edit is requested. Real Depth native checks on `fbe57890` remain valid for `5e6903b9` because only the root guard and tests changed.

**Remaining operational gate is separate**: the Owner's fixed production output root is still v1, with 7 valuable committed episodes and historical `.failed`/`.staging` evidence. The version-2 production writer rightly refuses that root. Codex delivered a safety-oriented **migration proposal**, not a finished verified migration/promoter; do not claim full deployment readiness or authorize automatic resume from this code review. Next step: implement and validate a minimal explicit v1→v2 transition/promotion on the server with old generation retained, then separately authorize resuming only the frozen Batch000 (100 episodes, 24059 source frames) on GPUs 4/5/6. Do not use GPU7 or 0–3; no 25GiB batch cap/four-hour global deadline should be reinstated.

This review is docs-only on G2 isolated base. **No PR merge, no V3 or V2 change, no production export/resume, no source/Gitlink mutation, no unauthorized file transfer.**
