# R09-B2 P4 Interpreter Provenance design v0.7 review

- Request commit: `8a1bbf578f146f86c768f9935e8403299c62c1a6`
- Design commit: `e4dbea68338b0fee9cf3a37af848e78bfc8ea04e`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.7_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

Design-only review. This review covers only the two remaining trust-boundary issues from ChatGPT v0.6 review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v06_4ca7f12_fa97814.md`: out-of-band request identity and the native-runtime/host-TCB boundary. It does not authorize implementation, P4 record regeneration, P5 compose/export, torchrun, GPU, model/data access, training, evaluation, inference, P5 closure, or B2-T.

## Previous blockers closed

### Request TOCTOU closed

v0.7 correctly moves the expected canonical request SHA out of the request body and into the frozen child argv. The loader reads the request bytes once, compares their SHA256 to that argv token before JSON parsing or bootstrap execution, and only then validates fields and bootstrap bytes. The verifier independently derives the same digest from verifier-owned request construction. This closes the prior same-path request replacement/self-declared-digest false-PASS class.

### Native layer is now explicitly declared as host TCB

v0.7 no longer silently treats the base executable SHA as sufficient proof for everything that executes before Python user code. It explicitly separates project/Python payload evidence from an execution-request `host_native_tcb` and records the child ELF, dynamic loader, resolved native dependencies, parent interpreter identity, and platform. This is the correct boundary direction.

## Finding

### HIGH — native-loader environment/injection state is not frozen, so the recorded dependency graph may not equal what executes

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.7_2026-09-01.md:20-32` freezes the dynamic loader path and a resolved native dependency list, but it does not freeze the loader-affecting environment that exists *before* the child Python process starts.

On Linux/glibc, variables such as `LD_PRELOAD`, `LD_AUDIT`, and `LD_LIBRARY_PATH` can inject extra native code or change dependency resolution before `-I -S -B -c <loader>` executes. Python isolated mode does not sanitize generic `LD_*` variables. A child can therefore execute native code that is absent from `resolved_native_dependencies` even while every recorded executable/library SHA remains unchanged.

The currently frozen P4 environment contract also does not contain fail-closed rules for these loader variables.

Required design fix:

1. Add a verifier-owned **native-loader environment grammar** to the host TCB / execution request.
2. At minimum, `LD_PRELOAD` and `LD_AUDIT` must be absent; no caller-controlled injection is allowed.
3. `LD_LIBRARY_PATH` must either be absent or frozen exactly and included in the dependency-resolution algorithm. Any other loader search/injection variable that affects the chosen native object set must be handled explicitly rather than inherited implicitly.
4. Parent preflight must derive/validate the resolved transitive native dependency closure under that exact frozen loader environment before spawning the child.
5. The child spawn must use exactly that sanitized/frozen environment, not the ambient parent environment.
6. Add permanent negatives where the executable/dependency files are unchanged but `LD_PRELOAD`, `LD_AUDIT`, or `LD_LIBRARY_PATH` is introduced/changed; rejection must occur before child/loader/bootstrap startup.

This does not require changing the v0.7 process-tree architecture. Keep the direct lexical `--no-python` worker, `-I -S -B -c` loader, out-of-band request digest, verified-bytes bootstrap, parent-bound Python installation manifest, and copy-only mode-specific staging.

## Positive observations

- Out-of-band request SHA is correctly independent of request contents.
- Loader verifies request bytes before parse and bootstrap side effects.
- Native/system code is explicitly separated from Gitlink/Python payload evidence rather than being silently trusted.
- The v0.6 direct lexical worker / verified bootstrap / copy-only staging architecture remains intact.
- Gitlink remains `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted yet.

Only the native-loader environment/injection grammar needs to be added; no architectural rollback is requested.

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
