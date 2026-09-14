# ChatGPT Review — Stage-1 v1.7 launcher replay no-I/O remediation

- Formal root: `467e6665b95be450ca5900c6aa6ce14e94f759d5`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Requested close verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION`

## Verdict

`REQUEST_CHANGES(tools/psm_wma/stage1_v17_launcher_replay.py:55)`

Blockers: **1 HIGH**
- Design/Authority: 0
- Production/Authority: 1 HIGH
- Evidence/Scope: 0
- child/runtime: 0

## Pair / scope verification

- Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal commit changes only the two approved implementation/test files; review/request bookkeeping is outside the formal root.
- Child/runtime production bytes are unchanged.
- No v1.7 request construction or Stage-1 retry/materialization authority is introduced.

## Prior blocker disposition

### CLOSED — no-I/O canonical witness

The canonical witness no longer invokes `subprocess`, `git show`, or any real root path. The exact frozen base is embedded in the approved test file as gzip/base64 bytes and decoded in memory. Before replay, the test directly asserts frozen source identity `18966 / 8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`. The complete parser table and 8-item source table remain present and the witness still directly asserts parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333` and outer `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`.

### CLOSED — parser-table order

Monotonic argv index enforcement remains present, so reordered parser targets fail `parser_target`.

### PARTIALLY CLOSED — surrounding-literal source targeting

The implementation improved from naked global replacement: for the four frozen self-check rows, `_GUARDS` now builds an exact `prefix + old + suffix` token and requires that token exactly once before replacing that token span.

However the controlling prior canonical review explicitly required moved/relocated contexts to fail `source_target`, not merely altered/duplicated tokens. The current helper searches the exact token over the entire source. If the entire frozen token is moved byte-for-byte outside its intended `boot(s)` or `main()` region, `raw.count(token) == 1` still succeeds and the helper replaces it. The later final outer SHA may fail as `replay_drift`, but the frozen authority contract requires the self-check target itself to be bound to its intended function/span and relocation to fail as `source_target`.

## Remaining HIGH

### HIGH — Production/Authority: self-check target is token-anchored but not function/span-anchored

File: `tools/psm_wma/stage1_v17_launcher_replay.py:55`

The v0.4 contract and the immediately prior ChatGPT exact acceptance require the first two self-check rows to bind specifically to `boot(s)` and the second two specifically to `main()`, with missing, duplicated, altered **or relocated** contexts failing `source_target`.

Current `_GUARDS` contains only local prefix/suffix fragments and `_replace_once()` counts the constructed token globally across the full source. This does not prove that the token still resides in the frozen function/region.

## Exact acceptance

1. Keep the public `ReplayBinding` API, current parser-order enforcement, owner-FD insertion, embedded canonical base, complete canonical binding, and exact parser/outer identity assertions unchanged.
2. Bind each of the four self-check replacements to its frozen function/span (`boot(s)` for bootstrap length/SHA; `main()` for RAW[2] length/SHA), using AST/function-region boundaries or an equivalently frozen region-aware scheme.
3. Require the target token to occur exactly once inside that frozen region and not be accepted merely because the same full token appears elsewhere.
4. Add at least one direct negative that moves an otherwise byte-identical self-check token outside its intended function/region and proves `BLOCKED_AUTHORITY_NOT_CLOSED:source_target`.
5. Preserve the existing no-I/O boundary and existing canonical `18966 -> 2336 -> 18875` witness and drift negatives.
6. `py_compile`, direct unittest, and `git diff --check` must pass.

## Scope boundary

This verdict authorizes only remediation of the already-approved two root files. It does **not** authorize implementation closure, v1.7 request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1. v1.6 authority remains consumed.
