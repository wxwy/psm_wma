# V3 B2-C RTX4090 S1 run06 closure（2026-09-27）

- 技术判定：cx（用户最新指定的构建/判断 owner）；执行验证：ds；ChatGPT 非在线审核，本文不冒充其 verdict。
- 正式执行 pair：root `57413889e3466c767f22956d98edc8b843b463d2` / child/Gitlink `a9aca770fd39b8eed9c456fc2dbdb8867189e78e`。本 closure 提交仅为 root bookkeeping，不改变 pair。
- Evidence：`artifacts/v3/stage_b2c_4090_s1/run06/{result.json,cuda_memory_trace.json,stdout_stderr.log}`（保持未跟踪）与 ds 报告 `/tmp/v3_b2c_run06_review_evidence.txt`。run01–run05 原始 FAIL 产物保留、不重跑。

## 冻结 B2-C §8 验收

| 合同 | run06 Evidence |
|---|---|
| 身份/数据 | pair lock 三值一致；Stage-A DCP host keys 549；CloseFridge ep0/cursor0，429 帧、raw15、16 payload；consumer0 token 152 与前次摘要一致；RGB→Wan VAE 主路径不变。 |
| 训练范围 | Local-only optimizer 20 tensors、165312 elements，LR 5e-5；host 参数冻结。 |
| 梯度与数值 | 16 个 finite native loss，mean 15.22149658203125；visual_proj、slot_queries、w0_fast_in_weight、local_memory2llm.weight、local_memory_modality_embed 的本地梯度 norm 与非零数均记录且有效。单 rank 本地 shard 即全量。 |
| 更新/事务 | `optimizer_steps=1`，trace 中 `optimizer_step=1`、`fast_state_commit=1`；前置断言保证 commit 前 sidecar/frontier 为空、host 样本 bitwise unchanged、Local 桥参数确实变化，最终 sidecar/frontier 恰一份、fast state 为 finite detached fp32。JSON 的 `host_unchanged`/`fast_state_committed` 为通过断言后的布尔报告，不是单独的数值测量。 |
| 资源/终止 | ds 单次执行、进程 exit 0、`result.json.status=PASS`、无 NaN/OOM；峰值 allocated 17005632000 B（约 15.84 GiB）、reserved 17924358144 B（约 16.69 GiB）。GPU0 结束后空闲。 |

原始 Evidence SHA256：`result.json` `3bb3654519e0f6362fe6a29e37a7e57aae06e47293a8e4cae0c804c48ce483c1`；`cuda_memory_trace.json` `51686a9ceaa80423dda8855b7cdeef9e259f2ef0cd58da67f251dca540083d49`；`stdout_stderr.log` `db08aed95da2b147899a0ba635601276c1c8e800b840908cedb698f5aa53cb3c`。

运行退出时有未显式 `destroy_process_group()` 的 NCCL 警告，但进程正常退出且 GPU 资源已释放；可在后续生命周期接线时清理。该警告不改变本次单段更新的 PASS 证据。

## 边界与下一步

B2-C 只关闭 1×RTX4090、T=16、单 slot、单 GA member、Local-only 的真实单步 wiring/resource smoke。它不证明多任务 grouped stream、host+Local 联合梯度、trainer 事务、checkpoint/resume 或正式 8×H100 训练。下一步依照 `PSM-WMA_V3_post_b2c_to_h100_gate_sequence_v0.1_2026-09-27.md` 的 H3-A/B/C/D/E/F；先做 H3-A 联合 autograd CPU/static，不把 4090 detached relay 用于正式联合训练。
