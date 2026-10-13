# DS_PRO — V3 对齐 V2 A2 Packed Native 的最小必要现场信息（只读、一次提交）

**日期：** 2026-10-13
**Owner决定：** 如果V2 A2验证正确，则对齐V2高效Packed Native执行。GPT已查阅V2 canonical代码、native-validation、full delivery和真实LIBERO/RoboCasa训练文档；**不需要你再读V2源码或提交重复证明**。
**对齐设计：** `docs/collab/chatgpt/reviews/2026-10-13_V3_V2_A2_packed_native_alignment_feasibility_and_design_5ac9a904.md`；最新V3实现Root `e730e3063ee3638f0bafd79473f52a76f851c935` /Child `5ac9a904c46da658e1b3e0816d3a7d95ce99c945`仅作为当前Github设计源，不能等同实际训练机RUN时Source Pair。

## 只读采集四组，合为一份Markdown（可附JSON片段）

**A. 当前运行身份（一张快照）**：`robo15train`或真实训练命名空间当前是否有唯一活跃writer、真实运行Root/Child/Gitlink SHA和`PYTHONPATH`、实际`PSM_V3_COMPACT_CACHED_VIDEO`/`PSM_V3_SHARED_EPISODE_CACHE`生效值、`--num-workers`、T/B/GA/world-size、last完整Checkpoint指针。若进程环境不可读，明确`UNKNOWN`，不要凭启动意图推测。

**B. V3 rank0 JSONL仅连续最近20个健康step**：输出逐步/统计`iteration`,`num_workers`,`native_forward_calls`,`native_backward_calls`,`valid_consumers`,`data_prepare_ms`,`batch_collate_ms`,`batch_transfer_ms`,`local_scan_ms`,`forward_ms`,`backward_ms`,`optimizer_ms`,`step_wall_s`,`peak_allocated_gib`,`peak_reserved_gib`,`missing_grad_tensors_rank_local`,`nonfinite_grad_tensors_rank_local`,`cuda_sampled`,存在的`*_cuda_event_ms`。不要把 `data_wait_ms` 当GPU闲置。特别核实正常有效窗口实际`native_forward_calls/backward_calls`是否32，而不是只依赖源码推断。保留record第一条/末条完整JSON可复核原始字段。

**C. 当前内存余量（一张快照）**：`nvidia-smi --query-gpu=index,memory.free,memory.used,utilization.gpu --format=csv`，进程自身PyTorchrank峰值allocated/reserved，给出GA2/B8当前native Batch8→拟单Member Packed128对OOM风险的观察。计算util只标记，不做Owner已撤销的硬阻塞条件；无权杀其它进程。

**D. V2已有的历史显存证据（可选）**：如服务器已有 `RoboCasa V2 GA2 8rank Packed`真实peak allocated/reserved的具体report一条，附日志路径及step；如果没有，报告`NOT_AVAILABLE`，不要追加GPU实验，也不要自行全盘长搜索。V2早期GA16单卡45GiB不同构型不可用于推定当前GA2。

## 交付与禁止项

一份`DS_PRO_V3_V2_A2_PACKED_ALIGNMENT_READONLY_2026-10-13.md`，正文含A/B/C，D可缺省。没有自动pytest/GPU/torchrun，**不要中断正在训练的Formal30k**。不要改任何生产代码、配置、DCP、logger、原训练工作树；不得切换Gitlink或启动新packed实验。证据只读采集结束即停止，交GPT一次审阅即可。

以上只是帮助GPT核验当前V3真实性能/资源，不要求用户重复回答之前已有的V2数据。