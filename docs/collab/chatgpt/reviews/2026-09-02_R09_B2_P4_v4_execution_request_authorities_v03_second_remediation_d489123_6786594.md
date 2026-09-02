# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request Authorities v0.3 second remediation

- Verdict: `REQUEST_CHANGES`
- Reviewed implementation: `d48912343525e8674f5f1070b0e4aeb07c6ecaab`
- Request/ledger head: `6786594e27ec669e5206f7d9ffe722aaa0636543`
- Approved design: `54830a20cab3e2d9995781faf1244684c6bd02d0`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: authorities static tooling / stdlib CPU only. No real preflight/staging/materialize/candidate/refreeze/P5/GPU/training authority.

## Independent findings

The previous implementation blockers are closed:

1. Historical artifact authority is now opened directly from the lexical path with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`; `fstat`, containment through the opened fd, and raw-byte reading all consume the same opened object. The prior pathname-check -> resolve -> reopen TOCTOU split is removed.
2. Historical D005 records now independently recompute `d005_sha256` from the decoded record with the self field removed before accepting the record.
3. Existing historical-D005 authority architecture remains consistent with the approved v0.3 design: fixed v2 evidence bytes, fixed historical source/verifier blob, verified absolute host-Git lookup, and current-request linkage only through the already-closed environment grammar.

No new main-validator blocker was found.

## BLOCKER — frozen permanent CPU fixture matrix is still incomplete

The approved v0.3 design freezes a substantially broader regression matrix than the tests currently present. The remediation adds directory rejection and record backend/schema/status/source/self-digest mutations, on top of the earlier positive, binding/outer-identity, lexical-symlink, partial verification-roster, historical-source/wrong-host-Git/verifier-blob, and one environment-effective drift fixture. That is not yet the frozen matrix required for closure.

At minimum add permanent targeted CPU fixtures for the still-uncovered contract branches below. Each request/authority mutation must recompute all non-target inner/outer identities so the intended branch is reached.

### A. Host-Git TCB / ambient isolation

- Prove the historical lookup argv is exactly `[verified_host_git, "-C", root, "show", historical_revision + ":" + historical_verifier_path]`; reject `-C` drift / argument reorder / extra argument / alternate Git path.
- PATH-shadow fixture: install an executable named `git` earlier in `PATH`, mutate ambient `PATH`, and prove it cannot influence the lookup or result.
- Ambient `os.environ` shadow must not affect authority validation.

### B. Artifact path / single-fd authority

- FIFO rejection in addition to directory/symlink.
- Explicit TOCTOU/single-open fixture: replace/retarget the lexical pathname after the authority fd has been opened and prove validation consumes the already-open object, with no pathname reopen. Instrument `os.open`/path reads as necessary and assert one authority-object open.
- Out-of-root fd target / containment rejection.

### C. Historical binding/source/verifier identity matrix

- Artifact `relative_path` drift (not only SHA drift).
- Pair `identity_sha256` drift separately from outer authorities identity.
- `historical_source` Gitlink and submodule revision drift, plus historical-source identity drift.
- `historical_verifier` relative path, root revision, Git-blob SHA field, and identity drift.
- Duplicate/swap artifact bindings, including recurrent/TTT swap and duplicate paths, as explicitly frozen by v0.3.

### D. Historical record exact-semantic/raw grammar

- Non-canonical record raw with semantically identical JSON must fail the canonical-record requirement.
- Cover historical source Gitlink/submodule drift inside record source, not only root revision.
- Keep backend/schema/status/self-digest targeted failures already added.

### E. Verification evidence

- Exact historical pretty-byte binding: semantically identical compact/reformatted verification bytes must fail the fixed raw SHA binding.
- Complete the design-frozen nested roster matrix: for top/checks/matched/backend levels exercise added + missing + false + non-bool/retyped branches, rather than the current representative subset only.

### F. Current environment cross-binding

Current remediation only targets an effective-set drift. Add targeted fixtures for:
- direct `d005_projection` drift,
- native-loader environment drift,
- P3 `PSM_R09_B1_TTT_ENABLED` drift,
- missing environment authority/backend section.

## Closure condition

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_AUTHORITIES_STATIC_TOOLS` is appropriate once the above frozen permanent regression matrix is present and passing, with no new implementation drift. The core authority implementation does not need a redesign.

Real execution/preflight/staging/P5/GPU/training remains unauthorized.