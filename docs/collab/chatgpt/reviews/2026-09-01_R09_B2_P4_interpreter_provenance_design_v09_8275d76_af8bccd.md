# R09-B2 P4 Interpreter Provenance design v0.9 review

- Request commit: `8275d764f97b7a687a54028f96743df2bd817e82`
- Design commit: `af8bccde4307710c515818d7cd0f32452afb1482`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.9_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

Design-only review. This review checks the remediation of the single HIGH from ChatGPT v0.8 review. It does not authorize implementation, P4 record regeneration, P5 compose/export, torchrun/distributed execution, GPU, model/data access, training, evaluation, inference, P5 closure, or B2-T.

## Findings

### Previous v0.8 blocker closed

v0.9 correctly expands the native closure seed set from the child/base Python-only view to the union of all approved runtime ELF payloads:

- lexical/base interpreter ELF;
- all base `lib-dynload` ELF extensions;
- all registry/editable/VCS ELF/native executables that will be present in copy-only staging;
- explicitly invoked native executables.

It also preserves the v0.8 all-absent loader environment and requires `PT_INTERP` / `DT_NEEDED` / `RPATH` / `RUNPATH` / `$ORIGIN` resolution under that same sanitized environment. This is the correct direction and should be retained.

### HIGH — P4 staging creation order conflicts with pre-spawn native closure verification

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.9_2026-09-01.md`, section **完整 runtime native closure**, requires the parent TCB to resolve the native graph for every ELF in the **copy-only staging** and fail before child spawn if any path/SHA/resolution differs.

However, v0.9 explicitly says the existing staging contract is unchanged. The retained v0.5-v0.8 P4 staging contract says `p4-agent` creates `<D005 run_root>/import_staging/<run-token>` once, and `p4-worker` only consumes that already-created staging. Therefore, before the outer `p4-agent` child is spawned, the staging tree whose actual `$ORIGIN` / `RUNPATH` semantics v0.9 wants to verify does not yet exist.

This is not interchangeable with resolving the original source/venv ELF locations: copy-only staging changes the ELF's final directory, so `$ORIGIN`-relative dependency resolution can change even when the ELF bytes are identical.

Required fix: choose and freeze exactly one model.

1. **Preferred:** the trusted parent materializes and verifies the copy-only P4 staging before spawning the outer agent. The parent then resolves the native closure against the final staging paths and passes a readonly, manifest-bound staging root to both agent and worker. Update the inherited contract so `p4-agent` no longer creates staging itself.

or

2. Define a verifier-owned target-path simulation grammar that proves the exact future staging destination and resolves `$ORIGIN`/RPATH/RUNPATH against that destination before materialization, then requires the later copy to reproduce the exact seed manifest/path layout. This is more complex and must be explicit; implementation must not guess it.

Permanent negative: same ELF bytes, but move the staged ELF to a different target directory such that `$ORIGIN` resolves a different `.so`; the pre-spawn verifier must fail.

### MEDIUM — `native_runtime_allowlist` lacks a verifier-owned completeness/enforcement grammar

v0.9 says static-graph-external `dlopen`/driver/plugin loads must be in `native_runtime_allowlist`, and unlisted loads fail closed. The allowlist fields (`triggering approved component`, canonical path/SHA, purpose, loading mechanism) are useful, but the design does not yet define how the verifier proves that the allowlist is complete before spawn.

A manually supplied allowlist plus path/SHA equality is not sufficient: the same approved native/Python component could contain another runtime `dlopen` path that is omitted from the request and never enters the static `DT_NEEDED` graph.

Required design clarification before implementation:

- define the verifier-owned discovery/proof grammar for dynamic loads (for example, explicit approved loader sites/components and their deterministic path-construction rule);
- any component capable of non-deterministic/unbounded runtime native loading must fail closed rather than merely being absent from the allowlist;
- caller-provided allowlist entries are observations; expected trigger/path/mechanism must come from verifier-owned frozen source/config evidence;
- add a shared-forgery negative where request and allowlist both omit a second native-load trigger from an approved component; verifier must still fail.

This does not require introducing a runtime sandbox in this design Gate, but it does require a pre-spawn proof rule strong enough that `unlisted runtime dlopen -> FAIL` is machine-verifiable rather than declarative.

## Positive observations

- The all-ELF seed union closes the previous Python-centric native provenance gap.
- v0.8 sanitized loader environment remains intact.
- `$ORIGIN` / RPATH / RUNPATH are explicitly recognized as part of native resolution.
- CUDA/driver/plugin libraries are not automatically trusted merely because they are installed.
- The design continues to separate static implementation approval from P4/P5 execution authorization.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted yet.

The next design revision should keep the v0.9 all-ELF closure and fix only:

1. the P4 staging materialization / pre-spawn closure ordering; and
2. the verifier-owned completeness grammar for runtime-native allowlist entries.

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
