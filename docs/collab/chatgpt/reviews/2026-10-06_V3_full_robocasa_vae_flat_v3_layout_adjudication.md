# V3 full RoboCasa corrected VAE — flat-v3 layout adjudication

Date: 2026-10-06

## Verdict

`SELECT_ROUTE_A_BUILD_CANONICAL_FLAT_V3_FIRST`

`DO_NOT_RUN_FULL_VAE_YET`

`DO_NOT_USE_PER_TASK_LOCAL_EPISODE_INDICES_AS_FINAL_CACHE_IDENTITY`

## Why

The existing v2.1→v3 conversion is valid. The issue is not conversion correctness; it is that the current converted target-atomic corpus is stored as 18 independent LeRobot v3 repos.

The canonical exact-window builder and Phase1B source binding both require one flat LeRobot v3 root. Phase1B additionally requires globally unique cache/source episode identity.

Per-task repos reuse episode_index from zero, so a direct per-task full VAE build would create duplicate episode indices across task classes and would not satisfy the frozen source-binding contract.

Therefore the correct sequence is:

1. Build one canonical flat RoboCasa target-atomic LeRobot v3 mirror from the 18 validated per-task v3 repos.
2. Validate the flat mirror against the already-passed metadata audit.
3. Run the existing canonical 8-GPU exact-window VAE launcher unchanged over all episodes.
4. Merge the canonical shard manifests.
5. Structural audit + bounded parity.

## ETL requirements

The flat-v3 ETL must be implemented as a repository tool by cx; ds must not write an ad-hoc local script.

It must preserve video pixels without transcoding and deterministically remap all identities:

- global task table must preserve **both** natural-language phrasings and underlying task-class strings;
- remap data-row `task_index` from each local phrasing index to the corresponding global phrasing index;
- remap `annotation.human.task_name` from each local task-class index to the corresponding global underlying-class index;
- remap `episode_index` to globally unique 0..N-1;
- remap global row `index` to globally unique contiguous indices;
- preserve `frame_index` inside each episode;
- rebuild meta/episodes and data/video file references consistently;
- write a deterministic mapping artifact:
  `task_class, local_episode_index, global_episode_index, local/global row ranges, local/global task indices`.

Do not collapse meta/tasks.parquet to only 18 task-class rows; that would destroy natural-language `task_index` semantics.

## Acceptance before full VAE

The flat mirror must prove:

- 18 underlying task classes;
- 9126 episodes;
- 2,231,347 frames;
- per-task episode counts exactly match the validated source audit;
- every global episode_index is unique;
- every global row index is unique/contiguous;
- task_index resolves to the same natural-language phrasing as before;
- annotation.human.task_name resolves to the same underlying task class as before;
- action/state values unchanged;
- selected first/middle/last RGB frames are pixel-exact to the per-task source;
- no video re-encode/transcode;
- one-episode LeRobotDatasetMetadata/LeRobotDataset read smoke passes from the flat root.

After this Gate passes, full VAE is authorized with the existing canonical launcher over all 9126 episodes, with no episode-limit staging.

Output must be placed on /mnt/data, not /mnt/data1, due projected cache size.

## Scope

No production model/trainer/inference code changes are authorized.

Only a tools-only flat-v3 ETL plus its tests/evidence is needed before the full VAE.
