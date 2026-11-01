# Issue #14 — frozen author CPU evidence

Formal Root `fd183f9e8fddfaef93b6ec9484184f071062ae41` / Child-Gitlink
`8664267704da3206e719f3c7eef2b5ed86e2a417`. Isolated candidate only.
The base is Root `9ba1dd110a4e3e99e717937c2f8d044fa077cdbf` and Child
`6c83596d6a259e89c4cd3e79424024983426ac3d`.

`final/gate.json` and raw JUnit/logs: **69 passed, 0 failures/errors/skips**;
50 new Issue14 tests + 17 unchanged config tests + 2 unchanged focused native
Core/media tests. Ruff 0.12.7 check/format for Root and Child and AST4 PASS.
Exact clean Pair and source bytes were checked before/after. Source bindings
cover 11 files. Scope is two Root production files and one Child adapter;
all other production code is unchanged, including MediaSink and Store/Scheduler.

Tests exercise the real public CPU dry-run, Runtime constructor and actor-config
creation, and NativeEpisode using the original native loop/HTTP codec/Local client
with a loopback model double and fake environment. The encoder boundary is
replaced; real MediaSink frame/prediction filtering remains in use. No genuine
MP4, FFmpeg, real simulator/model/GPU/DCP or active Job was accessed or started.
Two Tasks, indices0/1/2/3/49 and repeated indices verify dynamic selection;
media faults still preserve a valid Core commit and Local reset. This does not
establish GPU/simulator performance or real video encoding acceptance.

`attempts/initial_94e5a935`: **20 passed, 1 failed**, stop-on-first-failure.
A new fixture wrote plain invocation JSON, whereas the production CLI uses
save() with the immutable digest envelope; production correctly rejected it.
`attempts/fixture_envelope_719097ae`: **27 passed, 1 failed**, stopped because
the new actor fixture lacked the Store.locked coordinator lease used by CLI.
Both raw failed Gates, traceback, JUnit, source bindings and implementation diffs
are preserved unchanged. Only test fixtures and SESSION were corrected between
these Roots; production code and all assertions/thresholds were unchanged.
Do not add these partial counts to the final69 or claim all attempts passed.

`commands.json`, `run_gate.py`, environment overrides and the raw Issue14 snapshot
make the run reproducible. Historical test sources were not changed. No broad
CPU, GPU, OS or media-decoding Gate was rerun. Author PASS is not GPT or DS
independent acceptance. Publish candidate branches, request fresh Code Gate, stop.

The manifest hashes every bundled file except itself. Paths, raw whitespace and
byte content are preserved; no logs or JUnit were normalized for publication.
