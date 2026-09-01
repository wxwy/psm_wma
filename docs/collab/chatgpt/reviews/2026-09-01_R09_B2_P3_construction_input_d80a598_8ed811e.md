# R09-B2 P3 construction-input binding re-review

- Review request root: `d80a598e131911ba1f562414cfccb7b0b621ce37`
- Reviewed implementation root: `8ed811e5ef5638d3946d6da0fd81f2c9a1481f86`
- Submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: static P3 isolated-worker construction binding only; no GPU/HF/processor/model construction authorization.

## Verdict

**APPROVE_TO_CONTINUE_GPU_P3_IMPLEMENTATION**

The previous HIGH blocker is closed.

`prepare_isolated_worker()` no longer validates a detached tokenizer dict. It accepts the actual resolved `vlm_config`, canonicalizes the exact `.tokenizer` node consumed by the production helper, validates `repository=None`, `revision=None`, and `tokenizer_type == canonical local Edge path`, and stores that normalized binding in the worker record.

`run_production_processor_construction()` independently canonicalizes the tokenizer node from its actual `vlm_config` construction input and compares it with the previously validated binding before importing/calling the shared production constructor. A mismatch therefore fails before processor construction. The construction witness SHA is computed from that actual construction input rather than only from the earlier record.

The permanent regressions cover both required split-input attacks: validated local A + different-local-path B, and validated local A + remote B. Both fail before the production helper can be imported/called.

The shared production primitive remains `cosmos_framework.model.generator.omni_mot_model.build_vlm_processor`, and `OmniMoTModel.set_up_tokenizers()` uses the same primitive at submodule revision `21d064f`; its source remains covered by the existing model-source commit-blob provenance gate.

## Remaining pre-run requirements

This approval only permits continued static implementation. Before any `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`, the previously retained execution-level requirements still apply, including:

1. the actual isolated worker must demonstrate the approved order on the real production path: offline environment applied -> binding validated -> first production processor construction -> independent post snapshot;
2. actual processor assets must remain read-only across that construction;
3. actual production optimizer/DCP persistent-membership evidence must replace symbolic-only DCP claims where still outstanding;
4. exact run provenance / D005 / source commit-blob / single-GPU / <=24 GiB gates remain mandatory.

## Scope

Not authorized by this verdict:
- GPU execution;
- HF/Transformers processor construction;
- model construction;
- checkpoint/model weight/VAE/data/dataloader loading;
- forward/backward/optimizer/scheduler step;
- DCP save/load;
- B2-T, P4/P5;
- training/eval/inference/closed-loop/SR;
- multi-GPU/long training/backend freeze/Global/Agent/RL.
