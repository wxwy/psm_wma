# ChatGPT independent review — R09-B2 P4-v4 execution-request authorities v0.3 remediation

- Review date: 2026-09-02
- Latest prior ChatGPT anchor: `02e9022e0032272c0afcb9f19d1a10ac8a5f3099`
- Remediation implementation: `32f0bf9e37f85ebcbd0caf122dbc0b0955144c05`
- Closure request: `162152f42ab9ec1951862cee70fc022c1758f508`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Approved design: `54830a20cab3e2d9995781faf1244684c6bd02d0`

## Verdict

`REQUEST_CHANGES`

The previous two direct implementation defects were partly remediated: the historical record self digest is now independently recomputed, and a lexical final-symlink check plus a dedicated negative fixture were added. However the historical artifact path binding still violates the frozen single-fd / no-pathname-reopen / TOCTOU requirement, and the permanent authorities fixture matrix remains substantially incomplete.

## Findings

### HIGH — historical artifact path authority is still TOCTOU-vulnerable

`tools/g0/r09_b2_p4_v4_execution_preflight.py:165-182`

Current flow is effectively:

1. `lexical.is_symlink()`
2. `lexical.resolve(strict=True)`
3. `_read_regular_nofollow(resolved_path, ...)`

The `O_NOFOLLOW` open therefore protects the already-resolved target, not the lexical authority pathname. The lexical pathname can be replaced after step 1 and followed by step 2; opening the resolved target later does not detect that race. This also means the path identity checks and byte read are not anchored to one fd as required by v0.3.

Required remediation: bind the lexical artifact through the no-follow fd first, `fstat` that fd, derive/verify canonical containment from that already-open object, and consume the bytes from that same fd. Do not use a pre-open `is_symlink()` + later `resolve()` as the security boundary, and do not reopen a derived pathname for the authoritative byte read. Add a permanent TOCTOU/swap fixture proving the lexical pathname cannot be exchanged between checks and read.

### HIGH — permanent authorities fixture matrix is still not closed

`tools/g0/test_r09_b2_p4_v4_execution_preflight.py:629-706`

The remediation adds nested verification-roster mutations and a final lexical symlink fixture, but v0.3 froze a much wider permanent CPU matrix. Missing targeted regressions still include at least:

- historical artifact path/sha plus nested pair/source/verifier identity and revision/blob drift;
- verified host-Git mismatch, fixed historical `git -C <root> show ...` argv drift, and PATH-shadow irrelevance;
- FIFO and directory rejection plus lexical pathname TOCTOU/no-reopen behavior;
- record canonical-raw, backend, schema, status and `d005_sha256` self-digest targeted negatives;
- verification exact pretty-byte binding drift in addition to decoded nested-roster mutations;
- record swap / duplicate-path cases;
- current request environment missing / projection / effective / native / P3 drift under historical authority validation;
- ambient `os.environ` shadow irrelevance.

For intended-branch tests, recompute all non-target outer identities/digests so the test reaches the specific authority branch rather than failing earlier for an unrelated reason.

## Confirmed closed from previous review

- historical `d005_sha256` is now independently recomputed before acceptance;
- verification top/checks/matched/backend semantic key rosters remain frozen;
- historical verifier lookup still uses the supplied verified absolute host Git path;
- current-source `verify_pair()` is not used to self-authorize the historical v2 evidence;
- environment projection cross-binding remains in place;
- `main()` remains hard-stopped; no real preflight/staging/P5/GPU/training authority is granted.

## Closure condition

Return with a new implementation SHA after fixing the lexical single-fd TOCTOU binding and completing the frozen authorities CPU fixture matrix. If those pass without new regressions, the expected verdict is `APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_AUTHORITIES_STATIC_TOOLS`.
