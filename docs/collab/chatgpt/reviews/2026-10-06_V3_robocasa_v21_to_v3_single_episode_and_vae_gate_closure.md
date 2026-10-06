# V3 RoboCasa v2.1→v3 + single-episode corrected VAE Gate closure

- Date: 2026-10-06
- Formal production pair: root `b04fc2d4f1b2685bf9fb0e2b0f6277674bd2f93c` / child `8c3800565f66cfbce2929264f1c2a7854137482e`
- Execution Evidence: `/tmp/psm_wma_v3_robocasa_single_episode_vae_r1/`

## Verdict

`ROBOCASA_V21_TO_V3_SINGLE_EPISODE_AUDIT_PASS`

`CORRECTED_SINGLE_EPISODE_EXACT_WINDOW_VAE_PASS`

`APPROVE_TARGET_ATOMIC_FULL_EPISODE_VAE_AFTER_FULL_V3_METADATA_AUDIT`

`NO_N10_STAGING_REQUIRED`

## Gate A accepted evidence

CloseFridge episode 0:
- v2.1 frames = 429
- v3 frames = 429
- fps = 20
- timestamp max_abs = 0
- action [429,12] exact, max_abs = 0
- state [429,16] exact, max_abs = 0
- episode boundary/index aligned
- v3 task identity resolves via annotation.human.task_name -> meta/tasks.parquet -> CloseFridge
- three cameras first/middle/last exact at pixel level, max_abs = 0

This is sufficient to validate the conversion mechanics for the audited episode.

## Gate B accepted evidence

Same CloseFridge episode 0:
- source frames = 429
- left+wrist composed = 256x512
- VAE canvas = 192x320
- exact window = 17 frames, stride 1
- window_count = 413 = F-16
- latent anchors = [0,4,8,12,16]
- per-window independent encode
- latent = [5,48,12,20] fp32 finite
- first/middle/terminal independent re-encode parity:
  - exact_equal = true
  - max_abs = 0.0

## Offline VAE build provenance

The root builder is from the formal root. The actual runtime `vision_vae.py` used by the environment resolves to cosmos-framework commit:

`e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`

The formal child `8c380056...` does not contain that module. Therefore the full offline VAE build must explicitly pin and record:
- root builder SHA = `b04fc2d4...`
- offline VAE runtime SHA = `e3dc9ec...`
- Wan VAE checkpoint path/hash
- encode_exact_durations = [17,61,73]
- encode_chunk_frames = {"256":68,"480":24,"720":8,"768":8}

This is a provenance requirement, not a numerical blocker. Do not allow implicit environment drift during the full build.

## Full-data next step

Before launching the full target-atomic VAE:
1. prepare the complete canonical RoboCasa target-atomic v3 source;
2. metadata-only audit against v2.1:
   - 18 underlying task classes;
   - per-task episode counts match;
   - total episode count matches;
   - required action/state/camera/task fields present;
   - task identity remains annotation.human.task_name -> meta/tasks.parquet;
3. if metadata audit passes, encode ALL episodes. Omit `--episode-limit`.

No N=10 staging is required.

After the full build:
- merge all shard manifests;
- run cache structural audit;
- run bounded online parity probes;
- only then hand the cache to the consumer/trainer path.

No training authorization is implied by this review.
