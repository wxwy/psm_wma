# ChatGPT review — Stage-1 v0.5 pre-C rehearsal consumer CPU/static implementation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`
- Formal root: `034cbc43f0178e2e472bd642991311cc6116ee49`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:70)`
- Blockers: `3 HIGH`; Design/Authority: `0`; Production/implementation: `3 HIGH`; Evidence/identity: `0`; child/runtime: `0`.

## Formal target / scope

The formal root resolves. Its formal tree binds `cosmos-framework` as mode `160000` exactly to `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit resolves in `wxwy/cosmos-framework`.

The Gate is root-only CPU/static. The implementation changes `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no child/runtime mutation is part of this target.

The controlling V31 design is a v0.5-only lifecycle refreeze. It requires one non-consuming `rehearse_v05()` to seal the exact capability/callable identity, exact v0.5 tuple, exact six-key environment, full provenance/freshness closure, canonical JSON/Markdown/patch identities and witnesses, and a closed dry-run/post-write verifier. It also requires v0.3/v0.4 to remain permanently excluded and requires the eventual C path to be freshness comparison -> exactly one opaque write -> byte-exact verification -> hard stop, with terminal no-retry.

## HIGH 1 — the frozen six-key environment and v0.5 closure are not implemented exactly

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:69-90`.

`_SIX_KEYS` is defined as `git`, `local_v2`, `remote_v2`, `authority_ref`, `config`, and `project_root`. Those are semantic categories, not the inherited frozen six-key Git isolation environment (`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_NOSYSTEM`, `GIT_CONFIG_SYSTEM`, `GIT_NO_REPLACE_OBJECTS`, `LANG`, `LC_ALL`) that V31 preserves.

The same shape check accepts any two distinct output paths as long as they do not contain the strings `v0.3`/`v0.4`; it does not require the exact v0.5 JSON/Markdown pair. `frozen_snapshot` and `designated_absences` are also accepted as arbitrary tuples, without requiring the V31 closure: `.git`/config, local V2, the two ordered remote queries and their raw results, authority-ref facts, exact designated absences, raw identities, query argv/order/allowlists and predicates.

Independent behavioral check confirms that `rehearse_v05()` accepts `("foo.json", "bar.md")` together with the six semantic placeholder keys and returns a sealed plan. Therefore this helper can PASS a closure that is impossible under the frozen V31 contract.

Acceptance criterion: model the exact v0.5 paths and the exact six environment key/value contract, and give the frozen live closure a typed/exact schema that requires every V31 field, raw identity, ordered query/allowlist and predicate. Foreign/missing/extra/reordered closure facts must fail closed in rehearsal.

## HIGH 2 — `consume_once_v05()` is not one-shot and permits direct retry

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:107-116`.

The function has no consumed/retired state and no one-shot capability. The same `SealedPreCPlanV1` can be passed to `consume_once_v05()` repeatedly. After success it will call `plan.capability.apply_opaque_v1(...)` again; after a terminal consumer/verifier failure the caller can likewise invoke the same plan again.

Independent behavioral check against the reviewed implementation called `consume_once_v05()` twice with the same plan and unchanged snapshot: both calls returned `HARD_STOP_PENDING_INDEPENDENT_REVIEW`, and the injected capability was invoked twice.

This directly violates the frozen exact-once/no-retry lifecycle.

Acceptance criterion: make C admission intrinsically one-shot. A plan/capability must transition to terminal consumed state before or atomically with the only allowed opaque invocation; every later call after any admitted C attempt (success, rejected, partial/unknown, verifier failure, or exception) must fail before invoking the capability. Add direct tests for second-call rejection after success and every terminal failure class.

## HIGH 3 — capability identity and final canonical-byte closure are trusted, not sealed/verified

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:25-66` and `:81-104`.

V31 requires the unique host capability identity to include provider/module/path/blob-SHA/callable/ABI/transport and to be non-copyable/non-serializable. The implementation stores no callable qualname/identity, does not verify `blob_sha256` format/content, and does not establish the non-copyable/non-serializable property. A frozen dataclass alone is not that contract.

Likewise the implementation only checks that `descriptor`, `json_raw`, `markdown_raw`, and `patch_raw` are non-empty and computes length/SHA identities. It does not verify canonical JSON bytes, Markdown five-field sibling binding, line encoder/inverse witness, exact descriptor contents, or the exact add-only patch semantics itself. Those guarantees are delegated to arbitrary injected `dry_run` and `post_write_verify` callables whose identities/behavior are not sealed. A caller can provide callbacks that simply return `True`, causing rehearsal PASS for non-canonical/foreign bytes.

Acceptance criterion: freeze and validate the exact capability/callable identity and non-copyable/non-serializable semantics; implement the contract-critical canonicalization, sibling binding, line witness, exact descriptor/path operation and verifier invariants in the reviewed static core (or in separately frozen typed helpers whose identities are part of the sealed plan), rather than trusting unconstrained boolean callbacks. Add drift/fail-close tests for callable identity, capability copy/serialization, descriptor/path drift, JSON canonicalization, Markdown five-field binding, line witness, and verifier identity.

## Evidence note

The reported `5/5` unittest, `py_compile`, and `git diff --check` are auxiliary evidence only. The existing tests do not witness the exact six-key contract, exact v0.5 path binding, complete closure schema, repeated-call rejection, callable identity drift, copy/serialization rejection, or canonical JSON/Markdown/line-witness fail-close behavior. Because the implementation itself violates those frozen requirements, the Gate cannot close.

## Verdict / boundary

`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:70)`

No CPU/static closure is granted for this pair. Still NOT authorized: v0.5 request-pair construction/C, real consumer invocation, materialization, source-evidence, real Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
