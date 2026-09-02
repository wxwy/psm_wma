# ChatGPT Independent Review — R09-B2 P4-v4 Preflight Materialization Design v0.4

- Verdict: `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS`
- Design: `dcb5b12fbdd83dd3869884e702dc8484ac5e6bde`
- Request/ledger: `8280f246a6b309fedd55d5f9d5ad9a8fedcc4ae3`
- Prior ChatGPT review anchor: `f031ddeedc0555d676b5737bcbd15475925d6ea1`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Independent finding

The sole v0.3 blocker is closed. v0.4 now defines `created_paths` consistently as the ordered filesystem-mutation footprint of successful mkdir syscalls, not as a stat-verified set:

1. perform nofollow mkdir for target;
2. on successful mkdir, immediately append target to `created_paths`;
3. then perform the nofollow stat;
4. mkdir failure leaves target out of the prefix;
5. post-mkdir stat failure leaves the just-created target in the prefix and returns/raises POISONED with that failed path.

This is internally consistent with the previously frozen POISONED semantics and makes the six mkdir + six post-stat fault fixtures unambiguous.

The v0.3 items previously accepted remain unchanged in v0.4: SHA-bound raw-byte admission authority, per-capability UNUSED→CONSUMED one-shot latch including zero-footprint first-mkdir failure, required same-backend ancestor-chain overlap exception, full precheck before any mkdir, fixed recurrent→ttt_fast_weight six-step mutation order, and unconditional public CLI hard-stop.

No production/tooling changes were present from the prior review anchor to the formal request HEAD; only the v0.4 design, status, and Inbox/ledger changed. The request-head Gitlink remains exactly frozen.

## Authorized implementation scope

Only:
- `tools/g0/r09_b2_p4_v4_execution_preflight.py`
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`

Implementation must preserve the existing public `main()` hard-stop and must not call the reservation helper from CLI.

Required CPU fixtures include the exact six mkdir and six post-stat failure prefixes, raw-byte admission binding, one-shot latch, required ancestor exception, zero-mkdir precheck rejection, ambient independence, and no subprocess/P5/child/tooling side effects.

## Still not authorized

This approval is static-tool implementation authority only. It does not authorize a real execution request, real preflight/reservation/materialization, candidate generation, staging publication, P4 record/refreeze/evidence publication, P5 export/compose/authority update, GPU/CUDA/torchrun, model/data/checkpoint I/O, evaluation/inference, B2-T, or Local Memory training.
