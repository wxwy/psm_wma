# R09-B2 P4 Interpreter Provenance design v1.2 review

- Request commit: `8bb0a5f204ba9e59a488ec464b796ae851318513`
- Request-declared design commit: `476a5dd19755b5c1945694161674a52141b4b6ae` (**does not resolve in repository**)
- Actual request parent / design commit reviewed: `476a5ddfa8beb89315234819e1e1a917ea227bc6`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v1.2_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

Design-only review. No implementation, P4 record regeneration, P5 export/compose/retry, torchrun/distributed execution, CUDA/GPU, model/data/weights access, training, evaluation, inference, P5 closure, or B2-T is authorized.

## Findings

### Previous v1.1 addendum blocker is closed at the design-content level

The actual v1.2 design at `476a5ddfa8beb89315234819e1e1a917ea227bc6` correctly separates parameterized native-load wrapper definitions from concrete runtime invocations:

- the verifier still builds the analysis universe from all approved staged Python payloads;
- an admitted wrapper definition may forward one explicit positional path parameter through a statically bounded wrapper chain without itself creating a native-load target;
- the verifier independently enumerates all invocations of each admitted wrapper and requires each invocation target to be literal or verifier-owned fixed-path;
- wrapper definitions, invocations, direct Python native-load records, ELF records, and native runtime allowlist remain candidate evidence only and must exactly match verifier-recomputed sets;
- alias/container/callback/reflection escapes, nonliteral invocation, cycles, multiple/unknown definitions, and incomplete invocation sets fail closed.

This directly addresses the prior false rejection of generic PyTorch wrappers such as `torch.classes.load_library(path) -> torch.ops.load_library(path) -> ctypes.CDLL(path)` without introducing a filename-specific PyTorch exemption.

No new design-content blocker was found in the submitted v1.2 delta.

### HIGH — the formal request binds a nonexistent design commit

`docs/collab/chatgpt/CODEX_INBOX.md` as committed by request `8bb0a5f204ba9e59a488ec464b796ae851318513` declares:

`design commit=476a5dd19755b5c1945694161674a52141b4b6ae`

That SHA does not resolve in `wxwy/psm_wma`.

The actual parent of the request commit, and the commit that adds the v1.2 design document, is:

`476a5ddfa8beb89315234819e1e1a917ea227bc6`

This is not a cosmetic issue under the current Gate provenance rules. A formal request must unambiguously bind the exact object being reviewed. Silently substituting the request's parent for a nonexistent declared SHA would weaken the same request/evidence identity discipline enforced throughout R09-B2.

Required fix:

- do not modify the approved v1.2 design content solely for this issue;
- submit a new request-only commit that names the exact design SHA `476a5ddfa8beb89315234819e1e1a917ea227bc6` and the same Gitlink `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`;
- the corrected request must not introduce additional design or implementation changes.

A corrected request-only submission can be reviewed narrowly against this blocker.

## Positive observations

- The wrapper definition/invocation split is the correct remedy for the v1.1 generic-wrapper false rejection.
- The design preserves all-staged-Python analysis and exact verifier-owned invocation-set equality rather than weakening provenance to runtime observation.
- Wrapper escape cases remain fail closed.
- The previously established parent-first staging, all-ELF closure, sanitized native-loader environment, direct lexical worker, verified-bytes loader, and out-of-band request-SHA contracts remain unchanged.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted because the formal request does not bind a valid design object.

Still unauthorized:

- root P4/P5 tooling implementation;
- Gate venv/source checkout creation or mutation;
- P4 static record regeneration/refreeze;
- P5 export/retry/compose or `load_experiment_from_toml`;
- torchrun/distributed execution;
- CUDA/GPU;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training/evaluation/inference;
- P5 closure;
- B2-T or later gates.
