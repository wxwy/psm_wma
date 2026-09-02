# R09-B2 P4-v4 Execution Request `interpreter` v0.4 static closure review

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_INTERPRETER_STATIC_TOOLS`

Target:
- implementation/remediation: `6a036649518295c07571e510954167f1bb1c84fc`
- request ledger: `cc21241b377e28cc1912fbb53b61a133db2b6a84`
- approved v0.4 design: `be6260348f35d8606d11709fc1748c2b63690293`
- prior ChatGPT review: `e765a56483d8cd06a7b5b38248dd08ec2aa3a7d0`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Closure of the final two blockers

### 1. Lexical launcher real retarget fixture — CLOSED

The permanent fixture now creates a lexical launcher symlink pointing to `base-A`, freezes the four-field lexical identity, then actually replaces the symlink target with `base-B` and requires `validate_interpreter()` to fail with `lexical interpreter differs`.

This exercises the real `path -> different realpath` condition rather than merely mutating the recorded `realpath` field. Because `base-A` and `base-B` are byte-identical copies, the fixture specifically proves that the frozen realpath identity is enforced independently of payload-byte equality.

### 2. Recursive host-Git ELF dependency no-pathname-reopen fixture — CLOSED

The host-Git closure now canonicalizes dependency scheduling and defers each dependency read until its single processing point. The new permanent fixture:
- patches `Path.read_bytes()` to fail on any pathname reopen;
- wraps `_read_canonical_regular_nofollow()` and records the exact raw bytes bound to each canonical dependency;
- wraps `parse_elf_dynamic_raw()` and asserts the parser consumes exactly those bound raw bytes;
- verifies every canonical dependency is read at most once.

This closes the final recursive-closure TOCTOU/test gap while preserving the root-object single-fd binding already accepted in prior review.

## Previously accepted v0.4 authority remains intact

No new regression was found in the narrow remediation. The closed interpreter contract still has:
- exact four-field lexical interpreter identity;
- validated absolute host Git, single-fd root ELF bytes and bytes-derived recursive closure;
- source/bootstrap Git operations routed through validated host Git rather than ambient `PATH`;
- the unique 12-slot verified-loader grammar with `host_git_abs` as the final slot;
- child `FROZEN_STDLIB_LOADER` invoking only that bound executable;
- old 11-slot, direct exporter, `-m`, missing/reordered/extra argv and bound-field drift permanently rejected;
- request SHA checked against actual request bytes before loader argv construction;
- existing request/source/entry hard-stop regressions retained.

Reported static evidence is 37/37 CPU PASS plus `py_compile` and `git diff --check` PASS. This review does not treat count alone as closure evidence; the previously missing frozen fixtures are now concretely present.

## Scope

This closes only `interpreter` static parser/validator/provenance tooling and stdlib CPU fixtures.

Still NOT authorized:
- real P4-v4 preflight execution;
- staging/materialization/candidate generation;
- record/refreeze/evidence publication;
- P5 authority population/export/compose;
- torchrun/GPU/CUDA;
- model/data/checkpoint I/O;
- training/eval/inference;
- B2-T or Local Memory training.

Next allowed step is the next separately reviewed Execution Request section / static design work. Any real execution remains independently gated.
