# ChatGPT independent review — R09-B2 P4-v4 execution request `candidates` v0.1

- Design commit: `7eb00d7bc9c568f6704a972102a6ebb97a5b5e79`
- Review request commit: `42ca5927f18e6279e9b6da1d67873efefa669403`
- Prior closed run implementation/remediation: `8295b93bb9e64c24ebf0d8783a8f7ccfcf348750`
- Prior ChatGPT run closure: `84b8edba110c384386c190c807d419340acf8775`
- Gitlink at request HEAD: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: `REQUEST_CHANGES`

## Scope checked

Design/docs only. No parser implementation or execution was authorized or inspected as a closure. I checked the proposed exact `candidates` grammar against the already-closed `run` v0.2 contract and the stated future full-request/P5 handoff requirements. No other reviewer verdict was used as evidence.

## Blocking findings

### HIGH 1 — outer `candidates.identity_sha256` is present in the exact schema but has no frozen semantics

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_candidates_design_v0.1_2026-09-02.md:9-21` includes a top-level `identity_sha256`, but the prose defines self-digests only for `candidates.root` and each backend record. It never states what the outer digest hashes, nor its exact type/grammar.

Required remediation: freeze the outer identity explicitly, e.g. exact lowercase 64-hex equal to `canonical_sha256({key: value for key,value in candidates.items() if key != "identity_sha256"})`, and require permanent added/missing/retyped/digest-drift fixtures that recompute unrelated inner identities.

### HIGH 2 — the closed run v0.2 deferred candidate→run binding cannot be represented by the proposed exact backend schema

The closed run v0.2 contract deferred `candidate.{backend}.run == final_request.run.{backend}` to the candidates/full-request Gate. However candidates v0.1 fixes each backend record to exact `{backend,candidate_root,identity_sha256}` (`...candidates_design_v0.1...md:23-29`). There is no `run` binding field or other exact immutable run identity carried by a candidate record.

As written, a later full-request validator cannot prove from this section alone which exact final `run.<backend>` a candidate belongs to without adding a new field that this v0.1 exact schema currently forbids.

Required remediation: choose and freeze one model. Prefer adding an exact backend run binding whose value is canonical-equal to the corresponding final `run.<backend>` (or a frozen digest of that exact object), while preserving whatever later candidate payload contract needs. If the binding is intentionally deferred entirely to another future section, amend the already-approved lifecycle contract explicitly so there is a machine-verifiable authority path rather than an impossible `candidate.{backend}.run` requirement.

### HIGH 3 — candidate namespace root itself is not isolated from the closed run roots

`...candidates_design_v0.1...md:21` isolates `candidates.root` from source/submodule, while `:29` only requires the two leaf backend `candidate_root` paths not to overlap either run root. This still permits the outer candidate namespace root itself to equal or be an ancestor/descendant of a run root while its particular attempt/backend leaf happens to be a sibling.

That makes the future namespace authority non-isolated and leaves later mkdir/publication behavior ambiguous.

Required remediation: require `candidates.root.root` itself, plus both derived backend candidate roots, to have no equal/ancestor/descendant overlap with either closed `run.<backend>.identity.root`. Add fixtures for root==run, root ancestor of run, root descendant of run, and cross-backend cases.

### MEDIUM 4 — backend `candidate_root` ancestor-symlink fail-closed rule is not explicitly frozen

The root identity has an explicit existing-ancestor `lstat`/symlink rejection rule (`:21`). Each backend `candidate_root` is only described as a lexical absolute path equal to `<root>/<attempt_id>/<backend>` (`:27`). If `candidates.root` already exists and `<root>/<attempt_id>` is an existing symlink, the leaf path can escape despite the outer-root check.

The acceptance section mentions `existing ancestor symlink` generally, but the authority rule should be explicit rather than relying on fixture interpretation.

Required remediation: apply the same non-strict lexical path validator to each derived `candidate_root` after constructing the exact expected path; reject any existing symlink in every existing prefix. No directory creation or `resolve(strict=True)` is needed.

## Additional exactness to retain in v0.2

- `attempt_id` must explicitly differ from **both** `run.recurrent.run_token` and `run.ttt_fast_weight.run_token`, not an ambiguous singular “the run token”.
- backend labels remain byte-exact and there must be exactly two backends.
- candidate paths remain deterministic `<candidates.root>/<attempt_id>/<backend>` and must not exist merely because static validation ran.
- no ambient denylist, subprocess, project entry, staging, candidate materialization, record/refreeze, P5 export/compose, GPU/CUDA, model/data/checkpoint I/O, training/eval/inference.

## Verdict

`REQUEST_CHANGES`

Progress remains `entry ✅ → source ✅ → interpreter ✅ → environment ✅ → authorities ✅ → run ✅ → candidates 🟡`; 6/8 sections are closed. This review does not authorize candidates implementation or any real preflight/execution.