# V3 EvalV2 Phase B B2 — READY 150ms test-only narrow Code Gate

**Date:** 2026-10-29

**Formal verdict: `APPROVE_CODE`** — restricted to the **single-file READY startup test-only change**. **Author full unified 434 and DS independent CPU Evidence gates remain OPEN**; this approval authorizes *only one author full CPU Gate* on this Pair, not a DS PASS, production merge or native GPU run.

| Identity | Exact SHA |
| --- | --- |
| New Formal Root | `9657fb6ab590f228d760362e506d5dd1b626880a` |
| Child/Gitlink, unchanged | `0ae313e329d290fc6b8a50fda1112820fb7ac485` |
| Previous reviewed Root | `657061e6893bd61e685685089a1cf1f61e9eb1fe` |
| Separate author-evidence bookkeeping HEAD | `bac28c293d4b7900e39030ca86575c8085667e28` (not Formal Root) |

## 1. True remote incremental scope

Direct independent GitHub commit comparison shows **one Root file changed**, `tools/v3/eval_v2_production_tests/process_test.py`, **+3/-1**; Root direct parent is `657061e6...`. Actual new file GitBlob `8f1ae2f0432a51e782d1c37c309c98de4f1772b3` matches immutable author `source_proof.json` source binding. The Root submodule Gitlink independently reads `0ae313e329d290fc6b8a50fda1112820fb7ac485`; Child, production Actor, Store, Batch, F1/F2/F3, Gate scripts, tests and scientific contracts are unchanged. Bookkeeping commit `bac28c293d4b7900e39030ca86575c8085667e28` is an offspring of Formal Root carrying archived test evidence, and is not a new implementation target.

Actual patch:
```diff
-    value = actor(tmp_path, timeout=0.15)
+    # Allow Python startup/READY its own budget; stall still gets only 150ms.
+    value = actor(tmp_path, timeout=5.0)
+    value.timeout = 0.15
     start = time.monotonic()
     try:
         with pytest.raises((EOFError, OSError)):
             value.request("stall")
```

## 2. Original author FAIL root cause — independently verified from raw archived evidence

From [original PhaseA XML](https://github.com/wxwy/psm_wma/blob/bac28c293d4b7900e39030ca86575c8085667e28/docs/collab/codex/evidence/2026-10-29_eval_v2_ready_startup/original_phase_a_regression.xml) and [raw traceback](https://github.com/wxwy/psm_wma/blob/bac28c293d4b7900e39030ca86575c8085667e28/docs/collab/codex/evidence/2026-10-29_eval_v2_ready_startup/original_traceback.txt), original `657061e6/0ae313e3` author full Gate had `inference=145 PASS`; `phase_a_regression=72 PASS/1 FAIL` (`-x` at the 73rd, not the remaining 182), with precise failing test `test_stalled_actor_request_is_bounded_and_unrelated_process_survives`.

Exact failure: at `process_test.py:83` `actor(tmp_path, timeout=0.15)` → `actor(): assert value._receive()["kind"] == "READY"` → `Actor._receive` → `wire.py:sock.recv(4)` raises `TimeoutError: timed out`; **not** `request("stall")`. Thus initial diagnosis of startup READY budget accidentally sharing the 150ms *operation* deadline is supported by first original trace, not environment speculation. No evidence that Store new logic caused this failure.

Source checks: `scripts/robocasa_eval_v2_processes.py::Actor._receive` uses `self.timeout` for bounded socket/monitor. The patch raises timeout solely during setup/READY. On successful return, restores `value.timeout=0.15` **before** `start=time.monotonic()` and `value.request("stall")`; unchanged `try/except`, stop, owned registry close, foreign process survival and `elapsed<3s` assertions retain their tested semantics. No production timeout, request budget, online environment or other test changed.

## 3. Focused author evidence and boundaries

Directly read archive under `docs/collab/codex/evidence/2026-10-29_eval_v2_ready_startup/`:

- `process.xml`/log: 8 tests collected/passed, no failure/error/skip.
- `delayed_ready_probe.py`, `delayed.xml`, `delayed-ready.json`: probe injects `time.sleep(0.4)` **in the actual launched Python child code** before socket READY; uses instrumented wrappers to observe original `Actor._receive` and `Actor.request` without replacing their behavior. It observes READY timeout 5.0s and actual duration ~1.114s; the later stall runs with timeout0.15s, raises `TimeoutError`, elapsed ~0.172s; JUnit one PASS. The probe alters its **test-time child snippet only**, not production or committed test semantics.
- `handoff.json` / commit message report Ruff0.12.7 check, format and diff-check passing; their raw logs were not individually archived here, so treat these as author-reported, **not independently rerun**. New Formal Root source proof GitBlob verified.
- `original_gate.json` has FAIL, not converted to PASS; no 434-case author full Gate on new Formal Root yet. No DS test run by GPT.

No new reachable code defect or contract violation in this narrow patch. **A1-E1 (READY setup vs stall timeout coupling) CLOSED at source/focused-evidence level**. The separate broader CPU Evidence acceptance remains open.

## 4. Authorization and acceptance (no new architecture)

**Authorize Codex/author exactly once**, on a clean isolated Root HEAD `9657fb6ab590f228d760362e506d5dd1b626880a` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`, use new external evidence directory (not the old author failure or focused archive), to run the frozen entry `tools/v3/run_eval_v2_batch_b2_cpu_gate.py`. No code amendments and no repeated unrelated retests.

Accept only combined `145 inference + 255 Phase A + 34 Phase B = 434`, zero failure/error/skip, shell exit0, `gate.json.status=PASS`, `source_unchanged=true`, exact identities/import origin, Ruff/format/AST, native CPU OS B2/multisim/Round D5/Resume/Server death and owned cleanup. Preserve raw original logs/JUnit/gate/source hash and concrete OS witness.

**Next:** after author full Gate PASS, submit one evidence packet to GPT for focused evidence audit and perform one independent DS_PRO clean exact-Pair unified CPU replay. Independent DS Gate remains `REQUEST_CHANGES` until its own full successful behavioral proof. Any new failure must be reported raw, no automatic environment label or unbounded retries.

**Not authorized:** V3 or Child production merge, GPU/Cosmos/RoboCasa/EGL/Canary/900, training, checkpoint/vendor/runtime changes. No repeat F3 production review and no new Batch/Local-TTT architecture.
