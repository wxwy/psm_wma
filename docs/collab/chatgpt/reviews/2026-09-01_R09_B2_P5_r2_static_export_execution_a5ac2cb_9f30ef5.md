# R09-B2 P5 r2 isolated static-export execution review

- Request commit: `a5ac2cb1d33ab3231209b5fbf88b6ef3c6a47e59`
- Reviewed exporter/verifier revision: `9f30ef5054e11f58c60ec54d587924a1d0f2a2a4`
- Evidence-root revision: `8bde8c12876219b1a36d50b604e05701bf550e3e`
- Frozen production revision: `ddb4e0eae97fb545d5239c1ddb6d4387170f3780`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_RUN_P5_STATIC_EXPORT**

## Scope

This is a one-shot CPU-only authorization for the exact r2 static-export command frozen in request `a5ac2cb...`.

It authorizes exactly one invocation using:

- parent bootstrap: `/opt/conda/bin/python3.11 -I` from `/tmp`;
- exporter root: `/disk/rl/psm_wma_p5_test_9f30ef5` at `9f30ef5054e11f58c60ec54d587924a1d0f2a2a4`;
- production root: `/disk/rl/psm_wma_p4_d005_retry` at `ddb4e0eae97fb545d5239c1ddb6d4387170f3780`;
- evidence root: `/disk/rl/psm_wma_p5_evidence_8bde8c1` at `8bde8c12876219b1a36d50b604e05701bf550e3e`;
- Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb` for all three roots;
- canonical output: `/disk/rl/psm_wma_p5_static_export_20260901_r2`.

Any command, root, revision, Gitlink, output path, environment, retry policy, or exporter/verifier code change requires a new execution review.

## Findings

### Reviewed-code identity is bound before project import

The r2 command preserves the previously approved isolated bootstrap pattern. It starts from `/tmp` with Python `-I` and uses only standard-library modules before the trust checks.

Before inserting the exporter root into `sys.path`, it machine-checks for each production/evidence/exporter root:

- exact canonical absolute path;
- exact frozen HEAD;
- exact Cosmos Gitlink;
- exact submodule HEAD;
- root tracked+untracked full-clean state;
- submodule tracked+untracked full-clean state.

It also requires the new canonical output to be absolute, absent, and non-overlapping with all three frozen roots. Only after those checks pass is the exact exporter root added to `sys.path` and `run_parent_export` imported.

### r2 uses the newly reviewed locale-adjusted exporter/verifier contract

The executable exporter/verifier revision is the statically reviewed `9f30ef5...` revision approved in ChatGPT review `2026-09-01_R09_B2_P5_verifier_locale_94ced23_9f30ef5.md`.

That revision preserves exact P4 `set`/`unset`/`inherit_allowlist` binding and requires the effective child environment to equal the frozen P4 set plus exactly `LC_CTYPE=C.UTF-8`. Extra effective keys or a changed locale value fail closed. The D005-bound child request digests remain frozen to the locale-adjusted request identities.

### No implementation drift in this execution request

The diff from the prior ChatGPT static approval commit `07299f53...` to request `a5ac2cb...` changes only `SESSION.md`, `TODO.md`, and the execution request text in `CODEX_INBOX.md`. No exporter, verifier, test, production, or submodule code changed. The root Gitlink remains `21d064f...`.

### Failure and success semantics remain narrow

The authorized execution is CPU-only and offline. It may perform only the two child resolved-config compositions required by P5. The existing child guard rejects CUDA initialization and the parent requires pair-verifier `PASS` before canonical promotion.

If any child, parse, envelope, or verifier stage fails, the attempt must retain `failure.json`, canonical output must remain absent, and this authorization permits no retry.

## Gate decision

**APPROVE_TO_RUN_P5_STATIC_EXPORT** is granted for exactly one execution of the frozen r2 command in request `a5ac2cb1d33ab3231209b5fbf88b6ef3c6a47e59`.

A PASS result does not close P5. The generated resolved-config envelopes, verification result, exact runtime command/provenance, root identities, and output SHA/evidence must be submitted for an independent closure review.

This approval does **not** authorize:

- a second run or retry;
- changing any command/root/revision/path/environment;
- CUDA or GPU use;
- `torchrun` or distributed initialization;
- model, dataloader, optimizer, or checkpoint construction;
- weights/data/MP4 access;
- training, evaluation, or inference;
- P5 closure;
- B2-T or any later Gate.
