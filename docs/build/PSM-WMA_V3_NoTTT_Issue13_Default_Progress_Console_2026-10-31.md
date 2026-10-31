# Issue #13 — default No-TTT console split, isolated implementation

Authority: Owner + Issue13 + canonical request at V3
`3332d1825de8778e3d6dbb7e9ba98cbffff487c6`. This isolated branch starts there;
Child/Gitlink stays `0ae313e329d290fc6b8a50fda1112820fb7ac485`. Do not merge the
separate frozen training candidate or change the active C12200 A/B source.

## Scope and implementation plan

- Only standard Root No-TTT 4/8 GPU launchers and a small stdlib output wrapper.
- Preserve the exact original torchrun argv, chosen training Python, working
  directory, profiles, identity, env except `PYTHONUNBUFFERED=1` for pipe output.
- Default, no new enable/debug switch: persist combined raw stdout/stderr first,
  then display only complete `[CorrectedV3][progress]` lines. The existing
  Observer emits progress on rank0; do not modify its content or Journal.
- Open an exclusive unique raw log under `OUTPUT_ROOT/_launch_logs/JOB_NAME/`,
  never the fresh Trainer namespace. Startup may print the path once. Error,
  signal or log failure prints an explicit summary, path and bounded raw tail.
- The wrapper is a foreground process, not a logging service. No Torch/model
  imports, per-step instrumentation, fsync-per-line, filtering before raw write,
  new training timeout, or training/checkpoint logic. Fsync at close catches
  persistence failures; log setup/write/sync errors fail closed.
- Torchrun creates separate sessions for Rank subprocesses. On shutdown only,
  use Linux subreaper ownership and descendant identity checks to handle these
  sessions, bounded termination/escalation, adopted-child reaping and residual
  pipe drain. Do not scan process trees in the steady-state training hot path or
  signal another job. INT/TERM return130/143; preserve ordinary training exit7.
- Use system `python3` for the stdlib wrapper, separately from the unchanged
  selected `$PYTHON` for training. No dependency on the training Torch imports.

Expected files: `scripts/train_v3_matched_no_ttt{,_4gpu}.sh`, new
`scripts/no_ttt_console.py`, synthetic shell/process tests under tools/v3, and
minimal updates of existing fake-Python launcher fixtures to read the full log
instead of expecting suppressed diagnostic JSON on stdout. Preserve all argv,
profile/admission and Resume assertions.

## Targeted synthetic acceptance

Fake training only: mixed rank/stdout/stderr/progress/loader/checkpoint/traceback,
exact raw bytes, no-progress warnings, exit0/7/exec failure, unique Resume logs,
no premature Job claim, open/write/fsync faults, bounded huge/fragmented lines,
live progress flush and signals with owned separate-session descendants and a
foreign survival control. Compare pre/post launcher fake-command argv and env.
Bash syntax, shell static analysis, scoped Ruff0.12.7/format/AST and exact source
identity/diff. No previous CPU58/301, real data/DCP/model/torchrun/GPU or training.

Deliver a new Root implementation SHA, unchanged Child SHA, raw CPU evidence and
incremental GPT Code Gate request; then STOP. No canonical promotion, DS dispatch
or change to ongoing C12200 tests.

## Implemented behavior and runtime assumptions

The two launchers now exec the shared `scripts/no_ttt_console.py` through the
host's `python3`; the original training interpreter and complete torchrun argv
follow `--` unchanged. No optional enable switch. Requires Linux `/proc` and
child-subreaper support, already the target deployment platform. Setup fails
before training if the log or ownership guard cannot be initialized.

Raw files are exclusive0600, one per invocation. Writes are unbuffered OS writes
with short-write handling, before any terminal copy; fsync occurs only on close.
Incomplete/huge diagnostic lines never grow the display buffer without bound;
raw bytes, including invalid UTF8, remain exact. Existing normal progress lines
are far below the16KiB display framing bound. A detached console is independent
of raw persistence. Warnings with no progress and exit0 remain success.

Ordinary child exit codes propagate, signal exits normalize to128+signal, user
SIGINT/SIGTERM return130/143. Infrastructure persistence failures return nonzero
and display both wrapper exit and the observed child exit, log path and last8KiB.
Cancellation gives the original torchrun leader its signal, allows5s teardown,
then freezes/kills remaining owned descendants and bounds reaping/drain. No
process-tree scans, device APIs or training-time limits run during normal steps.
This is output supervision; checkpoint format/publication logic is untouched.

Preliminary synthetic results:17 output/process cases PASS; expanded21new+28old
launcher cases49PASS. Static Bash/ShellCheck0.10.0 and scoped Ruff0.12.7 pass.
Final exact-SHA evidence publication is separate from this implementation doc.
No real training/Checkpoint/GPU performance test is required or claimed here.
