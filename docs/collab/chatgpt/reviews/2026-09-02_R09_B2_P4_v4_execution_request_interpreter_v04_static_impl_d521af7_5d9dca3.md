# R09-B2 P4-v4 Execution Request `interpreter` v0.4 static implementation review

## Verdict

`REQUEST_CHANGES`

Target:
- implementation: `d521af7e2974d86f83a8975dc432631c875714be`
- request: `5d9dca32ba34fc874febdc1e669e550c16c83f2a`
- approved design: `be6260348f35d8606d11709fc1748c2b63690293`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Accepted implementation

The v0.4 runtime-authority blocker is closed in code:
- `FROZEN_STDLIB_LOADER` consumes an explicit `host_git` argv slot and invokes that absolute path rather than bare `git`;
- `verified_loader_argv()` now requires `git_executable` and emits the 12th slot;
- `is_verified_loader_argv()` rejects the old 11-slot grammar;
- `validate_interpreter()` reconstructs the 12-slot argv using the already validated host Git path;
- source/bootstrap parent-side Git operations continue to use the validated absolute host Git.

No code blocker was found in that narrow remediation.

## HIGH — frozen v0.4 permanent fixture matrix is not implemented

The approved v0.4 design explicitly made the following CPU negatives part of the closure contract:
- lexical launcher / realpath / retarget drift;
- host Git ELF / closure / symlink / relative / PATH-shadow;
- root single-fd raw no-reopen and recursive dependency no-pathname-reopen;
- 12-slot mutations for reorder, `FROZEN_STDLIB_LOADER`, root, bootstrap relative/SHA, request SHA, host Git, old 11-slot, direct exporter / `-m`, extra/missing argv;
- each mutated request must recompute outer interpreter identity so the intended authority branch is actually exercised.

At `d521af7`, permanent tests cover only a subset:
- lexical `sha256` mutation;
- host closure SHA mutation;
- relative host Git path;
- one isolation-flag reorder;
- host root one-open/no-`Path.read_bytes`;
- the pre-existing positive lexical symlink identity and positive loader grammar.

Missing permanent negatives include at least:
1. `realpath` / `realpath_sha256` drift and lexical-path retarget to a different realpath;
2. host Git symlink rejection and ambient `PATH` shadow proving it is irrelevant;
3. recursive dependency no-pathname-reopen (not only the root Git object);
4. old 11-slot rejection as a targeted request mutation;
5. slot-12 `host_git_abs` drift;
6. `FROZEN_STDLIB_LOADER` source mutation;
7. root/bootstrap-relative/bootstrap-SHA/request-SHA mutations;
8. extra argv and direct exporter / `-m` request mutations under the v0.4 interpreter validator.

The closure request reports `33/33 PASS`, but test count alone does not satisfy the approved v0.4 fixture matrix.

### Required remediation

Static/CPU only:
- add the missing permanent fixtures above;
- recompute `identity_sha256` for every interpreter mutation before validation;
- ensure each fixture fails on the intended `lexical interpreter`, `host Git`, or `loader argv` branch rather than being intercepted by outer identity;
- retain existing 33 tests and prior source/entry regressions.

No real preflight, staging/materialization, record/refreeze, P5 export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized.
