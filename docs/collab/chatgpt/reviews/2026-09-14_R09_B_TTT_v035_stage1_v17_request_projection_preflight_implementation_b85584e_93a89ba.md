# ChatGPT Review — Stage-1 v1.7 request projection preflight implementation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`
- Formal root: `b85584e18b9b4ebaf85d4a07f63a9d87908e0c98`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Controlling design: v0.2 + v0.3, with v0.3 superseding only the bootstrap-argv/contract preimage details.

## Verdict

`REQUEST_CHANGES(tools/psm_wma/stage1_v17_request_projection.py:70)`

Blockers: **3 HIGH**
- Design/Authority: 0
- Production/Authority: 2 HIGH
- Evidence/Scope: 1 HIGH
- child/runtime: 0

The implementation is not closed. This verdict does not restore or retry the consumed v0.5 construction authority and does not authorize request construction, launcher/materializer execution, Stage-1 materialization, source/checkpoint/manifest/data/cache/runtime I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

## Scope / positive findings

- Formal root immediate parent is the prior ChatGPT design-approval ledger commit; the formal implementation commit itself adds exactly the two approved root paths:
  - `tools/psm_wma/stage1_v17_request_projection.py`
  - `tools/psm_wma/test_stage1_v17_request_projection.py`
- Formal Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- The helper is pure stdlib plus import of the already-closed `AuthorityReplayError`; there is no Git, network, filesystem, subprocess, request-output, launcher/materializer, child/runtime, GPU, or training path.
- Public API and result field ordering follow the frozen v0.2/v0.3 design, including `bootstrap_argv: ProjectedBytes` in the v0.3 position.
- The implementation computes the v0.3 bootstrap argv formula using `["--", *items]` and sorted/compact bootstrap-contract JSON.

## HIGH 1 — Production/Authority: adapter blob identity is frozen but not verified

Location: `tools/psm_wma/stage1_v17_request_projection.py` input-identity checks around the start of `project_request_closure()`.

The v0.2 design freezes adapter source as the pair:

- Git blob OID: `4a51bddd15ec9a88883e3071cc550de85721599b`
- raw SHA-256: `87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816`

and explicitly says the helper itself must re-verify both injected-input identities.

The implementation defines:

```python
ADAPTER = (
    "4a51bddd15ec9a88883e3071cc550de85721599b",
    "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816",
)
```

but checks only:

```python
if _sha(adapter_source_bytes) != ADAPTER[1]:
    _fail("input_identity")
```

`ADAPTER[0]` is never consumed. Therefore the production helper does not implement the approved two-identity adapter authority.

### Required remediation

Without adding I/O, compute the native Git blob OID from the injected bytes and require it to equal `ADAPTER[0]`, e.g. the SHA-1 of `b"blob " + str(len(raw)).encode() + b"\0" + raw`, in addition to the raw SHA-256 check. Add direct negatives for raw-SHA and blob-OID authority drift.

## HIGH 2 — Production/Authority: frozen parser / bootstrap AST contract is not implemented

Location: `tools/psm_wma/stage1_v17_request_projection.py` inside `project_request_closure()`.

The controlling v0.2 design requires production validation that:

- parser argv is canonical compact JSON;
- all elements are strings;
- it exactly matches the frozen ordered flag/value table;
- duplicate/missing/extra flags and wrong flag/value adjacency fail-close while duplicate values remain legal;
- `bootstrap_payload()` has the frozen signature/shape and the allowed return AST only;
- forbidden Name/Call/Attribute/format/container/control-flow/other AST nodes are rejected.

The implementation currently does only:

```python
items = json.loads(parser_raw)
if not isinstance(items, list) or any(not isinstance(x, str) for x in items):
    _fail("argv")
```

and for `bootstrap_payload()` only checks one top-level function with that name, ordinary `args.args` empty, a nonempty body, and the final statement being `Return`.

It does **not** validate canonical parser reserialization, the frozen ordered flag/value table, duplicate/missing/extra flags, or adjacency. It also does not fully enforce the frozen function signature (posonly/kwonly/varargs/kwargs/defaults) or the frozen return/body/control-flow whitelist.

The exact outer/adapter whole-byte identity is a strong front-door check, but it does not replace the separately approved structural projection contract. This preflight exists specifically to prove that the future constructor's parser/projection logic understands the frozen bytes correctly rather than merely trusting them.

### Required remediation

Implement the frozen parser and bootstrap structural checks directly:

- require `json.dumps(items, separators=(",", ":"), ensure_ascii=False).encode("utf-8") == parser_raw`;
- enforce the exact frozen ordered flag/value table, allowing repeated values but rejecting duplicate/missing/extra flags and wrong adjacency;
- fully enforce the frozen `bootstrap_payload()` signature and allowed AST/body/return shape;
- fail only through the approved `AuthorityReplayError("BLOCKED_AUTHORITY_NOT_CLOSED:projection_<category>")` path.

The existing API does not need to change.

## HIGH 3 — Evidence/Scope: the claimed 3/3 direct suite never exercises the projection helper

Location: `tools/psm_wma/test_stage1_v17_request_projection.py`.

All three tests exercise only the private `_literal()` helper:

1. constant/add positive;
2. Name negative;
3. Call negative.

No test calls `project_request_closure()` at all.

Therefore there is no direct witness for the approved CPU/static matrix, including:

- canonical frozen outer + adapter positive;
- both input identities;
- RAW count/arity and `base64.b64decode` target/argument handling;
- adapter signature / return-node handling;
- canonical parser JSON and legal repeated values;
- duplicate/missing/extra flag and adjacency negatives;
- every `ProjectedBytes` raw/length/SHA identity;
- parser argv `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`;
- bootstrap argv `2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d`;
- bootstrap contract `182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702`;
- missing `"--"`, parser-bytes-as-bootstrap-argv, parser reorder, bootstrap raw drift;
- partial-result fail-close.

### Required remediation

Replace/extend the current literal-only suite with embedded gzip/base64 frozen outer and adapter fixtures, with no project/Git/path/network/subprocess I/O. Call `project_request_closure()` directly for the canonical positive and the complete approved negative matrix. Directly assert all exact identities and result field ordering.

## Closure condition

A future implementation-close request can be approved only when all three HIGHs are closed on a new exact formal pair. Passing `py_compile`, `git diff --check`, or a small unit count is supplementary evidence and cannot substitute for the missing production authority checks or canonical direct witness.
