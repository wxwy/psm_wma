# ChatGPT Independent Review — R09-B2 P4-v4 Preflight Materialization Design v0.6

- Review target design: `988dcbaac2fe9a7e5f55054a1d4884763905e9a3`
- Formal request / ledger head: `66954bcf9ba19816e7fc79e9c8347f6f54cb582b`
- Previous ChatGPT review anchor: `8511bf0f4795404ecabc3c71a0569b3e47592c29`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS`

## Basis

1. The sole v0.5 blocker is closed: namespace authority is now established before every reservation precheck by an anchored component-by-component `openat` chain starting at `/`, using `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`, with `fstat` verification and FD-only continuation.
2. After namespace anchoring, direct-child absence checks are namespace-FD-relative and future descendant paths are not re-traversed by multi-component pathname. This removes the pathname precheck → namespace-open race identified in the prior review.
3. The child mutation contract remains anchored: every root/middle/leaf mkdir/open/fstat step is relative to an already verified parent FD, and subsequent mutation never re-resolves the namespace pathname.
4. The v0.5 capability contract remains frozen: real full-admission factory only, immutable admission data/private proof, single one-way consumption state, complete canonical request fixture, no simplified forged request authority.
5. The frozen fixture matrix is sufficient for the next implementation review: namespace lexical/acquisition/direct-child precheck, ancestor retarget race, forge/mutation/reset, six mkdir plus six post-create verification fault points, exact poison prefixes, ambient/subprocess/P5/child isolation, and public CLI hard-stop with zero helper invocation.
6. Compare from the prior ChatGPT review to formal request HEAD changes only design/status/Inbox documents; `9bc78f1` implementation was not modified while this remediation design was under review. Gitlink remains frozen.

## Implementation scope

Only:
- `tools/g0/r09_b2_p4_v4_execution_preflight.py`
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`

The implementation review must verify the exact v0.6 anchored namespace acquisition and FD lifetime/close behavior, capability construction/immutability, full precheck-before-mutation property, exact six-step mutation/verification order and poison prefixes, no cleanup/retry/reuse, and the complete fixture matrix.

This verdict does **not** authorize any real execution request, preflight/materialization, candidate/staging publication, P4 record/refreeze, P5 export/compose, GPU/CUDA/torchrun, model/data/checkpoint I/O, evaluation/inference/training, B2-T, or Local Memory training. Public `main()` must remain unconditional hard-stop.
