# Independent Design Review — R09-B2 P4-v4 Exact Request / Record-Refreeze v0.4

- Gate: `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-DESIGN`
- Design SHA under review: `1ec06676f8ff55bb2869e95327ff8226ed9f3b89`
- Ledger/request SHA observed at review start: `d901c2d49cf76288918a1077c2572877c43205fa`
- Prior design SHA: `7679b4f9d15fff3c359359c29a53b7ff37b78f44`
- Prior ChatGPT review commit: `04592823565de7a59d2ef4a6b1c970326f780c58`
- Design: `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.4_2026-09-03.md`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved remote `V2` through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `d901c2d49cf76288918a1077c2572877c43205fa`; it is the ledger/review-request commit and its parent is exactly design SHA `1ec06676f8ff55bb2869e95327ff8226ed9f3b89`.

`0459282 -> 1ec0667` is one documentation/status-only remediation commit: it adds the v0.4 design and updates `SESSION.md` / `TODO.md`; no production P4/P5 tooling changed. The Cosmos Gitlink at the design SHA remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. GitHub exposes no check-runs for this design SHA; the submitted `git diff --check` is repository-recorded evidence rather than an independently rerun CI result here.

## Verdict

`REQUEST_CHANGES`

v0.4 correctly closes the three HIGH issues from the v0.3 review:

1. `resources_v1` now gives exact integer type/range/unit for `cpu_max` and `wall_seconds`, while only `network/gpu/torch/torchrun` are fixed false; command/environment/log/stop nested value grammar is now explicit.
2. `tree_sha256` is explicitly defined as SHA256 of raw `git cat-file tree` bytes and is separated from the Git tree OID, matching the already-closed P5 evidence spelling.
3. publication now uses a coherent clean-base model: current checkout/index stay at base while a verifier-owned temporary index constructs the six-blob tree/commit; CAS is followed by one-shot checked-out materialization and a fail-closed `POISONED_PUBLISHED` state if the post-CAS step fails.

Those corrections should be retained.

One new HIGH remains because the newly frozen execution-log namespace conflicts with the already-closed candidate namespace contract.

## HIGH-1 — `logs_v1` places persistent stdout/stderr inside a candidate namespace whose file set is already exact-closed

**Design:** `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.4_2026-09-03.md:11`

**Closed production contract:** `tools/g0/r09_b2_p4_v4_static_contract.py:52-73,103-122`

### Root cause

v0.4 freezes:

```text
logs_v1={stdout,stderr,json,sha256}
```

with all three values required to be paths inside `candidate_root`, with basenames `stdout.log`, `stderr.log`, and `result.json`.

The already-closed PASS candidate contract is stricter:

```python
if {entry.name for entry in candidate.iterdir()} != {*PAYLOAD_FILES, "candidate_link.json"}:
    raise ValueError("PASS candidate file set differs")
```

where `PAYLOAD_FILES == ("request.json", "result.json", "verification.json")`.

Therefore a successful backend candidate directory is allowed to contain exactly four files:

```text
request.json
result.json
verification.json
candidate_link.json
```

Persisting `stdout.log` and/or `stderr.log` in that backend candidate directory makes every otherwise-valid PASS candidate fail `load_pass_candidate()` before record/refreeze.

Moving those logs higher within the existing candidate-root subtree does not solve the contract. `_reject_failed_identity_reuse()` treats every direct child of the candidate history root as an attempt directory, and `stage_atomic_publication()` requires the selected attempt directory to contain exactly the two backend directories. A persistent log file or extra log directory in those levels therefore also violates existing closed namespace grammar.

The `json` basename `result.json` additionally needs explicit ownership: it must remain the existing canonical candidate payload, not a second logging artifact or an alias whose lifecycle can diverge from the candidate result chain.

This is a design-level blocker because the current wording cannot be implemented while preserving the already-approved candidate contract.

### Required acceptance criteria

1. Remove persistent `stdout.log` / `stderr.log` paths from the entire `candidates.root` subtree. Do not reopen or weaken the closed PASS/FAIL candidate file-set grammar.
2. If execution logs must persist, freeze a verifier-owned **separate log namespace** (for example an exact `log_root`) that is outside and non-overlapping with:
   - source root and `cosmos-framework`;
   - both run roots;
   - `candidates.root` and all attempt/backend descendants;
   - the fixed P5 evidence publication paths.
   Its path grammar, initial-absence rules, no-symlink rules, and one-shot ownership must be exact and caller-independent.
3. Keep candidate `result.json` solely as the existing candidate payload governed by the request/result/verification chain. If `logs_v1.json` is intended to refer to that exact file rather than to a separate log artifact, state that explicitly and ensure the logging layer never creates/replaces/re-serializes it independently. A simpler contract is to keep process logs entirely outside the candidate tree.
4. Freeze lifecycle semantics unambiguously:
   - pre-execution log targets are absent;
   - after execution any persisted stdout/stderr targets are regular non-symlink files in the separate log namespace;
   - creation/failure of logs must not add any file to a PASS or FAIL candidate directory beyond the already-closed exact sets.
5. Add permanent fixtures proving:
   - a successful logged execution still leaves each PASS backend directory with exactly `{request.json,result.json,verification.json,candidate_link.json}`;
   - any stdout/stderr artifact injected anywhere in the candidate namespace is rejected by the existing candidate verifier;
   - log-root overlap/substitution/symlink/path drift is rejected;
   - no caller or ambient path can redirect logs into source/run/candidate/P5 evidence namespaces.
6. Do not change `r09_b2_p4_v4_static_contract.py` candidate file-set semantics to accommodate the new logs. The remediation belongs in the new execution/log design, not by reopening a closed Gate.

## Accepted v0.4 direction

The following v0.4 changes close the prior review and should not be reopened by the next revision:

- exact execution nested type/range/path/order grammar;
- `cpu_max`/`wall_seconds` integer units and bounds; only the four capability booleans are false;
- `tree_sha256 = SHA256(raw git tree bytes)` with Git tree OID as a distinct identity;
- final P4 request wire remains unchanged and final candidates are verifier-constructed;
- candidate expectation/record authority and foreign-valid-pair parent join remain explicit;
- six payload SHA values remain verifier-derived, not caller-provided;
- publication uses clean base + verifier-owned temporary index + exact six-path tree diff;
- record commit has exact new tree and exactly one parent equal to base;
- checked-out CAS has one-shot post-CAS materialization and permanent `POISONED_PUBLISHED` on post-CAS failure;
- production execution/record/publication authorities remain `None` in this static Gate;
- record/refreeze still does not set P5 `AUTHORIZED_P4_V4_EVIDENCE`.

## Scope

Keep this design Gate in `REVIEW`. Do not implement the static tooling until a revised design closes HIGH-1.

This review authorizes no exact production request generation, real P4 preflight/staging/materialization/candidate/run-root creation, record/refreeze/evidence publication, P5 authority/export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory/LIBERO training.
