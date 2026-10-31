# Issue13 author synthetic shell evidence

Formal Root `24dbb677f7a60eeab6934c44352c7e00fa6d9b36`; unchanged Child/Gitlink
`0ae313e329d290fc6b8a50fda1112820fb7ac485`. Baseline3332d182. Isolated only.

`final/gate.json` / `final/junit.xml` / `final/pytest.log`: final clean exact-SHA
49 unique PASS (21 new +28 selected old launcher cases), zero fail/error/skip,
source unchanged. Two individual Bash syntax commands, ShellCheck0.10.0,
Ruff0.12.7 check+format and AST4. Original command argv/env tests use fake Python;
none executes real torchrun or model/data/Checkpoint/CUDA. Old CPU58/301 not run.
Child and the entire training/Checkpoint/Loader/Journal code are unchanged.

`examples/exit0` and `examples/exit7` contain ACTUALLY captured stdout, stderr,
raw full_launch.log, fake source and command/status. They are tiny additional
raw demonstrations, not added to the49 unittest count. Exit0 console shows one
startup path and only progress; exit7 additionally shows explicit failure/tail.
Never call these real training/model logs.

`audit.json` is AUTHOR Git/AST evidence: only3 Root production files; every
original shell training-command character/admission/export/cwd block preserved;
all46 old test assertions retained. Process scans only in shutdown cleanup,
stdlib helper imports, no Torch/device import or per-step instrumentation.
This is not independent GPT/DS execution or native GPU performance acceptance.

`history/first` contains the earlier17 PASS, `history/exploratory02` the precommit
49 PASS. These are not additional final tests and are not relabeled clean-Pair
runs. No test failures occurred. Tool setup used isolated /tmp shellcheck-py
0.10.0.1 (binary0.10.0); pip was unavailable, uv installed it outside the repo.

`run_gate.py` is the standalone source-frozen author replay helper (stdlib,
existing pytest/Ruff plus ShellCheck). Export it OUTSIDE a clean Formal checkout
before invoking; the later Evidence commit is not Formal Root. Use a new external
evidence directory. Original commands and safe-only env overrides are recorded.
Raw diffs are byte-exact; whitespace in their context-empty lines is intentional.
No private credentials, cache trees or training assets are packaged.

Post-publication STOP for GPT incremental Code Gate. No canonical merge, DS
dispatch, current C12200 A/B change, GPU/real training/DCP or benchmark replay.
