# PSM-WMA V3 H3-B — grouped persistent RoboCasa producer 设计 v0.1

- 日期：2026-09-27；状态：H3-B CPU/static 实现 authority，不授权 trainer、optimizer、checkpoint、GPU 或正式训练。
- 前置：H3-A CPU/static 已关闭；B1 `RoboCasaSegmentProducer` 是单 episode/slot 的事实来源，不改 raw15/chunk32/33-frame/T16/causal endpoint 合同。
- 责任：cx owner/实现；ds 后续执行验证；ChatGPT 为非在线审核者。

## 目录与 episode 身份

使用 Stage-A `RoboCasaLeRobotDataset` 原有 `split="train"`、`split_seed=42`、`split_val_ratio=0.01`、`fps=20`、`chunk_length=32`、`use_base_action=True`、`base_encoding="raw"`、`camera_set="left_wrist"`、`use_state=True`、`action_normalization=None`。catalog 只覆盖 `DEFAULT_ALL_ATOMIC_TASKS` 的 18 个 target/atomic 类；每个 shard 的 `_episode_records` 和 `_resolve_index` 是样本锚点 authority。episode UID 为 `(task, dated_shard, source_episode_index)`，不得仅用 source index；只接 `valid_len=source_frames-32>0` 的 train episode。

每个 UID 必须有同目录结构的离线 H5；`RoboCasaLatentReader` 对 episode ID、`frame_count`、left+wrist 两路 endpoint/valid/latent 精确校验。缺 cache、重复 UID、manifest 长度不符或非有限值一律 fail closed，不静默剔除。原始 LeRobot action 12D 只能按 upstream `_build_frame_wise_action` 转成完整 episode raw15；H5 robot/action 12D 禁止作 evidence。policy payload 仍由 Stage-A 官方 RGB dataset + `ActionTransformPipeline` 产生，cached latent 只进入 Local evidence。

catalog 按 UTF-8 task/shard/episode UID 排序，保存 source/cache 相对路径、frame_count、valid consumer/segment count 和输入 digest；manifest digest 对规范序列化内容求 SHA256。恢复时 manifest/config digest 必须一致。代码接受数据/缓存 root 参数，不硬编码机器路径。

## rank、slot、category 与两个 GA member

正式 world_size=8；episode UID 的 SHA256 整数 mod 8 定义唯一 rank owner，禁止 Python `hash()`。每 rank 固定 8 个 local slots（全局 slot_id=`rank*8+local_slot`），每次 optimizer window 计划 `active_GA=2` 个按时间先后 member；每个 member 每 slot 最多一个 T16 segment。全满时每 rank 的 `n_window=8*16*2=256`，8 rank 总量 2048 valid consumers/update；terminal remainder 按真实有效数缩小 `n_window`，不补假样本、不改变 T16/chunk32。

各 rank 在每个 epoch 内按 task 建队列；task 顺序采用冻结的 18 类顺序，episode 队列由 `seed=0`、epoch、task、rank 派生的独立 RNG 洗牌；绑定空 slot 时 round-robin 选择下一个非空 task，实现确定性类别平衡。每个 episode 每 epoch 只分配一次。slot 绑定后必须完整走完该 episode 的全部 segment 才 rebind；terminal 后下一 member 可绑定新 episode，其 S0 无 Local。若可分配 episode 不足以维持 8 slots，窗口规划 fail closed，不能静默减 B_stream 或循环复制样本；下一 epoch 只在当前 epoch 全部 episode 消费并全部 slot terminal 后开始。

每 slot 的 frontier 保存 `(episode_uid, cursor, next_segment_id)`；同 episode cursor 连续 `+1`，segment_id 在该 slot 单调递增。规划整个 GA2 window 时只生成 candidate frontier；失败或 skip 前 live catalog/slot/frontier 零变化。H3-B 只提供纯计划、producer binding 与 `SegmentBatch`，不扫描 TTT、不做 backward/optimizer/commit；H3-C 负责在同一个成功 optimizer step 后原子发布两个 member 的最终 frontier 与 fast state。

## 同 index native batch ABI

保留 B1 每 episode/slot 的单 row `SegmentBatch` 与独立 `SegmentProvenance`；一个 grouped member 是 8 个按 global slot_id 排序的单 row segment，避免把不同 source digest 错合成一个 provenance。消费 index `j=0..15` 时，只收集每 row `consumer_valid[0,j]` 为真的 payload/prefix；同一 native microbatch 的所有样本必须有同一 `j`，样本顺序按 slot_id，不跨时间拼接。一次 member 的真实有效计数为各 slot valid consumer 数之和，两个 member 的总数交给既有 `GAWindowPlan`，且 loss 归一化只执行一次。

## 最小实现与 CPU/static 验收

child 优先新增 `cosmos_framework/model/generator/mot/robocasa_grouped_segment.py` 与同名 `_test.py`，复用 B1 producer；必要时只在现有 producer 增加无副作用的 metadata/binding helper。不要修改 `OmniMoTModel`、trainer、B0 fast core、B2-B relay、Edge recipe、DCP 或 launcher。

CPU fixtures 必须覆盖：18 类 catalog 和 UID/digest 稳定；8-rank 无交叉且全集无漏；8 slots×T16×GA2=256；不同 slot 同 index batch；terminal remainder 与下一个 member 重绑 S0；连续段 evidence_source_step=t-1；重复/缺 cache/错帧数 fail closed；模拟 forward/optimizer 失败后 catalog/frontier 不变；固定种子重放的 episode/slot/step 顺序一致。Ruff/format、相关 B0/B1/H3-A CPU 回归与双仓 diff-check PASS。H3-C 另行实现 speculative fast-state chain 和真正原子 commit；H3-B PASS 不等于 8×H100 训练就绪。
