# ChatGPT Review — Stage-1 v1.7 request-instance design v0.3

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Formal root: `0fc7965d9d1b55a99d0b1a384764f68464b02949`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.3.md:20)`

## Blockers

- Design/Authority: **1 HIGH**
- Production/Authority: 0
- Evidence/Scope: 0
- child/runtime: 0

## Closed from v0.2

1. The previous construction-time I/O authority ambiguity remains closed: construction is limited to an explicit zero-mutation read-only allowlist.
2. The DS finding on the wrong remote-ref query is substantively fixed: v0.3 permits exactly two remote queries, one for advertised `V2` identity and one for `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` remote absence.
3. The fixed authority-ref remote observation is explicitly distinguished from local fixed-ref absence, and both observations are required in the future canonical request.
4. Frozen dependencies remain exact: formal parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`; launcher base `af19a9eb66ecaf8bd0b92a48ab1867f105026658 / 8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd / 18966`; closed replay root `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`; parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`; outer `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`.
5. The design remains construction-only: one future docs-only exact request, then an independent same-pair three-party request review before any Stage-1 attempt can be granted. v1.6 remains consumed/non-reusable.
6. Formal Gitlink resolves exactly to reachable child `93a89ba...`; no child/runtime production bytes changed.

## Remaining HIGH — empty stdout is not sufficient remote-absence authority

At v0.3 line 20, the design makes

`git ls-remote origin refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`

an authority-producing observation and says its empty output establishes remote fixed-ref absence. But the design binds only the command and raw output bytes/length/SHA; it does not require or bind a successful command result.

`git ls-remote` can produce empty stdout when the query itself fails (for example transport, DNS, authentication, or remote-access failure). Such a failure is not proof that the ref is absent. Treating empty stdout alone as `remote_ref=absent` would convert an observation failure into positive absence authority.

## Exact remediation

1. Keep the two-query closed network allowlist and all existing zero-mutation boundaries.
2. Require **both** remote queries to complete successfully (`return code == 0`) before their stdout may be used as authority, and bind the return code into the future canonical request.
3. For the fixed authority ref, define remote absence as exactly: successful exact query + zero stdout bytes/zero result lines. Any nonzero exit, timeout, transport/auth error, malformed response, or nonempty stdout must fail-close as `BLOCKED_AUTHORITY_NOT_CLOSED` and must not be interpreted as absence.
4. Prefer binding stderr bytes/length/SHA as well (or explicitly require empty stderr if that is the chosen frozen contract) so the request can independently distinguish success from transport diagnostics.
5. Preserve all other v0.3 constraints: exact formal/base/replay identities, local fixed-ref absence, designated path absences, fixed two output files, no source/checkpoint/manifest/data/cache/runtime I/O, no mutation/materialization, and independent exact request review before execution authority.

This verdict authorizes only docs-only remediation of the design. It does **not** authorize request construction, Stage-1 retry/materialization, launcher execution, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
