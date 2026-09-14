# ChatGPT Review — Stage-1 v1.7 launcher replay table-authority remediation

- Formal root: `64ffa794042ba866339446706e37c51335827d31`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Requested close verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION`

## Verdict

`REQUEST_CHANGES(tools/psm_wma/stage1_v17_launcher_replay.py:94)`

Blockers: **1 HIGH**
- Design/Authority: 0
- Production/Authority: 1 HIGH
- Evidence/Scope: 0
- child/runtime: 0

## Pair / scope verification

- Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child/runtime production bytes are unchanged.
- Relative to the prior same-Gate formal pair `98a7b0c746770eef767ac67321fc43aa6c6b6d9e / 93a89ba...`, the technical remediation is confined to the two approved launcher replay implementation/test files; review/ledger updates are bookkeeping.
- No request construction, Stage-1 retry/materialization, real source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1 authority is introduced.

## Prior blocker disposition

### CLOSED — exact ordered table identity is now represented

The helper now computes a deterministic JSON/SHA-256 digest of `parser_replacements` and `source_replacements`, and freezes exact canonical digest values. This closes the earlier inability to distinguish canonical rows from extra no-op rows or reordered source rows when the canonical parent path is taken. The direct test adds a parser extra-no-op negative and source-table reorder negative.

### PRESERVED — earlier closures remain

- self-check replacements remain function/span-aware using AST-derived `boot()` / `main()` regions;
- relocated self-check tokens fail `source_target`;
- parser replacement order remains monotonic/fail-closed;
- canonical base remains self-contained no-I/O test bytes with frozen `18966 / 8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd` identity;
- canonical parser and outer witnesses remain `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333` and `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`;
- base identity, RAW shape, source rows 0–7, parser adjacency/order, relocation, source drift and owner-FD negatives remain in scope.

## Remaining HIGH

### Production/Authority — canonical table authority is conditionally bypassable through `formal_parent`

File: `tools/psm_wma/stage1_v17_launcher_replay.py:94`

The new table-digest checks run only under:

```python
if binding.formal_parent == _CANONICAL_PARENT:
    ... validate parser/source table digests ...
```

But `replay_outer_payload()` does not itself require `binding.formal_parent` to equal the frozen parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`. `formal_parent` is otherwise unused by the replay. Therefore a caller can change only `binding.formal_parent` to a noncanonical value and thereby disable the new table-authority check while still injecting the same canonical base bytes.

Once the conditional is skipped, the previously demonstrated class of authority-neutral extra rows becomes possible again: for example an extra parser row whose old and new values are identical, or an extra source `(old, old)` no-op on a unique token. Such rows can leave the resulting parser/outer bytes and their final SHA-256 values unchanged, so the existing final `replay_drift` checks do not necessarily detect the bypass.

This means the new canonical table authority is optional rather than a frozen invariant for the dedicated v1.7 replay helper.

## Exact remediation

1. Preserve the current public API, exact table digests, function/span targeting, no-I/O canonical fixture, parser-order enforcement and all existing negatives.
2. Before any replay mutation, either:
   - require `binding.formal_parent == 08d5828cdb4c12afa3b798ff01826c91ceb8755a` and fail-close otherwise, then validate both table digests; **or**
   - validate both canonical table digests unconditionally for this dedicated v1.7 helper.
3. Add a direct negative proving that a noncanonical `formal_parent` cannot be used together with an extra/no-op parser or source row to bypass table authority.
4. Keep `py_compile`, direct unittest and `git diff --check` within the existing no-I/O CPU/static boundary.

## Scope boundary

This verdict does **not** close the implementation and does not authorize v1.7 request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1. v1.6 authority remains consumed.
