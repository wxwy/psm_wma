# R09-B2 P5 Evidence Git Authority v1.1 design review

## Request / design

- Request commit: `ca0a7cfa226ce23223f8fe1d56376783488187ec`
- Design commit: `e0e9f89002805f88b2c17c04597357e5ad909349`
- Previous ChatGPT review: `8907f184843dd5c006249faf992637cd07c9f739`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_IMPLEMENT_P5_EVIDENCE_GIT_AUTHORITY_STATIC`

This approval is limited to root-side P5 verifier tooling and stdlib CPU tests for the evidence-publication authority contract. It does not authorize any runtime/preflight/refreeze/export/compose/GPU/training operation.

## Findings

### PASS — evidence publication authority is now out-of-band

v1.1 no longer allows the three P4-v4 evidence files, or the currently observed evidence-root HEAD, to authorize themselves. `AUTHORIZED_P4_V4_EVIDENCE` is verifier-owned and can only be populated after a separately reviewed record/refreeze closure in a new reviewed verifier revision. An evidence commit therefore cannot bootstrap its own acceptance.

This closes the previous shared-replacement false-PASS: replacing all evidence files consistently and committing a new clean HEAD must still fail because the presented HEAD differs from the independently frozen authorized commit.

### PASS — submodule identity is exact, not merely clean

The design now requires:

`parent HEAD gitlink == authorized Gitlink == actual cosmos-framework HEAD`

in addition to full-clean state. A clean detached submodule at a wrong revision therefore cannot satisfy the consumer contract.

### PASS — descendant semantics are fail-closed

The accepted evidence root must be exactly the authorized evidence commit. Descendants are not accepted, even if the fixed evidence files are unchanged. This removes ambiguity around later unrelated commits and prevents a descendant HEAD from becoming a new authority source.

### PASS — fixed evidence bytes remain independently bound

The fixed P4-v4 request/result/verification files must be tracked regular files, and their bytes from `git show <authorized_commit>:<path>`, current filesystem bytes, canonical JSON bytes, and frozen verifier-owned content SHA256 must agree. Symlink, untracked, mutable, blob/current, or canonicalization drift remains fail-closed.

## Implementation constraints

1. Before a real P4-v4 record/refreeze publication exists, `AUTHORIZED_P4_V4_EVIDENCE` must be an explicit uninitialized state and the verifier must hard-FAIL before consuming P4-v4 evidence. Do not populate it with placeholder/guessed evidence identity.
2. The authority must not be overridable by CLI, environment, request JSON, evidence files, or caller-owned data.
3. The constant schema must cover both fixed backends (`recurrent`, `ttt_fast_weight`) and every fixed request/result/verification evidence path/content digest required by the consumer; tests must not silently exercise only one backend.
4. If a tree SHA256 is retained, define and test one deterministic verifier-owned derivation. It is defense-in-depth; the exact authorized commit plus fixed content hashes remains mandatory.
5. Permanent CPU negatives must include: mutually consistent replacement committed as a new clean HEAD, clean wrong submodule revision, descendant HEAD, dirty/untracked evidence root, symlinked evidence file, and content/canonical-byte drift.
6. Populating/changing `AUTHORIZED_P4_V4_EVIDENCE` after a future record/refreeze closure is a new reviewed verifier revision and requires a separate review. This approval does not authorize that future mutation.

## Gate decision

Authorized now:

- implement the P5 evidence Git-authority verifier checks;
- implement/update stdlib CPU Git fixtures and negative tests.

Not authorized:

- P4-v4 preflight execution;
- real staging creation;
- P4 record/refreeze or evidence publication;
- population of a future real `AUTHORIZED_P4_V4_EVIDENCE` identity;
- P5 export/compose or removal of execution-blocking stubs;
- `load_experiment_from_toml`;
- torchrun/CUDA/GPU;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- P5 runtime closure;
- B2-T or Local Memory training.
