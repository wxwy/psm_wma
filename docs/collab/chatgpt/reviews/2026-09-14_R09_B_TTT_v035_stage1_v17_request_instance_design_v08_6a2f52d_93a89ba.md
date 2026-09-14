# ChatGPT review — Stage-1 v1.7 request-instance design v0.8

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Formal root: `6a2f52d6adc641edb0ac9215c72481a7dfca620a`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.8.md:25)`
- Blockers: `2 HIGH`; Design/Authority: `2 HIGH`; Production: `0`; Evidence: `0`; child/runtime: `0`.

## Scope / lineage

The formal root is a docs-only remediation of v0.7. Its immediate delta is limited to `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.8.md`, `SESSION.md`, and `TODO.md`. The formal Gitlink remains exactly `93a89ba...`, and the child commit is reachable.

The claimed prior P0 failure is consistent with v0.7's approved phase semantics: the failed read-only object lookup occurred before P1 and before the first C freshness observation, so no C attempt was entered and the one construction authority was not consumed.

The newly frozen object identities are also individually real:
- formal-parent replay base: `08d5828...:docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`, blob `af19a9eb...`;
- replay helper: `50b0bffe...:tools/psm_wma/stage1_v17_launcher_replay.py`, blob `74455fce...`;
- adapter source in the formal parent: `08d5828...:tools/psm_wma/materialize_immutable_source_authority_root.py`, blob `4a51bddd...`.

v0.7's P0/P1/C timing, C-before-first-freshness consumption point, no-retry rule, detached request identity, two-query contract, and no-materialization boundary remain directionally correct.

## HIGH 1 — P0 read-source allowlist contradicts the new helper mapping

The role table explicitly permits the replay helper to come from implementation root `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`. Later, however, v0.8 says P0's allowed read-only source is still limited to `future formal root/its frozen parent`.

Those statements cannot both control the same P0:
- `50b0bff...` is not the frozen formal parent `08d5828...`;
- the future request formal root does not exist before the docs-only pair is created and committed;
- therefore the helper read is simultaneously explicitly allowed by the table and excluded by the generic P0 allowlist.

This must be a closed immutable-object allowlist, not inferred from a future root or ambient history.

### Acceptance

Replace the generic source rule with an explicit P0 object-source table using only already-existing immutable roots/objects. At minimum bind:
- replay base source to the exact `08d5828...` path/blob/length/SHA;
- replay helper source to exact implementation root `50b0bff...` path/blob/raw identity;
- adapter source to its exact approved root/path/blob/length/SHA;
- any projection-helper source, if it must be loaded during P0/P1, to its exact closed implementation root/object.

P0 must reject any source root/path/object outside that closed table. Do not use a not-yet-created future request root as a P0 acquisition authority.

## HIGH 2 — outer payload is still modeled as a Git-read object instead of replay-derived output

At line 25 v0.8 says P0 must obtain `outer payload` from its frozen formal tree and that the P0 result must list each item's source commit/path/blob/length/SHA.

That is not the frozen dataflow. The v1.7 outer payload is produced by `replay_outer_payload(base_source, binding)` from the canonical base and binding, then accepted only if it equals the frozen `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8` identity. No separate authoritative Git object/path/blob for the replayed outer has been frozen here.

Treating outer as another tree object recreates the exact class of role confusion that caused the v0.7 P0 failure and permits an executor to choose a test fixture or another stored copy as authority.

### Acceptance

Freeze the P0 dataflow explicitly:
1. acquire and verify the exact replay base object;
2. acquire/verify the exact closed replay helper/binding authority;
3. acquire and verify the exact adapter source object;
4. derive `outer_payload_bytes` only by `replay_outer_payload(base_source, binding)`;
5. require the derived outer to equal exact `18875 / 658e...` and bind it as a derived result, not as a Git path/blob;
6. feed only that derived outer plus the exact adapter bytes to P1.

The P0 result should record provenance for source Git objects and record replay derivation plus raw length/SHA for the outer output; it must not require a nonexistent outer source path/blob.

## Boundary

No request construction is approved for `6a2f52d...`. No materialization, launcher/materializer execution, source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized.
