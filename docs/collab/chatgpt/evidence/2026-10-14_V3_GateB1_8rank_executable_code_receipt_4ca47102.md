# B1 end-to-end 8-rank comparator executable — implementation receipt

Date: 2026-10-14
Author: GPT
**Status:** CODE_SUBMITTED / LOCAL_SYNTHETIC_CPU_70_PASS / INDEPENDENT_DS_CPU_GATE_PENDING / GPU_NOT_AUTHORIZED
**Exact implementation CODE SHA:** 4ca4710271936b286643d36ebeb41d0baeff7057 on isolated root branch wxwy/psm_wma:v3-gateb1-numeric-implementation-20261014.
The diagnostic branch tip may advance with documentation commits; CODE SHA remains formal implementation target. Neither original frozen Index8 nor Packed128 production Root/Child is modified.
SOURCE Index8 root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
TARGET Packed128 root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.
Live V3 Child/Gitlink remains 1d56320c08c56b0f8dd248919d152d81ae12ea7b (trusted-startup CPU Gate closed).

## New code completed

- New real-setup launcher tools/gates/v3_gateb1_run.py for separate original-source and Packed128 8-rank jobs; --mode prepare is CPU metadata-only; --mode execute refuses without Owner-approved exact-pair code/threshold JSON. Output namespace restricted to /tmp and evidence-only, not original Formal30k/checkpoint.
- Diagnostic original-cosmos reader adapter v3_gateb1_no_rescan.py; neither old frozen Child is edited, and existing offline-accepted dataset receipt, in-memory manifest and runtime requested-sample failures remain. No 451GB file rescans.
- Scoped same-job original DCP source adapter v3_gateb1_same_job.py; no original latest pointer publication and checkpoint saves actively refused through both native GA2 steps. No model/DCP load actually attempted on GPU yet.
- Native original GA2 invocation and pre/post optimizer + Local State capture via v3_gateb1_native_driver.py, plus b0 Native model stochastic site/CFG producer hooks in v3_gateb1_model_sites.py/v3_gateb1_producer_cfg.py. Real model callsite positions explicitly mapped; Source index-major Native forward observation actually carries index=None, now permitted only when the actual model-call index is separately validated.
- CPU postprocessor v3_gateb1_compare.py compares both original implementations 8 ranks x 2 steps x P0/P1 x two independently restarted runs, across true Full/Terminal Partial, with canonical ConsumerKey, Sigma/Epsilon/Condition Mask/Text CFG payload, per-FQN gradient/FP32 DeltaParameter/Adam moments/Fast State. Reports candidate-only before Owner freezes numeric thresholds.
- Fourteen newly added/updated Python implementation and CPU test files since previous B1 implementation milestone. Exact GitHub code diff bound to implementation SHA, not later bookkeeping.
- Critical bug fixes: explicit native same-job DCP identity versus warm-start; Source index=None observer ABI; GPU method save-denial spans two real GA2 steps; --vision-resolution must be explicit; evidence writer refuses missing actual Sigma/CFG witnesses.

## Verification

Author-controlled local synthetic CPU test suite (seven B1 tests in /mnt/data/b1_native_candidate): **70 passed**, Python 3.13.5 / torch 2.10.0+cpu / pytest 9.0.2, and fourteen-module py_compile PASS. The two final code blobs are verified: v3_gateb1_run.py blob 16b2518d3e764a921878f569a2761685cc35b279 and test_v3_gateb1_run.py blob e00c7563df01b35f221ec0afc06e07da4fcd6705. A prior GitHub commit included an earlier version; follow-up code SHA 4ca471... contains the final tested versions. Ruff not available locally; the independent DS CPU evidence has NOT yet been supplied.

Detailed DS request pinned exactly to this CODE SHA is on diagnostic branch:
docs/collab/chatgpt/requests/2026-10-14_DS_PRO_V3_GateB1_8rank_Executable_Entry_CPU_full_one_batch.md

## IMPORTANT limits, not yet a Gate PASS

- This is an **executable entry with native real-object seams**, not proven successful 8-rank Cosmos model DCP restore or full GPU equivalence. The entire execution branch is Owner GPU HOLD.
- GPU model/noise stochastic callsites outside explicit noiser and text CFG must receive static and/or running verification, with fail-closed disposition on missing sites; no claims of zero gaps from CPU mocks.
- The 8-rank startup and two native iterations have NOT executed; no independent GPU memory/time figures, no real Optimizer coverage, and no full P0/P1 Final×Terminal result.
- B1 numeric criteria still PROPOSED and require Owner signoff BEFORE GPU. Do not fabricate baseline matched-FQN threshold pass.
- B0 Gate and dataset offline validation remain CLOSED; no repeat. Gate M and Formal30k iter1301 remain HOLD. Owner deferred global V3 code audit.

**Verdict status:** Acknowledged coding progress. CPU and B1 GPU acceptance still OPEN; no authority to start GPU.
