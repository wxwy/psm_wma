# R09-B2 P3 GPU-only local processor/tokenizer exception review

- Review target root: `895ed37a698531073452d8fbbb08f8aecf85f876`
- Plan commit: `8c71a94ecbe5fdeaf0d4f6ff2c113d483b346bb9`
- Submodule/Gitlink: `fe133043e4afe5f79e586af42b849c44fcf46757`
- Verdict: **APPROVE_LOCAL_PROCESSOR_EXCEPTION**

## Why this exception is acceptable

The exception is narrowly required by the actual production construction path rather than by a synthetic test convenience. `OmniMoTModel.set_up_tokenizers()` unconditionally executes `lazy_instantiate(self.vlm_config.tokenizer)`, while the LIBERO Edge recipe resolves that tokenizer configuration to the local `EDGE_POLICY_CHECKPOINT` directory. Therefore a full-recipe optimizer inventory cannot truthfully instantiate the production model while also forbidding every processor/tokenizer read.

The approved exception is limited to constructing the recipe's real local Cosmos3-Edge processor/tokenizer configuration from an already-existing local directory. It does not authorize model-weight loading, VAE/data/base-checkpoint access, network resolution, remote-code download, monkeypatching, synthetic processors, or substitute tokenizers.

## Implementation hard gates

1. **Local-only must be enforced, not just intended.** Before model construction, resolve and record the exact `EDGE_POLICY_CHECKPOINT` path and require it to be an existing local directory. The implementation should force offline/local-only behavior where supported (`HF_HUB_OFFLINE` / `TRANSFORMERS_OFFLINE` or equivalent) so an incomplete local package cannot silently fall back to the network.
2. **Processor exception must remain file-scope narrow.** Record the processor/tokenizer class/config source and local path used. If construction attempts to resolve a non-local repository/revision, remote code, or network resource, return `BLOCKED`.
3. **No weight/VAE/data/base-checkpoint reads through this exception.** The collector/verifier must keep the existing execution flags and fail closed if processor construction causes model-weight, VAE, dataset/cache, or base-checkpoint materialization/access.
4. **No monkeypatch/synthetic fallback.** The object must be the recipe-resolved production processor/tokenizer. A stand-in that merely allows model construction cannot produce PASS.
5. **Prior P3 GPU PASS gates remain unchanged.** Verifier-owned recurrent-only prefix, empty selector exclusions, actual optimizer membership/state eligibility, recurrent-vs-TTT matched diff, TTT five-member exclusion, and real production checkpoint/DCP serialization-schema binding remain required. If real DCP-compatible persistent membership cannot be established without save/load or other prohibited mutation, the final result must remain `BLOCKED`.

## Scope

This verdict only approves the v0.2 local processor/tokenizer exception and preserves the earlier authorization to implement the root-side GPU-only P3 collector/verifier/tests. It does **not** authorize GPU execution.

A separate review is still required for the exact implementation and exact GPU command before `APPROVE_TO_RUN_GPU_ONLY_P3_GATE` can be granted.

Still not authorized: B2-T, P4/P5 runtime/training, checkpoint save/load, forward/backward/optimizer step, evaluation, inference, closed-loop, SR, multi-GPU, long training, backend freeze, Global/Agent/RL.
