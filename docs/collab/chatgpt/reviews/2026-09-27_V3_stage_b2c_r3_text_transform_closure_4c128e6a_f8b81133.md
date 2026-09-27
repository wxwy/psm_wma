# V3 Stage B2-C R3 Stage-A Text Transform closure review

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-R3-STAGE-A-TEXT-TRANSFORM`
- parent Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- formal implementation root: `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0`
- formal child/Gitlink: `f8b81133f22ab01197b7b36003207cf5cfeb2e41`
- design authority: `3091df07983d15f4ecad3a30b27fd721522aede4`
- review-request bookkeeping root: `04fef163efb011693bb39d3bd0f53e752ae2c98a` (not part of the formal implementation pair)
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2C_R3_STAGE_A_TEXT_TRANSFORM`

## Fresh-review basis

The formal root pins exactly child `f8b81133...`. Relative to the previously approved B2-C harness child, the remediation changes only:
- `examples/psm_wma_robocasa_local_s1.py`
- `examples/psm_wma_robocasa_local_s1_test.py`.

No dataset, ActionTransformPipeline, model, FSDP, DCP loader, optimizer, B0/B1/B2-A/B2-B/R1-A/R1-B production semantics changed.

ChatGPT independently reran on the exact child:
- R3 + B0/B1/B2-A/B2-B/B2-C/R1-A/R1-B ten-file CPU suite: **207/207 PASS**;
- Stage-A native contract suite in its own process: **26/26 PASS + 10 subtests PASS**;
- fresh real frozen-asset CPU preflight: **PASS**.

The Stage-A native unittest suite leaves global PyTorch grad mode disabled when mixed into later TTT tests in the same pytest process. That pre-existing test-state interaction was independently reproduced and isolated. It is not a production-path failure; the authoritative suites are therefore run in separate processes, where both pass completely.

## run03 blocker closed

run03 failed because the harness passed the raw `RoboCasaLeRobotDataset` payload directly into `OmniMoTModel.training_step`. The raw payload has `ai_caption` but is not model-ready and lacks `text_token_ids` / `sequence_plan`.

The reviewed remediation keeps the exact raw episode authority first:
- CloseFridge / 20250816 / episode0;
- exact flat-index resolution;
- raw frame sequence;
- native12 source action;
- official raw15 conversion;
- 16 cursor0 consumer anchors;
- exact overlap checks for every 32-transition chunk.

Only after those identity/action checks does the harness deep-copy each raw payload and run it through the frozen Stage-A `ActionTransformPipeline`.

## Stage-A transform parity

The transform is constructed from the frozen Stage-A config via `LazyConfig.load`; it does not hand-code a tokenizer substitute.

The reviewed path inherits the frozen Stage-A values including:
- `format_prompt_as_json=true`;
- Edge tokenizer config;
- `cfg_dropout_rate=0.1`;
- `max_action_dim=64`;
- `resolution=None`;
- Stage-A append/metadata settings.

A single deterministic Python RNG seed `0` is set before transforming the 16 consumers. The real dropout code still runs; all 16 transformed prompts remain non-empty, otherwise preflight fails.

Each transformed native payload is required to contain:
- non-empty 1-D long `text_token_ids`;
- WAM `sequence_plan` with text/vision/action present;
- vision clean frame `[0]`;
- action clean frame `[0]` (prepended state token);
- canonical `action_raw [33,15]`;
- model-space padded `action [33,64]` with zero tail and `raw_action_dim=15`;
- Stage-A left_wrist RGB;
- no cached `video_latent`.

The cached Wan latent remains Local evidence only.

## Independent real preflight

Fresh ChatGPT preflight output:
`/tmp/chatgpt_v3_b2c_r3_preflight_20260927_01/result.json`

Observed:
- status: PASS
- exact task/episode/cursor: CloseFridge / 0 / 0
- frames: 429
- payloads: 16
- raw action width: 15
- transform seed: 0
- consumer0 structured action JSON present
- consumer0 text token count: **152**
- token SHA256: `854e3c085df7ab1b392c0e4960875673123b22e5afd4d051c11c9ac119380aad`
- sequence-plan action conditioning: `[0]`
- `action [33,64]`
- `action_raw [33,15]`
- CPU execution only; no CUDA trace.

This matches cx's independently recorded frozen-asset preflight digest/count.

## Scope and execution authorization

`APPROVE_TO_CLOSE_V3_STAGE_B2C_R3_STAGE_A_TEXT_TRANSFORM`

R3 closure fixes only the Stage-A model-ready payload transform used by the B2-C harness.

Exactly **one** new full RTX4090 B2-C S1 execution is authorized:
- run name/output: `artifacts/v3/stage_b2c_4090_s1/run04`
- execution formal pair: root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0` / child `f8b81133f22ab01197b7b36003207cf5cfeb2e41`
- frozen CUDA13 `LD_LIBRARY_PATH` from R2;
- unchanged B2-C algorithm constants and Local-only optimizer;
- no retry, fallback, T/K/chunk change, alternate episode, cached-policy latent, or output-directory reuse.

run01/run02/run03 remain immutable.

This authorization does not yet close B2-C and does not authorize 8xH100 formal training. B2-C still requires fresh review of run04 GPU Evidence.
