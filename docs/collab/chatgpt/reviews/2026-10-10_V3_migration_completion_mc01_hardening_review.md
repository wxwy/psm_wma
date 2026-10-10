# V3 Migration Completion MC-01 — hardening source review and DS CPU-only handoff

Date: 2026-10-10.
Decision: **APPROVE_DS_CPU_STATIC_EXECUTION_ONLY / FULL_GATE_OPEN / RESUME_HOLD**.
This is a new implementation review, not a repeated certification of the old Dataset Index or FSDP2 fix.

## Exact implementation authority

- Implementation Root: `ee2de3fcb21d53b392a89fb6bc0409a57d6d4896`.
- Child/Gitlink: `95c82d12d6780fedf8becda18cbd36d550adaadf`.
- Parent Root: `ea4c5c7784a6e3b4759383bec5420ccd2cdc474b`.
- Parent candidate Child: `98cb4fd0cc59e71f27543d67fa33cbf4f3703657`.
- Original accepted Formal30k Child: `71e03c8501c94a2ad5fed60955af657d3f945b85`.
- The Root commit containing this review and the Inbox append is a docs-only successor of the implementation Root; its Gitlink stays exactly `95c82d12d6780fedf8becda18cbd36d550adaadf`. Owner handoff must state that exact execution Root. Do not substitute an arbitrary future branch tip.
- Branches: Root `V3`, Child `v3-local-ttt`. V2/v2 and original candidate training branches remain unchanged.

## Findings corrected in this increment

1. Old TelemetryJournal wrote to stdout before durable JSONL. A BrokenPipeError prevented the record reaching disk. Machine-readable logging now precedes and is independent of stdout.
2. Old JSONL aggregation retained unreplayed higher iterations after a resume rewind. Derived summaries now discard the superseded suffix, without editing the historical log.
3. An incomplete final record was sometimes published or glued to a new resumed row. The reader waits for newline completion. Journal startup refuses an incomplete/corrupt existing machine log and does not truncate evidence.
4. Old DCP audit could report COMPLETE for zero-byte files or two same-rank shards substituting for a missing rank. The check now requires nonempty in-bound files and expected per-rank coverage. COMPLETE still means filesystem inspection ONLY, not loadability or strict Resume PASS.
5. Plot output and persisted summary could disagree; plot failure could prevent a health report. Summary persistence is now consistent and records plot failures independently. Metrics are rendered as separate figures, not mixed-unit axes.
6. Original tuple-comprehension submission lost ownership of already-submitted futures if a later submit failed. The queue now owns futures before submission, drains on exceptions, validates returned identity, and rejects a second pending member. Actual thread-pool tests cover ordered consumption despite out-of-order completion.
7. Workers now also own a shallow LeRobot dataset wrapper; the preloaded HF table remains shared read-only. This does NOT independently prove real LeRobot thread safety or faster I/O.

## Scope audited

Child diff from parent candidate is exactly:
- `cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch.py`
- new `cosmos_framework/utils/ordered_prefetch.py`
- new `cosmos_framework/utils/ordered_prefetch_test.py`
- `examples/psm_wma_robocasa_formal_monitor.py`
- new `examples/psm_wma_robocasa_formal_monitor_safety_test.py`.

Root implementation adds only the CPU Gate runner/test, migration execution plan, scoped local evidence report, and matching Gitlink.
No increment changes to Local math, ordered transforms, dataset membership/order, cached-latent geometry, Trainer optimizer transaction, scheduler, FSDP2, model prefix path, DCP serializer, inference, simulator, or evaluation queue.
MM SESSION/TODO and all old evidence are untouched. Cached pixel-placeholder removal is NOT in this patch.

## Actual local evidence

Report: `docs/collab/chatgpt/evidence/2026-10-10_V3_migration_completion_local_cpu.json`.

- Byte-checked old Monitor source and original test blob before characterizing defects.
- New safety tests on old Monitor: 10 failed / 2 passed.
- New queue + original Monitor + new safety + runner tests after remediation: **50 passed, 0 failed, 0 skipped**.
- Syntax compilation: 8 local source/test files passed, including the adapter source; this is not compilation of the full Child tree.
- Real background Python threads, synthetic requests, synthetic filesystem DCP fixtures, and real Agg PNG serialization were exercised. No real dataset/DCP or GPU was used.
- Final uploaded code blobs match the locally tested bytes.

**Not executed here:** Ruff0.12.7; full project imports/pytest with LeRobot/pyarrow; real Source/Action/State/Latent/Token equality; 8-rank FSDP/throughput; strict saved-DCP Resume. Local environment lacks Ruff, LeRobot and pyarrow. The full-project CPU Gate remains OPEN. Passing new unit tests is not independent DS acceptance.

## DS_PRO authorization — one CPU/static attempt only

1. Use the existing sole project directory and original training Python environment. Perform only safe Git fetch/fast-forward to the owner-pinned execution Root and Child above. Preserve MM notes, all evidence, original output namespace and DCP. No worktree creation, reset/clean, source edits, formatting writes, commits or uploads.
2. From the Root, run `tools/v3/run_migration_cpu_gate.py` with exact `--expected-root`, `--expected-child`, and a NEW evidence directory outside the repository. The owner message provides literal hashes and command.
3. The runner verifies Root/Child/Gitlink, permitted notes, clean Child, original accepted ancestor, and source fingerprints. It sets CPU/offline variables, removes inherited torchrun variables in subprocesses, writes py_compile results outside source, requires Ruff0.12.7, runs Ruff check/format-check and focused pytest, and checks source immutability afterward.
4. Return `gate.json`, stage logs, XML, versions, and exact pair. First nonzero/exception/missing dependency means STOP. No `ruff --fix`, `ruff format` writes, skipped failing tests, dependency auto-install, or weakening of assertions by DS.
5. If and only if full CPU/static PASS, return a read-only inventory of the user-stopped formal job's latest pointer and complete checkpoint components/ranks. Do not assume the latest saved iteration is exactly800. Do not deserialize/run Policy, resume, or run GPU from this CPU authorization.
6. Frozen config digest expected: `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`. This runner deliberately reports actual digest as unmeasured; the later real Phase5 preflight must measure and compare it.

## Subsequent gates remain separate

After DS evidence is reviewed: real data equality and strict Resume using the last complete original DCP, then corrected Full Policy/simulator and evaluation identity/failure evidence. Workers0 is the reference; workers2/4 need measured parity/throughput. No fresh training in the formal namespace and no diagnostic checkpoint reuse.

The current Phase5 execution-cap flag is fresh-only: `--phase resume --stop-after-iter` is not a supported bounded Resume recipe. A valid bounded Resume method must be specified separately instead of changing max_iter/warmup/save_iter.

Remaining tasks and dependencies are recorded in `docs/build/PSM-WMA_V3_migration_completion_execution_plan_r1_2026-10-10.md`. This commit does not claim MC-02..07 complete or authorize their GPU execution.
