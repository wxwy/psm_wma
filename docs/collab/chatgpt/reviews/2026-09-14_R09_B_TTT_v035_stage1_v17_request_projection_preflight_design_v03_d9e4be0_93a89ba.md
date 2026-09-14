# ChatGPT review — Stage-1 v1.7 request projection preflight design v0.3

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`
- Formal root: `d9e4be0e990c2847f402c6e9913ea42a662ddb4c`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC`
- Blockers: `0`

## Scope / authority

This is a docs-only remediation design review. The formal root immediate parent is `112f9700b52aa85a9d83a679ce71e85143e84caa`; the formal commit adds only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_projection_preflight_design_v0.3.md`. The formal root Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`; child/runtime bytes are unchanged.

Approval is limited to the v0.2/v0.3 frozen implementation scope:
- `tools/psm_wma/stage1_v17_request_projection.py`
- `tools/psm_wma/test_stage1_v17_request_projection.py`

Pure stdlib / injected-bytes / CPU-static only. No Git/remote/filesystem/subprocess/request output. This design approval does not restore, retry, or replace the consumed v0.5 construction authority and does not grant request construction or Stage-1 materialization.

## Incremental review against prior same-Gate blocker

The sole v0.2 HIGH is closed.

The design now freezes the exact bootstrap argv preimage used by the frozen launcher:

```python
bootstrap_argv_raw = json.dumps(
    ["--", *parser_argv_items],
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")
```

This explicitly distinguishes the bootstrap argv bytes from `parser_argv.raw` and binds the exact identities:
- parser argv: `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`
- bootstrap argv: `2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d`
- bootstrap contract: `182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702`

The contract bytes are frozen as sorted-key compact UTF-8 JSON containing exactly the SHA-256 of the bootstrap argv preimage and bootstrap raw. The result schema is correspondingly extended with `bootstrap_argv: ProjectedBytes` between `parser_argv_items` and `bootstrap`.

The required CPU/static evidence directly tests the three exact identities and fail-closes omission of the `"--"` prefix, substituting parser bytes for bootstrap argv, parser-item reorder, and bootstrap raw drift.

## Preserved v0.2 controls

No regression was found in the already-closed controls:
- injected verified `outer_payload_bytes` and `adapter_source_bytes` inputs;
- helper-side revalidation of exact outer and adapter identities;
- AST-only extraction with strict bootstrap return whitelist;
- flag-aware argv validation allowing canonical repeated values while rejecting duplicate/missing/extra flags and bad adjacency;
- frozen dataclass schema and exact implementation/test paths;
- embedded/injected-fixture-only direct CPU/static evidence;
- no partial results on failure;
- no Git/path/network/subprocess/request-output I/O;
- projection failure/success does not consume or grant construction authority.

## Authorized consequence

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC`

Only the frozen root-only projection helper and direct CPU/static tests may now be implemented and then independently reviewed for close.

Still NOT authorized:
- any new request construction authority;
- retry/revival of the consumed v0.5 construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
