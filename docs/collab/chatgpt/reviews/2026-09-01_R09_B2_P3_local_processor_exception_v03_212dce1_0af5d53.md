# R09-B2 P3 GPU-only local processor exception v0.3 review

- Review target root: `212dce11677591199745e086b5bf4379241bf37d`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Verdict: **APPROVE_LOCAL_PROCESSOR_EXCEPTION**

## Review conclusion

v0.3 closes the remaining plan-level hardening gap around the unavoidable production VLM processor construction. The approved exception remains narrow: the real recipe may construct its actual processor/tokenizer only from the pre-existing local `EDGE_POLICY_CHECKPOINT` directory, under explicit offline mode, without model-weight/VAE/data/base-checkpoint/network access.

The plan now correctly requires pre-construction fail-closed checks for local-path validity, offline Hugging Face/Transformers environment, required local tokenizer assets, and rejection of remote repository/revision/code or synthetic/monkeypatched substitutes. These checks are compatible with the production path where `OmniMoTModel.set_up_tokenizers()` unconditionally instantiates `vlm_config.tokenizer` and the LIBERO Edge recipe resolves that tokenizer to `EDGE_POLICY_CHECKPOINT`.

## Implementation hard requirements

Approval is for implementation only. The collector/verifier must make the following machine-verifiable, not merely descriptive:

1. the recipe-resolved tokenizer/processor path must resolve exactly to the canonical absolute `EDGE_POLICY_CHECKPOINT` path; `repository`/`revision` must remain local/empty as expected;
2. `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` must be set before any processor/model construction; any remote-resolution attempt must fail closed;
3. the required local tokenizer assets must be checked before construction and recorded in the artifact;
4. the local package must remain read-only during the gate: no new or modified files may be produced under the Edge package/cache path by the collector;
5. this exception does not permit model-weight, VAE, dataloader/data, base-checkpoint, forward/backward/step, DCP save/load, checkpoint write, training callback, evaluation or inference;
6. all previously approved GPU-P3 PASS gates remain unchanged, including verifier-owned recurrent-only prefixes, empty selector exclusions, actual optimizer/state/DCP membership checks, TTT five-member exclusion, and the 24 GiB resource ceiling.

If any of the above cannot be proven without widening the execution surface, the only valid result is `BLOCKED`.

## Scope

This verdict does **not** authorize GPU execution. After implementation/tests are committed and independently reviewed, GPU execution still requires a separate `APPROVE_TO_RUN_GPU_ONLY_P3_GATE` decision.

No authorization is granted for B2-T, P4/P5, training, evaluation, inference, closed-loop, SR, multi-GPU, long training or backend freeze.
