# R09-B2 P4 Interpreter Provenance design v1.1 — ChatGPT addendum

- Request commit: `ff183a9f9691f3860133f038de255051dce8f0f9`
- Design commit: `538d414557af3890d2b45c8b19160aa6aa9f98c1`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.1_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

Design-only review. This addendum is the result of an independent re-review of v1.1 after a concurrent review write appeared on `V2`. It does not rely on the concurrent verdict and does not overwrite it. No implementation or runtime execution is authorized by this addendum.

## Previous v1.0 blockers closed

The v1.1 delta correctly closes the two v1.0 findings:

- `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.1_2026-09-01.md:7-9` expands Python analysis to every approved staged `*.py` payload, including registry wheels, and expands ELF analysis to `native_seed_union ∪ resolved_native_closure`.
- `...design_v1.1...md:13-23` gives explicit fail-closed rules for aliases, reassignment, dynamic targets, reflection, `eval`/`exec`/`__import__`, indirect ELF loading, `dlsym`, function pointers and unresolved target relationships.

These changes should be retained.

## HIGH — the all-file nonliteral-call rule rejects the frozen PyTorch 2.10 wheel by construction

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.1_2026-09-01.md:13-21` requires every staged Python file to be scanned and requires native-load targets to be literal or verifier-owned fixed rules. Parameterized wrapper definitions therefore fail even when they are never invoked by the frozen P4 entrypoint.

The frozen PyTorch 2.10 dependency contains exactly such wrappers:

- `torch/_ops.py`: `_Ops.load_library(self, path)` executes `ctypes.CDLL(path)` with a function parameter as the target.
- `torch/_classes.py`: `_Classes.load_library(self, path)` forwards the parameter to `torch.ops.load_library(path)`.

Because v1.1 now deliberately includes registry-wheel Python in the scan universe, a literal implementation of its detector must reject the canonical PyTorch wheel solely because these generic wrapper definitions exist. That makes the intended P4 `train+cu130` profile unable to pass interpreter provenance even when no frozen P4 callsite invokes those wrappers.

This is not an argument for weakening dynamic-target rejection. The missing contract is a distinction between a generic native-load **wrapper definition** and an actual **reachable invocation**.

### Required design fix

Keep the complete staged-Python universe, but introduce a verifier-owned wrapper-definition / invocation summary grammar. One acceptable direction:

1. Admit a parameterized wrapper definition only if its exact FQN, body/source-span SHA and native-load effect are verifier-owned and frozen.
2. Independently enumerate all invocations of each admitted wrapper in the approved runtime universe; every invocation target must resolve to a literal/verifier-owned fixed rule.
3. Reject unresolved escape/dispatch of wrapper objects: reflection, `getattr`, reassignment, star import, containers, decorators, callbacks, unknown aliases or other indirect invocation paths.
4. A parameterized wrapper invocation with non-deterministic target remains FAIL.
5. Request/allowlist/wrapper summaries are observations only; verifier recomputes definitions and invocations from frozen payloads and requires exact equality.
6. If a wrapper's invocation set cannot be proven complete, fail closed.

Equivalent designs are acceptable. Filename-specific suppression or blanket exceptions for PyTorch are not.

### Permanent CPU-only regressions

- generic wrapper definition + one fixed/literal invocation -> PASS only when wrapper summary and invocation record both match;
- same wrapper + dynamic/nonliteral invocation -> FAIL;
- wrapper object escapes through unresolved alias/container/callback/reflection -> FAIL;
- two fixed invocations while request/summary omits the second -> FAIL;
- canonical PyTorch-style `torch.classes.load_library(path) -> torch.ops.load_library(path) -> ctypes.CDLL(path)` chain must be handled through explicit wrapper/call proof rather than rejected solely because the wrapper definition parameter is nonliteral.

## Positive observations

- Registry-wheel Python is now part of the verifier-owned analysis universe.
- Transitive native-closure ELF objects are now included in native-load analysis.
- Parent-first staging, sanitized native-loader environment, direct lexical `--no-python` worker, out-of-band request SHA, verified-bytes loader, all-ELF native closure and copy-only staging remain sound design directions.
- The intended fail-closed posture for unresolved dynamic native loading should be preserved.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted by this review.

A v1.2 design should preserve v1.1's complete enumeration universe and fail-closed semantics while adding a verifier-owned generic-wrapper definition/invocation contract compatible with the actual frozen PyTorch 2.10 wheel.

Still unauthorized:

- root P4/P5 tooling implementation;
- creating/modifying any Gate venv or external source checkout;
- P4 static record regeneration/refreeze;
- P5 export/retry/compose or `load_experiment_from_toml`;
- torchrun/distributed execution;
- CUDA/GPU;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training/evaluation/inference;
- P5 closure;
- B2-T or later gates.
