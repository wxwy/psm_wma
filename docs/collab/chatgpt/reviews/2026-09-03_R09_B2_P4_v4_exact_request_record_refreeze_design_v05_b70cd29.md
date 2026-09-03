# Independent Design Review — R09-B2 P4-v4 Exact Request / Record-Refreeze v0.5

- Gate: `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-DESIGN`
- Design SHA under review: `b70cd294f4d9896cbe297d96535540b62cf43391`
- Ledger/request SHA observed at review start: `911e7cee02b32564448c46a56c6110c1e72001cb`
- Prior design SHA: `1ec06676f8ff55bb2869e95327ff8226ed9f3b89`
- Prior ChatGPT review commit: `b4242f3bfbe5ffed7aa7bd18a4fa529b721e9a1f`
- Design: `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.5_2026-09-03.md`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved remote `V2` through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `911e7cee02b32564448c46a56c6110c1e72001cb`; it is the ledger/review-request commit and its parent is exactly design SHA `b70cd294f4d9896cbe297d96535540b62cf43391`.

The remediation from prior review `b4242f3` to design SHA `b70cd29` is documentation/status-only: it adds v0.5 and updates `SESSION.md` / `TODO.md`; no production P4/P5 tooling changed. The Cosmos Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. GitHub exposes no commit statuses for the design SHA; the submitted `git diff --check` is repository-recorded evidence rather than independently rerun CI here.

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXACT_REQUEST_RECORD_REFREEZE_STATIC_TOOLS`

v0.5 closes the sole HIGH from the v0.4 review without reopening the already-closed candidate namespace contract.

### Closure of prior HIGH — execution logs are now outside the candidate namespace

The new `logs_v1={root,stdout,stderr,sha256}` freezes a verifier-owned external log root that is caller-independent, initially absent, and two-way non-overlapping with source/submodule, both run roots, `candidates.root` and all descendants, and the fixed P5 evidence publication paths. `stdout`/`stderr` are exact children `stdout.log` / `stderr.log`; after execution the log root may contain only those two `0600` regular non-symlink files. The design explicitly states that no logging operation may add or replace any file in the candidate namespace.

Candidate `result.json` remains solely the existing canonical candidate payload governed by the request/result/verification chain; the logging layer must not create, replace, or reserialize it. Permanent fixtures explicitly require a logged PASS candidate to retain the exact four-file set and require injected stdout/stderr anywhere in the candidate namespace to be rejected. The design also explicitly forbids modifying `r09_b2_p4_v4_static_contract.py` candidate file-set semantics.

This resolves the v0.4 incompatibility with the already-closed PASS candidate contract.

## Retained approved design contracts

The following previously-reviewed contracts remain acceptable and must be implemented exactly rather than reopened:

- production execution/record/publication authority constants remain `None` in this static implementation Gate;
- exact nested authority key/type/range/path/order/self-digest grammar;
- `cpu_max` and `wall_seconds` are bounded integers with explicit units; only `network/gpu/torch/torchrun` are fixed false;
- `tree_sha256` means SHA256 of raw `git cat-file tree` bytes, distinct from the Git tree OID;
- the existing final P4 request wire remains unchanged; final run/candidate identities are verifier-derived from the planned commitment;
- candidate expectation, parent-request join, request/result/verification provenance and cross-pair ownership remain exact;
- six payload SHA values are verifier-derived from the six raw bytes, never caller-supplied;
- publication is clean-base + verifier-owned temporary index + exact six-path `100644` tree diff;
- the record commit must contain the verified new tree and exactly one parent equal to the frozen base;
- publication uses one `update-ref ref new base` CAS, followed by one-shot checked-out materialization and full-clean verification;
- post-CAS materialization/final-verification failure is permanently `POISONED_PUBLISHED`, with no retry/repair and no P5 authority;
- record/refreeze does not set `AUTHORIZED_P4_V4_EVIDENCE`; that requires a later independent P5 verifier revision.

## Static implementation acceptance boundary

This approval authorizes only implementation of root static tooling and stdlib CPU fixtures described by v0.5. Implementation closure must be reviewed on the exact implementation SHA before any next Gate.

The implementation must not generate or freeze real production authority values, must not create or execute a real exact request/preflight, must not create real run/staging/candidate/log/evidence roots outside test-local temporary fixtures, and must not perform real record/refreeze publication.

No P5 authority/export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory/LIBERO training is authorized by this verdict.
