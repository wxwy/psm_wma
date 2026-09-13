# ChatGPT Review — Authority-root Launcher v0.8 Remediation Static Witness Closure

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `145f0d4af0b75165569e7b241841cd078e8359dd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The exact `cosmos-framework` entry at the formal root independently resolves to the stated child/Gitlink, and the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior reviewed `5ff4df58cc8e17644aab945de3de6d74b8b2967c / 93a89ba61306d840a008813f62f26a34d54850f4` pair. The child/runtime remains unchanged. The effective remediation delta is root-only: the v0.8 launcher fail-closes the add→owner gap, one new direct temporary native-Git witness covers Git-valid foreign replacement before first ownership bind, and the v0.8 annex/request/task records are updated consistently.

The formal request still asks only for `APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_WITNESS_CLOSURE`. It does **not** request materialization approval.

## Authority chain and prior blocker

The review applies the inherited v0.2/v0.3 frozen runtime bytes/FD ABI/tool identities, v0.4 launcher mutation/cleanup semantics, the v0.7/v0.8 static-witness requirements, and the exact prior ChatGPT review for `5ff4df5... / 93a89ba...`.

The prior sole HIGH required either (a) a CLEAN owner identity causally attributable to the exact `worktree add`, or (b), if that continuity could not be proved, terminal `ROLLBACK_INCOMPLETE` before treating CLEAN as owned or creating backing files; it also required a direct temporary-native-Git successful-add → Git-valid replacement-before-first-bind witness proving the replacement is neither accepted nor removed.

## Prior HIGH disposition — CLOSED

The remediation satisfies the second permitted acceptance path rather than claiming an identity proof that native Git does not provide.

1. `add_and_capture()` executes the exact native `worktree add` seam and, after a successful return, unconditionally raises `Stop("ROLLBACK_INCOMPLETE")`. It no longer calls `capture_owned()` after the mutation and therefore accepts no post-add pathname as owner authority.
2. In `main()`, assignment to `owned` never completes on that path. Consequently `assert_worktree()`, backing-file `handoff()`, FD handoff, and `execve()` are unreachable, and the exception handler does not call `cleanup()` because `owned` was never established. This preserves the rule that an unproven/foreign CLEAN must not be force-removed.
3. The new direct witness injects the exact missing race class against `P.add_and_capture(snapshot)`: after a real successful temporary native-Git `worktree add`, the original CLEAN is renamed and a copied replacement is installed at the same pathname before `add_and_capture()` regains control. The witness verifies the replacement is Git-valid enough to resolve the expected `HEAD`, then requires terminal `ROLLBACK_INCOMPLETE` and proves the replacement still exists with its `.git` authority.
4. The annex/request accurately describe this as a fail-closed static launcher. They explicitly state that a later, separately authorized execution design must retain causal creation identity during the mutation before any successful execution path can be enabled.

This closes the exact prior blocker without weakening its safety condition. The launcher is intentionally non-progressing after native add in this static snapshot; that is acceptable only because the requested verdict is PREPARE/static-witness closure, not execution or materialization authorization.

## Evidence scope

The formal request reports `py_compile`, `12/12` temporary CPU/native-Git witness PASS, payload bytes/SHA freeze, and `git diff --check` PASS. The remediation diff contains the required 12th causal replacement-before-first-bind witness and is consistent with the prior 11-case suite reviewed on the immediately preceding pair.

No new child/runtime production blocker is introduced by this root-only remediation.

## Final verdict

`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_WITNESS_CLOSURE`

This verdict binds only exact pair `145f0d4af0b75165569e7b241841cd078e8359dd / 93a89ba61306d840a008813f62f26a34d54850f4`.

**Scope boundary:** this approval closes only the docs/static-witness preparation gate. It does **not** authorize real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication/root audit, child/runtime edits, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1. A later execution-capable design must establish causal add-created owner identity and must return for fresh exact-pair review before any materialization authority can be granted.
