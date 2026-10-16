# F0 author CPU evidence

Author checks only; no independent DS/GPT verdict or training authorization.

Pair: Root `b3b64732efb225c3ee08b1d9f317a90228112b29` / Child-Gitlink `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021`.

`gate.json` records exact commands, cwd, cache/device overrides, exit codes and committed-source SHA256 witnesses. `unittest.log` includes CLI negative exit messages, synthetic old-file SHA256+mtime witnesses and semantic digest invariance. `pytest.xml` has 56 JUnit cases: 26 methods plus 30 unittest subtests, not 56 distinct test methods. All zero failure/error/skip. The unittest and pytest runs execute the same suite through two runners and are not additive coverage.

The test harness imports actual Trainer methods with explicit synthetic external dependencies. It creates only synthetic metadata/sidecars under temporary directories. Full production-import regression, real collectives, target-filesystem locking and configured model serialization/preflight await DS. No GPU, torchrun, real DCP or dataset was used.
