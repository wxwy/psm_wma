# ChatGPT Review — R09-A1 last pre-run evidence fixes @ d91ee0c / c0287e2

- Date: 2026-08-29
- Reviewer: ChatGPT
- Review request commit: `32e3bce9cf9815816f6fdb8cabc29f2effac7c5d`
- Reviewed root: `d91ee0c7b988571075805f1bf092030fa513b1b8`
- Reviewed submodule/Gitlink: `c0287e215f265134cb8b8d947de7eb398f0246cf`
- Verdict: **APPROVE_TO_RUN_CORRECTED_A1**

## Decision

The final pre-run static/evidence gates are closed.

Accepted:
- `segment_detach_value_exact` is now explicitly captured and consumed by verifier hard PASS;
- segment boundary now proves both value continuity and autograd detach;
- direct optimizer object-set equality is hard-gated;
- selected gradients must be present/finite and encoder/recurrent_backend/Local-adapter groups each require nonzero gradient;
- full-run CUDA peak must have positive allocated/reserved bytes and a non-null GPU device;
- verifier derives the training Gitlink independently from the supplied training root revision and requires `derived_gitlink == training_gitlink == training_submodule`; 
- D005 training-command sidecar is mandatory, source-matched, and SHA256-bound into the artifact;
- verifier root/submodule strict clean and verifier Gitlink==submodule remain hard PASS conditions;
- R09 stateless readout remains frozen and outside the corrected 16-tensor optimizer scope.

## Authorized run

Authorization is limited to the corrected R09-A1 bounded single-GPU smoke:
- one A100 GPU;
- 100 optimizer steps;
- Gate-A canonical checkpoint warm-start;
- corrected 4-prefix allowlist only;
- `PSM_R09_A1_ENABLED=1`;
- runtime probe enabled through `PSM_R09_A1_PROBE_OUTPUT`;
- preserve exact D005 command/cwd/env/resources/network/input/output/source provenance before launch;
- training must run from a committed clean source whose reviewed R09 model/config/probe code is identical to `d91ee0c / c0287e2`; record the exact launch root/submodule/Gitlink in the sidecar.

## Required closure evidence after the run

Stop at REVIEW and submit:
- exact training root/submodule/Gitlink + D005 sidecar;
- final 100-step log and checkpoint;
- runtime probe JSON;
- verifier output from committed clean verifier source;
- exact 16-tensor optimizer membership proof;
- per-selected grad evidence and group nonzero-grad proof;
- frozen checkpoint tensor unchanged proof;
- full-run VRAM + latency + state bytes + segment detach/reset evidence;
- final fixed-weight Normal/Zero/Shuffle Future+Action sensitivity with non-history invariants preserved.

Future/Action sensitivity is a post-checkpoint A1 closure gate; it does not block this authorized 100-step run, but A1 cannot be marked DONE without it.

## Still blocked

- R09-B / TTT
- multi-GPU
- long training
- matched SR
- backend freeze
- shared MoT changes
- Global / Agent / RL

Any model/dataflow/allowlist change beyond the reviewed source invalidates this authorization and requires re-review.
