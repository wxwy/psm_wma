# PSM-WMA V3 — No-TTT Issue #12 补充 Evidence 增量审核

- **审核日期**：2026-10-30（Asia/Shanghai）。
- **Frozen Formal Root** `e0fe911dfb9fd34957234828195cf051713f6c3d`；**Child/Gitlink** `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`；**完全未变，不重新进行源码 Code Gate**。历史 Code `APPROVE_CODE` 与 Issue#11 DS独立 CPU301 / raw6-of-6 `PASS` 保持。
- **本轮正式 verdict：`REQUEST_CHANGES` — Issue#12 真实GPU / B-Resume 未通过；仅更新补充 Evidence 的已知与未知项**。无确认的新生产代码 blocker，不授权直接更改 loader timeout、重跑GPU、合并或切换正式训练。
- [此前 Issue12 native Evidence 审核（同 Pair）](https://github.com/wxwy/psm_wma/blob/4b9ba54add654a06c788cf750172c57f44f51d46/docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_RealDCP_GPU_ArmA20_PASS_ArmB0_TIMEOUT_Evidence_GATE_REQUEST_CHANGES.md)。
- **新增输入**：Owner消息粘贴 `ISSUE12_SUPPLEMENTARY_EVIDENCE`、B四rank traceback摘录、CLONE/RUN Manifest粘贴，及上传文本 `粘贴的文本 (1)(20261030-071246).txt` 中完整 `arm_a_20step_monitor_v1` JSON（**为20行JSON字段导出，不是原训练 JSONL 的逐字节副本**）。GPT在当前容器直接对上传文件做 JSON parse、数值重算，未读取 DS服务器的原始B全量运行日志/内部 Worker Clock，也没有执行真实GPU。

## 1. Arm A 二十步原件导出复核：`A20_MONITOR_DATA=PASS_VERIFIED`

上传文件 **22,711 UTF-8 bytes**，SHA-256：
`48c2a6b2aa1c7eb1a94a08df11a27999598b926f02023903f1e611d4ce61b2a3`。
解析后：
- `rows=20`，iteration正好 `9601..9620`，无重/缺，全部`status=optimizer_committed`；每条 `native_forward_calls=4`，`native_backward_calls=4`，`missing_grad_tensors_rank_local=0`、`nonfinite_grad_tensors_rank_local=0`；这些字段均为rank0-local证据，不替代rank1–3原生监控。
- 全20步：`step_wall_s` **median20.723s**、mean20.721s；`data_prepare_ms` median**5889.119ms**；`gpu_data_stall_ms` median**5388.736ms**。
- 稳态18步（丢弃9601/9602）：`step_wall_s` median**20.490s**、mean**20.288s**；`data_prepare_ms` median**5884.427ms**，`gpu_data_stall_ms` median**5354.804ms**。
- 每步 `gpu_data_stall_status=ready`、`cuda_sampled=false`、`data_wait_ms=null`、`data_wait_reason=synchronous_producer_no_background_dataloader`，与 No-TTT nw0 路径一致。DS报告的 progress `data=5.35s` 对应 **`gpu_data_stall_ms`**，不是 `data_wait_ms`、也不是 `data_prepare_ms`。其5.35秒不应表述为“整个GPU空闲”。

## 2. ISS12-E3 — 指标字段疑义已关闭；DS关于 CUDA Event 的解释必须纠正

**独立源码确认**（Frozen Child `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`）：
- `examples/psm_wma_robocasa_formal_monitor.py:36-70` 的 `format_progress` 确实用 `_gpu_data_stall_display(record)` 填写 `data=`，仅status=`ready`显示数值。
- `examples/psm_wma_robocasa_corrected_telemetry.py:90-109,148-166`：`cuda_sample_interval=100` 控制 **常规 compute CUDA stages** `_sample_cuda`；另有 `data_stall_sample_interval=1` 控制 **独立的** `_sample_data_stall`，两者不是同一开关。
- 同文件 `:181-211`：在 `data_prepare` / `batch_collate` 范围独立执行 `torch.cuda.Event(enable_timing=True)` 两端录制；`:441-465` 检查 `end.query()`，使用 `start.elapsed_time(end)`，只在有效时返回 `ready`。`:515-570` 中 `gpu_data_stall_ms` 来自上述 CUDA events；`cpu_timing_scope=host_wall_cuda_dispatch_not_gpu_kernel_time` 仅限制 `data_prepare_ms` 等主机阶段。
- 因而 **DS新补证“`cuda_sampled=false` → gpu_data_stall并非CUDA Event，而是主机墙钟派生”是技术性错误**。20/20 `ready` 证明独立 CUDA-stream event 估计可用；`cuda_sampled=false` 仅说明本20步未命中每100步的常规 compute stage 采样。其测量语义仍为 **rank0 current CUDA stream data-stage gap estimate**，不等于全卡GPU idle或完整 CUDA compute decomposition。

**`ISS12-E3 METRIC_FIELD = CLOSED`；对 DS 错误说明形成定稿更正，不再为此追加 Gate或实验。**

## 3. ISSUE12-E1 — Arm B首个 Materialize Timeout 仍为当前运行阻断（HIGH，归因未确定）

- DS补证：4rank均于 Child `no_ttt_async_loader.py:295` 的 `result=next(self.iterator)` 抛 `DataLoader timed out after 120.0 seconds`；4 Rank都尚未生成首个 `optimizer_committed`，`arm_b monitor`为空。**`B_DCP_LOAD=PASS_REPORTED`但`B_RESUME_CONTINUITY=NOT_VALIDATED/FAIL_GATE`；`PERFORMANCE=INCONCLUSIVE`**。
- 冻结实际链路：`no_ttt_async_loader.py:125-136` 每个PyTorch DataLoader Worker首个`__getitem__`会调用 `AsyncWorkerRecipe.build()`；`no_ttt_async_recipe.py:195-254` 里面重建Cache、VerifiedIndex、`RoboCasaExactWindowSourceReader`、Tokenizer/Transform；`robocasa_exact_window_source.py:247-258` 会构造官方LeRobotDataset。父进程Preflight曾测单次 `lerobot_init_ms≈186s`，但Worker内冷启动wall **没有记录**，不能把该父进程数字直接当每个Worker耗时。
- DS的“32个loky PID”文本、42条warnings仅证明某些子进程活动，不是 DataLoader Worker `recipe.build`开始/完成的phase timing或packet-ready证据；没有PPID/实际spawn worker PID映射时也不能直接认定全部32个PID就是PyTorch DataLoader Worker。
- 与正式Job共享GPU4–7、CPU/IO/磁盘在高负载竞争可能加重120s问题，但未测量有效的冷启动分解或独占环境结果。**两种可能原因都未闭合，不能确认为生产源码bug，也不能仅归因为Owner并发豁免**。
- **Frozen验收违反点（已证实行为）：**真实B必须从C=9600提交9601..9620，实际0次commit；首次120s deadline异常导致实验失败。未发现损坏原正式Job的直接证据。
- **最小补证/修复门槛：**仅有原本已记录的Worker start/init/first-packet时间戳才能从本轮数据定位；没有就标 `NOT_MEASURED`，不再要求DS制造不存在的log。任何新的真实数据CPU试验或GPU重跑、或者调整超时/Worker数，须有后续Owner的明确范围授权；若定位是Loader冷启动设计问题，由Codex做最小实现调整、形成**新 Formal Root/Child Pair**并重新审核该增量，不重审旧301项。

## 4. Checkpoint Manifest / 权限旁证

- Owner粘贴的 `CLONE_MANIFEST.json` 是**文本正文**，尚非可独立以SHA验证的原始完整文件，但列出的源/arm_a/arm_b哈希在每个条目中相同且inode互异。注意 `files` map**实际列出14项**（`complete.v1.json`、4rank sidecar、4份DCP metadata、latest、2 configs、launch.lock、v3_job_identity），DS摘要用“13/13”应解释是否**不计`launch.lock`**，属 LOW 统计口径差异，**不据此判定DCP损坏**。本Manifest不覆盖全部24GiB DCP payload分片的逐个sha，A真实加载并完整20次commit属于功能性见证。
- `RUN_MANIFEST` 中 `gpu_sharing=OWNER_WAIVED_EXCLUSIVITY_CONCURRENT_WITH_FORMAL_JOB`，是 **DS提交的后续Owner批准转述/现场自记录**，不是此前 `e5fde3f7` 的原始书面修订；GPT目前未见那条独立Owner原话，故标 `WAIVER_REPORTED_UNVERIFIED`，不武断认定“未授权”或凭空否认DS确实收到Owner指示。这是事后溯源记录问题，不会改变本轮B失败和A共享资源基线不能与未来独占B直接对比的科学结论。
- 2TiB总RAM、available1.6TiB、swap8GiB满、GPU4–7正式训练共享100%利用率、盘接近99%，均为DS只读现场报告；其中“99%满”不等于已测出IO吞吐上限。旧Job未受影响是DS报告，不冒充GPT实时见证。

## 5. Final Gate / 下一步（不扩大实验）

- **`ARM_A_MONITOR_20_ROW=PASS_VERIFIED`；`ISS12-E3=CLOSED`**，CPU301/6raw无需复审；`CLONE_MANIFEST=REPORTED_14_ENTRIES`；`OWNER_WAIVER=REPORTED_UNVERIFIED`。
- **`ISSUE12=REQUEST_CHANGES`**（真实B4rank第一数据Timeout，0 commits；GPU性能与DCP连续恢复仍未证明）。前序 `APPROVE_CODE` 不受影响。
- **当前只允许保存与复核现有Evidence，无授权新GPU实验、正式训练切换、提高120s timeout或替换Worker/数据集构建路径。** 不要对同一内容反复要求整套日志/再做CPU301。若本轮没有Worker init阶段日志，承认该证据缺失；下一阶段再以Owner授权的最小诊断确认是否需要窄修。
