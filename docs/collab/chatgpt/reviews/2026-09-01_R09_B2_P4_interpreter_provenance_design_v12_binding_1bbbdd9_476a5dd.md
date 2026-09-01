# R09-B2 P4 Interpreter Provenance design v1.2 binding review

- Request commit: `1bbbdd94b6809304cfa4b3f8e42eedfd8a0b3d8b`
- Design commit: `476a5ddfa8beb89315234819e1e1a917ea227bc6`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.2_2026-09-01.md`
- Verdict: **APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE**

## Scope

This is a design/binding-only review. It reviews the request-only correction submitted after ChatGPT review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v12_8bb0a5f_476a5dd.md`. It does not authorize P4 record regeneration, P5 export/compose/retry, torchrun/distributed execution, CUDA/GPU, model/data/weights access, training, evaluation, inference, P5 closure, or B2-T.

## Findings

### Previous blocker closed — request now binds the real design Git object

The prior request `8bb0a5f204ba9e59a488ec464b796ae851318513` named non-existent design SHA `476a5dd19755b5c1945694161674a52141b4b6ae`, so ChatGPT correctly refused to infer the intended design commit from the parent relationship.

The new request `1bbbdd94b6809304cfa4b3f8e42eedfd8a0b3d8b` explicitly corrects the binding to:

`476a5ddfa8beb89315234819e1e1a917ea227bc6`

That object exists, is the actual v1.2 design commit, and contains `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.2_2026-09-01.md`. The request also preserves Gitlink `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb` and explicitly states that it changes only the request binding, not the design or requested authority.

### v1.2 design content remains accepted

The v1.2 design closes the prior generic-wrapper blocker by separating:

- verifier-owned wrapper **definition summaries** from concrete native-load events;
- verifier-owned enumeration of **all invocations** of admitted wrappers;
- full wrapper-chain expansion to the approved underlying native-load API;
- fixed/literal target requirements at actual invocations rather than at unused parameterized wrapper definitions.

This allows generic definitions such as `torch.classes.load_library(path) -> torch.ops.load_library(path) -> ctypes.CDLL(path)` to exist without being mistaken for a runtime load, while still requiring every real invocation to be independently found and proven by the verifier.

The design continues to reject wrapper alias/container/callback/reflection/return/decorator escapes, non-literal invocation targets, cycles/multiple definitions, incomplete invocation sets, shared-forgery omission, registry-wheel second triggers, and transitive-ELF second loader sites.

### Positive observations

- The correction is request-only and does not mutate the approved v1.2 design content.
- The corrected SHA is a concrete existing Git object rather than an inferred parent.
- Gitlink remains unchanged at the frozen Cosmos revision.
- The requested authority remains narrow: root-owned interpreter-provenance tooling and standard-library CPU tests only.

## Gate decision

**APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE**.

Authorized narrowly:

- implement the approved v1.2 interpreter-provenance contract in root-owned P4/P5 tooling;
- add/modify root-owned loader/bootstrap/verifier/exporter support required by that contract;
- add/modify root-only standard-library CPU tests and mocks;
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
- B2-T or any later gate.
