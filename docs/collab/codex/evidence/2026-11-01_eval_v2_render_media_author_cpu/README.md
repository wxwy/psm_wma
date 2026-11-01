# Split rendering / Media lifecycle author CPU evidence

Formal Root `46d3a604e66ca139e2f060fd4caaaa0583a1035f`; Child/Gitlink `d3b2a29b978ff4abef800b9e71fab4422b7a0d23`.
Candidate branch: `v3-eval-v2-render-media-20261101`; no V3 merge.

`final/gate.json` binds a clean exact Pair to192 passed/0failure/error/skip on
Python3.13.5. Ruff0.12.7 check/format, syntax and diff-check PASS. No GPU, real
EGL/OSMesa simulation, model, Server or FFmpeg. Loopback HTTP is a model double;
real Queue, CPU encoders and Linux owned-process/pidfd cleanup are exercised.
This is author evidence, not GPT or DS independent acceptance.

Exact commands, environment overrides and log paths: `final/invocation.json`,
`final/commands.json` and `author_cpu_runner.py`. Caches and pytest output were
external under `/tmp/psm-eval-render-media-20261101/final_author_cpu/`.
Raw finalJUnit/stdout/static logs are unchanged. Prior development29/192 passes
and the initial fixture-style stop remain separate; do not add them into192.

`formal_source_bindings.json` binds all23 watched source files to
their actual Git objects and SHA256. `scope_and_protected_trees.json` proves the
allowlisted diff and unchanged training/inference/data/checkpoint/vendor trees.
Root source diff excludes earlier frozen evidence and SESSION/TODO bookkeeping;
full changed paths/stat and Git base/formal SHAs are retained for full comparison.

Media tests include eight CPU slots for two rounds, full pipe/ignored TERM,
stdlib sentinel EBADF control, idempotence, startup error, live-residual failure,
Local/Core preservation, ownership/reuse/new child/helper checks and actual
Linux orphan TERM/KILL/reap with an unrelated surviving process. Rendering tests
use explicit EGL/NVML/sysfs doubles; real physical-device availability and
resource estimates remain a future target-host Canary, not an author CPU claim.
