# R09-B2 P5 Evidence Git Authority v1.1 implementation review

## Request / implementation

- Request commit: `6b2d0bb032e040ff5cabec600a0821dbedc8b63b`
- Implementation commit: `3e3a853c61dd32888932041e6afbfac466818e09`
- Approved design: `e0e9f89002805f88b2c17c04597357e5ad909349`
- Design approval: `7ecc1c8051abcf98867643b5ef7a246f3c8457b3`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_CLOSE_P5_EVIDENCE_GIT_AUTHORITY_STATIC`

This closes only the static P5 evidence-publication authority tooling and CPU-test contract.

## Findings

### PASS — authority is verifier-owned and currently uninitialized fail-closed

`tools/g0/verify_r09_b2_p5_full_config_diff.py` defines `AUTHORIZED_P4_V4_EVIDENCE` as `None` in the reviewed implementation. `verify_pair()` requires `_authorized_p4_v4_evidence()` before loading P4-v4 evidence; an unset authority therefore fails before P4-v4 evidence can become a PASS source.

No CLI, environment, P5 request, or P4 evidence field is used to populate the production authority. The unittest monkeypatch is test-only fixture injection and does not create a production caller-owned provenance path.

### PASS — exact publication identity is independently rebound

The verifier requires:

- evidence root and its `cosmos-framework` checkout full-clean;
- `HEAD == authorized commit` exactly; descendants are rejected;
- raw tree content SHA256 equals the frozen authority;
- parent `ls-tree` Gitlink equals the frozen Gitlink;
- actual submodule HEAD equals the same frozen Gitlink;
- both fixed backends and all three fixed files (`request.json`, `result.json`, `verification.json`) are present in the authority schema;
- each fixed path is a tracked regular file in the authorized commit;
- authorized-commit bytes and current bytes each hash to the verifier-owned frozen digest.

`load_p4_v4_preflight()` then performs the existing canonical-JSON and P4-v4 nested evidence validation after publication authority succeeds. Thus Git publication identity and semantic P4-v4 evidence validation remain separate checks.

### PASS — shared replacement and relocation-style publication attacks are covered

Permanent CPU Git fixtures cover:

- mutually consistent replacement of all six evidence files followed by a new clean commit -> FAIL because HEAD is not the exact authorized commit;
- unrelated clean descendant -> FAIL;
- clean submodule at a different HEAD -> FAIL;
- current fixed-file byte drift -> FAIL;
- symlink replacement -> FAIL;
- untracked evidence-root content -> FAIL.

These close the v1.0 false-PASS where a newly committed mutually consistent evidence set could otherwise self-authorize.

## Non-blocking test note

A dedicated assertion for the literal default `AUTHORIZED_P4_V4_EVIDENCE is None -> verify_pair FAIL` would improve regression readability. It is not a blocker here because the reviewed production path explicitly rejects any non-Mapping authority before evidence loading and the committed default is `None`.

## Gate decision / authorization

Authorized:

- close `G0-R09-B2-P5-EVIDENCE-GIT-AUTHORITY` static tooling;
- continue with separately reviewed design/static work that lists this closure as a prerequisite.

Not authorized:

- populating `AUTHORIZED_P4_V4_EVIDENCE` with future real P4-v4 evidence identity;
- P4-v4 preflight execution or staging;
- candidate generation;
- P4 record/refreeze or evidence publication;
- P5 export/compose or removing execution-blocking stubs;
- `load_experiment_from_toml` execution;
- torchrun/distributed/CUDA/GPU;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- P5 runtime closure;
- B2-T or Local Memory training.

Future real authority values may only be introduced after an independently reviewed P4-v4 record/refreeze closure, in a new reviewed verifier revision.
