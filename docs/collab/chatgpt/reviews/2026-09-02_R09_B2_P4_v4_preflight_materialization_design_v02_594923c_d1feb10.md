# ChatGPT Independent Review — R09-B2 P4-v4 Preflight Materialization Design v0.2

- Design: `594923c1f34120a72d1389c883ce6800a8187b51`
- Request/Ledger HEAD: `d1feb10d7e5f67044104468217235f146b9f300f`
- Frozen Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Prior review anchor: `9727516530f6389281c82b707923cb52089bef60`

## Verdict

`REQUEST_CHANGES`

v0.2 materially closes the v0.1 direction-level gaps: it introduces an admitted-request capability, freezes the exact six-directory reservation footprint, and represents ordinary cross-root non-atomicity with an explicit `POISONED` terminal. However, three implementation blockers remain in the v0.2 contract itself.

## Blocking findings

### B1 — `_AdmittedRequest` is not mutation-safe against its own mutable request object

The proposed capability is described as immutable, but one exact field is the `dict` returned by `load_execution_request(raw)`. A frozen wrapper does not deep-freeze that nested object. After admission, mutation of `capability.request["run"]` can therefore change the run roots/tokens consumed by the helper without changing `raw` or `request_sha256`.

Before implementation, freeze one exact rule: either deep-freeze the admitted request representation, or make every helper entry fail closed unless the request is still canonical-equal to the stored `raw` and the stored SHA still equals `request_sha256(raw)`. Materialization path/token derivation must remain byte-bound to the admitted raw, not merely object-bound to a mutable dict.

### B2 — permanent `POISONED` consumption is unimplementable for a zero-footprint first mkdir failure

The design forbids global/object-id registries and defines `_AdmittedRequest` as immutable, while also requiring every poisoned identity to be permanently unusable on a second call. If the first mkdir itself fails before creating anything, `created_paths` is empty and the filesystem contains no poison footprint. Under the current contract there is no state carrier that can make the second call distinguish this poisoned capability from a never-used capability.

Freeze one implementable rule. Examples: (a) a mkdir failure before the first successful creation is a pre-reservation failure and is not `POISONED`; only failures after a confirmed created path consume the identity, or (b) add an explicit per-capability one-shot consumption latch/state authority and define how it coexists with the claimed immutable capability without a global registry.

Also distinguish mkdir-failure versus post-mkdir-stat-failure prefixes. A stat failure after a successful mkdir must include that newly created directory in the truthful poisoned prefix; a mkdir failure must not.

### B3 — same-backend intended ancestor chain conflicts with the stated pairwise non-overlap rule

The required footprint is intentionally nested:

`<run_root> / <run_root>/import_staging / <run_root>/import_staging/<run_token>`.

Those three paths are ancestor/descendant by construction, while §3 also says the three paths / footprints are pairwise non-overlapping. Under the overlap semantics already frozen in the run/candidates contracts, both statements cannot hold simultaneously.

Freeze the exact exception: the two intended ancestor relations inside one backend footprint are required and allowed; equality, unexpected aliasing, cross-backend overlap, and overlap with source/candidate/other frozen authorities remain forbidden.

## Non-blocking confirmations

- Full execution-request static admission remains closed; this review does not reopen it.
- Keeping public `main()` on the existing SHA-bound full-admission hard-stop is correct for this Gate.
- Explicit fixed backend order and non-recursive mkdir are appropriate.
- An explicit `POISONED` terminal is the correct model for partial cross-root reservation once the one-shot state semantics above are made implementable.
- No real request, run root, candidate, staging, P5, GPU, model/data/checkpoint I/O, or training is authorized by this review.

## Required next verdict target

After a v0.3 design closes B1–B3 without modifying closed nested/full admission contracts, it may request:

`APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS`
