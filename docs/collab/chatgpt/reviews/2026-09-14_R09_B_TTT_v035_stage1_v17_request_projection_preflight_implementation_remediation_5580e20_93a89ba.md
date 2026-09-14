# ChatGPT independent review — Stage-1 v1.7 request projection preflight implementation remediation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`
- Formal root: `5580e20ca918ec3287f77c17cdfe485dd890b440`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(tools/psm_wma/stage1_v17_request_projection.py:96)`
- Blockers: **2 HIGH** — Production/Authority **1 HIGH**; Evidence **1 HIGH**; Design/Authority **0**; child/runtime **0**.

## Formal-pair correction

The previously transmitted expanded root `5580e20c7e406d7ceade9222353f355fe0a4a15d` is void: it does not resolve as a Git commit. The live correction explicitly names the sole valid root `5580e20ca918ec3287f77c17cdfe485dd890b440`. Git history independently confirms that the review-ledger commit `a04dd579998d196ff3bb5d5b969723582497d38f` has exactly this corrected root as its parent.

This review is only for the corrected exact pair above.

## Scope / Gitlink

The corrected formal root is one commit after the prior same-Gate remediation base `f06bac2a3fb9fa527cfaaf27154b92501956ec9b`. Its implementation delta is limited to the approved projection module/test plus `SESSION.md` / `TODO.md` coordination records. The formal-root `cosmos-framework` Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`; child/runtime bytes are unchanged.

The helper/test remain pure stdlib/in-memory: no Git, network, filesystem/path, subprocess, launcher/materializer, request output, runtime source/checkpoint/manifest/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1.

## Closed from `b85584e...`

The three previous implementation HIGHs are substantially remediated:

1. **Adapter dual identity is now production-enforced.** `_blob_oid(adapter_source_bytes)` and SHA-256 are both compared against the frozen `4a51bddd... / 87e22fac...` pair.
2. **Canonical parser/bootstrap authority is now production-enforced.** The implementation freezes the complete ordered flag/value table, requires compact canonical parser JSON, permits canonical duplicate values while rejecting ordered-table drift, freezes `2336 / 1a9543ec...`, derives `bootstrap_argv` from `["--", *items]` and freezes `2341 / 85ac67c8...`, and freezes the final contract at `182 / bec6a57a...`.
3. **The direct witness is now a real embedded fixture.** The test embeds/decompresses the exact 18,875-byte outer and exact adapter source entirely in memory, calls `project_request_closure()` directly, and checks the main frozen parser/bootstrap identities. The old 3/3 `_literal()`-only evidence problem is closed.

## HIGH 1 — Production/Authority: outer `RAW` single-literal grammar is still too permissive

Controlling v0.2 design freezes a stricter outer AST grammar than the implementation currently enforces:

- `RAW[0]` and `RAW[1]` must be `base64.b64decode(<single ASCII str-or-bytes literal>)`;
- `RAW[2]` must be a single bytes/string JSON literal;
- recursive `Constant(str|bytes)` / `BinOp(Add)` concatenation is reserved for the injected adapter `bootstrap_payload()` return expression.

Current production code instead uses the same recursive `_literal()` for all three outer positions:

```python
def _literal(node: ast.AST) -> bytes:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
        ...
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal(node.left) + _literal(node.right)
    ...

# RAW[0]/RAW[1]
raw = _literal(node.args[0])

# RAW[2]
parser_raw = _literal(raw_nodes[0].elts[2])
```

Therefore structurally non-authorized forms such as:

- `base64.b64decode("ab" + "cd")`, or
- `RAW[2] = b"[...]" + b"..."`

are accepted by the projection grammar when the injected identity constants are adjusted in a CPU/static witness. Exact outer SHA is an important first barrier, but it does not replace the separately frozen AST fail-close contract that this Gate explicitly approved.

### Required remediation

Keep the current public API and no-I/O boundary. Add an outer-only single-literal extractor, e.g. equivalent to:

```python
def _single_literal(node: ast.AST) -> bytes:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, (str, bytes)):
        _fail("raw_literal")
    raw = node.value.encode("utf-8") if isinstance(node.value, str) else node.value
    return raw
```

Use it for both `base64.b64decode(...)` arguments and `RAW[2]`. Keep recursive `_literal()` only for the adapter `bootstrap_payload()` return contract. Preserve the ASCII check for base64 arguments.

Add direct negatives proving concatenated outer base64 arguments and concatenated parser literals fail-close before producing any result.

## HIGH 2 — Evidence: the frozen direct matrix is still incomplete

The real embedded-fixture test is a major improvement, but the approved v0.2/v0.3 CPU/static acceptance matrix remains only partially witnessed.

Present evidence directly covers:

- canonical outer/adapter fixture identity;
- canonical projection call;
- schema field order;
- parser `2336 / 1a9543ec...`;
- bootstrap argv `2341 / 85ac67c8...`;
- contract `182 / bec6a57a...`;
- input drift;
- RAW count/arity and decode target;
- parser reorder/noncanonical spacing/duplicate flag/missing row;
- adapter signature and bootstrap-raw drift;
- `_literal()` Name/Call rejection.

But the frozen design explicitly requires additional direct evidence that is still absent or only indirectly implied:

1. **Outer single-literal-only negatives** for `RAW[0:2]` / `RAW[2]` (also needed to close HIGH 1).
2. **Malformed base64 and malformed JSON** direct negatives, rather than only target/noncanonical-order cases.
3. v0.3 explicitly requires fail-close witnesses for **omitting the leading `"--"`** in bootstrap argv and **substituting parser bytes for bootstrap argv**. Positive equality to the correct result is useful, but it is not the required negative fail-close witness.
4. v0.2 requires **every `ProjectedBytes` result identity** to be directly checked. The current positive test directly checks the three critical parser/bootstrap identities, but does not iterate/assert `byte_length == len(raw)` and `sha256 == sha256(raw)` for `selection`, `config`, `bootstrap`, `outer`, and `adapter_source`.
5. The design requires a **partial-result failure** witness: failed projection must raise and expose no `ProjectedRequestClosure` / partial result.

### Required remediation

Extend only `tools/psm_wma/test_stage1_v17_request_projection.py`, still using embedded/injected bytes only. Add the missing direct negatives/invariant assertions above. No project/Git/path/network/subprocess I/O is needed.

## Positive findings retained

- Adapter Git-blob OID preimage calculation is correct (`sha1(b"blob <len>\0" + raw)`).
- Parser ordered authority is explicit and exact, including valid repeated `/proc/self/fd/8` values.
- `bootstrap_payload()` top-level uniqueness, zero-argument signature, optional docstring + final return shape, and recursive return-literal restriction are materially stronger than the prior implementation.
- Exact parser/bootstrap-argv/contract identities are production-checked before return.
- The formal root contains no child/runtime modification.
- No request construction or Stage-1 authority is created by this helper.

## Authority consequence

Implementation is **not closed** for this exact pair.

This verdict does **not** restore or retry the consumed v0.5 construction authority and does **not** authorize:

- any new request construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

Only remediation of the already-approved two projection paths (plus coordination records) and a fresh exact-pair close review are permitted.
