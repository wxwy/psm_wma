# ChatGPT Review — Stage-1 v1.7 launcher replay remediation

- Formal root: `56ea8c7cfc36375a784aff2e30c07c2516e0adfe`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Requested close verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION`

## Verdict

`REQUEST_CHANGES(tools/psm_wma/stage1_v17_launcher_replay.py:55)`

Blockers: **2 HIGH**
- Design/Authority: 0
- Production/Authority: 1 HIGH
- Evidence/Scope: 1 HIGH
- child/runtime: 0

## Pair / scope verification

- Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child/runtime production bytes are unchanged.
- Remediation implementation remains confined to the two approved root files, with review/bookkeeping commits outside the formal root.
- No v1.7 request construction or Stage-1 retry/materialization authority is introduced.

## Prior blocker disposition

### CLOSED — parser replacement ordering

`replay_outer_payload()` now tracks `previous_index` and rejects parser replacement rows that do not appear in monotonically increasing argv order. The direct negative `test_reordered_targets_fail` covers the previously missing reordered-target fail-close.

### PARTIALLY CLOSED — canonical replay evidence

The test now carries the complete canonical parser table and 8-item source replacement table, and directly asserts parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333` plus outer `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`. Four self-check drift rows are also exercised.

However the witness is not valid for this Gate because it obtains the canonical base at runtime via `subprocess.run(["git", "show", ...], cwd="/disk/rl/psm_wma")`. The controlling v0.3/v0.4 design freezes a pure injected-bytes / no Git/path/FD/exec-I/O test boundary. A witness that performs real root Git/path I/O cannot close this CPU/static Gate.

## Remaining HIGHs

### HIGH 1 — Production/Authority: source self-check replacement is not exact surrounding-literal targeting

File: `tools/psm_wma/stage1_v17_launcher_replay.py:55`

The implementation still performs:

- `raw.count(old) == 1`,
- a separate `_GUARDS[old] in raw` presence check,
- then `raw.replace(old, new, 1)` globally.

This does **not** bind the replaced span to the exact `boot(s)` / `main()` surrounding literal required by v0.4. The guard may merely occur elsewhere in the source; the replacement itself is still selected only by naked-string global uniqueness.

The four self-check rows must be replaced only inside their frozen surrounding literal spans, with exact-one-context matching and `source_target` fail-close if that context is missing, duplicated, altered, or moved. The public `ReplayBinding` API can remain unchanged; an internal exact-context map keyed by the four frozen old values is sufficient.

### HIGH 2 — Evidence/Scope: canonical witness performs prohibited real Git/path I/O

File: `tools/psm_wma/test_stage1_v17_launcher_replay.py:12`

`canonical()` runs real `git show` against `/disk/rl/psm_wma`. This violates the frozen implementation/test scope: pure injected bytes / temporary CPU-static only, no Git/path/FD/exec I/O.

The canonical 18966-byte frozen launcher source must instead be supplied as test-owned immutable bytes (for example an embedded bytes/base64 constant in the existing test file), with explicit frozen `18966 / 8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd` assertions before calling the helper. No third fixture path is authorized.

## Exact acceptance

1. Keep the current public replay API and parser-order enforcement.
2. Replace `_GUARDS + global replace` for the four self-check rows with exact surrounding-literal span matching/replacement; altered or relocated contexts must fail `source_target`.
3. Remove runtime `subprocess` / `git show` / real repository path access from the direct test.
4. Inject the exact frozen canonical base bytes from within the approved test file and assert its frozen length/SHA before replay.
5. Retain the complete canonical parser table and 8-item source table, exact parser/outer identity assertions, reordered-target negative, owner-FD/base/parser/source negatives, and four self-check drift negatives.
6. `py_compile`, direct unittest, and `git diff --check` must pass under the no-I/O boundary.

## Scope boundary

This verdict authorizes only remediation of the already-approved two root files. It does **not** authorize implementation closure, v1.7 request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1. v1.6 authority remains consumed.
