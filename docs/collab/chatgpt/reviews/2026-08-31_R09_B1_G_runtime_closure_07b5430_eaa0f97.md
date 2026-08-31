# R09-B1-G bounded GPU smoke runtime closure review — root 07b5430 / runtime source 9dbd3ca / verifier fix 7204d20 / submodule eaa0f97

## Verdict

**APPROVE_TO_CLOSE_B1_G**

This closes only the bounded/noncanonical R09-B1-G runtime smoke contract. It does not convert the smoke into canonical Gate-A, formal-scale training, throughput, convergence, SR, eval/inference, or deployment evidence.

## Evidence reviewed

- Evidence commit: `07b54302ecee7725964ec4ef97410ecf5f8db307`
- Runtime source root recorded by D005/probe: `9dbd3ca8f07130c67bfe04c3cb380c20c561218a`
- Submodule/Gitlink: `eaa0f979974579939bc680ff683cf016bafdbce8`
- CPU-only verifier correction: `7204d202b32a335b3dde5bbafa6f26751b74a114`
- No GPU retrial was required for the verifier correction.

## Closure checks

### Gate-A bounded rebuild — PASS

- `smoke_batch1_gate_a`, `max_samples_per_batch=1`, `grad_accum_iter=1`.
- 2/2 finite optimizer steps: 18.811033, 17.932665.
- Complete iter2 DCP is recorded with recursive file size/SHA256 manifest for model/optim/scheduler/trainer.

### B1 bounded smoke — PASS

- `smoke_batch2_b1`, `max_samples_per_batch=2`, `grad_accum_iter=1`.
- First packed batch history evidence is PASS: sample 402/0 history absent; sample 402/1 history present with 1 valid history step; effective Local-history sample count=1.
- Exact rebuilt iter2 checkpoint is loaded model-only at iteration 0.
- 5/5 finite B1 losses: 17.975386, 15.754356, 17.088230, 14.520623, 16.162872.
- Complete iter5 checkpoint produced.

### Runtime/provenance contract — PASS

Final `smoke_contract.json` reports PASS with all 19 checks true, including:
- source root/submodule/Gitlink chain;
- exact two-phase D005 command/profile binding;
- single NVIDIA A100-SXM4-80GB binding and CUDA peak recording;
- cache-only / no-online-VAE fallback in both phases;
- B1 first packed batch has effective Local history;
- checkpoint schema removes only historical GRU keys;
- 553 frozen common tensors are bitwise unchanged;
- exact optimizer target membership;
- TTT encoder gradients absent/zero as required by the frozen contract;
- adapter gradient groups present/finite with nonzero signal;
- exact B0 five-member TTT state schema, 18,953 B/sample;
- fresh/segment/reset/detach state semantics;
- verifier root/submodule tracked-clean.

CUDA peak recorded: allocated 8,501,718,528 bytes; reserved 8,556,380,160 bytes.

## Verifier false-negative repair review

The post-run verifier corrections are acceptable as CPU-only evidence interpretation fixes rather than runtime/model changes:
1. checkpoint-load regex escaping was corrected;
2. adapter gradient acceptance was corrected from “every tensor in a group must be nonzero” to the intended group-level evidence requirement;
3. probe paths are compared after `Path.resolve()` so an absolute D005 path and the same relative CLI path do not falsely mismatch.

These changes do not alter model weights, runtime algorithm, training command, data, checkpoint handoff, or GPU execution. Re-running GPU would therefore be unnecessary and would violate the bounded no-auto-retry discipline.

## Scope after closure

R09-B1-G may move from REVIEW to DONE/CLOSED as a **bounded runtime smoke**.

Still blocked and requiring separate approval/evidence: canonical/formal-scale training, eval/inference/closed-loop, multi-GPU, long training, matched SR, backend freeze, shared-MoT/RoboTTT expansion, Global, Agent and RL.
