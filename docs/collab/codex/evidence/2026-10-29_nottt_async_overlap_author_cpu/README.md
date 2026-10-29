# Author CPU evidence — Issue #9

Final exact Pair is in formal_pair.json; final/gate.json + raw JUnit/logs are authoritative for author CPU only. Native GPU overlap/performance and real DCP Resume are NOT executed.

`history/locked01_failed_fixture` is the initial 66986d5f / 5124a2b7 Pair: 55 passed / 1 failed, stopped before regression. The new per-GA fixture assertion incorrectly selected initial frontier instead of pending lazy-Restore frontier; no production checkpoint change was needed. The correction preserves all frontier assertions. Additional final changes freeze resolved roots and report comparable fake-compute wall intervals. This RED is never relabeled as GREEN.

`history/locked02_failed_legacy_fixtures` binds e8c49c07 / d64e5c1d: new async72PASS; regression122PASS/1FAIL/1SKIP before stop. Existing namespace config fixture used unsupported SimpleNamespace plus missing receipt, and another strict semantic test targeted the Owner-exempt historical Job. New fixtures use supported structured records/receipt and an ordinary strict Job with all prior assertions retained. Exactly one forbidden real-data debug node is explicitly deselected by the final synthetic-only gate; its source is preserved and it is not counted as PASS.

`preliminary/` contains separate exploratory passes and available setup failures; their sums are not added to final totals, and their sources were not all identical to the final Pair. Initial recipe pytest invocation needed disabling repository addopts in the isolated CPU environment.

Timeline uses actual worker-owned CPU Source/Transform and a CPU-only hash-compute callback, not CUDA. It proves overlap and no early commit, not GPU acceleration. Three-Window timing includes spawn cold start; asynchronous total wall can exceed the serial control. The unchanged old RAW backend has an expected RED target witness.

Temporary checkpoint/cache containers, pytest basetemp trees and model-like fixtures are not published. Only whitelisted logs, JSON, JUnit, diffs, static audit and source bindings are copied. Protected audit is internal author review, not GPT or independent DS.
