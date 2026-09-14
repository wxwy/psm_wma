# ChatGPT independent review — Stage-1 v1.7 request-instance design v0.6

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Formal root: `76307bb65c08c1f9f35e3832be89c9cc617953eb`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.6.md:27)`
- Blockers: `2 HIGH` — Design/Authority `2`; Production `0`; Evidence `0`; child/runtime `0`.

## Scope / positive findings

1. Formal root immediate delta is docs-only: `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.6.md`, `SESSION.md`, `TODO.md`.
2. Formal root Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime bytes are unchanged.
3. v0.6 correctly records the v0.5 construction authority as permanently consumed and does not revive it.
4. Closed projection implementation `079167743685247d6aae62a671436e834411a3cb / 93a89ba...` is correctly treated as a prerequisite, not materialization authority.
5. The detached canonical JSON / Markdown sidecar model, two-query remote allowlist, one-request/no-retry goal, no materialization, and independent exact-pair request review boundaries remain directionally correct.
6. Non-conflicting v0.5 rules remain applicable, including remote `V2` as construction provenance rather than runtime equality, and fixed authority-ref/path absence as runtime freshness.

## HIGH 1 — Phase C start / authority-consumption boundary is internally contradictory

Section 2 says Phase C begins only after Phase P succeeds **and all same-round zero-mutation observations below are completed**. Section 3 then defines the Git/.git/local-ref/two-remote-query/path-absence/environment reads as **Phase C** reads, and explicitly says an observation failure is non-retry because Phase C has already begun.

These two definitions are mutually exclusive:
- under §2, an observation failure happens before Phase C and therefore before authority consumption;
- under §3, the same observation happens inside Phase C and consumes the one construction authority before it can fail.

This is an authority semantic, not wording-only: it determines whether a failed freshness/remote observation may be repeated.

### Required remediation
Freeze one unique consumption point. Recommended structure:
- `P0`: immutable input acquisition, non-consuming;
- `P1`: pure projection, non-consuming;
- `C`: consuming construction attempt. `C` starts **before** the first same-round `.git` / ref / remote / path-absence / environment observation; entering `C` consumes the authority; any observation/output/identity failure thereafter permanently exhausts it and forbids retry.

Alternatively choose a different boundary, but the design must state one unambiguous rule consistently in all sections.

## HIGH 2 — Phase P has no authorized source for required formal-tree outer/adapter bytes

Phase P requires injected `formal-tree frozen outer bytes and adapter bytes`, but Phase P itself forbids Git, filesystem/path, network and subprocess I/O. The only explicit permission to read formal Git commit/tree/blob and outer/adapter bytes appears in Section 3 under Phase C. Yet Section 2 requires Phase P success before Phase C can begin.

That creates a circular dependency:

`need formal outer/adapter bytes -> read is only authorized in Phase C -> Phase C requires Phase P success -> Phase P requires those bytes`.

The closed helper being injected-byte-only does not solve the orchestration authority that obtains those bytes.

### Required remediation
Add a closed non-consuming Phase-P input-acquisition authority, e.g. `P0`, that allows only immutable reads needed to obtain and independently verify the exact frozen formal objects/bytes for outer and adapter (including object identity and raw digest), with no remote/network, no mutation, no output and no request construction. Then pass those verified bytes to pure `P1` projection.

Equivalent alternative: freeze the exact outer/adapter bytes as externally supplied invocation inputs together with a mechanically verifiable source/identity contract. Do not leave their origin to ambient worktree/Git inference.

## Disposition

The design is not yet authorized to construct a request instance. The two blockers can be fixed docs-only; projection implementation need not be reopened absent regression.

Still NOT authorized:
- request construction under v0.6;
- revival/retry of v0.5 construction authority;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O beyond a future explicitly approved construction allowlist;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
