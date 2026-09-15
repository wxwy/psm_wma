# ChatGPT independent review — Stage-1 v1.7 pre-C rehearsal consumer CPU/static

Formal pair:
- root: `6c4e395f38591c4b27a5627c184fc739af968669`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:54)`

Blockers: `1 HIGH`
- Production/implementation: `0`
- Design/Authority: `0`
- Evidence/Scope: `1 HIGH`
- child/runtime: `0`

## Positive closure

The prior authority-binding blocker is closed on this exact pair.

- `SourceObjectV1.identity_ok()` now checks the exact nested raw identity and requires the computed Git blob OID of those raw bytes to equal the frozen `blob_oid`.
- `_validate_closure()` pins all three P0 `(name, root, path, blob_oid)` tuples plus exact raw `(name, length, sha256)` identities.
- all eight P1 injected objects are pinned by exact ordered `(name, length, sha256)` identities and self-hash validation.
- `ReplayBindingV1` now pins the exact base SHA/size, owner-FD pair, exact parser/source rows, and `parser_argv_items`; closure validation also requires those items to equal the JSON-decoded already-pinned parser raw bytes.
- direct foreign-but-self-consistent P0/P1 and ReplayBinding drift tests fail before any consumer invocation.
- formal root resolves and its `cosmos-framework` Gitlink is exactly the declared child.

## HIGH 1 — CPU/static evidence violates its own no-real-source-I/O scope

Location: `tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:54`

The current fixture executes:

`replay_helper = Path("tools/psm_wma/stage1_v17_launcher_replay.py").read_bytes()`

This performs a real filesystem read of a production source file in the formal CPU/static unittest. The controlling v3.1 implementation design requires the implementation validation to be pure in-memory and explicitly forbids real `source` I/O; the current CODEX request repeats that hard scope (`real consumer/Git/network/source/data/cache I/O` forbidden).

Therefore the reported `9/9 PASS` is not admissible evidence for closing this CPU/static Gate even though the production helper itself is now structurally correct. This is an Evidence/Scope blocker, not a production-correctness blocker.

### Acceptance criterion

- remove the runtime filesystem/source read from the unittest path;
- provide the replay-helper bytes through an already frozen in-memory fixture/literal (or equivalent zero-I/O static fixture) whose exact blob/raw identities are validated by the same production closure logic;
- preserve the current P0/P1/ReplayBinding exact-pin checks and foreign-self-consistent fail-close matrix;
- rerun the CPU/static suite with no real source/Git/network/data/cache I/O and show the same exact public production API path still passes/fails as required.

No v0.5 request construction/C/materialization authority is granted on this pair. Child/runtime/GPU/training remain out of scope.
