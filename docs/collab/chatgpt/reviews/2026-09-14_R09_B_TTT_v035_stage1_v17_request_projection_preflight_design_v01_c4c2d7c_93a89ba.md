# ChatGPT Review — Stage-1 v1.7 request projection preflight design v0.1

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`
- Formal root: `c4c2d7c66b50a829dccbec811d670cc8f470c5f2`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_projection_preflight_design_v0.1.md:24)`
- Blockers: `2 HIGH` — Design/Authority 2; Production 0; Evidence 0; child/runtime 0.

## Pair / scope / boundary verification

The formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`; child/runtime bytes are unchanged. The formal commit is docs-only: new projection-preflight design plus `SESSION.md` / `TODO.md`. The request is correctly separated from construction/materialization authority: it proposes only a future pure-stdlib helper and direct CPU/static tests, with no Git, remote, filesystem, subprocess, request output, launcher/materializer, source/checkpoint/manifest/data/cache, child/runtime, GPU or training path. The consumed v0.5 construction authority is explicitly not revived or retried.

## HIGH 1 — outer-only input cannot produce the required bootstrap raw bytes

The proposed API is:

```python
project_request_closure(outer_payload_bytes: bytes) -> ProjectedRequestClosure
```

and the design requires the helper to project raw bytes/length/SHA for selection, config, parser argv, **bootstrap**, bootstrap contract and replay identities using only injected canonical outer bytes.

That is not compatible with the frozen launcher structure. In the controlling launcher base `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`, `boot(s)` does not embed the bootstrap raw as a constant. Its final return is:

```python
return raw.decode()
```

where `raw` is obtained earlier by reading the frozen adapter blob (`git cat-file blob ...`), parsing the adapter source, locating `bootstrap_payload`, and extracting that function's return constant/tuple. The outer source itself only carries the expected bootstrap length/SHA guard. The approved replay changes identities/guards but does not change that dependency shape.

Therefore, from `outer_payload_bytes` alone, a no-I/O AST helper cannot reconstruct the complete bootstrap raw bytes required by the design's own output contract. A canonical positive implementation would either fail or have to invent/ambiently source bootstrap bytes, both disallowed.

### Required remediation

Preserve the no-I/O boundary, but change the projection authority input so all required bytes are actually available. Recommended options:

1. Add a second injected, independently identity-checked frozen adapter-source input (or directly injected verified bootstrap raw bytes) and statically extract/verify `bootstrap_payload` from that injected source; or
2. If the helper is intentionally outer-only, narrow its output to bootstrap expected length/SHA only — but that would no longer satisfy the frozen future-request complete-closure requirement and would require a separate explicit request-design refreeze.

Option 1 is the narrow remediation.

Acceptance must prove the injected adapter/bootstrap authority identity before projection and fail-close any missing/wrong/drifted input without Git/path/subprocess access.

## HIGH 2 — blanket duplicate argv-item rejection rejects the canonical parser itself

The design says the helper must parse parser argv as a full string array and reject `duplicate` items, and the CPU/static matrix requires a `duplicate argv item` negative.

The canonical v1.7 parser legitimately contains duplicate **values**. In particular, both:

- `--cwd`
- `--bootstrap-project-root`

use `/proc/self/fd/8`.

This duplicate-value case was already an explicit reason the approved launcher-replay design moved from value-only replacement to flag/position-aware authority. Therefore a rule that rejects any repeated string/item is incompatible with the canonical positive fixture.

### Required remediation

Do not reject duplicate values globally. Instead:

- reject duplicate/missing/extra **flags** or malformed flag/value structure;
- require all argv elements to be strings;
- bind the whole parser to the exact canonical compact JSON bytes/SHA and/or the frozen ordered flag/value table;
- add a negative for duplicate flag / malformed adjacency, not for a legitimate repeated value.

The canonical positive must retain the duplicated `/proc/self/fd/8` value and pass.

## Positive findings

- Separating projection preflight from construction authority is the correct boundary after the consumed zero-write construction failure.
- AST-only, non-executing parsing is appropriate.
- The proposed no Git/remote/filesystem/subprocess/output-write boundary is appropriate.
- Failure taxonomy and all-or-nothing result semantics are directionally correct.
- Embedded frozen fixtures / explicitly injected bytes are the correct CPU/static evidence model.
- Preflight success must still not grant construction authority; the design correctly preserves the need for later implementation-close review and then a new independent construction design/approval.

## Disposition

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_projection_preflight_design_v0.1.md:24)`

This verdict authorizes only docs-only design remediation. It does not authorize implementation yet, does not restore or retry consumed construction authority, and does not authorize request construction, Stage-1 materialization/execution/retry, launcher/materializer execution, source/checkpoint/manifest/data/cache/runtime I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
