# R09-B2 P4-v4 Execution Request `authorities` v0.3 static implementation review

## Verdict

`REQUEST_CHANGES`

Target:
- implementation: `c2104e536f9bf496d140e0a3e717ca34ff5b1608`
- request: `b7f27f7b1cd1669b3eb664e9e8b808c2efdb65d8`
- approved design: `54830a20cab3e2d9995781faf1244684c6bd02d0`
- ChatGPT design approval: `b38507738313add72239915efd04d4139c91d6d6`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Accepted implementation

The principal v0.3 authority model is implemented in the intended direction:
- the historical D005 v2 artifacts are pinned to fixed paths and raw SHA256 values;
- historical source/verifier identity is separated from the current execution-request source;
- the historical verifier Git object is read through the supplied absolute host Git rather than ambient `git`;
- the historical pretty `verification.json` is byte-bound, decoded, and checked against the frozen nested boolean roster;
- current-source `verify_pair()` is not used to pretend the historical pair is current-source evidence;
- the already-closed environment projection/object/P3 grammar is reused for the only allowed historical→current cross-binding;
- the existing `validate_environment_pair()` wrapper and execution hard-stop remain present.

The positive authorities test also uses the real repository historical artifacts, which is valuable.

## HIGH — historical artifact lexical symlink binding is not enforced

`tools/g0/r09_b2_p4_v4_execution_preflight.py`, `_read_historical_artifact()` (approximately lines 170-190 in the implementation):

```python
path = (root / relative).resolve(strict=True)
if path.is_symlink() or not path.is_relative_to(root):
    ...
raw = _read_regular_nofollow(path, ...)
```

This checks `is_symlink()` only **after** resolving the lexical artifact path. A final-component symlink such as

```text
artifacts/.../recurrent.json -> real-record.json
```

is converted to `real-record.json`; `path.is_symlink()` is then false, and `O_NOFOLLOW` is applied to the resolved target rather than the frozen lexical binding. Therefore a lexical symlink can be consumed instead of being rejected by this function.

The approved v0.3 contract explicitly freezes non-symlink/no-follow artifact bindings and includes symlink fixtures. The implementation must reject the lexical `(root / relative_path)` when its final component is a symlink before resolving/opening it, while retaining root-containment and single-fd raw semantics. A permanent fixture must replace one fixed artifact path with a real symlink and prove the authorities validator fails on the path-binding branch.

## HIGH — frozen historical record self-digest semantic check is omitted

`validate_authorities_pair()` verifies fixed raw SHA, canonical JSON, backend/schema/status/source, but does not independently recompute:

```text
record.d005_sha256 == canonical_sha256(record without d005_sha256)
```

The approved v0.3 design explicitly requires each historical record self digest to be independently recomputed. Exact outer artifact-byte binding is not a substitute for this frozen semantic check: the authority model deliberately combines fixed bytes, historical verifier identity, and decoded semantic validation rather than treating one anchor as sufficient for all others.

Add the independent self-digest check for both records and a targeted permanent negative fixture. The fixture should mutate a record's internal `d005_sha256` in an isolated temporary authority fixture and recompute any non-target outer bindings needed to exercise the semantic branch.

## HIGH — v0.3 permanent CPU fixture matrix is largely missing

At `c2104e5`, the authorities-specific permanent suite contains only two test functions:
- a real-artifact positive;
- limited outer identity / recurrent binding-SHA drift.

That does not close the approved v0.3 fixture contract. Add permanent CPU fixtures covering at least:

1. **Historical artifact binding/path**
   - recurrent/TTT/verification binding path and SHA drift;
   - record swap;
   - duplicate artifact paths;
   - final symlink rejection;
   - FIFO and directory rejection;
   - pathname-reopen / single-fd raw behavior.

2. **Historical source/verifier identity**
   - historical source root revision, Gitlink, submodule revision and identity drift;
   - historical verifier path/root revision/blob SHA/identity drift;
   - historical Git object blob mismatch.

3. **Host-Git TCB**
   - supplied Git path differs from `request.interpreter.host_git.path`;
   - PATH-shadow `git` cannot influence the lookup;
   - spy/assert the actual historical lookup argv is exactly the frozen absolute-Git `-C <root> show <revision>:<path>` grammar, with no bare Git/fallback.

4. **Historical records**
   - canonical JSON drift;
   - backend swap/drift;
   - schema/status drift;
   - independently recomputed `d005_sha256` failure.

5. **Historical verification semantic roster**
   - top-level added/missing/retyped fields;
   - `checks` added/missing/retyped fields;
   - `distinct_outputs` false/non-bool;
   - every `matched` roster added/missing/false/non-bool class;
   - recurrent and TTT backend roster added/missing/false/non-bool class.

6. **Current environment cross-binding**
   - missing environment authority;
   - projection drift;
   - effective/native drift;
   - P3 backend-value drift.

7. **Ambient isolation**
   - `os.environ`/PATH shadow does not alter artifact bytes, Git lookup authority, or verdict.

For intended-branch mutations, recompute all non-target identities/digests so the test reaches the targeted authority branch rather than failing early on an outer identity.

## Scope / authorization

This verdict remains static/CPU only. It does **not** authorize real P4 preflight, staging/materialization/candidate generation, record/refreeze, evidence publication, P5 authority/export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training.

The `authorities` section remains open until the implementation and the frozen permanent fixture matrix are independently re-reviewed and closed.
