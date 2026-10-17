# F1 final author CPU evidence

Formal Root `6ebf8998a7935f2ad690bb547c5db5e5a4322e6d` / Child-Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41`. Isolated branch `v3-f1-checkpoint-rng-20261016`. Author self-test only; DS/GPT PENDING.

Combined run: **57 methods** (29 F1 +28 F0), **53 subtests**, 110 JUnit bookkeeping cases, zero failure/error/skip, 51.879s. Four parent-process warnings are retained: PyTorch TypedStorage deprecation and intended no_dist load path. Child process warnings and complete injected-error chains are preserved in pytest.log. No counts are added across repeated runs.

Real Torch2.10.0+cpu/DCP/Gloo and NumPy2.2.6 execute tiny synthetic checkpoint fixtures. External Cosmos config/log/S3 imports are scoped test stand-ins; CUDA RNG bytes and Trainer model/device dependencies are explicit stand-ins. Full dependency/configuration and persistent target filesystem still require independent DS verification. No GPU, torchrun, production assets or training.

`gate.json`: commands/cwd/environment/versions/RC/source hashes. `pytest.log` + `pytest.xml`: full final combined execution. `witnesses.json`: all 14 Gloo scenarios and single-rank deterministic next-draw witness. Live stalled rank failed at 10.06 seconds. Both successful ranks restore model/optimizer/scheduler/Local state and distinct per-rank RNG next draws exactly. The independent standard-library reader checks marker/pointer/files. `unchanged_scope.json` was measured for production c0fc4cad; final Child changes only tests and its production bytes were compared equal. `manifest.json` binds final Pair/contract/log hashes.

Frozen contract SHA256 `aa3f7c6db2bdf5a7c193de1398b7ff1aa81b59b08554552f6fa86fc3e2748185` is unchanged. It records c0fc4cad as production candidate; final 2d128ed5 is its test-only successor. Earlier `2026-10-16_V3_F1_author_cpu` remains preserved as preliminary evidence for 264cff2f/c0fc4cad; it does not replace this final Pair.

Metadata and Local sidecar bodies are hashed; model/optimizer shard bodies use extent/file-size checks. Permanent post-commit storage/process failure cannot promise rollback; see contract failure table. No historical evidence or checkpoint is cleaned. These are author CPU results, not formal acceptance or training authorization.
