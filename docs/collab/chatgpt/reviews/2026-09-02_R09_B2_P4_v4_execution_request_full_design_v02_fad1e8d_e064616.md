# ChatGPT independent review — R09-B2 P4-v4 Execution Request FULL admission v0.2

- Design: `fad1e8d6959fcfee76129e04dc213e7fd6ea49f1`
- Formal request: `e0646166160c2566b4e8946252ac5f9d45df5911`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Prior review anchor: `5493b5f232ba6d39f62339ebe0ce59ca35557c2a`

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_FULL_STATIC_TOOLS`

## Findings

The two v0.1 design blockers are closed without reopening any previously closed nested section contract.

1. **Source-root binding is now implementable without changing `validate_source`.** The v0.2 design explicitly keeps `validate_source(request["source"], request["entry"], git_path)` and its return value unchanged. After successful source validation, the full layer constructs exactly one `source_root = Path(request["source"]["root"])` from the same parsed canonical source value and passes that object only to `validate_authorities_pair`. This correctly replaces the impossible cross-function source-root object-identity requirement with canonical-value binding.
2. **Host Git identity reuse remains exact.** The `git_path` returned by `validate_host_git` is required to be the same `Path` object passed to source, interpreter, and authorities in the same invocation. This is compatible with the existing closed validator interfaces.
3. **Subprocess scope is corrected.** The v0.2 fixture contract no longer incorrectly forbids subprocess used by the already-closed source validator or fixed historical authority lookup. It freezes the actual requirement: the FULL orchestration layer introduces no new subprocess/bare-Git/PATH/which/P5/child/torchrun path.
4. **Environment authority remains unique.** FULL admission routes environment-D005 projection only through `validate_authorities_pair`; it must not call the legacy `validate_environment_pair` or `verify_d005_pair`, and it must not introduce a second environment/P3 allowlist.
5. **Execution remains hard-stopped.** Successful admission returns only the validated in-memory request. The existing single-fd request SHA binding and unconditional `RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")` in `main()` remain mandatory. This approval does not authorize creation/materialization, real preflight, record/refreeze, evidence publication, P5 export/compose, GPU, B2-T, or Local Memory training.

## Implementation acceptance focus

Implementation review should verify the exact validator order, same-object `git_path` forwarding, one-time `source_root` construction after successful source validation, authorities-only environment binding, absence of new FULL-layer subprocess paths, request immutability/no future-root creation, and permanent hard-stop fixtures.
