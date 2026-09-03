# Independent Implementation Review — R09-B2 P4-v4 Exact Request / Record-Refreeze Static Tools

- Gate: `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-STATIC-TOOLS`
- Implementation SHA under review: `6c521c115b05006d20d8ce37288b72331c9cb7f2`
- Ledger/request SHA observed at review start: `a37f9be1e4626579606769c7dab2ca9bc579c7c1`
- Approved design SHA: `b70cd294f4d9896cbe297d96535540b62cf43391`
- Design approval review: `7194e6452cdbb5914910f0a84ccd01b8c691d1b8`
- Implementation parent: `1280b442c30c90eca39165b5bdf3346e697ca22e`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved remote `V2` through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `a37f9be1e4626579606769c7dab2ca9bc579c7c1`; it is the ledger/review-request commit and its parent is exactly implementation SHA `6c521c115b05006d20d8ce37288b72331c9cb7f2`.

The implementation commit changes only `SESSION.md`, `TODO.md`, `tools/g0/r09_b2_p4_v4_static_contract.py`, and `tools/g0/test_r09_b2_p4_v4_static_contract.py`. No P4 execution/preflight entry, P5 verifier/exporter, or Cosmos submodule code changed. The Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. `AUTHORIZED_P4_V4_EVIDENCE` remains `None`, and `run_parent_export()` still hard-stops before export. GitHub exposes no statuses/check-runs for the implementation SHA; the submitted `13/13 PASS`, `py_compile`, and `git diff --check` are repository-recorded evidence rather than independently rerun CI here.

## Verdict

`REQUEST_CHANGES`

The implementation does not authorize runtime side effects, but it cannot close the requested static-tools Gate. Two HIGH issues remain.

## HIGH-1 — log namespace exclusion is still caller-selected rather than verifier-owned

**File:** `tools/g0/r09_b2_p4_v4_static_contract.py:38-53`

### Root cause

The approved v0.5 design requires `logs.root` to be caller-independent and to be non-overlapping with every frozen source/submodule, both run roots, the complete candidate namespace, and the fixed P5 evidence publication namespace.

The implementation exposes:

```python
validate_logs(value, forbidden_roots)
```

and only verifies that `forbidden_roots` is a non-empty tuple. The exclusion set itself is not derived from an admitted final request or any verifier-owned authority, and its members are not bound to the frozen source/run/candidate/P5 identities.

Therefore a caller can omit a mandatory namespace. For example, a correctly re-digested `logs.root=/candidates/attempt/logs` can pass when `forbidden_roots=("/source",)` is supplied. This defeats the exact non-overlap property while all local schema/digest checks still succeed.

The new fixture at `tools/g0/test_r09_b2_p4_v4_static_contract.py:25-34` does not cover this: it supplies the expected forbidden roots itself and only mutates `stdout` or a source-overlapping root.

### Required acceptance criteria

1. Do not trust an arbitrary caller-provided list/tuple as the namespace authority.
2. Derive the forbidden namespace set from verifier-owned, already-validated inputs (final request/planned commitment/source/run/candidates plus fixed P5 evidence paths), or accept an exact structured namespace object whose keys and identities are independently validated before `logs.root` is accepted.
3. Add permanent fixtures where the caller omits/substitutes each mandatory source/submodule/run/candidate/P5 namespace; a log root inside any omitted namespace must still fail after the logs self-digest is recomputed.
4. Preserve the closed PASS/FAIL candidate file-set semantics; do not solve this by widening candidate directories.
5. Keep production authority values `None` and perform no real execution.

## HIGH-2 — the requested full static-tools closure is materially incomplete relative to approved v0.5

**Files:**
- `tools/g0/r09_b2_p4_v4_static_contract.py:17-53`
- `tools/g0/test_r09_b2_p4_v4_static_contract.py:25-34`
- `SESSION.md:8`
- `TODO.md:92`

### Root cause

The Inbox requests `APPROVE_TO_CLOSE_P4_V4_EXACT_REQUEST_RECORD_REFREEZE_STATIC_TOOLS`, while `SESSION.md` itself describes this SHA as the **first minimal implementation** and states that it only adds `AUTHORIZED_P4_V4_EXECUTION_AUTHORITY=None` plus a no-I/O log schema/digest/path/non-overlap validator.

That is a valid incremental slice, but it is not the complete static implementation approved by design v0.5. The approved design also freezes, among other items:

- full `execution_authority_v1` nested grammar and binding;
- final request construction from the planned commitment;
- `candidate_expectation_v1` provenance and parent-request join;
- `record_authority_v1` and verifier-derived six-payload SHA binding;
- `record_publication_authority_v1`;
- raw Git-tree SHA versus tree-OID checks;
- clean-base temporary-index six-path tree construction;
- single-parent commit validation, CAS race semantics, post-CAS materialization, and `POISONED_PUBLISHED` fixtures;
- production execution, record, and publication authority constants all defaulting to `None`.

At this SHA, only the execution authority constant and `logs_v1` lexical validator were added. No record authority, publication authority, candidate expectation/parent-join implementation, tree/CAS static machinery, or corresponding fixture matrix is present. Closing the entire static-tools Gate would therefore allow the project state to advance without the implementation closure that the approved design explicitly requires.

### Required acceptance criteria

Choose one of two auditable paths:

**A. Narrow the Gate/slice:**
- rename/reframe this request as a log-namespace static-validator slice with a slice-specific approval token;
- keep `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-STATIC-TOOLS` `IN_PROGRESS`;
- fix HIGH-1 and request same-SHA slice review.

**B. Request full Gate closure:**
- implement the remaining v0.5 static contracts and test-local stdlib fixtures listed above;
- add explicit production `None` authorities for execution/record/publication as designed;
- cover exact nested grammar, provenance/foreign-valid-pair rejection, tree identity, six-path diff, wrong-parent/merge, CAS race, post-CAS failure, and poisoned-state acceptance cases;
- preserve `AUTHORIZED_P4_V4_EVIDENCE=None` and the P5 exporter hard-stop;
- do not create or execute real request/run/staging/candidate/log/evidence roots outside test-local temporary fixtures;
- submit the resulting new implementation SHA for a new same-SHA closure review.

The current `13/13 PASS` is useful evidence for the small existing candidate/log helper suite, but it cannot evidence contracts that are not implemented or tested yet.

## Accepted implementation properties

The following are correct and should be retained:

- `AUTHORIZED_P4_V4_EXECUTION_AUTHORITY` is still `None`;
- logs self-digest uses the P4 canonical JSON spelling with trailing newline;
- `stdout`/`stderr` are exact children `stdout.log` / `stderr.log` of the lexical log root;
- lexical ancestor/descendant overlap checking itself is symmetric;
- the closed candidate exact file-set implementation was not modified;
- `AUTHORIZED_P4_V4_EVIDENCE` remains `None`;
- `run_parent_export()` remains hard-stopped;
- Cosmos Gitlink is unchanged;
- no real preflight/publication/GPU/training path was opened.

## Scope

Keep `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-STATIC-TOOLS` in `IN_PROGRESS/REVIEW`. This review authorizes no production exact-request generation, P4 preflight/staging/materialization/candidate/log creation, record/refreeze/evidence publication, P5 authority/export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory/LIBERO training.
