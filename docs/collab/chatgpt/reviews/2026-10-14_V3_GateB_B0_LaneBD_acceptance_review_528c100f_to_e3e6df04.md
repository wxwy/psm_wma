# PSM-WMA V3 — Gate B0 CPU Lane B/D independent acceptance review

**Date:** 2026-10-14  
**Reviewer:** GPT (independent design/code/evidence/Gate)  
**Scope:** isolated CPU-only diagnostic B0; **not** B1 GPU parity nor source DCP migration.  
**Previous diagnostic candidate Root:** `528c100fd120c3fad52739f2ec09a8cd8cab50e6` on `v3-gateb-comparator-b0`.  
**Remediated diagnostic candidate Root:** `e3e6df04eba7d3a5ab160b1563eee7146e1ee584` on the same isolated branch.  
**Production V3 child/Gitlink:** `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1` unchanged (not a Gate B comparator leg).  
**Comparator source:** Index8 `b159f45906f7261d028aecc226ab7f2bb9807eb9` + Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`; target Packed128 `c4731bca1a590663db88bd6cd74dbcf9fd513a85` + Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
**Verdict:** **REQUEST_CHANGES** on **OLD diagnostic candidate**; **NEW candidate REMEDIATED_IN_SOURCE / B0_CPU_EXECUTOR_RETEST_PENDING**. No Gate B0 approval.

## Evidence independently assessed

User-supplied DS_PRO single-round report `DS_PRO — V3 Packed128 Gate B0 Lane B/D Completion` (2026-10-14; executor-only) states:
- Exact old diagnostic `528c100f` and both comparator source/target pairs with clean worktrees and resolved imports; py_compile three files **exit0**; 21 pytest passed **exit0**; B1 `--mode paired-run` negative gate **exit2** with `GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED`.
- Ruff (0.12.7) **exit1**, two F401 unused imports in `tools/gates/test_v3_packed128_gateb_compare.py:6,8`.
- Both real CPU `--verify-payloads` Legs reached exact source/target config_digest and identical 8-rank×2-window `plan_fingerprint=6a4d9c6a03aedfedd679179d05c6fe59eb7317d4bebf6d6b5d39f9978b6932b5`, including terminal partial and native Index8 16+16 each GA across ranks; then **both exited2** before materialization/report output with `CFG global RNG scope requires one Python main thread and nw=0`.
- DS thread-start probe reported `tqdm._monitor.TMonitor` daemon created by `tqdm.contrib.concurrent.thread_map` during `_preflight_catalog`; this benign progress bar thread explains `threading.active_count()==2`. A log assertion about its RNG behavior is executor-supplied, not assumed as authorization to allow arbitrary threads.
- Therefore `compare-cpu-reports` NOT_RUN; real payload hash/CFG replay NOT_VERIFIED. Prior Lane C trusted old iter1300 Sidecar 17-field schema, all 8 ranks, DCP static, 484-path source immutability and two-window evidence remains useful; no need repeat Lane C. Source checksum reported steady; real DCP load/GPU training never performed.

## Finding B0-01 — MEDIUM — progress-monitor thread false blocker

- **File:line (OLD):** `tools/gates/v3_packed128_gateb_compare.py:106` (`scoped_python_cfg_rng`); `_preflight_catalog` in same file initiates dataset metadata readers, triggering tqdm monitor before transform.
- **Root cause:** strict one-Python-thread invariant is reasonable while temporarily substituting global Python RNG state, but `tqdm.TMonitor` spawned earlier by metadata load breaks the invariant without validating any transformed consumer.
- **Violation:** C0/B0 real CPU source/target CFG/data/materialized payload parity must be exercised without weakening protection against genuine concurrent global RNG observers.
- **Acceptance:** prevent progress monitoring thread *before metadata initialization* in isolated diagnostic only, keep `scoped_python_cfg_rng` main-thread/single-live-thread constraint; test real tqdm progress monitor/thread_map, unknown background-thread fail-closed and restoration under errors; both source/target real `--verify-payloads` and `compare-cpu-reports` must then succeed or emit new honest blocker evidence.
- **Remediation:** NEW `e3e6df04` added `scoped_disable_tqdm_monitor` outer scope around source metadata + CPU materialize. This sets `tqdm.std.tqdm.monitor_interval=0` for the diagnostic block, restores value on all exits. Strict unknown-thread reject remains. GPT local isolated candidate: pytest **25 passed**, `py_compile` 3 files exit0, `thread_map` real no-TMonitor smoke PASS, unauthorized paired-run exit2. **DS target-venv runtime still pending**, no B0 PASS claim.

## Finding B0-02 — LOW — Ruff F401 unused imports

- **File:line (OLD):** `tools/gates/test_v3_packed128_gateb_compare.py:6,8` `dataclasses` and `os` are unused.
- **Root cause:** two stale test imports fail repository Ruff 0.12.7 checks.
- **Violation:** Gate B0 requires Ruff0 on all 3 isolated candidate files.
- **Acceptance:** narrow remove imports, run actual Ruff in DS venv on exact NEW SHA; compile/pytest CPU smoke all green.
- **Remediation:** NEW `e3e6df04` removes only those imports and adds scoped-tqdm safety tests; GPT local pytest/compile PASS, real DS Ruff remains unverified.

## Source diff and scope

GitHub independently compared `528c100f..e3e6df04`: **only two diagnostic files** changed (`v3_packed128_gateb_compare.py`, `test_v3_packed128_gateb_compare.py`); no models/training code, no `cosmos-framework` Gitlink, no source/checkpoint writes. Root docs HEAD has no bearing on diagnostic implementation identity.

## Next evidence / narrow DS recheck

1. Pin diagnostic SHA `e3e6df04eba7d3a5ab160b1563eee7146e1ee584`, clean isolated checkout and two original comparator Pairs. Ruff, py_compile, pytest and blocked paired-run CPU tests in one round.
2. Without repeating Lane C: re-run real Index8 then Packed128 `--mode cpu-plan-only --num-workers 0 --steps 2 --hash-all-shards --verify-payloads`, two new /tmp output namespaces, original iter1300 readonly. Save payload/CFG RNG witnesses and compare both JSON with `compare-cpu-reports`.
3. One consolidated DS report with exact SHA, test exits, two Leg output/tracebacks and source immutability; no per-probe back-and-forth.
4. Only after DS report may GPT reassess fresh exact NEW diagnostic SHA and potentially close CPU B0. No GPU FSDP8 native checkpoint load, forward/backward, P1 training-distribution sigma, gradient parity, migration or iter1301 resume is authorized by this review.

**No formal B0 approval.** The old diagnostic implementation has blockers; the new candidate must earn its own scoped B0 verdict. Packed128 Gate A and Full Prefetch C0 CPU closures remain unaffected.
