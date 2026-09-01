# R09-B2 P4 Interpreter Provenance design v1.0 review

- Request commit: `5cf134ccdc14723007ac3adbec0b996ed4852f93`
- Design commit: `3be0f9076b6e3348140afce6171547cab44bf519`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.0_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

Design-only review. This review does not authorize implementation, P4 record regeneration, P5 export/compose/retry, torchrun/distributed execution, GPU/CUDA, model/data/weights access, training, evaluation, inference, P5 closure, B2-T, or any later Gate.

## Previous v0.9 blockers

The v1.0 design correctly closes the two blockers from ChatGPT review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v09_8275d76_af8bccd.md`:

1. **P4 staging order is now coherent.** `design_v1.0:7-9` moves final copy-only staging creation into the parent TCB before outer-agent spawn. Native closure is therefore resolved against the actual final staging layout, so `$ORIGIN`/`RPATH`/`RUNPATH` are evaluated against the path that runtime will consume. Agent/worker are readonly consumers.
2. **The dynamic-load allowlist is no longer caller-owned truth.** `design_v1.0:13-19` requires verifier-owned source/ELF site enumeration and explicitly rejects request+allowlist shared omission of a frozen second trigger.

These changes should be retained.

## HIGH — `native_load_contract` does not enumerate the complete runtime code universe

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.0_2026-09-01.md:15-17` is still incomplete in two independent ways.

### A. Python-site enumeration excludes registry-wheel Python payload

The design says the verifier enumerates Python native-load sites from the Gitlink tracked source plus staged **first-party/VCS** source manifests. It does not include staged Python files originating from registry wheels.

That is a false-PASS boundary because registry-wheel code is executable runtime code and can initiate native loads. The frozen training environment includes PyTorch as a wheel, and PyTorch 2.10 contains concrete Python native-load sites such as `torch/_ops.py` calling `ctypes.CDLL(path)` and distributed/CUDA helpers calling `ctypes.CDLL(...)`. If request/allowlist omit one of those sites, the current v1.0 grammar can still report a complete source-site set because those wheel `.py` files were never in the verifier enumeration universe.

Required fix:

- define the Python source universe as **all approved runtime Python source payload**, regardless of source type: first-party editable, registry wheel, and VCS;
- derive it from the same verifier-owned staging/source manifests already used for payload provenance;
- any executable `.py` payload excluded from native-load analysis must be explicitly proven unable to perform or reach a native-load mechanism, otherwise FAIL;
- add a permanent shared-forgery negative where a registry-wheel Python file contains a second `ctypes.CDLL`/`torch.ops.load_library` trigger and both request and allowlist omit it; verifier must still FAIL.

### B. ELF-site enumeration is limited to the original seed set, not the resolved closure

The design says the verifier checks each v0.9 **ELF seed** for `dlopen`/`dlmopen` family sites. But v0.9 also resolves a transitive native dependency closure. A dependency object in that closure can itself perform a runtime dynamic load even when the original seed does not.

If runtime `dlopen` outside the allowlist is meant to be fail-closed, the detector cannot stop at the seed set.

Required fix:

- scan every verifier-owned ELF object whose runtime native-load behavior is claimed to be constrained: at minimum `seed ∪ resolved_native_closure`;
- alternatively, if a class of closure objects is deliberately treated as opaque host TCB, state that exact class explicitly and do not claim its runtime loads are covered by `native_runtime_allowlist`;
- add a negative where the seed has no loader symbol, a transitive dependency has an extra loader site, and request+allowlist omit it; verifier must FAIL.

## MEDIUM — the loader-site detector needs an exact reject grammar, not only an example API list

`design_v1.0:15-16` lists `ctypes.CDLL/PyDLL`, `torch.ops.load_library`, `torch.utils.cpp_extension.load`, `dlopen` wrappers, and ELF `dlopen/dlmopen` symbols, but implementation cannot infer “etc.” safely.

The design should freeze a verifier-owned detection grammar and fail closed on unsupported indirection, including aliases/wrappers/function-pointer or `dlsym`-style construction where completeness cannot be proven. This is especially important because general-purpose libraries such as PyTorch expose path-parameterized loading APIs; if the canonical profile cannot satisfy the static grammar, the Gate should fail explicitly rather than silently skip those sites.

## Positive observations

- Parent-first final staging is the correct fix for `$ORIGIN` path dependence.
- The source-span / ELF-callsite evidence direction is appropriate.
- The explicit shared-omission negative is consistent with the project’s peer-equality-is-not-truth rule.
- v0.8 sanitized native-loader environment and v0.9 all-ELF seed union remain appropriate and should not be rolled back.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted yet.

The next design does not need another architecture rewrite. Preserve v1.0 parent-first staging and verifier-owned allowlist derivation, and close only the enumeration-universe issue:

1. all staged Python source types, including registry wheels;
2. all relevant ELF objects in the resolved native runtime closure;
3. exact fail-closed loader-site detection grammar.

Still unauthorized:

- root P4/P5 tooling implementation;
- Gate venv/source modification;
- P4 static record regeneration;
- P5 export/retry/compose or `load_experiment_from_toml`;
- torchrun/distributed execution;
- CUDA/GPU;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training/evaluation/inference;
- P5 closure;
- B2-T or later Gate.
