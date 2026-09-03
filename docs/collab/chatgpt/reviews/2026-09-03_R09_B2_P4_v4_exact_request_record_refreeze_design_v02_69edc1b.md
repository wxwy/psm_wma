# Independent Design Review — R09-B2 P4-v4 Exact Request / Record-Refreeze v0.2

- Gate: `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-DESIGN`
- Design SHA under review: `69edc1bee45656bcd2ea73065f8430ddc842c6f6`
- Ledger/request SHA observed at review start: `091994defe7bf50201263f88e9cc1e8715808f07`
- Prior design SHA: `675e299ef30603ffd704731cf723b31b6c59216e`
- Prior ChatGPT review commit: `35c8fa7e7debc892f6b34b9c9307e07476da7a47`
- Design: `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.2_2026-09-03.md`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment still has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved remote `V2` through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `091994defe7bf50201263f88e9cc1e8715808f07`; that commit is the ledger/review-request commit and its parent is exactly design SHA `69edc1bee45656bcd2ea73065f8430ddc842c6f6`.

`35c8fa7 -> 69edc1b` is one documentation/status-only remediation commit: it adds the v0.2 design and updates `SESSION.md` / `TODO.md`; no production P4/P5 tooling changed. The Cosmos Gitlink at the design SHA independently resolves to `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. GitHub exposes no check-runs for this design SHA; the submitted `git diff --check` result is repository-recorded evidence rather than independently rerun CI evidence here.

## Verdict

`REQUEST_CHANGES`

v0.2 closes the *conceptual* gaps identified in v0.1: it preserves the closed P4 request wire, introduces distinct execution/record/publication authorities, binds record to a parent request, and moves Git publication to a base-tree/ref CAS model. Those directions are correct and should be retained.

However, the revised document is still not exact enough to authorize implementation. Three implementation-level HIGH blockers remain: authority schemas/final-request construction are still partially prose-defined; candidate→parent binding does not freeze the actual field provenance of the current P4 evidence wire; and the Git CAS contract does not yet constrain the new commit object or the successful post-CAS worktree/index state.

## HIGH-1 — authority schemas and final-request mapping are still not fully closed

**Design:** `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.2_2026-09-03.md:9,13,19,25`

**Current frozen schema:** `tools/g0/r09_b2_p4_v4_execution_preflight.py:35-56`

### Root cause

v0.2 correctly keeps the existing P4 request top-level key set unchanged and gives an exact outer key set for `execution_authority_v1`. But the nested authority schemas remain implementation-defined prose:

- `planned_source` / `source` are said to freeze repo root/revision/tree/Gitlink/blob/current bytes, but their exact key sets, path grammar and identity digest are not stated;
- `command`, `resources`, `logs` and `stop` are called closed schemas without listing their exact keys/values/digest semantics;
- `record_authority_v1` is described as “exact绑定” but has no exact key set or self-digest definition;
- `record_publication_authority_v1` likewise has no exact key set or canonical self-digest definition.

That leaves the static implementation free to invent authority wire shapes and execution/resource semantics, which is precisely what this design Gate must prevent.

The final-request mapping is also incomplete. The current frozen request grammar contains:

- `CANDIDATES_KEYS = {root, attempt_id, recurrent, ttt_fast_weight, identity_sha256}`;
- per-backend `CANDIDATE_ITEM_KEYS = {backend, candidate_root, run, identity_sha256}`.

v0.2 explicitly maps final `run.identity/run_token`, `candidates.root/attempt_id`, and `run.roster_sha256`, but does not freeze each final `candidates.<backend>` item or the candidate/container identity SHA derivation. “final request 仅由 verified planned commitment 构造” is directionally correct, but the omitted fields still leave more than one implementation.

### Required acceptance criteria

1. Enumerate exact key sets and canonical/self-digest rules for every production authority and nested object introduced by this Gate:
   - `execution_authority_v1` nested `planned_source`, `source`, `command`, `resources`, `logs`, `stop`;
   - complete `record_authority_v1`;
   - complete `record_publication_authority_v1`.
2. Freeze canonical spelling explicitly (P4 canonical JSON or a separately named canonical function) for every authority digest.
3. Freeze final request construction completely. For each backend, at minimum:
   - `final.run[backend].identity == planned[backend].run_identity`;
   - `final.run[backend].run_token == planned[backend].run_token`;
   - `final.run[backend].roster_sha256 == planned[backend].staging_projection.projection_sha256`;
   - `final.candidates.root == planned.root` and `attempt_id == planned.attempt_id`;
   - `final.candidates[backend].backend == backend`;
   - `final.candidates[backend].candidate_root == planned[backend].candidate_root`;
   - `final.candidates[backend].run == final.run[backend]`;
   - per-backend candidate `identity_sha256` and outer candidates `identity_sha256` are verifier-rederived with the frozen P4 canonical spelling.
4. No caller-provided final candidate item, run object, identity SHA, token, roster digest, root or attempt value may survive construction.
5. Add permanent fixtures for every nested authority key-set drift and every omitted final-candidate mapping dimension.

## HIGH-2 — candidate→parent “deterministic mapping” is not yet a frozen field-provenance contract

**Design:** `...exact_request_record_refreeze_design_v0.2_2026-09-03.md:19-21`

**Current P4 evidence wire:** `tools/g0/export_r09_b2_p5_resolved_config.py:325-397`

**Current candidate publication validator:** `tools/g0/r09_b2_p4_v4_static_contract.py:1-150`

### Root cause

The current per-backend PASS `request.json` is not merely a projection of the top-level execution request. Its frozen schema includes:

`backend, production_source, p4_run, p4_staging, request_defaults, interpreter, loader_argv, effective_environment, native_loader_environment, payload_manifest, producer`.

The corresponding `result.json` additionally contains runtime evidence such as `native_closure` and `pre_p5_run_root_roster`, and `verification.json` carries its verifier identity/check chain.

v0.2 says candidate request/result/verification must be verified as a deterministic mapping from the parent request, but it does not state the verifier-owned source of each one of these fields. Some values can be derived from the final request/planned commitment; others come from already-closed historical/source authorities; others are runtime-observed evidence that must be validated, not simply “rederived” from the parent request.

The existing `stage_atomic_publication(candidates)` validates a candidate pair and returns six raw payloads, but it still has no parent-request argument. A future implementation therefore needs an explicitly frozen join algorithm, not only a record authority that happens to contain both the parent SHA and six output SHAs.

Without a field-provenance contract, an implementation could populate `record_authority_v1` with a parent request SHA and a different, independently valid pair of six payloads, while still satisfying the prose-level schema unless the implementation invents stronger checks on its own.

### Required acceptance criteria

1. Freeze a verifier-owned expected-candidate mapping contract for **every field** of per-backend `request.json`. For each field state whether its sole authority is:
   - the exact parent final request;
   - the exact planned commitment / planned roster projection;
   - an already-closed verifier-owned source/historical authority;
   - or a specifically named runtime observation.
2. Do not call `result.json` / `verification.json` deterministic parent projections when they contain runtime-observed evidence. Instead freeze the exact chain that must be validated:
   - candidate request bytes must equal the verifier-derived expected request;
   - result must bind that request SHA and preserve all request-owned fields exactly;
   - roster/native-closure/runtime fields must pass the already-closed verifier-owned validators;
   - verification must bind exact request/result SHA and exact verifier identity/check set.
3. `record_authority_v1` must be verifier-generated from the already validated parent/planned identities and the six verified raw payload bytes; it must not accept caller-provided payload SHA values as authority.
4. Freeze the cross-backend invariant object as an actual exact schema/digest, not only prose. Be explicit about which object contains “effective launch” / P3 selector fields; those are not top-level fields of the P4 candidate request wire.
5. Permanent fixture: construct a fully valid candidate pair from a different exact request/attempt/token/root and prove it fails **only** at the parent-binding join even though its own P4 candidate/P5 handoff grammar passes.

## HIGH-3 — Git CAS does not yet freeze the record commit object or successful post-publication state

**Design:** `...exact_request_record_refreeze_design_v0.2_2026-09-03.md:25`

### Root cause

v0.2 substantially improves the publication model: it freezes a base commit/tree/ref/Gitlink, requires an exact six-path tree diff, and uses `update-ref <ref> <new> <base>` CAS. But two critical pieces remain unspecified.

First, `git update-ref` does **not** require `<new>` to be a child of `<base>`. The design verifies the candidate tree, but it never states that the new record commit object itself must have:

- exactly that verified new tree;
- exactly one parent;
- that sole parent equal to the frozen base commit.

Without this, an implementation could CAS the target ref from `base` to an unrelated or merge commit whose tree happens to contain the correct six-file state, breaking the intended auditable single-transition history.

Second, the design does not freeze the successful worktree/index state. It requires pre-publication `HEAD/ref==base` and `index==base`, then permits a plumbing-style tree/commit/CAS publication. If the target ref is the currently checked-out HEAD branch and the six files are not also materialized/staged consistently, a successful CAS leaves HEAD at the new commit while the worktree/index still represent the base tree. The repository immediately becomes dirty. The already-closed later P5 evidence authority requires exact authorized HEAD plus full-clean root/submodule, so this successful state cannot be consumed without an additional checkout/reset/repair side effect that is not defined here.

### Required acceptance criteria

1. Freeze the record commit object relation:
   - verified `new_tree` is the commit tree;
   - exactly one parent is present;
   - the sole parent is the frozen `base_commit`;
   - no merge/alternate-parent commit is permitted.
2. State whether commit metadata is canonical/frozen or intentionally treated as an output to be reviewed later. In either case, parent/tree must be independently verified before CAS.
3. Freeze one coherent post-CAS repository model:
   - **checked-out target-ref model:** before CAS, worktree and index are prepared to exactly `new_tree`; after successful CAS, verify `HEAD==ref==new_commit`, `write-tree==new_tree`, root/submodule full-clean, six current bytes exact and no unrelated mutation; CAS failure leaves a poisoned non-authoritative state with no automatic retry/repair; **or**
   - **dedicated non-checked-out ref model:** explicitly remove the `HEAD/ref==base` assumption for that publication ref and separately define the later reviewed mechanism that materializes the exact evidence commit into the full-clean evidence root required by P5 authority.
4. Do not leave successful publication in a state that requires an unreviewed checkout/reset to become P5-admissible.
5. Add fixtures for a correct-tree/wrong-parent commit, merge commit, CAS race, and successful-CAS post-state cleanliness/index-tree equality.

## Accepted v0.2 direction

Retain the following:

- closed P4 execution-request wire is not expanded with command/path/SHA fields;
- execution authority is separate and production-default `None`;
- record authority is separate and production-default `None`;
- publication authority is separate and production-default `None`;
- caller `--request` / matching caller SHA cannot itself become execution authority;
- record is intended to bind one exact parent request/planned identity plus the exact six payload bytes;
- candidate link remains validation-only and is not published;
- publication uses a verifier-built six-blob tree and compare-and-swap ref update;
- record/refreeze never writes `AUTHORIZED_P4_V4_EVIDENCE`;
- P5 evidence authority remains a later independent reviewed verifier revision;
- this design/static Gate authorizes no real request/preflight/staging/candidate/record/P5/GPU/training side effect.

## Scope

Keep `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-DESIGN` in `REVIEW`.

The next acceptable review object is a new design SHA that closes the three HIGHs above. Do not start static implementation from `69edc1b`, and do not generate or execute an exact request, P4 preflight, record/refreeze commit, P5 authority/export, GPU, or training step under this verdict.
