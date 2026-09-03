# Independent Design Review — R09-B2 P4-v4 Exact Request / Record-Refreeze v0.3

- Gate: `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-DESIGN`
- Design SHA under review: `7679b4f9d15fff3c359359c29a53b7ff37b78f44`
- Ledger/request SHA observed at review start: `2031779fe53ba9372d37d13cc831f7c499ce1ff3`
- Prior design SHA: `69edc1bee45656bcd2ea73065f8430ddc842c6f6`
- Prior ChatGPT review commit: `0b518b9fb5750126db60d4d174edaeaf44373cd3`
- Design: `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.3_2026-09-03.md`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved remote `V2` through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `2031779fe53ba9372d37d13cc831f7c499ce1ff3`; it is the ledger/review-request commit and its parent is exactly design SHA `7679b4f9d15fff3c359359c29a53b7ff37b78f44`.

`0b518b9 -> 7679b4f` is one documentation/status-only remediation commit: it adds the v0.3 design and updates `SESSION.md` / `TODO.md`; no production P4/P5 tooling changed. The Cosmos Gitlink at the design SHA remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. GitHub exposes no check-runs for this design SHA; the submitted `git diff --check` is repository-recorded evidence rather than an independently rerun CI result here.

## Verdict

`REQUEST_CHANGES`

v0.3 closes most of the structural gaps from v0.2: final P4 candidate items are now explicitly mapped, candidate expectation/record authority distinguishes request-owned versus runtime-observed evidence, six payload SHA values are verifier-derived, and the new record commit is required to have exactly one parent equal to the frozen base. Those improvements should be retained.

Three remaining HIGH issues still prevent a unique, internally consistent static implementation.

## HIGH-1 — execution-authority value grammar is internally contradictory and still under-specified

**Design:** `docs/build/PSM-WMA_R09_B2_P4_v4_exact_request_record_refreeze_design_v0.3_2026-09-03.md:7-9`

### Root cause

The design freezes:

```text
resources_v1={cpu_max,wall_seconds,network,gpu,torch,torchrun,sha256}
```

and then states that the “后五值固定 false”. In the declared field order, those five values are:

`wall_seconds, network, gpu, torch, torchrun`.

Taken literally, this freezes `wall_seconds=false`, which contradicts the stated role of the execution authority as a bounded CPU-only execution contract. Interpreting the sentence as “the four capability booleans are false” would produce a different implementation than the literal design.

The same paragraph gives exact key sets but still does not freeze the value grammar needed for permanent type/range fixtures: whether `argv` is a non-empty `list[str]`, whether `cwd`/log paths are canonical absolute lexical paths, the exact environment mapping grammar, numeric type/unit/range for `cpu_max` and `wall_seconds`, or the exact type/order/member set of `stop.fail_on`.

### Required acceptance criteria

1. Correct `resources_v1` unambiguously. Freeze exact types and semantics for `cpu_max` and `wall_seconds` (including units and allowed range); freeze only the actual capability booleans `network/gpu/torch/torchrun` to `false` unless a different reviewed contract is intended.
2. Freeze exact value grammar for every execution-authority nested field, not only its key set:
   - `command.argv`, `cwd`, `environment`;
   - `resources.cpu_max`, `wall_seconds`, capability booleans;
   - `logs.stdout/stderr/json` path grammar and existence/isolation requirements;
   - `stop.fail_on`, `one_shot`, `cleanup_retry_repair`.
3. Keep all three production authorities `None` in the static implementation Gate.
4. Add permanent fixtures for wrong type/range/unit, extra/missing nested members, path substitution, and boolean/value drift.

## HIGH-2 — the checked-out CAS pre-state is mutually impossible

**Design:** `...exact_request_record_refreeze_design_v0.3_2026-09-03.md:21-23`

### Root cause

v0.3 simultaneously requires, before CAS:

- worktree/index are “精确准备 verified new_tree”;
- root/submodule are full-clean;
- `HEAD == ref == base`;
- `write-tree == base`.

But `new_tree` must differ from `base_tree` by exactly six new evidence blobs. Therefore these conditions cannot all be true:

- if the current index/worktree already represent `new_tree`, `git write-tree` cannot equal the base tree;
- if `HEAD==base`, `write-tree==base`, and the checkout is full-clean, the index/worktree represent the base state rather than the six-file `new_tree` state.

This is not an implementation detail; it makes the frozen publication state machine unsatisfiable.

### Required acceptance criteria

Choose and freeze exactly one coherent publication model. A clean-base plumbing model is acceptable, for example:

1. **Pre-CAS:** root/submodule full-clean, `HEAD==target_ref==base_commit`, current index/write-tree equal the base tree, and the six target paths are absent.
2. Build six blobs, `new_tree`, and the single-parent record commit without modifying the current checkout/index (for example via a verifier-owned temporary index or equivalent plumbing object construction).
3. Verify `new_commit.tree == new_tree` and its sole parent is `base_commit`, then perform the single CAS `update-ref target_ref new_commit base_commit`.
4. Because the target ref is explicitly checked out, freeze the one-shot post-CAS operation that materializes `new_commit` into the current index/worktree. No ambient/manual reset may be outside the reviewed state machine.
5. Verify final `HEAD==ref==new_commit`, index/write-tree==`new_tree`, root/submodule full-clean, exact six current bytes/modes/blobs, and no other diff.
6. If CAS succeeds but post-CAS materialization/verification fails, freeze the state as `POISONED_PUBLISHED`; no retry/repair and no P5 authority.
7. Add failure-injection fixtures before CAS, during CAS/ref race, during post-CAS materialization, and during final clean verification.

An alternative staged-before-CAS model is possible only if the design explicitly drops the contradictory pre-CAS “full-clean/write-tree==base” claims and freezes the exact expected staged diff. The design must choose one model rather than leave this to implementation.

## HIGH-3 — `tree_sha256` identity is not defined relative to Git tree OIDs

**Design:** `...exact_request_record_refreeze_design_v0.3_2026-09-03.md:7-9,21`

### Root cause

The design introduces `source_binding_v1.tree_sha256` and `record_publication_authority_v1.base_tree_sha256`, but it never defines what bytes those SHA256 values cover. The opening rule that “all new digest” values use P4 canonical JSON only defines self-digests of JSON authority objects; a Git tree is not a canonical JSON object.

There are at least two plausible, non-equivalent interpretations:

1. the Git tree object ID (`git rev-parse <commit>^{tree}`; currently a 40-hex Git OID in this repository);
2. `SHA256(git cat-file tree <commit>` raw tree bytes`).

The already-closed P5 evidence verifier uses the second meaning for its field named `tree_sha256`: it hashes the raw bytes returned by `git cat-file tree <commit>`. If record/refreeze uses another meaning, the later P5 authority cannot be bound without a silent identity translation.

### Required acceptance criteria

1. Freeze `tree_sha256` explicitly. To preserve the closed P5 contract, use the same spelling unless a separate reviewed migration is intended:

```text
tree_sha256 = SHA256(raw bytes from `git cat-file tree <commit-or-tree-oid>`)
```

2. Treat the Git tree OID as a distinct identity. If it must be carried in an authority, name it separately (for example `tree_oid`); otherwise require it to be verifier-derived from the frozen commit and cross-check it before computing `tree_sha256`.
3. Apply the same semantics consistently to source bindings, base-tree authority, candidate `new_tree`, record commit verification, and the later P5 authority handoff.
4. Add fixtures that reject substituting a Git tree OID for the raw-tree SHA256, a wrong raw-tree SHA256 with correct OID, and wrong tree bytes with otherwise valid commit/ref fields.

## Accepted v0.3 direction

The following parts now satisfy the prior review direction and should be retained:

- the closed ten-key P4 final-request wire is not expanded;
- final `run` and each final `candidates.<backend>` item are explicitly verifier-constructed from the planned commitment, including identity SHA recomputation;
- execution, record, and publication authorities remain separate and production-default `None`;
- candidate evidence now has an exact expectation object and explicit request/result/verification provenance categories;
- six payload SHA values are computed by the verifier, not supplied by a caller;
- a fully valid foreign candidate pair is required to fail the parent-request join;
- candidate links remain validation-only and are not published;
- the record commit is constrained to exactly one parent equal to the base and the verified new tree;
- record/refreeze still does not set `AUTHORIZED_P4_V4_EVIDENCE`; that remains a later independent P5 verifier revision.

## Scope

Keep this design Gate in `REVIEW`. Do not implement the static tooling until a revised design closes the three HIGHs above.

This review authorizes no exact production request generation, real P4 preflight/staging/materialization/candidate/run-root creation, record/refreeze/evidence publication, P5 authority/export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory/LIBERO training.
