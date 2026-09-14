# ChatGPT review — Stage-1 v1.7 request projection preflight implementation second remediation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`
- Formal root: `079167743685247d6aae62a671436e834411a3cb`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Prior same-Gate reviewed pair: `5580e20ca918ec3287f77c17cdfe485dd890b440 / 93a89ba61306d840a008813f62f26a34d54850f4`

## Final verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC_IMPLEMENTATION`

Blockers: `0`.

## Incremental review against the two prior HIGHs

### 1. Production/Authority — CLOSED

The prior outer-RAW structural gap is closed.

- `RAW[0]` and `RAW[1]` base64 arguments now pass through `_single_literal()`, which accepts only a single `ast.Constant(str|bytes)`.
- `RAW[2]` parser JSON also passes through `_single_literal()`.
- Recursive `Constant/BinOp(Add)` handling remains isolated to adapter `bootstrap_payload()` return via `_literal()`.
- `_decode()` preserves ASCII checking and strict `base64.b64decode` shape before decoding.

This now matches the approved v0.2 outer-AST contract rather than accepting concatenated outer literals.

### 2. Evidence — CLOSED

The direct embedded-fixture matrix now covers the previously missing evidence.

- All three outer RAW elements have concatenation-rejection witnesses.
- Malformed base64 and malformed parser JSON are direct negatives.
- The canonical public `project_request_closure()` witness still runs against the embedded frozen 18,875-byte outer and frozen adapter bytes.
- Every returned `ProjectedBytes` field is checked for `byte_length == len(raw)` and `sha256 == sha256(raw)`.
- Parser argv remains checked against the exact ordered `FLAG_VALUES` table and canonical compact JSON.
- Bootstrap argv remains checked against exact `["--", *parser_argv_items]` serialization.
- Wrong bootstrap-argv construction without the prefix / substituting parser bytes is forced through the production identity guard and fails `projection_identity`.
- Failed calls do not return a `ProjectedRequestClosure`; production has no partial-return path.

The prior adapter dual identity, canonical ordered parser, strict bootstrap function/return AST, exact parser/bootstrap-argv/contract identities and embedded no-I/O fixture remain intact.

## Scope / boundary

Compared from the prior ChatGPT notification head `848842bcf6aec81654248d67ce8c721ef88f062c` to formal root `079167743685247d6aae62a671436e834411a3cb`, the formal delta is limited to:

- `tools/psm_wma/stage1_v17_request_projection.py`
- `tools/psm_wma/test_stage1_v17_request_projection.py`
- `SESSION.md`
- `TODO.md`

The formal root Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`; child/runtime production bytes are unchanged.

The helper/test remain pure stdlib and injected-byte-only: no Git, remote, filesystem/path reads, subprocess, launcher/materializer, request-output or runtime execution path is introduced.

## Authorized consequence

This approval closes only the Stage-1 v1.7 request-projection CPU/static implementation Gate.

It does **not** restore or retry any consumed construction authority and does **not** authorize request construction, Stage-1 materialization/execution/retry, launcher/materializer execution, source/checkpoint/manifest/data/cache/runtime I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

A future request-construction attempt requires a new construction design/authority and its own exact-pair review chain.
