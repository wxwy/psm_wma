# ChatGPT review — Stage-1 v1.7 request-instance recovery design v1.2

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN`
- Formal root: `19181644aa7d8f08abfdc9c206f24d2dfc9acb1e`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence: `0`; child/runtime: `0`.

## Formal target / Gitlink

This is a fresh formal pair relative to the previously reviewed recovery design `7b528dc2fb754d9f27cab6ae157c15abaec654bc / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root tree independently resolves `cosmos-framework` as a mode-160000 Gitlink exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is reachable in `wxwy/cosmos-framework`.

The immediate formal delta is docs-only: `SESSION.md`, `TODO.md`, and `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.2.md`. No project production code or child code changes in this target.

## Authority chain

v1.2 explicitly inherits v1.1 except where it refreezes the future request identity tuple. v1.1's fail-closed facts remain authoritative: the prior v1.0 construction authority is permanently consumed; no retry, continuation, reinterpretation, or conversion into materialization authority is permitted. The v0.5-v1.0 lifecycle and closure rules remain in force unless explicitly rewritten.

## Remediation review

The v1.1 design already froze the future output sibling pair as `...request_instance_v0.3.{json,md}` and preserved P0/P1 non-consuming semantics, C-before-first-freshness consumption, same-round zero-mutation closure, two exact remote queries, absence checks, canonical JSON plus detached Markdown identity, and hard stop for independent request review.

v1.2 adds one narrow identity refreeze:

- `future_request_formal_parent = 08d5828cdb4c12afa3b798ff01826c91ceb8755a`
- `future_request_child_gitlink = 93a89ba61306d840a008813f62f26a34d54850f4`
- exact future JSON path `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json`
- exact future Markdown path `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.md`

The two identity values are not inferred from current HEAD, remote V2, environment, history, or worktree state. They are frozen design literals and must be copied byte-for-byte into P0/request identity.

## Independent consistency checks

The `future_request_formal_parent` value is semantically consistent with the existing request schema and replay authority: the historical v0.2 request JSON uses `formal_parent=08d5828...`, and v1.0 freezes the same value as canonical `ReplayBinding.formal_parent`. This field is an authority/replay parent identity, not the Git parent of the future request commit; therefore v1.2 does not conflict with the actual repository commit parent of this design.

The `future_request_child_gitlink` is exactly the formal Gitlink and exactly the frozen v1.0 `--child-gitlink` parser value. v1.2 also requires both future JSON and Markdown to bind the same parent/child tuple with the P0/P1 identities, preventing ambient substitution.

The future v0.3 output pair remains the sole permitted output pair; historical v0.1/v0.2 pairs remain excluded as candidate/template/input/output authority.

## Lifecycle / scope

P0 remains limited to the already-closed three-object allowlist and complete literal `ReplayBinding`; P1 remains injected-byte-only. Neither consumes authority. C begins immediately before the first live freshness observation and consumes the new one-shot authority; any later failure is terminal/no-retry.

A successful C may create only the docs-only v0.3 request pair and then hard-stop for independent exact-pair review. This design approval does not authorize materialization, launcher/materializer execution, source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

## Verdict

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

No current blocker remains for this exact recovery-design pair.
