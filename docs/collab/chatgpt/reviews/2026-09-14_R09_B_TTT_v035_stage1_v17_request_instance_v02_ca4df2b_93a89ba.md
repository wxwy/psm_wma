# ChatGPT Review — Stage-1 v1.7 exact request instance v0.2

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`
- Formal root: `ca4df2bd9e01139b6f9e9abf507e6cf086726d63`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.2.json:3)`
- Blockers: `3 HIGH`
  - Request/Authority: `3 HIGH`
  - Design/Authority: `0`
  - Production/Authority: `0`
  - Evidence/Scope: `0`
  - child/runtime: `0`

## Re-lock / scope

The formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`; no child/runtime bytes changed. The formal remediation commit is docs-only: the replacement v0.2 Markdown/JSON plus `SESSION.md`; the additional deltas from the prior reviewed pair are review/coordination bookkeeping.

Incremental review is against the three HIGHs in v0.1. The prior execution-boundary blocker is closed in v0.2: the Markdown now states one post-approval Stage-1 attempt, zero-write fail-close on pre-mutation drift, authority exhaustion on failure/consumption, no retry, and a new request/new approval requirement. The prior moving-`V2` equality semantics is also directionally fixed: remote `V2` is now described as construction provenance, not runtime equality freshness. However the exact request is still not closed for the three independent authority reasons below.

## HIGH 1 — the v0.2 "fresh" observation is stale/reused, not a new same-round snapshot

`observed_at_cst` is newly set to `2026-09-14T18:45:00+08:00`, but `remote.v2.stdout_sha256` remains exactly `4f15ef60aa3158fafcb4842e9fbc8bec6d904652640ebd5e01c7986c53a80a99`, the same v0.1 construction observation whose bound raw value was:

`bb99c6df4cf6ba615e09e3ff4c8c065509b4dc6e\trefs/heads/V2\n`

That observation predates the v0.1 exact-request review/notification commits and the v0.2 replacement construction. Formal history confirms `bb99c6df...` is an ancestor of `ca4df2bd...`, while the branch had already advanced through the v0.1 review before v0.2 was created. `SESSION.md` records the v0.1 review finals and then creation of v0.2, but no new same-round read-only observation corresponding to the new `observed_at_cst`.

Therefore v0.2 has fixed the *semantic category* of `V2` (provenance-only), but it has not supplied a fresh construction observation as required by the approved v0.2/v0.3/v0.4 design chain. A new timestamp cannot turn the reused v0.1 remote result into a fresh v0.2 snapshot.

### Required remediation

For the replacement request, take a new same-round allowlisted zero-mutation snapshot. Bind the actual local `V2` observation and the exact successful remote `V2` query result from that round, including command, timeout, return code, raw stdout/stderr identities and the raw advertised commit/ref value. Treat that `V2` identity only as immutable construction provenance and prove its observed commit is an ancestor of the new exact formal request root; do not require runtime equality against the naturally moving collaboration branch.

The fixed authority-ref and designated absence facts remain runtime freshness and must be freshly re-observed and fail-closed under the frozen design.

## HIGH 2 — canonical JSON still does not contain the approved complete closure

The v0.2 Markdown says the sibling JSON binds the complete inherited closure, but the JSON object does not actually contain several fields frozen by the approved request-construction design.

Material omissions/regressions include at least:

- `.git` directory identity and `.git/config` raw bytes/length/SHA;
- local fixed-authority-ref observation/return code;
- designated clean-root/index/evidence/pending absence results;
- local `V2` observation;
- exact remote commands and the raw/byte-length observations required by v0.4 (the `V2` entry lacks command/stdout length/stderr length/raw advertised value; the authority-ref entry lacks the command);
- selection/config/bootstrap byte lengths required alongside hashes;
- bootstrap-contract identity/length;
- the canonical parser argv itself (only its size/SHA is present);
- the frozen base path and other inherited request fields needed to mechanically reconstruct the exact replay/preflight closure.

The six key/value environment is now present, as are replay module/test identities, owner-FD and targets, but those partial additions do not satisfy the full inherited contract. In particular, dropping the `.git`/config/local-ref/path observations also prevents the future pre-mutation checker from revalidating the approved same-round snapshot rather than silently narrowing freshness authority.

### Required remediation

Restore the complete inherited v0.4 request-construction closure into the canonical JSON. It must be sufficient for a mechanical checker to recompute and compare all frozen request/base/replay/parser/environment/FD/target and freshness facts without relying on prose, stale v0.1 fields, ambient defaults or inference.

At minimum, bind the exact observation time; formal/base/replay identities; `.git` and config identities; local `V2`; local fixed-ref result; both exact remote observations with the v0.4 success contract; designated path absences; selection/config/bootstrap/contract length+SHA identities; canonical parser argv plus its bytes/SHA; six environment key/values; owner-FD insertion; replay output; and cwd/index/evidence targets.

## HIGH 3 — declared canonical JSON identity does not match the committed sibling bytes

The v0.2 Markdown binds the sibling JSON as:

- `2496 bytes`
- SHA-256 `32d0543b32a2449b1dd3efd487b2afc0099fa2ca9a2310d3a875148061cc4fc5`

Those values match the committed pretty-printed sibling JSON raw bytes.

But the JSON itself declares canonicalization as:

`UTF-8 sorted-keys compact JSON plus newline`

Recomputing that declared serialization from the exact committed JSON object yields:

- `2381 bytes`
- SHA-256 `925e5afa8220de095c610edd9552b8530c1f4eca19d9904904cf963a3b141c92`

So the Markdown-bound identity is the raw pretty-printed file, while the request tells runtime to recompute a different canonical representation. The request therefore has two incompatible whole-JSON authorities.

### Required remediation

Choose exactly one canonical byte representation and make the committed sibling, the sidecar Markdown identity, and the runtime recomputation rule agree byte-for-byte. The cleanest path is to emit the final JSON itself in the declared sorted-key compact UTF-8 + newline representation after all missing fields are restored, then bind that exact final length/SHA in the Markdown. Do not preserve the current `2496 / 32d...` values after the object changes.

## Positive findings retained

- Formal parent/base/replay identities are still consistent with the closed launcher-replay implementation.
- Replay module/test blob/raw identities are now explicitly present.
- Six environment key/value pairs are now explicit.
- Fixed authority-ref remote absence contains successful `returncode=0`, zero stdout bytes/lines, empty-stream SHA and zero stderr bytes/SHA.
- Remote `V2` is no longer defined as runtime equality freshness; `bb99c6df...` is in fact an ancestor of the formal request lineage.
- One-attempt post-approval semantics are materially improved and close the prior v0.1 execution-boundary contradiction.
- No launcher/materializer execution, child/runtime mutation, source/checkpoint/manifest/data/cache I/O, GPU or training is in this formal scope.

## Authority consequence

`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_V17_AUTHORITY_ROOT` is **not granted** for this exact pair.

This review permits only a docs-only replacement-request remediation under the already frozen construction design, including a genuinely new same-round allowlisted read-only snapshot and a corrected canonical Markdown/JSON pair. It does **not** authorize Stage-1 materialization/execution/retry, launcher/materializer execution, source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1. v1.6 authority remains consumed and non-reusable.
