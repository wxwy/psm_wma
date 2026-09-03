# Independent Design Review — R09-B2 P4-v4 Exact Request / Record-Refreeze v0.1

- Gate: `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-DESIGN`
- Design SHA under review: `675e299ef30603ffd704731cf723b31b6c59216e`
- Ledger/request SHA observed at review start: `657a7d46b5ea108179f008c4401feda9bae0d455`
- Design: `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.1_2026-09-03.md`
- Prior handoff closure: implementation=`28b859203d1735e33e0b1d8d7813429841e1c778`, ChatGPT review=`90cb466f4e1f8b3858897608096dbe894abf4455`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved remote `V2` directly through the connected GitHub repository API immediately before review. At review start remote `V2` HEAD was `657a7d46b5ea108179f008c4401feda9bae0d455`; that commit only appends the design-review request and its parent is exactly design SHA `675e299ef30603ffd704731cf723b31b6c59216e`.

The design SHA is documentation/status-only: it adds the v0.1 design and updates `SESSION.md` / `TODO.md`; no production P4/P5 code or Cosmos submodule changed. Gitlink at the design SHA independently resolves to `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. GitHub exposes no status/check result for the design SHA.

## Verdict

`REQUEST_CHANGES`

The overall separation is correct — exact-request freeze, one later CPU preflight, record/refreeze, and still-later P5 evidence authority should remain distinct Gates — but v0.1 is not yet precise enough to implement without reopening already-closed schemas or leaving a valid alternate evidence path. Three HIGH blockers remain.

## HIGH-1 — exact-request freeze and later execution authority are not a closed wire contract

**Design:** `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.1_2026-09-03.md:13-19`

### Root cause

The current closed P4 execution-request schema is exactly:

`{schema_version,entry,source,interpreter,environment,run,candidates,backends,authorities,execution_contract}`.

It has no command, request-path, or request-SHA field. The current CLI separately accepts caller-provided `--request` and `--request-sha256`, validates them, then hard-stops.

v0.1 says the later allowed command must be frozen “在请求中” including the `--request` raw/SHA, but does not define whether this is the existing P4 request or a second execution-authorization object. If it is the existing P4 request, adding its own raw SHA is self-referential and reopens a closed wire schema. If it is a second object, its exact schema, identity digest and production authority are absent.

v0.1 also does not freeze the deterministic mapping from the already-closed planned commitment to final request bytes. In particular it does not state, field-by-field, that final `run` identities/tokens come from the planned commitment, each `run.roster_sha256` equals that backend's `staging_projection.projection_sha256`, final candidate roots/attempt mapping are exactly the planned values, and all other closed sections are byte/semantic identical to the commitment.

Without this, a static implementation could generate a semantically valid but uncommitted final request, or later unlock the current CLI using a caller-controlled path/SHA pair.

### Required acceptance criteria

1. Preserve the existing P4 execution-request key set. Do not add command/path/SHA fields to that wire object.
2. Define one separate verifier-owned **exact-request freeze record / execution authority** schema with exact keys and digest semantics. It must bind at least:
   - exact planned-commitment raw/SHA (and its reviewed source identity);
   - exact final P4 request raw/SHA and immutable output path;
   - exact source commit/tree/Gitlink/current-byte bindings;
   - exact command argv/cwd/environment/resource/log/stop contract needed by the later execution Gate.
3. Define the final request construction mapping field-by-field from the planned commitment; no caller-provided run/candidate/root/token/roster values are accepted.
4. Keep all production freeze/execution authorities `None` in this implementation Gate. A later execution Gate must freeze the exact reviewed authority before the CLI hard-stop can be removed/bypassed.
5. The executable path must compare against verifier-owned frozen raw/path/SHA/argv, not merely accept a caller-supplied `--request` + matching caller-supplied SHA.
6. Add fixtures for alternate-valid request substitution, command/path/SHA substitution, planned→final mapping drift, and authority-None fail-before-create/execute.

## HIGH-2 — record/refreeze is not cryptographically bound to the one reviewed exact request

**Design:** `...exact_request_record_refreeze_design_v0.1_2026-09-03.md:21-25`

### Root cause

The existing `stage_atomic_publication(candidates)` validates a dual PASS candidate directory and returns the six payload raw bytes, but it does not take or verify the parent exact execution-request raw/SHA. Candidate payloads contain backend/run/staging/source data, yet they do not carry the parent execution-request SHA as a frozen identity.

v0.1 says record/refreeze happens after the dual PASS and revalidates candidate links/payloads, but it never requires those candidates to be the outputs of **the exact request that received the execution review**. Therefore a different, individually valid dual candidate pair could satisfy candidate/P5 grammar and be recorded.

The design also says “pair shared-source/cross-backend invariants” without enumerating the exact equalities/differences, leaving implementation discretion in the most important evidence-chain join.

### Required acceptance criteria

1. Define a separate record/refreeze authority (production default `None`) frozen only after the runtime PASS review. It must bind:
   - exact parent execution-request raw/SHA;
   - exact planned-commitment SHA;
   - exact attempt id / candidate root;
   - exact backend run roots, run tokens, roster digests;
   - exact six candidate payload SHA256 values (or a deterministic verifier-derived equivalent).
2. Record/refreeze must prove each backend candidate request/result/verification is the deterministic output/binding of that exact parent request, not merely a valid P4-v4 candidate.
3. Freeze the exact cross-backend invariant set: which fields must be identical, which are backend-owned differences, and how P3-only environment difference is handled. Fixtures must mutate each bound dimension.
4. Reject a fully valid candidate pair from a different exact request/attempt/token/root even if its own candidate links and P4/P5 schemas pass.
5. `candidate_link.json` remains validation-only and must never enter the six published evidence blobs.

## HIGH-3 — “six raw files + one Git commit / commit-or-none” lacks a frozen Git publication algorithm

**Design:** `...exact_request_record_refreeze_design_v0.1_2026-09-03.md:25-27`

### Root cause

The design requires the six raw payloads to be published in one Git commit but does not freeze the authority or mechanics that make that commit evidence-safe. It does not specify:

- exact evidence repository/root and target ref;
- exact pre-record parent commit/tree/Gitlink;
- full-clean worktree/submodule and index==HEAD requirements;
- exact six fixed target paths and file modes / nonexistence requirements;
- proof that the new tree differs from the parent **only** by those six blobs;
- prevention of unrelated staged files;
- race-safe ref update if HEAD/ref moves concurrently;
- what “commit-or-none” means when file/blob/tree/commit creation succeeds but final publication fails.

A normal `git add/commit` implementation could accidentally include unrelated staged changes or race with a moving ref. Merely producing one commit is not sufficient evidence.

This is especially important because the already-closed P5 evidence authority later accepts only an exact reviewed evidence commit/tree/Gitlink and rejects descendants; record/refreeze must therefore produce an auditable six-file tree transition, not just any commit containing those files.

### Required acceptance criteria

1. Define one verifier-owned record publication authority (default `None`) containing exact evidence repo identity, exact base commit/tree/Gitlink, exact target ref, six fixed paths, and expected candidate blob SHA256 values.
2. Before publication require full-clean root and submodule, target ref/HEAD exactly at the frozen base, index/tree exactly the base, target paths absent/non-symlink, and no unrelated staged/untracked mutation admitted into the published tree.
3. Construct/verify the candidate Git tree so `diff(base_tree,new_tree)` is exactly the six fixed regular files with exact raw bytes/modes; Gitlink and every other tree entry remain unchanged. No parse/rewrite/reserialize and no candidate link.
4. Publish using compare-and-swap semantics: target ref may move only from the frozen base commit to the newly verified record commit. Ref drift/race must fail without publishing that record.
5. Define “commit-or-none” precisely as **no authoritative ref publication on any failure before the final CAS**. Dangling Git objects, if allowed, must be explicitly non-authoritative; partial worktree/index state must never be accepted by the later P5 authority.
6. Add fixtures for dirty/staged/untracked state, wrong base/ref/Gitlink, target preexistence/symlink, unrelated-tree injection, short/failed six-blob publication, concurrent ref movement, and exact six-path tree diff.
7. Record/refreeze still must not set `AUTHORIZED_P4_V4_EVIDENCE`; only a later reviewed P5 verifier revision may freeze that exact resulting commit/tree/blob authority.

## Accepted design direction

The following should be retained:

- exact-request freeze, execution, record/refreeze and P5 authority remain separate review/execution Gates;
- no historical P4-v2/D005 artifact or ambient caller value becomes authority;
- PASS candidate is `{request,result,verification,candidate_link}`, FAIL candidate is `{request,failure}`;
- candidate link is not published;
- six P4 payloads must be byte-preserved, not parsed/re-serialized for record;
- P5 evidence authority remains a later verifier revision and record commit cannot self-authorize;
- current production constants/hard-stops remain unchanged during design/static implementation.

## Scope

Keep this Gate at `REVIEW`. Do not implement or execute exact request generation, preflight, record/refreeze or P5 authority until a revised design closes the three HIGHs above.

This review authorizes no real request/preflight/staging/materialization/candidate/run-root creation, record/refreeze/evidence publication, P5 export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory/LIBERO training.
