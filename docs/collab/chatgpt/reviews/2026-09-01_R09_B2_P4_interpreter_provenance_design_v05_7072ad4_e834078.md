# R09-B2 P4 Interpreter Provenance design v0.5 review

- Request commit: `7072ad48528d97327ff22f57425cfd7c755527f5`
- Design commit: `e83407863d9c110715e71dff7d5a56b25b650278`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.5_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

This is a design-only review. It reviews the remediation of ChatGPT review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v04_befc5ed_55d9526.md` and does not authorize implementation, P4 record regeneration, P5 compose/export, torchrun, GPU, model/data access, training, evaluation, inference, P5 closure, or B2-T.

## Findings

### Previous v0.4 blockers closed

The v0.5 design correctly closes the previous worker, bytecode, P5-freshness, and hard-link blockers:

- torchrun is switched to `--no-python`, so PyTorch no longer synthesizes a direct `python -u -m cosmos_framework...` worker command;
- outer/worker/P5 Python argv all include `-B`, and the bootstrap checks `sys.flags.dont_write_bytecode` / `sys.dont_write_bytecode` rather than relying on a `PYTHON*` environment variable ignored by `-I`;
- P5 staging is moved under the P5 attempt root and is explicitly forbidden from creating or overlapping the frozen D005 production run root;
- staging is copy-only and worker reuse is readonly, eliminating hard-link source aliasing.

These points should be retained.

### HIGH — the shell worker wrapper introduces a new unbound executable/interpreter trust boundary

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.5_2026-09-01.md:7-17` makes the torchrun `--no-python` training script a root-owned executable shell wrapper, `tools/g0/r09_b2_p4_worker_exec.sh`, which then `exec`s the lexical Python bootstrap.

This closes the *Python* worker bypass but creates a new first-executed program before the worker bootstrap: the shell interpreter selected by the wrapper's shebang / executable format. The design binds the wrapper source SHA but does not bind the shell executable identity, its startup semantics, or any shell-specific environment startup surface. A changed `/bin/sh`/`bash` (or an environment-sensitive shell startup path) can execute before the Python worker bootstrap validates any P4 provenance.

PyTorch 2.10 `torch.distributed.run` does not require this shell hop. With `--no-python`, `config_from_args()` sets `cmd = args.training_script` and passes the remainder as `cmd_args`. Therefore the frozen worker executable can be the already-bound lexical venv Python itself, with worker args `-I -S -B <bootstrap-loader> --mode=p4-worker ...`.

Required fix:

- eliminate the shell wrapper from the trusted execution path; preferred grammar is `--no-python <lexical-venv-python> -I -S -B ...`;
- or, if a shell wrapper is retained, explicitly bind the exact shell interpreter binary + complete startup environment and prove no shell startup file/code can run. This is strictly more complex and is not recommended;
- permanent CPU test must assert the PyTorch 2.10 `--no-python` worker executable is exactly the lexical interpreter, not any shell or indirect launcher.

### HIGH — root-owned bootstrap code is still executed before its own runtime identity is established

`...design_v0.5...md:7` starts the outer agent as:

`<lexical-python> -I -S -B <root>/tools/g0/r09_b2_p4_bootstrap.py --mode=p4-agent ...`

and the proposed worker wrapper likewise executes the same root-owned bootstrap path directly.

The P4/P5 verifier can statically bind the bootstrap Git blob/current-byte SHA, but that does not establish the *runtime* bootstrap identity before Python opens and executes the file. If the production root/bootstrap bytes drift between static evidence and execution, module-level bootstrap code runs before that bootstrap can fail closed on its own SHA. This is the same execution-boundary class previously rejected for the P5 exporter bootstrap.

Required fix:

- the frozen outer/worker/P5 command must not execute a root-owned Python file before verifying the exact reviewed bytes;
- use an isolated stdlib-only loader whose code is frozen directly in the command/request (or an equivalently independently bound launcher): read the bootstrap bytes once, verify exact expected SHA/path/source revision, then `compile`/`exec` those already-verified bytes without reopening the path;
- the loader must also establish the exact production root/Gitlink/full-clean/output-mode preconditions applicable to that process before executing project bootstrap bytes;
- add a negative where bootstrap bytes are changed while argv/path remain the same; no bootstrap side effect may occur before rejection.

### HIGH — base stdlib / lib-dynload remain executable import roots without payload provenance

`...design_v0.5...md:35-36` retains the v0.3 runtime rule that all imports come from copy-only staging **plus base stdlib/lib-dynload**. The earlier contract binds the base executable and derives the stdlib/dynload paths, but v0.5 does not bind the bytes of those executable Python/extension payloads.

The bootstrap itself necessarily imports stdlib modules before staging/project provenance can be checked. A drifted `pathlib.py`, `hashlib` support module, `runpy.py`, `zipfile.py`, or a native module under `lib-dynload` can therefore affect validation/execution while the record still reports the same base executable SHA and the same path grammar.

Required fix:

- define the Python installation trust anchor explicitly. At minimum bind verifier-owned manifests for the exact base stdlib and `lib-dynload` payload used by bootstrap/runtime, including regular-file type, relative path and SHA256; unknown/extra executable payload in those roots must fail according to an exact grammar;
- the parent/preflight that is authorized to start the lexical child must verify this Python-installation manifest before child startup; child self-verification alone is too late for stdlib code already used at startup;
- if the project intentionally treats the host Python installation as an external trusted computing base rather than project evidence, state that explicitly as a frozen trust assumption and bind the exact installation identity at the execution-request layer. Do not silently infer trust from the base executable SHA alone;
- add a negative where the base executable is unchanged but a bootstrap-used stdlib or lib-dynload file changes.

## Positive observations

- `--no-python` is the correct PyTorch mechanism for preventing the default direct-Python worker synthesis.
- `-B` plus explicit `sys.dont_write_bytecode` checks correctly replaces the ineffective `PYTHONDONTWRITEBYTECODE` approach under `-I`.
- P5 attempt staging is correctly separated from the frozen D005 run root.
- Copy-only staging and readonly worker reuse are appropriate.
- The v0.3 profile/source/getpath and tracked+untracked clean boundaries remain useful and should be preserved.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted yet.

A v0.6 design should preserve the v0.5 worker/bytecode/freshness/copy fixes while closing only the three remaining execution-trust boundaries above: remove/bind the shell hop, verify project bootstrap bytes before execution, and explicitly bind or declare the base Python stdlib/lib-dynload trust anchor.

Still unauthorized:

- root P4/P5 tooling implementation;
- creating/modifying any Gate venv or external source checkout;
- P4 static record regeneration;
- P5 export/retry/compose or `load_experiment_from_toml`;
- torchrun/distributed execution;
- CUDA/GPU;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training/evaluation/inference;
- P5 closure;
- B2-T or any later gate.
