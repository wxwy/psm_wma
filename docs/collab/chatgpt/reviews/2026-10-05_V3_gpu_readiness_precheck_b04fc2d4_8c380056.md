# V3 Corrected GPU readiness precheck — GPT review

- 日期：2026-10-05
- Gate：`CORRECTED-V3-GPU-READINESS-PRECHECK`
- formal root：`b04fc2d4f1b2685bf9fb0e2b0f6277674bd2f93c`
- child/Gitlink：`8c3800565f66cfbce2929264f1c2a7854137482e`
- production promotion：CLOSED
- current execution host：single RTX 4090 24GB

## Verdict

`CORRECTED_V3_GPU_READINESS_PRECHECK_CLOSED_CONTRACT_GREEN`

`GPU_OPTIMIZER_SMOKE_BLOCKED_ON_CURRENT_SINGLE_24G_HOST`

`APPROVE_TO_RUN_CORRECTED_V3_8XH100_FRESH_ITER0_TO_ITER1_WHEN_AVAILABLE`

`FORMAL_TRAINING_NOT_AUTHORIZED`

## Production-pair strict preflight

Executed on a clean formal-root worktree with the exact reviewed child SHA.

Parameters:
- root = `b04fc2d4...`
- child = `8c380056...`
- strict snapshot10 cache/source
- T=16
- B_stream=8
- GA=2
- K=4
- world_size=1 only for bounded preflight/catalog validation
- max_iter=30000
- save_iter=100
- warmup=500

Result: PASS / exit code 0.

Witnesses:
- exact root/child/Gitlink lock PASS
- config digest = `5d272cffcade65138cc9ebcb5014e1aeca0024888feb509b5a8f5a52da9335e7`
- cache manifest SHA256 = `fa7e52256f177f1160aa431374d9e1da028579c78ca3cfb9c5e11084600d4006`
- cache corpus digest = `aae2573c3b4b8123a060f737de49940259362e9b970111d0b60c2d89f8896df6`
- source binding digest = `dc56c44fa9feae8e7e534663ab1acfaa585f28410de7b983ea6cd87deddd35a4`
- Edge config witness = `da6a23cbf4477aafda3e773874bf2c98d6869156e8a450d944e2f28c94eee00b`
- base DCP metadata witness = `2e2a8e10dee283cf5e4d077833543c46f1851daf5e1f872a8f6c6efe7572960b`
- 10 episodes available
- base checkpoint path valid

## Trainable/memory inventory

DCP metadata:
- total tensors: 549
- total parameters: 3,369,657,024
- dtype: BF16
- model-weight storage lower bound: about 6.74 GB

Production generation selector:
- selected generation parameters: 1,423,379,648

Local runtime:
- Local parameters: 95,680

Total trainable:
- 1,423,475,328 parameters

Single-GPU lower-bound training memory:
- BF16 model weights: ~6.74 GB
- BF16 trainable gradients: ~2.85 GB
- Adam first+second moments if FP32: ~11.39 GB
- subtotal: ~20.98 GB

This subtotal excludes:
- activations;
- CUDA allocator/communication buffers;
- optimizer implementation overhead;
- temporary forward/backward tensors;
- possible FP32 master parameters (~5.69 GB if present);
- any additional tokenizer/decoder residency.

Therefore a 24GB single GPU does not provide a defensible safety margin for a real optimizer-step Gate.

The formal trainer is also explicitly world-size aware and intended for sharded multi-GPU execution. A world_size=1 success would not be representative of the formal readiness geometry.

## Next authorized Gate

When an 8×H100 execution environment becomes available, ds may run only:

`CORRECTED-V3-8XH100-FRESH-ITER0-TO-ITER1`

Required conditions:
- exact formal pair `b04fc2d4... / 8c380056...`;
- current production child branch must still resolve to `8c380056...`;
- strict corrected preflight on that H100 host must PASS first;
- world_size=8 / T16 / B8 / GA2 / K4;
- fresh output namespace;
- no resume on the fresh Gate;
- exactly one optimizer iteration;
- finite outer/action/local losses and gradients;
- exact optimizer inventory generation+Local;
- Local candidate publishes exactly once after optimizer success;
- save/validate iter1 DCP if the launcher contract saves at this Gate;
- rank-local Local/Dataloader state evidence if written;
- stop immediately after iter1.

Still unauthorized:
- iter2+;
- same-job resume;
- readiness10;
- formal 30k;
- server GPU/simulator/SR.

Same-job resume requires a separate Gate after fresh iter1 closes.

## Deferred Owner obligation

The historical Phase3.5 >=3 task classes / >=9 exact windows parity is no longer a production-promotion blocker by Owner refreeze, but remains required as supplemental evidence before formal long training unless refrozen again.
