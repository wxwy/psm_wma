# ChatGPT Independent Review — R09-B2 P4-v4 Execution-Request Lock design v0.4

- Review date: 2026-09-02
- Prior ChatGPT anchor: `ef8f9e835fcef528492f570618db7b53cb032485`
- Design commit: `1d7bad8723f388e5947cb590f026b89e09b64439`
- Formal request head: `03761910e703c43af60dc4b6180b0624d20544bb`
- Frozen Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: `REQUEST_CHANGES`

## Scope checked

Only the v0.3 blockers and v0.4 scope drift were reviewed. No P4/P5 runtime, materialization, record/refreeze, export/compose, GPU, model/data/checkpoint I/O, evaluation or training was authorized or executed.

`ef8f9e8 -> 0376191` is two commits: the v0.4 design/status update and the request-ledger append. `1d7bad8 -> 0376191` changes only `docs/collab/chatgpt/CODEX_INBOX.md`. Gitlink remains exact.

## What v0.4 closes

1. **The v0.3 hash fixed-point is correctly identified and the migration direction is sound.** Removing `preflight.json` (and all P4 evidence/pointer files) from the future run-root roster makes `run.roster_sha256` depend only on staging directories + payload-manifest files, which are pre-execution deterministic. This is compatible with the fact that P5 already reads `request.json/result.json/verification.json` from the evidence namespace rather than from a run-root pointer.
2. The planned commitment now has an explicit top-level schema, backend schema, projection schema and self-hash definitions.
3. The previously closed `O_RDWR -> write/fsync -> same-FD seek/readback -> fchmod(0444) -> fstat -> close` terminal-state contract is preserved.

These portions should not be reopened unless a later revision regresses them.

## Blockers

### B1 — `planned` candidate binding contradicts the already-closed Candidates contract

v0.4 defines each backend object as:

```text
{backend,run_identity,run_token,candidate_root,attempt_id,staging_projection,identity_sha256}
```

and says `run_identity` / `candidate_root` both use `RUN_IDENTITY_KEYS`, while both backend `attempt_id` values must not be reused.

That is incompatible with the production `validate_candidates()` contract already closed in Execution Request static admission:

- there is **one pair-level** `candidates.attempt_id` shared by both backends;
- the pair-level `candidates.root` is the `candidate_root` identity object (`RUN_IDENTITY_KEYS`, kind=`candidate_root`);
- each backend item's `candidate_root` is a **string path** exactly equal to `<pair candidate root>/<shared attempt_id>/<backend>`;
- `attempt_id == run_token` is forbidden per backend, but the same pair-level attempt id is intentionally shared across the two backend candidate paths.

Therefore v0.4 cannot be deterministically transformed back into the already-frozen final request candidate section without inventing semantics, and its current `attempt_id must not reuse` rule requires the opposite of the closed validator.

Required remediation: freeze the planned candidate data in the same shape as the closed contract. For example, make `planned` contain one pair-level candidate-root identity + one shared 64-hex `attempt_id`, and backend records contain the derived candidate path string (or embed an exact canonical projection of the full closed `candidates` section). Preserve all existing candidate/run overlap and reuse rules; do not create a second candidate grammar.

### B2 — `source_tree_sha256` is not a defined Git identity

The authority key-set freezes `source_tree_sha256`, but no computation is defined. In this repository the Git tree object id at design commit `1d7bad8` is `954e94d40b70e47576480c5ea86c3dae7a89c65b` (40 hex), not a SHA-256 field.

Required remediation: choose and freeze exactly one meaning:

- preferably `source_tree_oid` / equivalent = the exact Git tree object id returned by the reviewed commit; or
- if an independent SHA-256 is desired, define the exact byte source and command/serialization whose bytes are hashed, then require that value in fixtures.

Do not leave a field named `source_tree_sha256` whose verification algorithm is implementation-defined.

### B3 — input lock-spec semantic schema / mapping is still not exact

v0.4 freezes the **output commitment** schema, but the single-FD canonical spec being read still has no exact semantic schema/key-set or field-to-output mapping in this revision. The design says the spec is canonical-parsed and authority-bound, yet it does not state which exact spec fields provide the closed request sections, pair candidate namespace, run identities/tokens, payload manifest/projection inputs, or whether the spec is itself the commitment payload.

This leaves multiple implementations able to satisfy the prose while deriving different commitment bytes from the same authority metadata.

Required remediation: freeze the exact spec schema version, exact top-level/nested key-sets, self-hash if any, and a one-to-one mapping from spec fields to every output commitment field. Caller/CLI/environment must remain non-authoritative.

## Re-review boundary

A v0.5 re-review only needs to check B1–B3 above plus scope drift. Do not reopen the v2 roster migration concept, the P5 canonical hash definition, or the same-FD poison contract if they remain unchanged.

If B1–B3 are closed without adding runtime authority, the expected verdict is:

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`

That approval would authorize only root static planned-commitment tooling + stdlib CPU fixtures. It would **not** authorize the P4/P5 handoff migration implementation, final request generation, record/refreeze, real P4 CPU preflight, P5 export/compose, GPU, B2-T, or Local Memory training.
