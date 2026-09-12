# ChatGPT Review — Authority-root Execution Authority Implementation Design v0.2

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-EXECUTION-AUTHORITY-IMPLEMENTATION-DESIGN`

## Exact formal pair

- root design SHA: `e69d78c02bd946d44a3a00e455668e83a639917c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The corrected formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink resolving to `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental design review against the prior exact pair `569a34d50e5106f982c3ed111171d67ea3344bc9 / 93a89ba...` and its two HIGH blockers. The formal delta is docs/status only; no root tooling or child/runtime implementation is changed by this pair.

## Prior blocker closure

### Prior HIGH-1 — bootstrap identity was declarative rather than causally observed: CLOSED

v0.2 now freezes an execution-time process observation using Python 3.11 `sys.orig_argv` before any project import. It requires the exact original invocation shape `[frozen_python, -I, -S, -B, -c, bootstrap_utf8, --, *adapter_argv]`, computes the observed bootstrap raw digest from the actual `-c` payload, computes the observed argv digest from the actual post-`-c` projection, compares declared and observed values before `sys.path.insert` / `runpy`, and requires a direct changed-`-c` subprocess adversarial witness. That is the direct causal witness requested by the prior review.

### Prior HIGH-2 — native Git isolation lacked an exact contract/direct witness: PARTIALLY CLOSED

v0.2 materially improves the contract:

- exact non-inherited Git environment is enumerated;
- an exact Git command prefix is frozen, including `--no-replace-objects` and fixed `-c` settings;
- production transport is moved from a remote alias to a direct endpoint;
- direct native tests are required against temporary repositories and a temporary bare remote, including real CAS create/delete and replace/config/rewrite adversaries.

Those changes close the prior reliance on injected subprocess seams alone.

## Current blocker

### HIGH-1 — local Git config authority is still deferred to the future request but is not frozen as an implementable typed ABI/policy in this design

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.2.md:34`

The security-sensitive local-config admission rule is still incomplete. The design says production must reject `include*`, `url.*`, `remote.*`, `protocol.*`, hooks/attributes/filter/alias keys and any key outside a "fixed allowlist", then says the **next request** will freeze the config SHA/allowlist.

However this Gate is asking to authorize implementation now. The exact allowlist is not enumerated here, and no parser/invocation/Evidence-v1 field is defined for a request-supplied config SHA or allowlist. Therefore an implementer still has discretion over which remaining local-config keys are accepted and how the later request's config authority is causally conveyed into production. A future prose request cannot retroactively define an implementation-time exact-key ABI that does not exist in the approved implementation design.

This also creates a practical authority ambiguity: a normal linked/project worktree may contain benign repository config such as `core.*` and remote metadata, while this document simultaneously says `remote.*` is rejected and leaves the actual fixed allowlist for later. Whether the intended real repository passes preflight is therefore not mechanically determined by the current frozen design.

**Exact acceptance:** before implementation authorization, freeze one complete local-config authority contract in this design. Either:

1. define the exact hard-coded allowlist (all accepted key names and value constraints), make every other local key fail-closed, and include that exact policy in the production-computed isolation fingerprint; or
2. explicitly add typed invocation/parser/Evidence-v1 fields for the reviewed config digest/allowlist, define their canonical encoding and runtime recomputation, and require exact-key validation plus mismatch rejection before the first object/ref/transport action.

In either case, define how the actual Git-dir/config path is resolved without relying on mutable alias/config semantics, and add direct temporary-repository witnesses for one accepted minimal config plus rejected extra/changed keys. The next one-shot request may bind concrete values only through this already-frozen ABI/policy; it must not invent a new config-authority channel after implementation approval.

## Closed behavior retained

- the v0.1 two-file root tooling allowlist remains unchanged;
- four-module pre-import closure remains required;
- direct endpoint rather than `origin` remains the production authority;
- no-replace/global/system isolation is explicit;
- direct temporary bare-remote CPU/static CAS witnesses are required;
- the next actual request must still contain all execution-significant bytes/values with no post-approval substitution;
- this Gate remains CPU/static and does not authorize real materialization.

## Blocker summary

- prior HIGH-1: CLOSED
- prior HIGH-2: PARTIALLY CLOSED
- current blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.2.md:34)`

This verdict binds only the exact formal pair `e69d78c02bd946d44a3a00e455668e83a639917c / 93a89ba61306d840a008813f62f26a34d54850f4`.

No modification of the two root tooling files, real materialization/source/checkpoint I/O, candidate/ref/evidence mutation, collection/receipt, child/runtime changes, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
