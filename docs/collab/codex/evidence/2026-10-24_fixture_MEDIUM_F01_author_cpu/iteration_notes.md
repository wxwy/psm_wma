# F01 iteration record

- Baseline watchdog with two new deterministic tests:2failed. One failed with injected OSError before cleanup; other retained a live distinct-session child. Test finally clauses reclaimed their controlled children/foreign controls.
- green:6passed; first fix killed child but raw process snapshot showed a zombie. Strengthened reaping and assertion to require PID and PGID absent;green2:6passed, final process lists empty, foreign alive.
- green3:7passed after guarding evidence allocation and monitoring I/O as well as _retain.
- Interrupted_candidate full attempt was stopped for the lifecycle boundary correction. It is NOT a PASS; source hash/log/JUnit kept.
- An accidental duplicate execution-test path command was stopped and its raw output retained under interrupted_duplicate_command. SIGINT was converted by the broad exception guard; the owned tree was reclaimed by verified PID ancestry. This exposed cancellation propagation: cleanup now re-raises KeyboardInterrupt/SystemExit after reclaiming. Interrupted_cancellation_guard run likewise NOT a PASS.
- green_final:8passed, including interruption propagation. The final combination is run_final.py with exactly5unique paths; no source edits after its frozen16-file hash. Final JUnit alone determines published total; earlier counts are separate.

No production/Child/real GPU/model/Kitchen/DCP/history operations. All kill operations targeted only each controlled run's verified descendant tree; independent live controls survive final watchdog tests.
