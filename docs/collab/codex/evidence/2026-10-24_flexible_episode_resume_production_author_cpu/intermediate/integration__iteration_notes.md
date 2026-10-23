# Integration gate iteration history

All runs are CPU-only. Server means a tiny fake-model HTTP process; simulator
means the unchanged Child CLI/run_policy with fake environment/runtime/state
fixtures. No real model, GPU, RoboCasa physics or training is invoked.

- Initial fixture iteration: fresh5 passed; synthetic legacy source omitted the
  original `.run.lock`, so admission correctly returned `MISSING_RUN_LOCK`.
  Fixture was corrected to reflect the real legacy launcher's lease. The initial
  raw log was overwritten during this fixture iteration; its traceback/count
  remain available in the tool transcript. No replacement raw log is fabricated.
- `run01/`: retained first multi-case execution, 9 passed then busy-lease test
  failed because the fixture expected RuntimeError while production correctly
  raised typed `ResumeStoreError` (a ValueError) with `RUN_LOCKED`. The test now
  requires that exact typed rejection and code.
- `run02.log/xml`: 10 passed then a genuine production counter regression was
  exposed: `_unfinished_executions` read authoritative episode_progress.jsonl but
  matched optional UI `episode_start` rather than authoritative `start`. Third
  episode runtime error consequently produced executed=2/failed=0 rather than
  executed=3/failed=1. Parent repaired the production schema/event check; the
  assertion was retained.
- `run03.log/xml`: both targeted counter/resume and media-upgrade cases passed.
  Media case also exercises real tiny predicted/environment MP4 and initial PNG,
  guarding against nested rollout path lists in the new summary.
- `run04.log/xml`: full source-file rerun, additionally including real Child
  Local reset HTTP500 => rejected core => fresh recovery with a new server.
  Result: 13 passed in45.97s, no skip.
- `run05.log/xml`: newly added final-source-rescan failure negative, using a
  genuine Child third-Episode failure plus injected second discover_history
  failure. Checks final report/current summary PARTIAL (not stale RUNNING),
  preserved executor error and both cleanup witnesses, excluded unvalidated
  sources, nonzero return and retained raw evidence. Result: 1passed,
  13deselected in2.99s. This targeted run is not described as an all14-case rerun;
  Parent combined gate executes the final file.

The runtime-probe adapter calls the real Root/Child Git and base identity builder
on tiny repositories. Actual protected CLI, Store, lock, reservations, executor,
owned process cleanup, Child Local ledger/HTTP ack/reset, core validator, catalog
and current summary are exercised. State15 itself is a fake observation fixture;
these tests do not claim physical ABI/benchmark or true DCP load acceptance.
