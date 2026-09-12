# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `64db875135addac644c96d0028ab5c08a1dddf54`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `166e5f5f6470bcc7c77f8c3326914e1281e922b6`; the child is unchanged.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed against the complete approved real-adapter design chain v0.1-v0.6 and the prior ChatGPT exact-pair review for `166e5f5... / 93a89ba...`.

The reported `44/44` stdlib tests, four-file `py_compile`, Ruff and `git diff --check` are auxiliary evidence only; source/contract correctness is reviewed independently.

## Prior blocker status

The remediation materially closes several prior findings:

- **Prior CAS command-result / ownership blocker: CLOSED.** Local CAS now requires the actual `update-ref` command to succeed, and remote CAS additionally requires the expected `--porcelain` create/delete marker plus fresh ref observation. The new temporary-repository tests cover same-candidate creation and already-absent delete attribution.
- **Prior deterministic candidate metadata blocker: CLOSED.** `CommitMetadata` is explicitly injected through `GIT_AUTHOR_*` / `GIT_COMMITTER_*`, message bytes are supplied to `commit-tree`, and tests show ambient repository user config does not alter the candidate revision while frozen date drift does.
- **Prior primary-vs-secondary failure ABI blocker: PARTIALLY CLOSED.** `primary_phase="rollback"` is no longer accepted and ordinary `FAIL` now rejects non-null rollback failure fields. A separate terminal-reachability gap remains below.
- **Prior real CLI/preflight blocker: PARTIALLY CLOSED.** A CLI, regular-FD raw/canonical preflight, formal-tree/Gitlink checks, module/tool identity checks, fixed-ref absence checks and the `prepare -> verify -> publish` call chain now exist. However the CLI still bypasses the frozen evidence transaction itself, so the real execution seam is not closed.

## Current blockers

### HIGH-1 — the real CLI publishes refs without any transaction evidence finalizer, so the approved evidence commit protocol is bypassed

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:183` (`run_authority_cli`)

`run_authority_cli()` performs preflight, `prepare_candidate()`, `verify_candidate()`, then calls:

```python
publish_candidate(invocation.request, candidate, binding, transaction)
```

with no `finalizer` at all. The CLI parser also has no final-evidence path and no inputs/producer for the exact execution record fields such as actual `argv_sha256`, sanitized-env identity and remote identity.

Therefore a CLI success can create and preserve both authority refs and return a candidate revision while producing **no accepted transaction evidence** and never traversing the approved `EvidenceCommit -> guard unlink` linearization protocol. `write_pending_evidence()` and `verify_evidence_*()` are only exercised as separate helper tests; they are not on the real adapter execution path.

This violates the design chain that explicitly made evidence finalization part of the same authority-owned publication transaction. The next Gate is an exact execution request, not another implementation Gate, so it cannot be expected to invent a new wrapper or modify this production adapter.

**Exact acceptance:** keep remediation in this implementation Gate and wire the CLI's actual publication through the frozen finalizer transaction. The executable path must construct the exact evidence record from actual witnessed state/identity, accept/bind the fixed evidence destination required by the execution request, call `write_pending_evidence()` from the authority finalizer, and prove directly that CLI PASS leaves `accepted evidence + exact local/remote candidate refs`, while writer/validator/pre-commit evidence failure causes the already-frozen rollback / `ROLLBACK_INCOMPLETE` behavior. The CLI test must assert the accepted evidence file, not only the two refs.

### HIGH-2 — `EvidenceCommit` can be marked committed by an arbitrary/no-op callable; it is not the frozen guard/digest/activation-bound capability

**Location:** `tools/psm_wma/immutable_source_authority_root.py` (`EvidenceCommit`)

The approved v0.5/v0.6 protocol freezes a one-shot capability tied to the same request/candidate/binding/witness activation and requires sealing against the exact evidence guard identity and record digest before `consume_by_unlink()` performs the sole guard-unlink commit transition.

The implementation instead exposes:

```python
commit.seal_for_guard(callable)
commit.consume_by_unlink()
```

and merely executes the arbitrary stored callable before setting `_committed=True`. It carries no request/candidate/binding activation identity, no activation epoch, no guard identity and no record digest. A finalizer can therefore do `seal_for_guard(lambda: None); consume_by_unlink()` and make authority treat the transaction as committed although no guard was unlinked and no PASS became verifier-visible. Existing authority tests use such no-op consumers in several committed cases, so the invariant is not mechanically established by the capability itself.

**Exact acceptance:** implement the frozen one-shot capability semantics rather than an arbitrary callback latch. Seal/consume must be bound to the exact same activation/witness plus the concrete guard/evidence digest (or an equivalent authority-owned opaque guard capability), wrong/different/replayed state must fail pre-commit, and `committed=True` must be reachable iff the actual guard-unlink commit action succeeds. Add a direct negative proving a no-op/foreign consumer cannot mark the commit committed and a real writer integration proving `guard absent <=> commit committed <=> accepted PASS`.

### HIGH-3 — the verifier still accepts ordinary no-owned `FAIL` with incomplete/unprovable final-state proof

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:533` (`verify_evidence_bytes` terminal checks)

v0.5 froze the no-ownership publication-try rows (`pre_publication`, `local_cas`) precisely: after the recovery/final-proof routine is entered, ordinary `FAIL` is legal only when fresh final local **and** remote observations are concrete absent and `rollback.complete=true`; foreign/unreadable/unprovable final state must be `ROLLBACK_INCOMPLETE`.

The implementation only enforces complete rollback for ordinary `FAIL` when `owned` is true:

```python
if status == "FAIL" and owned and not (... rollback["complete"]):
    reject
```

Thus a valid `pre_publication` or `local_cas` shape with `owned=false`, `rollback.entered=true`, `rollback.complete=false` and a foreign/unreadable final observation can still be serialized as ordinary `FAIL` and pass the terminal checks, even though the frozen table requires `ROLLBACK_INCOMPLETE`.

**Exact acceptance:** for every publication-try ordinary FAIL, including no-owned `pre_publication/local_cas`, require the frozen terminal proof: recovery entered and `rollback.complete=true` with both final observations concrete absent. Any entered recovery with incomplete/unprovable final proof must require `status=ROLLBACK_INCOMPLETE` plus the secondary rollback/final-proof failure fields. Add positive/negative tests for pre-publication foreign/unreadable and local-CAS ambiguous final state.

### HIGH-4 — module/interpreter identity preflight validates caller-pointed copies, not the code/interpreter actually executing the CLI

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py` (`_verify_module_identity`, `_verify_executable_identity`, `main`)

The CLI accepts caller-provided `cwd`, adapter path, authority-module path and interpreter path, verifies those files against the formal tree / provided digest, but never binds those identities to the code actually loaded into this Python process. In particular:

- the actual running interpreter (`sys.executable`) is not compared to the frozen interpreter path;
- the executing adapter module's `__file__` is not bound to `cwd / adapter.repo_path`;
- the imported authority module's actual `__file__` is not bound to the claimed authority-module path.

The current CLI test demonstrates this separation: it copies the module files into a temporary repository/formal tree, then invokes an already-imported `main()` from the test process. The copied files are what preflight attests, not necessarily the loaded implementation that performs the mutations.

That defeats the purpose of the frozen execution identity: an alternate Python/module could execute while pristine formal-tree copies are supplied only as attestable decoys.

**Exact acceptance:** preflight must bind the actual executing interpreter and loaded adapter/authority module files to the frozen identities. At minimum compare the resolved actual `sys.executable` and actual module `__file__` identities to the frozen paths, then verify their bytes/OIDs using the same fail-closed rules. Add direct negatives where the formal-tree copy is pristine but the executing module/interpreter identity differs; rejection must occur before candidate/ref mutation.

## Non-blocking observations

- The new CAS return-code/porcelain ownership logic is a meaningful improvement and should be retained.
- Deterministic commit metadata injection should be retained.
- The exact-pair formal tree remains within the approved implementation family plus collaboration bookkeeping; the child/Gitlink is unchanged.
- The input FD helper checks the opened object is a regular file and uses `pread`; the final execution request should keep the launcher's FD-open semantics explicit so the approved non-symlink/read-only intent remains fail-closed.

## Blocker summary

- production/contract blockers: `4 HIGH`
- Evidence-only blockers: `0`
- total blockers: `4`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:183)`

This verdict binds only the exact formal pair `64db875135addac644c96d0028ab5c08a1dddf54` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same CPU/static implementation Gate. This verdict does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, real source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
