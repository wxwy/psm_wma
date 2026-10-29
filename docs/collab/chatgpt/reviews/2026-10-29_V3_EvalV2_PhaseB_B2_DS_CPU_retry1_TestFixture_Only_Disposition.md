# V3 EvalV2 Phase B B2 — DS 独立 CPU retry1 Evidence 增量复核与测试夹具整改授权

日期：2026-10-29。正式 Root `323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728`；Child/Gitlink `774c2edb93ec5a6ba85ba1124757064d7cc779a5` **未变化**。上一轮 Phase B 第二批生产源码 `APPROVE_CODE` 维持，**不重复审生产代码**。本次是新增 DS Evidence-only Gate：`REQUEST_CHANGES`，未达到独立 `424 PASS`。

## 新增现场执行报告与证据边界

DS_PRO 报告在原隔离干净 Pair 的第二次（已授权）重跑仍 `gate.status=FAIL`。两次均 inference145 PASS + Phase A255 PASS、无源码变化。第二次 phase_b_runtime 执行22项，21 PASS/1 FAIL（`-x`后剩余2项未执行）；首个 `[1-2-2]` 真实 OS 场景通过且出现 B2，后续 `[2-3-1]` 失败于 `runtime_test.py:177` 的 `assert any(c["size"]==2 for c in calls)`；该次记录全为 size1。前次 `[1-2-2]` 端口冲突已另行审查。原始日志/JUnit/ss/proc留在 DS 服务器 `/tmp/ds_pro_v3_evalv2_b2_20261029/evidence/` 和 `evidence_retry1/`；GPT本轮仅验证真正冻结的代码和DS报告一致性，**没有独立读取DS服务器原件**。

## R2-E1 — 端口预探测错位：test-only

Formal Root `tools/v3/eval_v2_batch_tests/runtime_test.py:29-45` 预探测 `127.0.0.1`，生产 `scripts/eval_robocasa_18task_queue.py:74-89` 的 `require_free_ports` 用 `0.0.0.0`；不同loopback listener下测试会选出生产正确拒绝的端口。建议只把**测试** `free_ports` 探测范围对齐为 `0.0.0.0`，保留有序连续端口保护及同地址监听。无需修改生产端口保护。新增一个不同loopback绑定已占用时测试不能错误选择该端口的确定性负例；避免依赖固定生产端口或触碰生产进程。

## R2-E2 — 跨GPU有限请求不能强制每次Batch2：test-only

Formal Root `runtime_test.py:149-190` 的 `test_real_OS_multisim_native_B2_delivery_D5_task_reuse_and_resume` 参数为 `[(1,2,2),(2,3,1),(1,3,1)]`；对于每个参数，都要求 `any(size==2)`。Child `robocasa_batch_transactions.py:_pump` 按每个 Server 自己的队列和 `batch_wait_ms` 收集，过等待窗会合法flush B1；G2/N3不同GPU/Server的请求不能跨Server合并。因此在共享CPU时序下即使生产完全正常，也不保证该场景一定出现 B2。**B2 是功能上限能力，不是全部实际微批的固定大小。**

授权 Codex 在已有参数化测试里把 `any(size==2)` **只保留给 G1/N2/E2 的正面 OS 用例**；对于其余 G2/N3、G1/N3 必须保留逐GPU Server 数/PID、sum(batch sizes)=总replans、per-member prediction/assignment/frontier/prefix、D5 barrier、交错执行、全部 Core、完成后Resume byte parity/no new work及 owned cleanup 原有断言，不放宽。不得把分开的Server误解释为一个Batch；不得改真实生成路径或伪造batch2 telemetry。已有Child `robocasa_batch_transactions_test.py` 的纯CPU Actor B1/B2/B3/partial/cold-hot-hot exact-call测试、G1/N2真实 OS B2 断言必须原样保留。

不得无条件删除Batch2断言、仅检查 `calls` 非空后放行、扩大 `batch_wait_ms` 以掩盖偶发或通过sleep/人工mock伪造B2。测试失败后其他真实错误应正常暴露，不得自动标记环境问题。

## Gate/下一步

- **生产源码 Gate：`APPROVE_CODE` 不变**；当前 DS 独立 CPU Evidence Gate `REQUEST_CHANGES`（test-only），未关闭。
- **Codex** 仅可在独立候选修复 Root `tools/v3/eval_v2_batch_tests/runtime_test.py` 及其必要的同目录 test，禁止生产代码、Child、架构/训练/Checkpoint/Vendor/G1/旧431修改；留下两次失败原始 Evidence，交付**新 Formal Root SHA + 原 Child SHA**、精确 Diff、focused old/new负例及作者完整CPU证据。
- 新 Root 虽为 test-only 亦须做**极窄 fresh incremental Code/Evidence review**，但**不重复审查未变生产代码**。
- 之后 DS 在**新的干净新Pair**上独立重跑一次统一 Gate：预期424或因增加新test产生更高真实测试数，0fail/error/skip、shell0、gate PASS、源不变、OS B2 G1正证、其他多GPU/Resume/owned evidence。无GPU/Cosmos/DCP/RoboCasa/900，不合并V3。
- 真实1GPU/M2/B2 Canary与正式900继续待Owner单独授权。不要等待共享训练停止或进行额外架构批次。

精确实源码：
- https://github.com/wxwy/psm_wma/blob/323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728/tools/v3/eval_v2_batch_tests/runtime_test.py#L149
- https://github.com/wxwy/cosmos-framework/blob/774c2edb93ec5a6ba85ba1124757064d7cc779a5/cosmos_framework/inference/robocasa_batch_transactions.py#L140
