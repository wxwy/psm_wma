# ChatGPT review — Stage-1 v1.7 consumer-capability design v2.1

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSUMER-CAPABILITY-DESIGN-V21`
- Formal root: `e1def003a645bf63da0e3e0007f2a7c4313325d9`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_CAPABILITY_IMPLEMENTATION`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

## Formal target / scope

This is a fresh formal pair relative to V20. The formal root changes only root docs/status for this Gate and its tree binds `cosmos-framework` mode `160000` exactly to the declared reachable child. No child/runtime implementation change is in scope.

## Delta reviewed

V20 was rejected for one HIGH: the design simultaneously declared the V18 C/v0.4 pair permanently terminal while allowing a future construction to reuse those same v0.4 paths, which would be an implicit retry.

V21 closes that exact blocker without weakening the consumer-capability closure:

- v0.3/v0.4 are permanently forbidden for future descriptor, patch, result, readback, input/output, cleanup, and residue handling;
- the only future tuple is a new, non-overlapping v0.5 JSON/Markdown pair;
- v0.5 itself still requires a future independent formal construction authority and same-pair review; this design does not grant construction authority;
- the pre-C `PatchConsumerV1` probe remains explicit, no-I/O, registry-based, non-PATH/non-import/non-tool-name lookup, and fails closed before C on mismatch/unavailability;
- the producer still performs exactly one strict UTF-8 conversion and hands the same immutable `patch_text` object through the frozen orchestration opaque-handoff ABI;
- the consumer remains exact-once, add-only, limited to the two ordered v0.5 paths, with no hidden Git/network/environment/child access;
- `APPLIED` / `REJECTED_NO_WRITE` / `PARTIAL_OR_UNKNOWN` remain exhaustive terminal semantics; only `APPLIED` permits byte-exact readback of the two v0.5 paths;
- any readback/identity/partial failure remains terminal with no second invocation, cleanup, repair, or retry.

No new contradiction or scope expansion was found. This Gate remains docs-only and authorizes only design of a future consumer-capability implementation.

## Verdict / boundary

`APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_CAPABILITY_IMPLEMENTATION`

Still NOT authorized: v0.3/v0.4 repair/retry/reuse; v0.5 construction; consumer implementation or invocation; P0/P1/C; materialization; launcher/runtime execution; real source/checkpoint/manifest/data/cache I/O; collection/receipt/record/publication; child/runtime/config mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
