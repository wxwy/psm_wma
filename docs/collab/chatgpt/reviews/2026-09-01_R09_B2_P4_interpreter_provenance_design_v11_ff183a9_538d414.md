# R09-B2 P4 Interpreter Provenance design v1.1 review

- Request commit: `ff183a9f9691f3860133f038de255051dce8f0f9`
- Design commit: `538d414557af3890d2b45c8b19160aa6aa9f98c1`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.1_2026-09-01.md`
- Verdict: **APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE**

## Scope

Design-only review. This approval authorizes only the root-owned P4/P5 interpreter-provenance tooling and standard-library CPU tests described by the v1.1 design. It does not authorize P4 record regeneration, P5 export/compose/retry, torchrun/distributed execution, CUDA/GPU, model/data/weights access, training, evaluation, inference, P5 closure, or B2-T.

## Findings

### Previous v1.0 blockers closed

1. **All staged Python payload is now in the verifier-owned analysis universe.**

   `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.1_2026-09-01.md:5-8` requires fail-closed AST analysis over every approved staged `*.py` regular payload across first-party editable, registry-wheel, and VCS sources. This closes the v1.0 false-PASS where a registry-wheel Python file such as PyTorch could contain a second native-load trigger omitted by both request and allowlist.

2. **Native-load analysis now covers transitive closure ELF objects, not only initial seeds.**

   `...design_v1.1...md:9` changes the ELF universe to `native_seed_union ∪ resolved_native_closure`. A loader site in a transitive dependency therefore participates in the expected verifier-owned set and cannot be omitted by request-side shared forgery.

3. **The detector grammar is now explicit and fail-closed.**

   `...design_v1.1...md:11-24` enumerates the approved Python call forms, accepted alias/path grammar, and explicit rejection classes (`getattr`, reassignment, star import, wrappers/function-pointer forwarding, non-literal targets, `eval`/`exec`/`__import__`, and unresolved aliases). The ELF side likewise requires one-to-one fixed target records and rejects `dlsym`, function pointers, computed strings, unmatched loader imports/strings, and unresolved target relationships.

   The important security property is that request-side `native_runtime_allowlist` is not authoritative: the verifier independently derives the complete expected record set from the frozen staged Python/ELF universe and requires exact equality.

### Existing architecture remains coherent

The v1.1 changes preserve the previously reviewed contracts:

- lexical venv launcher distinct from base interpreter;
- `train` extra + `cu130` install profile;
- verifier-owned editable/registry/VCS source provenance;
- `-I -S -B -c` verified-bytes loader;
- out-of-band request SHA in argv;
- direct lexical `torch.distributed.run --no-python` worker path;
- parent-bound Python-install and host-native TCB;
- all-absent/sanitized native-loader environment;
- parent-first copy-only final P4 staging and isolated P5 attempt staging;
- all-ELF native dependency closure and explicit dynamic-native-load contract.

No new design-level false-PASS path was found in the submitted v1.1 delta.

## Implementation caveat / required review focus

The v1.1 detector is intentionally conservative. The implementation may discover that the frozen CPython/PyTorch profile contains generic dynamic-loading machinery that cannot satisfy this static grammar. That outcome must remain **FAIL/BLOCKED**, not be solved by silently weakening the grammar, adding repr/runtime-observed fallbacks, or caller-owned allowlists.

The implementation review must therefore verify permanent negatives for at least:

- registry-wheel Python second-trigger shared forgery;
- transitive-ELF second loader-site omission;
- indirect/non-literal/unknown Python native-load construction;
- `dlsym`/function-pointer/computed ELF loader target;
- exact expected-set equality vs request allowlist;
- existing request/bootstrap/native-loader/staging provenance negatives from v0.x/v1.0.

## Gate decision

**APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE**.

Authorized narrowly:

- add/modify root-owned loader/bootstrap and P4/P5 verifier/exporter support required by the approved interpreter-provenance design;
- add/modify root-only standard-library CPU tests and mocks for the approved contract;
- no submodule changes;
- no actual Gate venv/source checkout creation or mutation;
- no P4/P5 execution.

Still unauthorized:

- P4 static record regeneration/refreeze;
- P5 export/retry/compose or `load_experiment_from_toml`;
- torchrun/distributed execution;
- CUDA/GPU;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training/evaluation/inference;
- P5 closure;
- B2-T or later gates.
