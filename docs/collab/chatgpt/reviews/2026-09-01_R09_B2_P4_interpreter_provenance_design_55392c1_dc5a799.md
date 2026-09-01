# R09-B2 P4 interpreter-provenance design review

- Request commit: `55392c1262a21320b1a14a0c95605ed72b461753`
- Design commit: `dc5a7994a2ebaa2d7bd488d9a09b954b0b69e93d`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.1_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

This is a design-only review of the P4 interpreter-provenance remediation. It does not authorize implementation, P4 record regeneration, P5 compose/export, CUDA/GPU, torchrun, model/data access, training, evaluation, inference, P5 closure, or B2-T.

The diagnosed root cause is valid. The current P4 verifier resolves `<production-root>/cosmos-framework/.venv/bin/python` before constructing/validating `command.argv[0]` and the interpreter asset, thereby collapsing the venv launcher identity into the underlying uv base Python. The proposed separation of lexical venv launcher and base executable identity is therefore necessary.

## Findings

### HIGH — distribution provenance is both under-bound and not independently grounded

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.1_2026-09-01.md`, section `新的 P4 interpreter schema`, constraint 5.

The proposed distribution manifest records package name, version and `.dist-info/METADATA` SHA256 for `pydantic`, `pydantic-core`, `hydra-core`, `omegaconf`, `torch` and a dependency closure. That is insufficient as an executable-package provenance boundary.

1. `METADATA` does not bind the Python/native files that will actually be imported. Package code can change while its METADATA stays byte-identical. A modified `pydantic/__init__.py`, extension module, or dependency file could therefore pass the proposed verifier.
2. The design says the verifier reconstructs the manifest from the current venv, but does not define an independent verifier-owned source for the expected package set/versions. A changed venv plus a newly generated matching P4 record can therefore self-consistently PASS. This is the same class of false-PASS as caller-owned provenance / peer equality.
3. `Requires-Dist` closure from the same installed METADATA cannot be the authority for what the closure is: changing the installed metadata can change both the claimed dependency graph and the observed manifest together.

Required design change:

- bind the environment to an independent tracked source at the frozen Cosmos Gitlink, preferably the tracked `uv.lock` (and the relevant `pyproject.toml` group/marker resolution) or an explicit verifier-owned expected manifest/digest derived and frozen from that tracked source;
- define the exact platform/Python/group resolution used for the expected package versions (`CPython 3.13`, Linux/x86_64, and the exact dependency groups/extras relevant to this D005 environment);
- separately bind installed distribution **payload identity**, not only METADATA. A sufficient design is to bind `.dist-info/RECORD` plus verify every hashed installed file named by RECORD, or deterministically hash the complete importable payload for every accepted distribution. Missing/unhashed executable payload entries must fail closed unless explicitly justified and separately bound;
- keep the observed package manifest in the P4 record as evidence, but the verifier must compare it to independently derived/frozen expected truth rather than accepting the current venv as truth.

### HIGH — the proposed child "pre-import" checks occur after Python startup code may already have executed

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.1_2026-09-01.md`, section `P5 的受控消费与 import 前断言`.

Launching the lexical venv interpreter normally initializes Python `site` before `_child()` can run. During that startup, venv/system site-packages can process `.pth` files, and `sitecustomize` / potentially user-site customization can execute Python code before the proposed `sys.executable`, `sys.prefix`, manifest, `sys.path`, Hydra, or Cosmos checks run.

The current design binds selected distributions and `pyvenv.cfg`, but it does not bind or reject this earlier startup surface. Therefore an unbound `.pth` file or `sitecustomize.py` can execute before the claimed trust boundary and still leave all later checks apparently valid.

Required design change:

Choose and freeze one explicit strategy before implementation:

1. **No-startup-code strategy:** launch the P5 child in a mode that suppresses normal site processing (for example a reviewed `-S` bootstrap), verify lexical launcher/base/cfg/package payloads with stdlib only, then add only the exact approved site-packages path without processing arbitrary `.pth` files before importing Hydra/Pydantic/Cosmos. Account explicitly for Python 3.13 venv `sys.prefix` semantics under that mode; do not assume the current prefix assertions remain valid.

or

2. **Fully-bound normal-site strategy:** keep normal venv startup, but independently bind/reject every startup-active artifact before execution authorization: require `include-system-site-packages = false`; define user-site behavior; enumerate and hash/reject every `.pth` file; reject or bind `sitecustomize.py`/`usercustomize.py`; and ensure no external site-packages directory can participate anywhere in `sys.path`, not merely at a higher priority than the venv path.

Whichever strategy is chosen must have permanent CPU negatives for `.pth` startup injection, `sitecustomize`, system-site enablement, and an unexpected external site-packages path.

### MEDIUM — `sys.path` grammar is underspecified

The design currently says an unapproved higher-priority site-packages path must fail. This leaves lower-priority external site-packages ambiguous and is not an exact grammar.

Required:

- specify the complete allowed path classes/order for the child before project imports: exporter script/bootstrap source as applicable, exact production `PYTHONPATH`, exact stdlib/base dynamic-library paths, and exact bound venv site-packages;
- any other site-packages path, regardless of priority, must fail unless explicitly frozen;
- define duplicate/symlink-equivalent path handling and canonicalization.

## Positive observations

- Separating lexical launcher identity from the resolved base executable directly addresses the observed venv de-virtualization bug.
- Requiring `command.argv[0] == lexical_path` is the correct launch semantic; `realpath` should remain provenance only.
- Binding launcher file type and raw symlink payload is materially stronger than hashing only the resolved target.
- Binding `pyvenv.cfg` and checking venv prefix/base-prefix separation is appropriate once the startup strategy is made explicit.
- Preserving old P4 v2 records and consumed P5 attempts as immutable history, while requiring a new schema/new records/new request hashes/new output path, is correct.
- The implementation boundary is appropriately root-tool/CPU-static only and does not authorize runtime work.

## Gate decision

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is **not granted**.

Revise the design to close both executable-package provenance and pre-guard Python startup-code trust boundaries. After that, resubmit a design-only request. No implementation or record regeneration is authorized by this review.

Still not authorized: P4 record refreeze, P5 export/retry/compose, `load_experiment_from_toml`, CUDA/GPU, torchrun, model/dataloader/optimizer/checkpoint construction, weights/data/MP4 access, training, evaluation, inference, P5 closure, or B2-T.