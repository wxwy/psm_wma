# HIGH-07 author CPU Evidence

Synthetic CPU only; no real model, server, simulator, training, DCP or GPU execution.

Implementation Root `320fda57c2cf450fbf0042183d7761a70b56f215`; Child/Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41`.

`baseline.log` intentionally preserves three pre-fix expected failures. Final 33 methods +50 subtests PASS (JUnit83 includes subtests); 55 unrelated deselected, no fail/error/skip. `gate.json` binds actual commands/env/RC and source hashes. `run_checks.py` is the exact author runner with machine-local paths; DS should use handoff delta commands. `regression_witnesses.json` includes actual queue argv, immutable protocol and synthetic results.
