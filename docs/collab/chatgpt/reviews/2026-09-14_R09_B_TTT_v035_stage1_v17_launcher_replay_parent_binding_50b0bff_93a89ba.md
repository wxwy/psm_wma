# ChatGPT Review — Stage-1 v1.7 launcher replay parent-binding remediation

- Formal root: `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Requested close verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION`

## Verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION`

Blockers: **0**
- Design/Authority: 0
- Production/Authority: 0
- Evidence/Scope: 0
- child/runtime: 0

## Pair / scope verification

- Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child/runtime production bytes are unchanged.
- Relative to the previously reviewed same-Gate formal root `64ffa794042ba866339446706e37c51335827d31`, the effective implementation delta is confined to the two approved root paths; intervening ChatGPT review/inbox files are bookkeeping only.
- No request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 authority is introduced.

## Prior blocker disposition

### CLOSED — canonical table authority can no longer be bypassed by changing `formal_parent`

The prior formal root authenticated the exact ordered parser/source replacement tables only when `binding.formal_parent == 08d...`, while `formal_parent` itself was not frozen by the helper. A caller could therefore alter that field and bypass the table-digest authority.

`50b0...` closes the bypass for the canonical replay path:

1. The exact canonical base raw SHA is frozen as `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`.
2. When the injected base has that canonical SHA, the helper first requires `binding.formal_parent == 08d5828cdb4c12afa3b798ff01826c91ceb8755a`; mismatch fails as `BLOCKED_AUTHORITY_NOT_CLOSED:base_identity`.
3. Only after that parent check does the helper authenticate the parser and source replacement programs against the frozen ordered table digests.
4. The direct negative `test_canonical_parent_bypass_fails` exercises the previously exploitable field drift.

This is the correct authority composition for the canonical v1.6 replay: canonical base bytes imply the frozen formal parent, which in turn is inseparable from the frozen parser/source table identities. Noncanonical in-memory toy fixtures used by the generic pure helper do not weaken the canonical path because they do not carry the canonical base SHA.

## Regression check

The previously closed controls remain present:

- pure injected-bytes helper; no I/O entrypoint;
- embedded no-I/O canonical base witness with `18966 / 8b0fad...` identity;
- parser replacements are flag/adjacent-value aware and ordered;
- owner-FD is zero in the base and inserted exactly once after `--bootstrap-project-root` value;
- self-check source replacements are function/span anchored to `boot()` / `main()`;
- exact canonical parser result `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`;
- exact canonical outer result `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`;
- table authority rejects extra/reordered/noncanonical replacement programs before mutation;
- failure matrix covers base identity, RAW shape, source rows 0–7 drift, relocation, parser reorder/wrong-adjacent, owner-FD, extra no-op/reordered table, and canonical parent bypass.

The submitted evidence reports `py_compile`, direct `unittest=13/13`, and `git diff --check` PASS. The approval is based on the production authority inspection above; the passing test count is supporting evidence, not a substitute for the code-level closure.

## Scope boundary / next action

This verdict **closes only the Stage-1 v1.7 launcher-freeze CPU/static implementation** for this exact pair/Gate.

It does **not** authorize:
- construction of a v1.7 execution request;
- Stage-1 retry/materialization;
- reuse or revival of the consumed v1.6 authority;
- source/checkpoint/manifest/data/cache I/O;
- child/runtime/config mutation;
- GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

A future v1.7 exact request must be constructed separately with fresh observations and then undergo its own exact-pair request review/approval before any one-shot Stage-1 execution authority can exist.
