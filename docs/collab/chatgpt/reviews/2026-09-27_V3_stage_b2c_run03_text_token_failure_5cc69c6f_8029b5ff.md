# V3 Stage B2-C run03 failure review — missing Stage-A text transform

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- execution formal root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- run: `artifacts/v3/stage_b2c_4090_s1/run03/`
- result: `REQUEST_CHANGES`
- no run03 retry authorized.

## What passed before failure

run03 used the frozen non-empty CUDA13 `LD_LIBRARY_PATH` and successfully passed:
- TorchCodec exact CloseFridge ep0 decode;
- Stage-A Edge model materialization;
- Stage-A DCP host load;
- Local-only 165,312 parameter selection / host freeze;
- B1 cached-latent evidence preparation;
- R1-A model-owned FSDP Local scan;
- B0 scan completion.

This proves the previous TorchCodec environment issue and the run01 Tensor/DTensor Local-scan defect are both closed in the full real 4090 harness.

## Failure

The run failed on native consumer 0 inside `OmniMoTModel._load_and_tokenize_text_data`:

```text
KeyError: 'text_token_ids'
```

The B2-C harness builds native payloads directly from `RoboCasaLeRobotDataset`. That raw dataset returns `ai_caption`, but the Stage-A training recipe does not feed the raw dataset directly to the model.

The frozen Stage-A config uses:

```text
get_action_robocasa_sft_dataset
  -> RoboCasaLeRobotDataset
  -> ActionSFTDataset
  -> ActionTransformPipeline
```

and specifically freezes:
- `format_prompt_as_json=true`
- `tokenizer_config = Edge processor/tokenizer`
- `cfg_dropout_rate=0.1`
- `max_action_dim=64`
- `resolution=None`.

`ActionTransformPipeline` applies the structured action prompt formatter and then `TextTokenizerTransform`, emitting `text_token_ids`, `sequence_plan`, padded action and other model-ready fields.

Therefore directly tokenizing the raw task string after the fact is not sufficient authority: it could silently differ from the Stage-A JSON prompt/tokenization path.

## Required remediation

Keep the exact raw episode0/shard/index authority used to prove identity/raw15 overlap, but construct each native model payload through the same Stage-A `ActionTransformPipeline` configured from the frozen Stage-A dataset config.

Required order:

```text
exact raw RoboCasaLeRobotDataset consumer
→ copy raw sample
→ Stage-A ActionTransformPipeline using frozen config
→ require text_token_ids present
→ require sequence_plan present
→ require padded action/model payload semantics
→ native callback / custom_collate_fn
→ OmniMoTModel.training_step
```

The raw episode/action authority must not move to a shuffled iterable dataset and must not substitute another episode.

The transformed payload's `action_raw` must remain consistent with the official raw15 transition authority already checked by the harness.

## Resource status

run03 did not fail from OOM. No algorithm constants may change.

run01/run02/run03 remain immutable. Any new full run requires:
1. narrow harness remediation;
2. CPU/static fresh review;
3. one explicit new run authorization with a new output directory.
