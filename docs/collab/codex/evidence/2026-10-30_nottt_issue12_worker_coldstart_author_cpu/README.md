# Issue12 narrow worker cold-start author evidence

Formal Root `fd9021b0908b4b2763b3d02508b1f34df377dc97`, Child/Gitlink
`224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`. Isolated candidate only.

`final/gate.json` binds the exact clean source; `async.xml` 47 and
`regression.xml` 11 unique PASS cases, no failure/error/skip. Combined58.
Ruff0.12.7 check/format/AST4 and import origin pass. These are author synthetic
CPU results, not GPT/DS execution or a full repository gate. Old CPU301 not rerun.
`run_gate.py` is the frozen standalone author replay helper, adapted from the
prior exact-pair runner; no new production launcher. It requires a NEW external
evidence directory and the exact clean Formal checkout, not this evidence HEAD.
The helper itself and all published artifacts are hash-bound.

`witnesses/` reports actual small synthetic source build/read and owned spawn PID,
not the DS real source. `final/timelines/` reuses the unchanged synthetic loader
overlap oracle. Do not compare these milliseconds to the DS193s real cold start
or claim real GPU acceleration/first-packet success. GPU/native DCP tests NOT RUN.
RAM retained Arrow cap is an extra independent worker cache, not RSS prediction.

`protected/` is a read-only internal AUTHOR Git/AST audit: only two production
files change; 12 protected blobs and all10 original recipe-test definitions are
unchanged. Check root.diff and child.diff for the complete formal deltas.

History is retained and excluded from the final PASS count: exploratory01 pytest
dependency-hook collection error; exploratory02 9PASS/1FAIL new regex expected
the wrong guard (original strict SourceReader rejected correctly); exploratory03
46PASS before the final spawn integration; focused04 rejected the new test's
B1/GA2 fixture by the unchanged B8/GA4 guard; focused05 the new recipe proxy
omitted rate/caption/token fields; focused06 1PASS after fixing only the fixture.
No original assertions or native-profile checks were relaxed.

Raw warnings are retained: pynvml deprecation, CPU affinity advisory for nw8,
and resource_tracker cleanup of two registered semaphores after worker shutdown.
Tests explicitly verify owned worker PIDs are reaped and foreign processes
survive. This does not claim a broad native resource qualification.

No test datasets, cache trees, .pt payloads, credentials, or production assets
are copied into this package. Canonical V3/Child, formal training, DCP, Config,
Job identity, old evidence and the separate EvalV2 line were not updated.
