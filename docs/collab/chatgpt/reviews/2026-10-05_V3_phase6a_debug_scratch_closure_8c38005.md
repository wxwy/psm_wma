# V3 Corrected Phase6A online Local-TTT CPU/static debug scratch closure — GPT review

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE6A-DEBUG-SCRATCH`
- Phase6 design authority root：`5c2435eaffc8565e54fe7fc780c75a00ff9675d9`
- production child/Gitlink（unchanged）：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- Phase6 scratch parent：`afb9ca8d9f8ec080518a838f56a681073eb4b495`
- initial Phase6A implementation：`18a52c46aef16d42a1eaa438c502cad021076ef8`
- final Phase6A scratch SHA：`8c3800565f66cfbce2929264f1c2a7854137482e`
- frozen design：`docs/build/PSM-WMA_V3_phase6_online_inference_eval_design_v1.1_2026-10-05.md`

## Verdict

`APPROVE_TO_CLOSE_PHASE6A_DEBUG_SCRATCH`

`APPROVE_TO_RUN_PHASE6_ENCODE1_OBSERVATIONAL_PARITY_ONLY`

`PHASE6_SERVER_GPU_SIM_NOT_AUTHORIZED`

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

本 verdict 关闭 Phase6A CPU/static/debug implementation，并只授权下一步 bounded Encode1 observational parity。不得据此提升 scratch 到 production child/Gitlink，不授权 server GPU smoke、simulator、18-task SR 或正式训练。

## Independent review findings

1. Corrected wire 已与 B1 分离：active version/format 为 corrected composite + canonical raw15；evidence row 只含 source_step/composite_image/executed_action；historical separate-camera/causal-endpoint/mean-RMS/B1 wire 均 fail-closed；active modules 无 historical B1 import。
2. shared spatial preprocessing 保持 Policy off-mode 输入语义：server policy 与 Local 共用 `prepare_robocasa_composite_frame`；旧 server reference 与新 helper 在 image_size=128/192/256/320 的 resize/repeat/reflection-pad 和 image_size metadata 上逐字节一致。
3. Encode1 helper 满足 code-level contract：严格 T_pixel=1、normal full encode、禁止 streaming/retained encoder cache、输出 finite fp32 z_t，visual96 精确复用 Phase4 公式；real Wan 数值 parity 尚未在本 Gate 执行。
4. required route 强制 model-owned `scan_local_memory`；missing scan fail-closed；DTensor 参数要求既有 FSDP registration；generic OnlineLocalMemory direct-core fallback 不进入 Corrected required route。
5. H_pred/R/T 独立：R=1/4/8/16 仅受 H_pred=16 约束；N>T 顺序分块并 carry detached fast state；N20/T8 与 per-step scalar reference 的 final token/state/telemetry 一致。
6. replay/reset/session identity 正确：session 绑定 episode/image_size/preprocess_profile；exact replay encoded_steps=0 且不重复 Encode1/Local update；changed composite/action same frontier fail-closed；reset 清除 state/replay。
7. status telemetry 完整：cold、normal、replay 均提供 adapted_steps/inner_loss_mean/fast_state_norm/fast_update_norm；replay 不伪装成再次适配。
8. executed action authority 为 post-decoder canonical raw15；canonical command 覆盖 mode/base clip-or-zero/rot6d/gripper，并可重新 decode 为相同 submitted env12。
9. simulator chronology 正确：保留 pre-action composite；decoder 后调用 env.step；仅 env.step 成功返回后 record_completed；decoder/env.step failure 零 evidence；done/success successful step 仍记录；unexecuted tail 不记录。
10. server transaction 为 prepare -> prefix -> generation/output validation -> commit，generation failure -> abort；required `/predict_batch` fail-closed；off-mode不调用 Encode1。

## Evidence

- final corrected Phase6 focused（含 R contract）：**49 passed**
- Phase6+Phase4/5 joint regression：**175 passed, 3 skipped**；3 skips 均为 Phase4/5 optional real-asset smoke，不属于 Phase6A
- cx protected Phase4/5 regression after corrective：**161 passed, 2 skipped**
- Ruff check / Ruff format --check / py_compile / git diff --check：PASS
- forbidden-file diff：空

Phase6 full scratch diff仅触及 design §21.1 允许的 inference/server/simulator/client/test/ledger 范围；Phase1A/1B/2/3 datasets、checkpoint/dcp.py、Phase5 trainer/resume/optimizer、parallelize_vfm_network.py、attention、memory_prefix.py 均保持 diff-empty。

## Next Gate authorization

只授权：`PHASE6-ENCODE1-OBSERVATIONAL-PARITY`。

使用 strict snapshot10 + matching flat source + Wan VAE，对 bounded real RGB witness 比较：A=cache exact-window actual Z_t[0]；B=corrected independent Encode1(current composite)；C=repeated-current Policy visual tokenizer encode 的 first latent。至少报告 A/B、B/C、A/C 的 padded z、post-crop（若适用）、visual96 的 exact_equal/max_abs/mean_abs/RMSE/finite/geometry。

本轮先 observational、不设 threshold、不自判 production PASS。不得启动完整 policy/DCP、server GPU、simulator 或 SR。Phase6 parity 不替代 Phase3.5 production thresholded Gate。

## Remaining blockers

1. Phase6 Encode1 real observational parity 尚未执行；
2. Phase3.5 >=3 task classes / >=9 windows thresholded production parity 仍 OPEN；
3. scratch 尚未 production promotion；
4. server GPU smoke / simulator / 18-task SR / formal training 均未授权。
