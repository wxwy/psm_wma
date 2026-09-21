# PSM-WMA R09-B TTT v0.3.2 — Memory Prefix Phase A/B Runtime Verification Results

- Date: 2026-09-21
- Executor: Codex / ds_pro
- Status: RUNTIME-VERIFIED PASS / UNIT-CLOSURE-PASS
- Root profile lock: `5b42eba1ef9cacef8dfbd0bcc9a8fe8c808d0277`
- Child production profile lock: `60be568e809786f94ae81ed8de668131b1083f6a`
- Child test-closure commit: `879c8e07f353836e8613d50a0cb9530805d7e97d`

## 1. Locked runtime setup

- checkpoint: iter_000003000, LIBERO 4in1 Local-Memory active
- suite/task: libero_10 task 0
- sampler: UniPC, num_steps=30, shift=5.0
- guidance=1.0
- B=1, single env, single episode
- `--profile_inference`
- action_horizon=8
- max_steps=520
- mode: required / TTT
- GPU 0 shared with training workload

## 2. Phase A/B performance results

| Metric (steady p50) | baseline `e1f3fc7` | Phase A `8f6d439` | Phase B `60be568` | off baseline |
| --- | ---: | ---: | ---: | ---: |
| model.diffusion_sampling | 15241 ms | 2791 ms | **1996 ms** | 1445 ms |
| model.generate_total | 15280 ms | 2845 ms | **2050 ms** | 2202 ms |
| server.total | 16483 ms | 3789 ms | **3032 ms** | 2235 ms |
| model.prepare_inference | 24 ms | 24 ms | 25 ms | 526 ms |
| model.pack_template | 18 ms | 19 ms | 19 ms | 18 ms |
| history_overhead_total | 1110 ms | 888 ms | 921 ms | — |
| episode wall-clock | 821 s / 394 steps | 183 s / 320 steps | **161.8 s / 316 steps** | 164.6 s / 520 steps |
| SR | 1/1 | 1/1 | **1/1** | 0/1 |

Episode wall-clock values are descriptive only because episode step counts differ. The primary attribution metrics are the steady-state server/model timing values.

## 3. Attribution conclusion

Phase A:
- diffusion 15241 -> 2791 ms
- **-82%, about 5.5x faster**
- host-sync confirmed as the dominant original slowdown source

Phase B:
- diffusion 2791 -> 1996 ms
- **-28% relative to Phase A**
- required/off residual ratio: about **1.9x -> 1.38x**

Conclusion:

> Phase B materially recovered the Text-KV reuse performance that was previously disabled by Memory Prefix while preserving the successful Local Memory behavior in the profile episode.

Batched `num_envs=4` throughput remains out of scope because the current text-KV reuse contract is B=1 only.

## 4. Unit-test results and open regression

On production child `60be568`:

- new `inference_text_kv_memory_test.py`: included in passing batch
- `memory_prefix_test.py`: one regression
- `unified_mot_test.py`: pass
- `attention_test.py`: one FlexAttention flaky failure under GPU contention; standalone pass; unrelated because Memory Prefix rejects FlexAttention
- combined relevant batch: 62 passed, 1 failed, 1 skipped

Regression:

`test_memory_prefix_owner_guards_fail_before_packed_attention_work[False-memory0-sequence_sharded-None-native MemoryState]`

Root cause: the test passed bare `object()`; Phase B production code uses the new `MemoryState.supports_memory_prefix()` capability contract.

## 5. Test-only closure

Child commit `879c8e07f353836e8613d50a0cb9530805d7e97d` replaces the invalid bare-object fixture with a concrete `MemoryState` subclass that inherits the default fail-closed `supports_memory_prefix() == False`.

No production file changed in this closure commit.

Closure retest completed on child `879c8e07f353836e8613d50a0cb9530805d7e97d`:

- `memory_prefix_test.py`: **27 passed** (exit 0)
- combined `memory_prefix_test.py + inference_text_kv_memory_test.py + unified_mot_test.py`: **63 passed, 1 skipped** (exit 0)
- the skip is the by-design multi-GPU FSDP end-to-end training case and is unrelated to Memory Prefix

No profile rerun was required because the closure commit changes only the test fixture; profiled production code remains byte-identical to `60be568`.

**Final Phase B status: IMPLEMENTED / STATIC-REVIEWED / RUNTIME-VERIFIED PASS / UNIT-CLOSURE-PASS.**

## 6. Artifacts reported by runtime executor

- `results/libero_profile/ttt/iter_000003000/libero_10/profile/task_000/episode_000.json`
- `results/libero_profile/ttt/iter_000003000/libero_10/summary.json`
- `/tmp/psm_profile_srv_ttt.log`
- `/tmp/psm_profile_ttt_phaseB_run.log`
- launcher: `/tmp/psm_profile_run.sh`
