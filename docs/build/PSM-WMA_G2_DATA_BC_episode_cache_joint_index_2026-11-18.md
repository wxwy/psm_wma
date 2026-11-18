# G2 DATA_B/C: episode state15 and causal joint index (2026-11-18)

The code lives in V3 g2/data/episode_state.py, joint_index.py, aligned_provider.py,
and tools/g2/build_data_bc_cache.py. This is a real-data scoped candidate, not
a formal G2 train/val or Phase5 training acceptance.

## A. Storage and source coordinate frame

B root:
  /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-state15/
  tasks/<task>/episodes/episode_xxxxxx/state15.pt
  tasks/<task>/episodes/episode_xxxxxx/COMPLETE.json
  manifest.json

Each episode has one numeric state15 tensor [N_original_20Hz_frames,15], FP32
CPU with current original source-world base Pose5 and UNCHANGED official G1 EEF10.
Only state is saved, no duplicate G1 action labels, videos or latent. The file
embeds the SHA-bound official G1 source index receipt, origin frame count, recipe,
20Hz source range and original task caption. COMPLETE.json SHA-binds the file.
No map or spatial update rate resampling of state is permitted.

C root:
  /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-g2-data-c/
  tasks/<task>/episodes/episode_xxxxxx/joint_index.json
  tasks/<task>/episodes/episode_xxxxxx/COMPLETE.json
  manifest.json + CORPUS_COMPLETE.json

Each C episode stores the compact logical spatial state timeline (1Hz-ish/terminal)
plus one index record for EVERY legal G1 20Hz decision window. Each window binds:
  state15_frame = action_start_frame = decision_frame
  action_last_frame = decision_frame+15
  observation_last_frame = decision_frame+16
  spatial_state = latest published spatial frame <= decision_frame
  task static text_id, SG and metadata, selected VAE View physical owner/frame,
  per-View Wan recipe/content hash, native metric projection and membership.
One selected floor_top variant only: clean producer selection is explicitly
mapped to floor_top_w_rbs when with_robot is configured. Future owner forbidden.

## B. Real execution proof

Task/episode                 Original state15      Spatial  G1 windows
CloseBlenderLid/000009       [493,15]              51       477
CloseBlenderLid/000075       [345,15]              36       329
CloseBlenderLid/000104       [434,15]              45       418
DATA_C TOTAL                 1272 frames           132      1224

Additional DATA_B-only dynamic navigation episodes:
NavigateKitchen 002022 / 002024 / 002033 = 177 / 163 / 237 frames.
These have source state15, but DATA_C is not written until their independent VAE
cache exists and has passed its own declared recipe/source checks.

G1 SourceBindingDigest:
f91b0b477a048beb439f1d73e7414f6b1d2a0307eee54c858d6cd8503ea19020

Pose5 source-world recipe:
9f0dc5c922e90a71177308298e2f4d85d6769fce40c4f9f72e8ee77640df9fdf

Actual B32 Wan View VAE recipe:
b1c6e1f6b2a6b69ae1ffdc5afa47d3454f4d3289d22854a5ed2645ebc130fad1

Initial DATA_C recipe:
e8da63970bfe1f511afac45721fa12d75dc5803b07acac36d0a060c0f8d7cf0d

## C. Usage and read boundary

Invoke tools/g2/build_data_bc_cache.py with explicit:
--source-root, --g1-verified-index, --g1-cache-root, --views-root,
--data-b-root, --data-c-root, --task-class, --episodes, --view-vae-recipe-id,
--top-view-variant with_robot.

Use --only-b for episodes without ready View VAE. The run is CPU only and never
runs VAE, renderer, ROS or simulator. It refuses unsafe overwrites or partial
outputs. Complete episodes are revalidated for resume, and the corpus manifest
can incrementally include newly completed episodes.

CandidateAlignedG2Provider returns actual CPU FP32 state15 and native
G2SampleIdentity, StaticTaskText and selected SpatialView latents using
the existing official mmap/LRU ViewReader. The model G2TrainingDataAdapter
consumed the three real episodes at decision frames 16/32/48 for R1+R2,
preserving G1 action15 labels and refusing future/unknown recipe.

IMPORTANT: candidate provider evidence_scope IS NOT verified_data_c.
The current initial enhanced text template is marked production_template_frozen=false,
and the G1 exact train/val split receipt has not been frozen for G2. Both root
manifests carry training_ready=false. The fixed Phase5 G2RunRecipe MUST reject
this candidate; do not rename evidence_scope or flip completion markers.
Next gates are static text/split approval, trusted DATA_C provider+receipt,
real full Edge Phase5 R1/R2/Local action loss and DCP smoke, then online ABI.
