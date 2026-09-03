# Independent Design Review — R09-B2 P4-v4 Log Namespace Binding v0.6

- Parent Gate: `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-STATIC-TOOLS`
- Requested design verdict: `APPROVE_TO_IMPLEMENT_P4_V4_LOG_NAMESPACE_BINDING_STATIC_SLICE`
- Design SHA under review: `b0e18260845025996331e825207261234ce34622`
- Ledger/request SHA observed at review start: `edfc6f8527e7d0e43cd77267b5c5e5c090e0d08f`
- Prior slice implementation SHA: `1ef7f4962346e4cdbdf3a179ef657eb59db09591`
- Prior ChatGPT review: `ab8d6e02e93225cc43eb501967fa7d5bae126cc7`
- Approved parent design: `b70cd294f4d9896cbe297d96535540b62cf43391`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved remote `V2` through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `edfc6f8527e7d0e43cd77267b5c5e5c090e0d08f`; it is the ledger/review-request commit and its parent is exactly design SHA `b0e18260845025996331e825207261234ce34622`.

`ab8d6e0 -> b0e1826` is one docs/status-only design commit: `SESSION.md`, `TODO.md`, and new `docs/build/PSM-WMA_R09_B2_P4_v4_log_namespace_binding_design_v0.6_2026-09-03.md`. No production P4/P5 tooling or Cosmos submodule code changed. The Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. GitHub exposes no check-runs for this design SHA; submitted `git diff --check` is repository-recorded evidence rather than independently rerun CI here.

## Verdict

`REQUEST_CHANGES`

The v0.6 direction is correct in one important respect: `validate_logs(logs, binding)` no longer accepts caller-selected namespace mappings, and the proposed module-private opaque verifier-issued binding directly addresses the prior identity-substitution defect. However, the current issuance dependency is temporally impossible for the preflight log use case and relies on a publication-authority validator that is not yet an actually closed implementation dependency.

## HIGH-1 — log-binding issuance depends on a post-preflight publication authority, creating a temporal cycle

**Design:** `docs/build/PSM-WMA_R09_B2_P4_v4_log_namespace_binding_design_v0.6_2026-09-03.md:7-9`

### Root cause

v0.6 proposes:

```text
issue_log_namespace_binding(final_request, planned_commitment, p5_publication_authority)
```

and says the factory first calls the already-closed final-request/planned/source/run/candidates validators and a `P5 publication-authority validator`; if any production authority is `None`, issuance fails.

That does solve caller substitution in principle, but it uses the wrong authority layer for the six P5 paths.

The approved v0.5 record/refreeze design defines `record_publication_authority_v1` with `payload_sha256`, where that payload digest is rederived from the six verified raw candidate payloads. Those six payloads only exist after the real P4 preflight has run and produced/verified the recurrent + TTT request/result/verification files.

The log namespace binding, by contrast, is required before the preflight child/process can be executed, because it is what authorizes where `stdout.log` and `stderr.log` may be created.

The dependency therefore becomes:

```text
issue log binding
  -> run preflight
  -> produce/verify six candidate payloads
  -> derive record/publication authority containing payload_sha256
  -> issue log binding
```

That cycle cannot be satisfied in a real execution sequence.

There is a second concrete dependency problem in the same paragraph: the repository currently has no closed implementation of the v0.5 `record_publication_authority_v1` / publication-authority validator. The parent static-tools Gate is explicitly still `REVIEW/IN_PROGRESS`, and current P5 code only has `AUTHORIZED_P4_V4_EVIDENCE=None` plus the later evidence verifier. The v0.6 design must not describe an unimplemented publication-authority validator as an already-closed prerequisite.

The phrase that the submodule root path must “equal the frozen Gitlink identity” also mixes two identity types. The path should be exactly `<source_root>/cosmos-framework`; the Gitlink is a separate 40-hex commit identity that must be cross-checked against the validated source binding/submodule revision, not compared to the path value.

### Required acceptance criteria

1. Keep the scope limited to the log-namespace binding slice; do not require implementation of record/refreeze/CAS to close this design.
2. Remove the dependency on any authority whose value requires post-preflight candidate payload bytes.
3. Freeze a **pre-execution P5 namespace identity** that is available before the preflight runs. Acceptable patterns include:
   - derive the six absolute evidence paths from a verifier-owned pre-execution evidence/root binding plus the already-fixed P4-v4 evidence relative paths/backend/file names; or
   - introduce a small pre-execution `p5_namespace_plan_v1` whose only job is to bind the evidence root/ref and exact six relative paths, with its own canonical digest and production default `None` until separately frozen.
   This pre-execution namespace plan must not contain or depend on candidate `payload_sha256`.
4. Later `record_publication_authority_v1` may independently bind the same six paths plus the verified payload digests/commit/tree/CAS data, but it must not be required to issue the preflight log binding.
5. Do not claim a validator is already closed unless it exists in the reviewed code. If the slice introduces a new pure validator for the pre-execution namespace plan, name it as new slice implementation and keep the parent record/refreeze/CAS Gate `IN_PROGRESS`.
6. Freeze the submodule binding with distinct types:
   - `submodule_root == source_root / "cosmos-framework"` as a path identity;
   - `gitlink == validated_source.gitlink` as a lowercase 40-hex commit identity;
   - when filesystem/Git verification is in scope, submodule HEAD/Gitlink are cross-checked separately.
7. The opaque binding should store/revalidate only identities available before execution: final-request raw SHA, planned raw SHA, validated source/run/candidate identities, and the pre-execution P5 namespace-plan digest/raw SHA. It must not require record payload SHA.
8. Permanent fixtures must prove:
   - binding can be issued in a test-local pre-execution state where no candidate payload exists yet;
   - source/submodule/run/candidate/P5 path substitutions with valid lexical paths are rejected;
   - wrong P5 namespace-plan digest/path set is rejected;
   - a post-preflight record/publication authority is not required for log binding issuance;
   - binding forge/copy/reuse/reset and production-None authority paths remain fail-closed.
9. Preserve production execution/record/publication authorities as `None`, and authorize no real filesystem/log/request/preflight/publication side effect in this static design/implementation slice.

## Accepted v0.6 direction

The following aspects are correct and should be retained:

- `validate_logs` consumes an opaque verifier-issued binding rather than caller namespace mappings/tuples/paths;
- public construction, mapping substitution, mutation/reset, copy/pickle, reuse and second issuance are intended to fail closed;
- source, submodule, ordered recurrent/TTT run roots, candidate root, and six P5 evidence paths are all intended to be verifier-derived;
- binding stores parent raw-SHA identities and revalidates them on consume;
- namespace-substitution fixtures remain mandatory;
- the parent exact-request/record-refreeze/CAS static-tools Gate remains `IN_PROGRESS`;
- production authorities remain `None` and no real execution is authorized.

## Scope

Do not approve `APPROVE_TO_IMPLEMENT_P4_V4_LOG_NAMESPACE_BINDING_STATIC_SLICE` at design SHA `b0e1826` yet. Revise only the pre-execution authority dependency described above; no expansion into real record/refreeze/CAS implementation is required.

This review authorizes no production exact-request generation, P4 preflight/staging/materialization/candidate/log creation, record/refreeze/evidence publication, P5 authority/export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory/LIBERO training.
