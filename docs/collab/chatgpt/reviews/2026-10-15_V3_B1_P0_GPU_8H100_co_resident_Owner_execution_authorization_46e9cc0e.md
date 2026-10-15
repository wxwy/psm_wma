# V3 B1 P0 GPU Smoke — Owner 8×H100 共驻执行授权

**日期：** 2026-10-15  
**Owner 原话：** “直接让ds做B1 P0 GPU Smoke，显存够的，就是计算挤兑”。此前 Owner 已批准 P0 Smoke 的代码版本与 r2 数值阈值。  
**裁决：** `OWNER_APPROVES_B1_P0_GPU_SMOKE_CORESIDENT`，**可在仍有其他用户任务时共享 8×H100 运行，100% util 不是单独 STOP 条件**。这是**执行授权**，**不是** B1 parity PASS、完整 B1 测试授权、Gate M 或 Formal30k 授权。  
**可机读 Owner 回执：** `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_46e9cc0e.json`。该 JSON 是在 Owner 本轮明确授权后由 GPT 写入 GitHub V3；DS_PRO 应从 V3 读回，并复制到训练机 `/tmp` 的只读回执文件后用于 `--owner-authorization-json`，**不得自行修改回执字段**。  
**批准作用域**（严格小于完整 B1）：`P0_FIXED`，`repeat=0`，严格依次 SOURCE `index8`、TARGET `packed128` 各**1**次独立 `8×H100` 作业，每作业完整执行 `iter1301`、`iter1302` 两次 GA2 train step；只允许只读原始 iter1300 DCP，所有写入隔离 `/tmp`。

## 冻结对象与权限

| 对象 | Root | Child/Gitlink |
|---|---|---|
| Diagnostic runner | `46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a` | `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1` |
| SOURCE Index8 | `b159f45906f7261d028aecc226ab7f2bb9807eb9` | `937066ffd90f2bf783ad4fbb4909e9c0b8922982` |
| TARGET Packed128 | `c4731bca1a590663db88bd6cd74dbcf9fd513a85` | `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686` |

B0 full shard fingerprint `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`、Owner numeric r2 SHA `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda` 必须严格校验。当前已验收的代码 CPU Gate 144 pytest PASS、Ruff PASS、GPU Readiness Prepare PASS，不因共驻重做 B0/451GB/全仓审计。

## GPU 共驻启动门槛与停止条件

先记录新的 `nvidia-smi` per-GPU memory.free / total / util /进程情况及 CUDA 错误状态。**即使其他用户利用率100%，只要每张卡当前剩余显存≥16384 MiB、8张健康、训练不需要杀/停/重置/降优先级其他用户进程，就可以按本授权启动。** 这个16GiB阈值是最低启动护栏，并非已经证明 Packed128 真实峰值小于16GiB；DS 还应结合此前实际训练峰值和现场剩余显存判断是否留有保守余量。

出现任一卡显存不足、CUDA OOM/reset、NCCL 失败、系统不稳定、数据损坏、非有限 Loss/Gradient/FastState、DCP/latest 变化等，立即停止**自己的 B1 作业**并反馈，不要自动重跑或降配置强行通过。不因其他用户100% util alone 拒绝。共驻下的 wall/throughput 仅供上下文，不作为单独吞吐性能判据。

**SOURCE 先执行**。SOURCE 两步 8-rank证据齐全且无错误后，必须有独立人工检查/手动放行才启动 TARGET。若 SOURCE BLOCKED，则 TARGET NOT AUTHORIZED。TARGET 完成后仅比较 P0 repeat0，**不能自动继续 P1、repeat1**。

全部 Tensor/JSON 只写 `/tmp` 专用命名空间，原始 `iter_000001300`、latest、正式训练目录不可写。Checkpoint GPU 恢复使用已经验收的 B0 权威 FP + 小文件/mtime witness，不再次全量哈希 32 shards。不得更改任一冻结代码/文件，不得调整 r2 阈值。

## 授权范围的代码实现限制与额外执行纪律

现有 runner `v3_gateb1_run._owner_receipt()` 验证 JSON 中的 `gate/authorized/numeric_thresholds_frozen/numeric_policy_sha256/implementation_sha/checkpoint_fingerprint/source_root/source_child/target_root/target_child/approval_reference`，但**不会逐项验证 JSON 中额外的 `approved_scope` 字段**。因此 DS_PRO 必须在自己的独立临时启动脚本中核验 `approved_scope.profiles==["P0_FIXED"]`、`repeats==[0]`、`legs_in_order==["index8","packed128"]`、两步窗口和 GPU 护栏，且所有 CLI `--profile P0_FIXED --repeat 0` 严格不变。该权限边界不能因脚本入口接收更宽参数而扩大。DS 的 `/tmp` 脚本可验证回执，不得写入 GitHub 生产代码或修改授权 JSON。

原始更详细启动命令、STOP 条件和 P0 数值比较方式：
`docs/collab/chatgpt/requests/2026-10-15_DS_PRO_V3_B1_GPU_P0_2step_smoke_owner_gated_then_full_gate.md` (位于 **V3** 分支；冻结的诊断 Git checkout 上没有此文档)。

**报告结果：** `DS_PRO_V3_B1_P0_GPU_Smoke_46e9cc0e_2026-10-15.md`。必须包含 2次作业的 8-rank JSON/PT、精确 DCP/Local 恢复、P0 两步每 FQN 数值对比及所有 runtime witness；结论只能 `PASS_FOR_P0_SMOKE_ONLY` 或 `BLOCKED`，仍不得声称完整 B1 GPU PASS。GPT 对真实 GPU 证据独立审核后再决定是否建议后续 P1/重复运行。

**权限状态：** `OWNER_GPU_AUTHORIZED_FOR_P0_REPEAT0_TWO_LEGS_ONLY`; `P1/REPEAT1/GATE_M/FORMAL30K_HOLD`。
