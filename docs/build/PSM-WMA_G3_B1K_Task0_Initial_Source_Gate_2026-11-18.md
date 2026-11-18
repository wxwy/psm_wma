# PSM-WMA G3 / BEHAVIOR-1K 2026 — Task 0 initial source Gate

## Scope and status

**Scoped source-binding PASS, Full Map NOT_RUN.** This increment does not
generate a scene mesh, native Room occupancy, Views, Island, SG, VAE or a
simulator-resumable episode. Do not call its JSON a
`nav_sg_spatial_snapshot_v1`.

The source is the official public B1K 2026 Task 0 data:
`turning_on_radio` in `house_double_floor_lower`, downloaded into the
user-approved **data** G3 root:

`/home/robo-shenzhen/benchmark/behavior1k_2026/`

Official B1K code: `v3.9.3-post2`,
`a8247a8cc1633fe1ca0cc66aa07243d46c64f155`.
The root V3 baseline used for this independent adapter: 
`ea4989a990f95fb9a2cadb40852322034c724fb9`.
This is a standalone candidate only; it does not change the running
G2 View producer, nav_sg, Cosmos Gitlink, checkpoint or input datasets.

## What is actually proved

- The official scene template has 261 distinct object definitions and 261
  matching initial state records; every template object has a valid finite
  root-link pose, category, model ID and scale.
- Official BDDL role names map to actual scene object identities:
  `radio_receiver.n.01_1 -> radio_89`,
  `table.n.02_1 -> coffee_table_koagbh_0`,
  `floor.n.01_1 -> floors_ulujpr_0`,
  and `agent.n.01_1 -> robot`.
- Episode metadata binds each of 200 demonstrations to a unique
  `task_instance_id` and `raw_episode_id`.
- Of these 200 IDs, **199** have corresponding `*-tro_state.json` files
  containing the three task-object initial states and one R1Pro initial pose.
  Episode index 199 / raw episode 3000 / task instance 300 is missing the
  public task-instance state. The missing `_0_300_template-tro_state.json`
  is not present even in the official downloaded ZIP; it is not a failed
  local extraction. Do not silently reuse 299 or any other state.
- All recorded raw poses and orientations are **source-native values**.
  Coordinate frame and quaternion conventions remain unverified until an
  actual OmniGibson scene-load Gate.
- This data is an **initial source index only**. Full 623D HDF5 dynamic
  states cannot be mapped to complete current scene geometry by column slicing.

## Implementation

`g3/behavior1k/source_adapter.py` has two separable responsibilities:

1. `initial_scene` validates static B1K template object and BDDL identity.
2. `bind_episodes` validates official episode-to-task-instance mapping and
   produces a source-bound record, refusing missing/duplicate target data.

`build_task0` is the pinned entry point; other tasks need explicit mapping
and validation rather than guessed file naming.

This purposely avoids importing the G2 native Snapshot validator, whose
`full_map_mujoco_source` mode requires native MuJoCo-specific source proofs
and is not suitable for relabeling B1K data.

## Gate commands and evidence

Use an isolated directory, not a running V3 checkout:

```bash
B=/home/robo-shenzhen/benchmark/behavior1k_2026
cd "$B/experiments/g3_source_candidate"
PYTHONPATH="$PWD" "$B/environment/tools/bin/python" -m unittest discover -s tests -v
PYTHONPATH="$PWD" "$B/environment/tools/bin/python" -m g3.behavior1k.source_adapter \
  --b1k-root "$B" --output-dir "$PWD/out"
```

Expected observed result:

- 5/5 CPU unit tests PASS; 0 failure/error/skip.
- Real source: 261 scene records; 200 episodes; 199 complete initial task
  state bindings; one explicitly blocked Task Instance 300;
  `SOURCE_BINDING_PARTIAL`, `full_map_ready=false`.
- Actual raw-file evidences and original scene JSON are not mutated.
- Machine-readable source outputs:
  `out/task0_initial_scene_source.json` and
  `out/task0_initial_episode_bindings.json`.

## Next independent Gate: genuine GT geometry

On the user-approved bms root
`/home/shenzhen/data1/szrobot/benchmark/behavior1k_2026/`,
load the licensed real scene using the pinned OmniGibson/Isaac Sim runtime.
An actual GT source provider must record stable object/part identities,
world transforms, visual/collision mesh or permitted geometry observations,
Room/floor/wall support, occupancy evidence, timestamp and robot pose,
bound to the same task instance. It must NOT bypass asset-use terms.

The native nav_sg / G2 source mode must either be extended with explicit
B1K provenance or have a separately validated source adapter. Reusing the
MuJoCo mode name with falsified hashes/source proofs is forbidden.

Acceptance of *one-frame Full Map*: geometry, Room and View projections
exist; target radio/table IDs and positions match the actual simulator
scene; visual confirmation against the same real render; missing
directions/Islands are handled explicitly; SG relations have evidence.
Only after this may one full Episode and event/owner indexing begin.

No Atomic standalone SR, Agent, G3 training or 200-episode View production
is authorized by this Gate.
