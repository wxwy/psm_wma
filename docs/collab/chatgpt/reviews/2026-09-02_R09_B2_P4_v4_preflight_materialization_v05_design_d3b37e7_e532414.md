# ChatGPT Independent Review — R09-B2 P4-v4 Preflight Materialization v0.5 Design

- Design SHA: `d3b37e7df718ea9be70c648d405bc21b83522bf5`
- Formal request / ledger HEAD: `e532414f92c1a1e7c1d93dc7219173fc5deb539b`
- Previous ChatGPT anchor: `8e1d019e7f47121e3af5cf47b17c7ec2960535b1`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: `REQUEST_CHANGES`

## Scope checked

The v0.5 design correctly addresses the prior implementation review in three important ways:

1. capability construction is moved back behind real `load_execution_request(raw)` admission, with immutable admission data / plan and one-way consumption semantics;
2. run-root/middle/leaf mutation is redesigned around parent-directory FDs with `mkdir(..., dir_fd=...)`, `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` child opens, and `fstat` verification;
3. the permanent fixture matrix is expanded to real admission, forge/mutation/reset rejection, precheck zero-write, six mkdir + six post-create verification faults, parent retarget, ambient/tool exclusion, and CLI hard-stop.

These directions close the substantive B1/B2/B3 findings from review `8e1d019`.

## Blocking finding

### B1 — namespace anchor acquisition / precheck ordering is not frozen strongly enough

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_preflight_materialization_design_v0.5_2026-09-02.md`, §3 says the namespace is opened with `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` into a verified directory FD and descendants are then created relative to that FD. This correctly protects descendants *after* the namespace FD exists, but the contract does not freeze how the namespace FD itself is obtained relative to pathname prechecks.

If implementation does:

1. pathname-based canonical/symlink precheck of `namespace` / ancestors;
2. later `os.open(namespace, O_DIRECTORY|O_NOFOLLOW|...)` using the full pathname;

then a symlink/rename race in an ancestor can retarget the namespace before the FD is acquired. The run-root TOCTOU is therefore only moved one level upward.

Required v0.6 clarification:

- establish the namespace anchor **before all reservation prechecks**;
- obtain it without trusting a previously checked full pathname. Preferred static contract: open `/` (or another explicitly frozen parent anchor) and walk each namespace component using `os.open(component, O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC, dir_fd=parent_fd)`, `fstat` each component, closing prior FDs as appropriate; alternatively accept an already-open namespace FD as the helper authority and bind all reporting paths to that authority;
- after the namespace FD is anchored, perform reservation existence/symlink checks relative to that FD, not by re-resolving the namespace pathname;
- fixture must include namespace/ancestor retarget between lexical precheck and would-be acquisition and prove either fail-closed or continued binding to the original anchored directory with zero external-target writes.

For future-nonexistent run roots, it is sufficient and safer to prove each backend root direct-child name absent relative to the anchored namespace FD; descendant `import_staging/<token>` nonexistence follows from the root being absent. Do not reintroduce multi-component pathname traversal merely to precheck nonexistent descendants.

## Non-blocking accepted points

- v0.4 `created_paths` semantics remain coherent: successful mkdir is recorded immediately; post-create verification failure retains that path in the poisoned mutation footprint.
- per-capability one-shot semantics remain acceptable for this static Gate; cross-process persistence is correctly deferred to the later exact-request execution Gate.
- public `main()` remains permanently hard-stopped in this Gate.
- no real request/preflight/materialization, candidate, record/refreeze, P5 export/compose, GPU/CUDA, model/data/checkpoint I/O, B2-T, or Local Memory training is authorized.

## Verdict

`REQUEST_CHANGES`

Only the namespace-anchor acquisition/precheck ordering must be frozen before implementation. The rest of v0.5 is acceptable and should not be reopened absent new drift.
