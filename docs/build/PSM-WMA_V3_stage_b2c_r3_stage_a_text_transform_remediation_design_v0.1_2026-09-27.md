# PSM-WMA V3 Stage B2-C R3 — Stage-A Text Transform Remediation v0.1

- Date: 2026-09-27
- Remediation Gate: `V3-STAGE-B2C-R3-STAGE-A-TEXT-TRANSFORM`
- Parent Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- Parent B2-C design: root `ced270eb07bbf9fac321e410f6d1992911d591cb`.
- Execution pair remains root `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61` / child `8029b5ff002a350d22ee955db0463cc2e2d3665a` until cx forms a remediation pair.
- run03 failure review is the authority for the defect.
- CPU/static remediation only. No GPU execution is authorized by this design.

## 1. Goal

Fix only the missing Stage-A model-ready text/action transform in B2-C native payload construction.

run03 already proved:
- exact ep0 video decode works under frozen CUDA13 runtime;
- Stage-A host load works;
- Local-only optimizer profile is correct;
- R1-A FSDP Local scan works in the full real model.

R3 must not reopen those contracts.

## 2. Exact Stage-A transform authority

The frozen Stage-A config at:

`artifacts/v3/stage_a_edge_raw15_run02/psm_wma_v3/edge_robocasa/smoke/config.yaml`

uses `get_action_robocasa_sft_dataset` and freezes the RoboCasa dataset transform fields including:
- `format_prompt_as_json=true`
- `tokenizer_config.tokenizer_type=/disk/rl/models/Cosmos3-Edge-Policy-DROID`
- `cfg_dropout_rate=0.1`
- `max_action_dim=64`
- `resolution=null`
- `append_viewpoint_info=true`
- `append_duration_fps_timestamps=true`
- `append_resolution_info=true`
- `append_idle_frames=true`.

The implementation must derive these values from the loaded frozen Stage-A config rather than restating a divergent local constant set.

## 3. Preserve exact raw episode authority

The existing harness raw source remains authoritative for:
- task `CloseFridge`
- date `20250816`
- episode index 0
- raw frame identity 0..428
- raw native12 action
- official raw15 conversion
- exact consumer step anchors
- overlapping raw15 transition equality.

Do not replace this identity logic with shuffled/first-available iteration.

For each consumer step t:
1. fetch the exact raw payload using the already-validated raw dataset index;
2. keep the existing raw15/video/identity assertions;
3. make an isolated copy of the payload;
4. run that copy through a Stage-A-equivalent `ActionTransformPipeline` built from the frozen config;
5. use the transformed payload for the native callback.

## 4. Transform output contract

For every transformed consumer payload require:
- `text_token_ids` exists, is 1-D `torch.long`, non-empty and finite/integer by type;
- `sequence_plan` exists and is the expected WAM action-policy plan;
- `action` is the model-space padded action produced by the transform;
- `action_raw` preserves the unpadded canonical action contract;
- `video` remains the Stage-A left_wrist RGB payload;
- no `video_latent` exists;
- the transformed payload remains one-sample collatable by `custom_collate_fn`.

The harness must record, for at least consumer0:
- final structured `ai_caption`;
- text token count and a stable digest of token IDs;
- sequence-plan summary;
- action/action_raw shapes.

Do not record the whole token sequence in Gate result JSON unless needed; digest/count is sufficient.

## 5. Determinism and cfg dropout

Stage-A training enables `cfg_dropout_rate=0.1`.

B2-C is a deterministic wiring smoke, not a stochastic training sample study. The harness must explicitly freeze the Python RNG state before transforming the 16 payloads and record the seed in result JSON.

The chosen fixed seed must be tested to produce non-dropped, non-empty text for consumer0 and all 16 payloads. If any caption is dropped to empty by the frozen Stage-A transform, the harness must fail preflight rather than silently select a different seed during GPU execution.

No per-run random reseeding or retry is allowed.

## 6. CPU/static acceptance

cx must add focused tests proving:

1. raw payload without transform lacks `text_token_ids`, reproducing run03 cause;
2. frozen Stage-A transform adds `text_token_ids` and `sequence_plan`;
3. JSON prompt formatter is actually active; the final caption is structured JSON, not raw task text;
4. transform config values are read from the Stage-A config contract;
5. transformed `action_raw` / official raw15 transition semantics remain consistent;
6. model-space action padding remains compatible with the existing action-policy model path;
7. consumer0..15 raw index/episode identity is unchanged;
8. fixed RNG seed yields stable text-token digest/count across two CPU runs;
9. no Edge model weights, VAE forward, DCP load or GPU is needed for the CPU/static test;
10. all prior B0/B1/B2-A/B2-B/B2-C/R1-A/R1-B CPU regressions remain PASS.

## 7. Scope

Prefer modifying only:
- `examples/psm_wma_robocasa_local_s1.py`
- `examples/psm_wma_robocasa_local_s1_test.py`.

A small helper import from existing Action SFT/transform code is expected.

Do not modify:
- RoboCasa dataset production classes;
- ActionTransformPipeline production semantics;
- B0/B1/B2-A/B2-B/R1-A;
- optimizer/profile;
- model/FSDP code;
- DCP loader;
- TorchCodec environment handling.

cx must not run GPU.

## 8. Next execution

After cx fresh pair:
- ChatGPT and ds perform fresh CPU/static review.
- Only a fresh explicit approval may authorize one new full RTX4090 S1 run04 in a new unique directory.
- run01/run02/run03 stay immutable.
