# ChatGPT Review — Stage-1 v1.7 launcher replay implementation

## Exact pair

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Root: `97020af908d55d39349c9a7426b960e63a72f4eb`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Controlling design: `5acb0bdadcc5ecbc22b720e5eeac6a3c95780bdc`
- Prior design verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`

## Verdict

`REQUEST_CHANGES(tools/psm_wma/stage1_v17_launcher_replay.py:47)`

Blockers: **3 HIGH** total.
- Design/Authority: 0
- Production/Authority: 2 HIGH
- Evidence: 1 HIGH
- child/runtime: 0

## Scope / pair verification

- Formal root is one commit after the prior ChatGPT design-notification head and changes only `SESSION.md`, `tools/psm_wma/stage1_v17_launcher_replay.py`, and `tools/psm_wma/test_stage1_v17_launcher_replay.py`.
- `cosmos-framework` Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- No child/runtime production bytes changed.
- Implementation remains stdlib-only and exposes no `main()` / Git / path / FD / network / `os.execve` execution path.

## Positive findings

1. The public dataclasses / exception / `replay_outer_payload()` API follow the approved design shape.
2. Base length/SHA verification exists before replay.
3. Parser replacement is flag/adjacent-value-aware, so equal old values for `--cwd` and `--bootstrap-project-root` can be independently replaced.
4. Existing owner-FD flags are rejected; one owner pair is inserted after `--bootstrap-project-root`.
5. Parser and final outer bytes/SHA are checked against binding identities.
6. Formal scope does not construct a v1.7 request and does not revive consumed v1.6 execution authority.

## HIGH-1 — Production/Authority: v0.4 surrounding-literal source targeting is not implemented

Location: `tools/psm_wma/stage1_v17_launcher_replay.py:47` (`_replace_once`).

The controlling v0.4 design explicitly requires the four newly frozen bootstrap/parser self-check substitutions to be anchored to their exact surrounding literals in `boot(s)` / `main()`, not performed as global bare-string replacement. The implementation instead does:

```python
if raw.count(old) != 1:
    _fail("source_target")
return raw.replace(old, new, 1)
```

This only proves that the naked `old` string is globally unique. It does not prove that the match is the semantically frozen `boot(s)` bootstrap guard or `main()` RAW[2] guard. Therefore the production helper does not implement the approved v0.4 authority contract.

Required remediation: make source replacement target authority context-aware for the four self-check identities (and preserve exact-one-match fail-close), so replacement is accepted only when the frozen old literal occurs in the exact intended surrounding guard. No generic global substitution is acceptable for those four identities.

## HIGH-2 — Production/Authority: parser replacement order is not fail-closed

The controlling v0.3 design, inherited by v0.4, freezes the parser table order and explicitly requires reordered targets to fail-close. The implementation validates uniqueness and adjacent old values, but does not bind iteration order to source argv order or to the frozen canonical table.

For example, if `binding.parser_replacements` contains the exact same targets but `--bootstrap-project-root` is presented before `--cwd`, both replacements still succeed; final parser bytes can remain canonical, so the final SHA check does not detect the reordered authority table.

Required remediation: enforce the frozen parser replacement ordering (e.g. each resolved target index must be strictly increasing in the approved table order, or an equivalent exact-table/order check). Reordered, missing, extra, duplicate, or wrong-adjacent targets must fail as the frozen contract requires.

## HIGH-3 — Evidence: no canonical v1.6 direct replay witness

Location: `tools/psm_wma/test_stage1_v17_launcher_replay.py:22` onward.

The reported `5/5` tests are all synthetic toy fixtures. They do not instantiate the controlling canonical binding and do not replay the exact frozen launcher base:

- formal parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`;
- launcher base blob `af19a9eb66ecaf8bd0b92a48ab1867f105026658` / raw SHA `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd` / 18966 bytes;
- complete flag-aware parser table;
- complete 8-item source replacement table;
- expected parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`;
- expected outer `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`.

The v0.4 design made that direct canonical round-trip mandatory, plus drift negatives for each newly frozen self-check literal and the previously frozen parser/source drift classes. Passing toy tests cannot close that Evidence requirement.

Required remediation: add a CPU/static direct test that loads/injects the exact canonical frozen base bytes without production I/O, builds the complete canonical binding exactly as designed, and asserts exact parser and outer bytes/SHA. Add direct negatives for reordered parser targets and each of the four surrounding-literal self-check drifts, alongside the already-required wrong flag/adjacent value/owner-FD/base identity/source drift cases.

## Boundary

This verdict does **not** authorize implementation closure, v1.7 request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

v1.6 execution authority remains consumed. Any future Stage-1 attempt still requires implementation closure first, then a newly constructed exact v1.7 request with fresh observation and fresh independent review.
