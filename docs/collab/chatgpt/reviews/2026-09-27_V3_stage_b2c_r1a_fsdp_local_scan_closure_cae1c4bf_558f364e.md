# V3 Stage B2-C R1-A FSDP Local Scan closure review

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-R1-FSDP-LOCAL-SCAN`
- parent Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- formal root: `cae1c4bf5d681f93228a9b1a5c74e14d1b5acee4`
- formal child/Gitlink: `558f364efaf6704c9d65037c17ec250a9331be8a`
- design authority: `b5404e9896892b2156e2cca11ef64db871b34def`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2C_R1_FSDP_LOCAL_SCAN`

## Fresh-review basis

This review is bound to the exact fresh pair above.

ChatGPT independently reran the ten-file CPU/static suite on that pair:
- **205/205 PASS**
- 4 GPU tests deselected by scope
- zero CPU/static failures
- 55.99 s.

ds independently reviewed the same pair and reported:
- **205/205 PASS**
- independent `/tmp/v3_b2c_r1a_verify.py`: **26/26 PASS**
- 0 blocker / 0 hard-fail.

## Failure root cause closed at static contract level

The immutable B2-C run01 failed at B0 scan because Local encoder/core parameters were root-FSDP DTensors while the B1 evidence tensors were ordinary Tensors. The direct B0 adapter call bypassed the root FSDP forward lifecycle.

R1-A fixes that architecture rather than converting Local parameters out of FSDP:
- `Cosmos3VFMNetwork.scan_local_memory(...)` delegates to the exact model-owned `local_memory_runtime.encoder/core`;
- when root FSDP is active and Local Memory is enabled, `register_fsdp_forward_method(model, "scan_local_memory")` is registered after root sharding;
- the adapter accepts the model-owned scan capability and routes production scan through it;
- the B2-B relay passes the bound model scan capability;
- DTensor-owned Local parameters without a registered scan capability fail before B0 work.

## Preserved ownership and semantics

The implementation does not:
- use ignored Local parameters;
- convert model Local DTensors to plain tensors;
- copy Local weights into a side module;
- disable FSDP;
- enable inference mode;
- add a 4090-only Local implementation.

The adapter and relay retain object identity with:
- `model.net.local_memory_runtime.encoder`
- `model.net.local_memory_runtime.core`.

Local trainable inventory remains exactly **165,312 parameters**. B0/B1/B2-A/B2-B contracts, fast-state transaction semantics and serial gradient relay are unchanged.

CPU/static parity proves:
- model-owned scan output/state/present semantics match direct B0 scan;
- S0 and terminal padding are unchanged;
- gradients to Local slow parameters match the direct route;
- success commits only after the existing B2-B optimizer/transaction lifecycle;
- failure does not publish sidecar/frontier state.

## Scope boundary

`APPROVE_TO_CLOSE_V3_STAGE_B2C_R1_FSDP_LOCAL_SCAN`

This closes only the R1-A CPU/static remediation contract.

It authorizes **at most one R1-B tiny RTX4090 FSDP lifecycle micro-smoke** under the frozen design. It does not authorize a second full B2-C S1 run.

Full run02 remains blocked until:
1. R1-B tiny micro-smoke passes;
2. its Evidence is independently reviewed;
3. a new explicit run02 authorization is issued.

The immutable failed run01 Evidence remains unchanged.
