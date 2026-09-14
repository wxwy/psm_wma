# ChatGPT independent review — Stage-1 v1.7 request projection preflight design v0.2

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`
- Formal root: `ec12f296a321d22f52d9de652a4007a0a1f5d35b`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_projection_preflight_design_v0.2.md:47)`
- Blockers: `1 HIGH` — Design/Authority 1; Production 0; Evidence 0; child/runtime 0.

## Scope and inherited-boundary verification

The formal root immediate commit changes only `SESSION.md` and the v0.2 docs-only design. The formal root Gitlink resolves exactly to reachable child `93a89ba...`; no child/runtime bytes changed.

The prior two v0.1 ChatGPT HIGHs are substantively closed:

1. The helper now takes both `outer_payload_bytes` and independently verified `adapter_source_bytes`, so complete bootstrap raw projection can remain pure/no-I/O while matching the real frozen launcher structure.
2. Parser validation now permits duplicate values while rejecting duplicate/missing/extra flags and bad adjacency, so canonical repeated `/proc/self/fd/8` values no longer self-reject.

Also positive: exact implementation paths, frozen result dataclasses, injected-input identity checks, AST-only extraction, embedded-fixture tests, no Git/path/network/subprocess/request-output I/O, and no construction-authority consumption are all correctly preserved.

## HIGH — bootstrap contract does not freeze the exact bootstrap-argv preimage

Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_projection_preflight_design_v0.2.md:47`.

The v0.2 design freezes the contract object keys and sorted/compact serialization, but does not freeze how `bootstrap_argv_sha256` is computed. This is materially ambiguous because the frozen launcher does **not** hash the parser JSON bytes directly.

The actual frozen launcher computes:

```python
actual = json.loads(RAW[2])
bootstrap_argv_raw = json.dumps(
    ["--", *actual],
    separators=(",", ":"),
    ensure_ascii=False,
).encode()
bootstrap_argv_sha256 = sha256(bootstrap_argv_raw)
```

Then it emits the canonical contract from:

```python
{
    "bootstrap_argv_sha256": bootstrap_argv_sha256,
    "bootstrap_raw_sha256": sha256(bootstrap_raw),
}
```

This distinction is observable and authority-relevant:

- parser argv: `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`
- bootstrap argv (`["--", *parser_items]`): `2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d`
- bootstrap contract: `182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702`

An implementation that naturally hashes `parser_argv.raw` would produce the parser SHA `1a9543ec...`, not the required bootstrap-argv SHA `85ac67c8...`, while still satisfying the current prose that the contract is derived from canonical argv/bootstrap bytes. This is exactly the class of projection ambiguity this preflight Gate exists to eliminate.

### Required remediation

Freeze the exact formula in the design:

```python
bootstrap_argv_raw = json.dumps(
    ["--", *parser_argv_items],
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")
```

Require exact `2341 / 85ac67c8...` for that preimage, then require the canonical contract to be exactly `182 / bec6a57a...`. Add direct CPU/static assertions for both identities.

No API expansion, I/O, construction authority, launcher execution, or child/runtime change is required for this remediation.

## Authority consequence

This design is not yet approved for implementation. The already-consumed v0.5 construction authority remains consumed and non-retriable. No request construction, Stage-1 materialization/retry, launcher/materializer execution, source/checkpoint/manifest/data/cache/runtime I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1 is authorized by this review.
