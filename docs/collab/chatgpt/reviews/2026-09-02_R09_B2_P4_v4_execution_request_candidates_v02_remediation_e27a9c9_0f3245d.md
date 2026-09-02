# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request `candidates` v0.2 Remediation Closure

- Review date: 2026-09-02
- Approved design: `f8a7231b76fe04e3a570dc2e432da8e018008cd5`
- Base implementation: `28b378c8861a2994fa6ae2f18b61d5ce8d909b8a`
- Remediation under review: `e27a9c9607f2a88d165b3fa79d77a9311b8f9c57`
- Request / ledger HEAD: `0f3245d3e16259cad259d25740eeed681eb0482b`
- Previous ChatGPT review: `60cdf44466f781610ff1e80bac529c5566d2f6e8`
- Gitlink at request HEAD: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_CANDIDATES_STATIC_TOOLS`

## Independent findings

The prior review accepted the main `validate_candidates()` contract and left only the frozen permanent CPU fixture matrix incomplete. The remediation is appropriately narrow: tests plus a minimal fail-closed type guard for a retyped `attempt_id` exposed by the new fixture.

The previously missing frozen branches are now materially covered:

1. outer `candidates` exact schema includes explicit missing and retyped cases in addition to extra/digest drift;
2. candidate namespace root has candidate-specific relative, dot, dotdot, repeated-separator, and double-leading-separator failures;
3. derived backend candidate leaf has the same candidate-specific lexical grammar failures;
4. a valid existing candidate namespace root with a symlink at the derived attempt prefix is explicitly rejected, proving the leaf reuses the existing-ancestor symlink rule rather than relying on the root-only test;
5. attempt grammar now covers uppercase, non-hex, short, and long values, and both run-token equality cases remain covered;
6. ambient-environment independence and no-future-root-creation positive behavior remain covered;
7. source/submodule/two-run-root bidirectional overlap, backend label/run binding, root/leaf mapping, inner/outer identity, and pair reuse coverage remain intact.

The only production-code change is the explicit `isinstance(attempt_id, str)` guard before the SHA-256 regex, which is a fail-closed correction required to make the frozen retyped fixture produce a contract `ValueError` rather than a type exception. No execution/materialization semantics were added.

I found no new validator-level blocker and no scope drift between the previous review anchor and the request HEAD. The request HEAD remains on the frozen Gitlink.

## Gate boundary

This verdict closes only the `candidates` static parser/validator and permanent stdlib CPU fixture section. It does **not** authorize candidate creation/materialization, run-root or staging creation, real P4 preflight, record/refreeze/evidence publication, P5 authority/export/compose, subprocess project execution, torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.

After this closure, the Execution Request nested-section status is 7/8 static sections closed; `backends` remains pending.
