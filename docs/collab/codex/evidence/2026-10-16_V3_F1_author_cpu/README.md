# F1 author CPU evidence

Exact Pair: Root `264cff2f9ba4c8e8ff0b2cc8a7ca9f5a45021e1c` / Child-Gitlink `c0fc4cadccedb5838d3f2e512ea96179a3c969e9`. Author result only; DS/GPT PENDING.

Combined pytest: 56 methods (28 F1 +28 F0), 53 subtests, 109 JUnit bookkeeping cases, zero failure/error/skip, 50.77s. Four warnings are preserved in pytest.log (PyTorch TypedStorage deprecation and intended no_dist load path). Direct F1 unittest repeats those same 28 F1 methods, 47.14s, not additional coverage.

Real CPU PyTorch2.10.0+cpu, NumPy2.2.6 and Gloo execute synthetic tiny checkpoint fixtures. External Cosmos config/log/S3 are isolated; CUDA RNG bytes and Trainer model/device dependencies are explicit test stand-ins. No GPU/torchrun, production DCP/model/data or training. Full dependency/configuration and persistent target filesystem still require DS.

`gate.json` contains exact commands, cwd, source hashes, versions, overrides and RC. `unittest_verbose.log` retains all Gloo cases, error chains and a live-rank timeout at 10.06s. `witnesses.json` extracts per-rank error/publication/RNG and matching next-draw results. `unchanged_scope.json` compares approved F0 AST/source to verify unchanged legacy save/async, Local/codec/base/tests and launcher. Source hashes match the committed Child.

Only metadata and Local sidecar bodies are hashed by this protocol; large DCP shard bodies are checked by declared extent/file sizes, not rehashed. Existing checkpoints/evidence are never deleted. Post-commit permanent storage/process failure cannot promise rollback; see frozen contract failure table. CPU proof is not production readiness or GPU authorization.
