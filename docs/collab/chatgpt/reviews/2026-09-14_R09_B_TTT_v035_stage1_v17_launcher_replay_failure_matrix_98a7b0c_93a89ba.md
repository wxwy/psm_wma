# ChatGPT Review — Stage-1 v1.7 launcher replay failure-matrix closure

- Formal root: `98a7b0c746770eef767ac67321fc43aa6c6b6d9e`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Requested close verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION`

## Verdict

`REQUEST_CHANGES(tools/psm_wma/stage1_v17_launcher_replay.py:100)`

Blockers: **1 HIGH**
- Design/Authority: 0
- Production/Authority: 1 HIGH
- Evidence/Scope: 0
- child/runtime: 0

## Pair / scope verification

- Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to the prior reviewed same-Gate formal root `467e6665b95be450ca5900c6aa6ce14e94f759d5`, the complete formal delta remains inside the approved launcher replay helper/test path plus review/coordination bookkeeping.
- No child/runtime production bytes changed.
- No v1.7 request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, GPU/CUDA/torchrun, training/eval/inference or LIBERO4IN1 authority is introduced.

## Prior blocker disposition

### CLOSED — function/span relocation authority

The helper now imports `ast`, derives top-level `boot()` / `main()` function spans, and for the four frozen self-check rows requires the exact target token both globally unique and uniquely present inside the intended function span before replacement. The direct relocation negative moves the bootstrap token to `main()` while leaving `boot()` empty and correctly requires `source_target` fail-close.

### CLOSED — no-I/O canonical witness

The canonical launcher base remains embedded in the approved test file as gzip/base64 bytes, decoded entirely in memory and asserted against frozen base identity `18966 / 8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`. No runtime `subprocess`, `git show`, repository pathname or other Git/path/FD/exec I/O remains in the direct witness.

### CLOSED — canonical identities / current negative matrix

The current test matrix retains:
- complete canonical parser table and 8-item source table;
- exact parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`;
- exact outer `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`;
- parser reordered-target, wrong-adjacent-value, duplicate-old-value and owner-FD negatives;
- source rows 0–7 drift negatives;
- base-identity and RAW-shape negatives;
- relocated self-check guard negative.

## Remaining HIGH — replacement-table authority itself is not frozen exactly

File: `tools/psm_wma/stage1_v17_launcher_replay.py:100`

The controlling v0.3/v0.4 design does not merely require the final parser/outer bytes to match. It explicitly freezes parser replacement authority so duplicate/missing/reordered/**extra target** fails closed, and freezes the source replacement table as ordered with no missing/duplicate/**extra** rows.

The current helper validates each supplied row while iterating and then relies on the final parser/outer SHA. It does **not** first bind `binding.parser_replacements` and `binding.source_replacements` themselves to the exact frozen canonical ordered tables (or an equivalent frozen table digest/shape).

This leaves concrete accepted non-canonical bindings that preserve the final bytes:

1. **Parser extra no-op target.** A caller can add an otherwise valid existing argv flag as an extra replacement with `expected_old_value == new_value`, positioned monotonically. The row passes flag uniqueness / adjacent-value / order checks, changes no bytes, and the final parser SHA still matches. The design requires the extra target itself to fail `parser_target`.
2. **Source extra no-op target.** A caller can append an extra `(old, old)` source row for a string that occurs exactly once. `_replace_once()` accepts it, output bytes are unchanged, and the final outer SHA still matches. The design requires extra source rows to fail `source_target`.
3. **Source-table order is not itself authenticated.** Independent canonical rows can be reordered when their substitutions commute and still produce the exact same final outer bytes. The design freezes the source table as ordered, so table-order drift must not be accepted merely because the final SHA is unchanged.

Therefore the final SHA is necessary but insufficient as authority for the replacement program itself.

## Exact acceptance

1. Keep the current public API, function/span self-check targeting, parser position ordering, embedded canonical base and no-I/O boundary.
2. Before applying replacements, bind `binding.parser_replacements` to the exact frozen canonical ordered parser table and `binding.source_replacements` to the exact frozen canonical ordered 8-row source table, or to an equivalent immutable canonical table identity/digest that detects count/order/value drift.
3. Extra, missing, duplicate, reordered or otherwise non-canonical parser rows must fail `BLOCKED_AUTHORITY_NOT_CLOSED:parser_target` before parser mutation.
4. Extra, missing, duplicate, reordered or otherwise non-canonical source rows must fail `BLOCKED_AUTHORITY_NOT_CLOSED:source_target` before source mutation.
5. Add direct negatives for at least: parser extra no-op target, source extra no-op target, source reorder of independent canonical rows, and source missing row. Preserve all existing 11-case matrix coverage and exact canonical identities.
6. `py_compile`, direct unittest and `git diff --check` must pass inside the existing no-I/O boundary.

## Scope boundary

This verdict authorizes only remediation of the already-approved launcher replay helper/test files. It does **not** authorize implementation closure, v1.7 request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1. v1.6 authority remains consumed.
