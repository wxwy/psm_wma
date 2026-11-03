# Codex 窄范围修复任务 — R01 Media Summary Phase B 字符串误报

- 来源：2026-11-03 DS_PRO R01 GPU Canary；独立 GPT 源码核实。
- 历史 Formal Pair：Root `e7ce99d7a0bbb7a81ea7afcee7253548687dc223` / Child-Gitlink `c93f2abf4fb27d36176ff8db094379a853cec796`；其现有 `APPROVE_CODE` 和独立 CPU122 是历史 scoped verdict，R01 GPU Canary **FAILED**。当前候选 `v3-eval-v2-replan-ack-r01-20261102`。
- 真实 GPU Canary DS 数据：CloseFridge×1，GPU6 Server/GPU4 EGL，19 replans = 19 MP4 = 19 VIDEO_SAVED receipt =19 ACK，Episode completion COMPLETE，Core SR1/1有效、进程 clean，然而 `media_summary.status=MEDIA_INCOMPLETE`、CLI exit1。
- **真实根因**：
  - Root `scripts/robocasa_eval_v2/config.py:244–254` native `manifest.execution.profile="phase_b_native_batch_v1"`。
  - Root `scripts/robocasa_eval_v2/generated_media.py:34–37` 却要求该 Manifest 字段等于 `"phase_b"`，误判 `server_ack_required=true`；于是汇总在 MP4 inventory/receipt check 前失败，`saved=acknowledged=0` 只是累计未运行，不是硬件保存丢失。
  - Child `cosmos_framework/evaluation/robocasa_v2/contract.py:107–115` 规定 native manifest 的正式 literal 必须是 `phase_b_native_batch_v1`，不得修改该合同去迎合错误代码。
- **仅授权**：在**隔离候选新 Formal Root SHA** 中用最小变更改正 `generated_media.publish()` 的 Profile 判断；若使用同源常量更稳固可采用，但请勿拓展到大规模重构。**不改 Child、Action、TTT、SR、Scheduler、Media Encoder、保存策略、GPU 环境或机器人任务；Child Gitlink 应继续是 `c93f2abf4fb27d36176ff8db094379a853cec796`**。
- **必须提供的定向测试**：
  1. 使用真实 native `execution.profile=phase_b_native_batch_v1` 的合法 Store+Episode+Generated receipt，设置 `server_ack_required=true`，`publish` 应 COMPLETE。对旧实现必须 RED。
  2. 同一 Phase B 下 `server_ack_required=false` 必须 MEDIA_INCOMPLETE；Phase A/manifest 不含 execution 时 `server_ack_required=false` 正常 COMPLETE，不能修复时误放宽。
  3. 断言 `publish` 在正确 Phase B 分支确实进入 inventory、receipt/Video file hash 逐个核对；删一个 MP4 或变更 Receipt 仍 MEDIA_INCOMPLETE。保持 Core `summary.json` 的 SR/valid authority 不变。
  4. Ruff check/format、py_compile、仅相关 media/report CPU regression；不重复跑历史379/122全套，不运行真实 GPU。
- **数据复核**：若 DS 能读取原 R01 产物，请在不修改历史 `out/R01` 的前提下，对其独立**副本**离线运行新 `publish` 汇总，并严格核实每个已落盘 MP4/receipt/sha/index。记载 `offline_reconciliation` 状态与原 `R01_FRESH_EXIT=1` 并存，不能擦除历史失败。若只是代码开发环境无此服务器数据，将 offline 验收明确留给 DS_PRO 不得伪报完成。是否新 GPU Fresh Run 须 Owner 另行明确授权。
- **停点**：提交新 Formal Root/Child-Gitlink、原始旧版 RED、新版 GREEN 与小范围源码 diff/作者证据后停止，交 GPT fresh incremental Code Gate；DS 独立 CPU/硬件逐 Gate 分别授权。不合并 V3、不启动训练/900EP、不触 GPU0–3 或其他GPU训练、不改 out2/No-TTT/旧 Canary/H2/H3、Checkpoint/日志。
- 详细 Evidence review：`docs/collab/chatgpt/reviews/2026-11-03_V3_EvalV2_R01_GPU_Canary_Media_Profile_Evidence_REQUEST_CHANGES.md`。
