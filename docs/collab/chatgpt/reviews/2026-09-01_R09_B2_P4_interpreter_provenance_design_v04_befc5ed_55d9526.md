# R09-B2 P4 interpreter-provenance design v0.4 review

- Request commit: `befc5ed6abfd45bed2e4db5528226c083c509f50`
- Design commit: `55d95262356c4b54770d84aeb8bdcb4d52df739d`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

This is a design-only review of `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.4_2026-09-01.md`. It does not authorize implementation, P4 record regeneration, P5 compose/export, GPU, torchrun, training, evaluation, or inference.

v0.4 does close the v0.3 review's immediate outer-process issues: it removes direct normal-site startup for the outer P4/P5 launcher, introduces a tracked `-I -S` bootstrap, proposes a no-pyc exact staging import root, and upgrades source cleanliness to tracked+untracked full-clean. However, the complete process tree and output-freshness contracts are not yet closed.

## Findings

### HIGH — `torch.distributed.run` worker processes bypass the proposed hardened bootstrap

Design `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.4_2026-09-01.md:9-15` hardens the outer P4 launcher as:

`<lexical-venv-python> -I -S .../r09_b2_p4_bootstrap.py --mode=p4-train -- <torch.distributed.run argv>`

and then proposes `runpy.run_module("torch.distributed.run", run_name="__main__")` after bootstrap validation.

That only hardens the torchrun agent process. PyTorch 2.10's actual `torch.distributed.run.config_from_args()` constructs worker execution separately: when Python execution is enabled it chooses `cmd = os.getenv("PYTHON_EXEC", sys.executable)`, appends `-u`, optionally `-m`, then appends the training module/script. It does **not** propagate the outer `-I -S` flags or the root bootstrap. See upstream PyTorch `v2.10.0`, `torch/distributed/run.py:922-940`.

Therefore the frozen `--nproc-per-node=1` D005 still creates one worker whose effective command is equivalent to:

`<lexical-venv-python> -u -m cosmos_framework.scripts.train ...`

That worker re-enters normal `site`, the original venv site-packages and `.pth` startup surface, and it does not inherit the parent process's rewritten `sys.path`. The v0.4 statement that P4 and P5 both have no normal-site execution is therefore false for the actual training worker process.

**Required design fix:** freeze the complete worker-launch contract, not only the torchrun agent. Every training worker must itself enter the same reviewed bootstrap before any project/third-party import. The design may use an exact verifier-owned worker wrapper / `PYTHON_EXEC` contract, a `--no-python` executable wrapper, or another mechanism, but it must specify and machine-verify the exact generated worker argv, mode, interpreter flags, staging root, and rank environment. Add a permanent CPU test that derives/intercepts the PyTorch 2.10 worker command and proves no direct `python -u [-m] cosmos_framework...` worker is possible.

### HIGH — `PYTHONDONTWRITEBYTECODE=1` is ineffective under the frozen `-I` startup

Design `...design_v0.4_2026-09-01.md:25-29` relies on `PYTHONDONTWRITEBYTECODE=1` to guarantee that P4/P5 cannot create `__pycache__`/`.pyc` in the staging/source roots.

But Python isolated mode `-I` implies `-E`; all `PYTHON*` environment variables are ignored. Thus `PYTHONDONTWRITEBYTECODE` is not a valid bytecode-write control for the very interpreter mode frozen by this design. CPython's command-line contract explicitly states that `-I` implies `-E`, `-P`, and `-s`, and that all `PYTHON*` environment variables are ignored.

**Required design fix:** make bytecode suppression an interpreter/bootstrap property rather than an ignored environment variable. For example, freeze `-B` on every outer and worker interpreter invocation and/or set and assert `sys.dont_write_bytecode = True` in the stdlib bootstrap before any third-party/project import. The permanent test must execute the actual `-I -S` bootstrap shape, import a staged source module, and prove no pyc is created. This requirement must also hold for every torchrun worker after the previous HIGH is fixed.

### HIGH — P5 staging under the D005 production run root violates the frozen `fresh` output contract

Design `...design_v0.4_2026-09-01.md:19-29` says the shared bootstrap creates a fresh staging directory "位于 D005 run root" and P5 uses the same bootstrap model.

The frozen P4 verifier, `tools/g0/verify_r09_b2_p4_d005.py:202-222`, defines D005 freshness by requiring the derived production `run_root` not to exist at all (`return not expected.exists() and not tracked`). P5 static compose is not authorized to instantiate the future production run output tree.

If P5 creates its import staging under the D005 run root, it destroys the exact `fresh` condition before any future P4/B2-T execution and makes static compose mutate production-output state.

**Required design fix:** make staging roots mode-specific and provenance-bound. `p4-train` may derive a staging directory under the authorized training run root only when that training execution is separately approved. `p5-compose` must stage under its own P5 attempt/output staging root, outside the production root, D005 run root, evidence root and exporter root, and must leave the frozen production run root absent. Add a permanent negative proving P5 staging cannot create or descend from `outputs.run_root`.

### MEDIUM — hard-link staging is not an isolated payload snapshot

Design `...design_v0.4_2026-09-01.md:19-25` prefers stdlib hard-links and falls back to copies. A hard-linked staging file aliases the source inode; a later source/venv mutation also mutates the supposedly isolated staging payload after its manifest was checked. This weakens the stated purpose of staging as a frozen import snapshot.

**Required fix:** prefer copy-only materialization for executable/importable payload, or define an equivalent immutable-snapshot mechanism and prove source mutations cannot alter staged bytes after verification. A static regression should mutate the source after staging and prove the staged manifest/import bytes remain unchanged.

## Positive observations

- The v0.3 profile/source/getpath work remains useful and should be retained.
- P4 and P5 now share one intended bootstrap design rather than diverging at the outer process.
- The design correctly rejects local pyc/pycache, `.pth`, customize modules, symlinks and untracked import shadows from the staged runtime path.
- Production/submodule/VCS source cleanliness is now explicitly tracked+untracked full-clean.
- Old P4 v2 records and both consumed P5 attempts remain historical and are not proposed for retry.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted yet. A revised design must close the full torchrun worker process tree, use an effective bytecode-disable mechanism under `-I`, and preserve D005 production-output freshness during P5 compose. The hard-link isolation issue should also be resolved before implementation approval.

This review does **not** authorize:

- P4/P5 tooling implementation;
- creating or modifying a Gate venv;
- P4 static record regeneration;
- P5 export/retry/compose;
- `load_experiment_from_toml`;
- CUDA/GPU;
- torchrun/distributed initialization;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training, evaluation or inference;
- P5 closure;
- B2-T or any later Gate.
