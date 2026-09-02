# R09-B2 P4-v4 Execution Request `authorities` v0.3 fixture closure review

- Verdict: `APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_AUTHORITIES_STATIC_TOOLS`
- Implementation: `3e6de3b0f1a5fdfa071b5356e1174fdf6ec8afc9`
- Request/ledger: `c7ca4d0361a26a992a1fc4aa332cd23bf3ae8fd2`
- Approved design: `54830a20cab3e2d9995781faf1244684c6bd02d0`
- Previous ChatGPT review: `93725da863f05e1e3175e85468274dc18680aac6`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Scope

Independent static/CPU review only. No real preflight, staging/materialization, candidate generation, record/refreeze, P5 authority/export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized by this review.

## Result

The five fixture gaps from the previous review are now closed without changing the already-reviewed authority production logic:

1. FIFO/non-regular historical artifact is exercised with a writer thread so the test does not hang and the `fstat` regular-file rejection branch is reached.
2. Historical artifact access is permanently asserted to perform one lexical `os.open` with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`; the production path remains fd-bound after that open, closing the pathname-reopen/TOCTOU concern.
3. Historical D005 record non-canonical raw bytes are explicitly rejected even when the decoded object is otherwise semantically valid.
4. Historical `verification.json` pretty-printed bytes are exact-byte bound: semantically equivalent reformatting is rejected by the frozen SHA binding.
5. Verification semantic grammar now has permanent mutations across top-level, `checks`, `matched`, and backend maps for added/missing/false/non-bool cases.

The previously-added permanent regressions for pair/source/verifier identity drift, record backend/schema/status/source/self-digest drift, record swap, environment projection/native/P3/missing-backend drift, verified host-Git argv and PATH shadow, symlink/directory handling, and ambient isolation remain present.

No new production-logic blocker was found. The request HEAD keeps the exact frozen Gitlink.

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_AUTHORITIES_STATIC_TOOLS`

This closes only the `authorities` static section. `run`, `candidates`, and `backends`, plus any real execution request/preflight, remain separate Gates.
