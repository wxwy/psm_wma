# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.12

**状态**：v0.11 superseded（仅 terminal provenance 部分；v0.10 已批准范围不受影响并保持有效）；待三方同 SHA 设计审核。仅冻结 tail truncation 政策整改，不授权实现、GPU 或训练。
**基线**：v0.11（root `59609f1`）获 MM、Kimi 双方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`（v0.11 扩增部分）与 ChatGPT（review=`e31fb2a`）`REQUEST_CHANGES`。唯一阻塞 HIGH-1：builder 固定条数构造可合法地在最后一个 shuffled episode block 中途截断，该尾组无真实 terminal 行，与「每组恰好一条 `is_episode_end=true`」的 verifier 冻结不变量矛盾，且 end-of-manifest 时 lifecycle 语义未定义。v0.11 其余部分（manifest-route 方向、wrapper additive attach+缺键 fail-closed、model 侧缺键 fail-closed、白名单扩增集合）获 ChatGPT 明确接受，本 v0.12 原样保留，仅补齐 tail 政策。

## 1. Tail truncation 政策（ChatGPT HIGH-1 整改，采用其选项 B）

冻结以下五条，覆盖 builder / verifier / lifecycle 三侧：

1. **builder 构造不变**：固定条数（`optimizer_updates * grad_accum * max_samples_per_batch`）与 suite round-robin 算术不变；`is_episode_end=true` 仍只标记**真实** episode 终止（`start_frame` == 该 episode 最后 valid window 的 `start_frame`），显式禁止任何近似。截断尾组自然零 terminal，不伪造。
2. **尾组认证（certified tail group）**：一个 `(suite, epoch, episode_index)` 组允许零 `is_episode_end=true` 当且仅当同时满足——(a) 该组的 ordinal 构成该 suite 全部 record 的**最大后缀**（组内 ordinal 连续且含该 suite 最大 ordinal）；(b) 组内 record 数 < 该 episode 的 valid window 计数（verifier 经 dataset 独立重算）；(c) 组内无 `is_episode_end=true`。每 `(suite, epoch)` 至多一个尾组。其余每个组仍必须**恰好一条** `is_episode_end=true` 且位于该组最大 `start_frame`（完整组的最大 start_frame 即真实 terminal）。
3. **verifier 整改**：`required` 集合增 `is_episode_end`（v0.11 不变）；断言改为「每组：恰好一条真实 terminal，或经 §1.2 三项条件认证的尾组零 terminal」；非尾组缺 terminal、尾组内含 terminal、尾组 ordinal 非后缀、尾组计数不小于真实 valid window 数，均 fail-closed。旧 manifest 因缺键 FAIL，强制重新生成（v0.11 不变）。
4. **lifecycle end-of-stream 语义**：manifest 单次消费（single-pass）；尾组 owner 的 open segment 永不 commit、永不 reset，随进程结束丢弃——无 pending Local 事务泄漏：fast state 是进程本地状态，checkpoint 严格 slow-only（config/optimizer/checkpoint design v0.2 已冻结），任何未 commit candidate 不可能进入 artifact。**禁止**在存在 open segment 时于同进程内重新迭代 manifest（owner 从 timestep 0 重新 admission 将触发 C5A stale-state fail-closed，此为合同保护而非合法路径）；⑪ Runbook 必须把 manifest 规模定为覆盖计划 optimizer updates 的单次通过。
5. **lifecycle 代码零新增**：tail 政策不需要新 lifecycle 钩子——open segment 保持 open 即为确定态；backward 异常 abort 路径不变。

## 2. 验收增补（CPU/static，替换 v0.11 §4 对应条目）

- builder fixture：构造在 episode block 中途结束的 manifest——尾组零 terminal 且无伪造 terminal；其余组恰好一条真实 terminal。
- verifier fixture：认证尾组接受；非尾组缺 terminal 拒绝；尾组内含 terminal 拒绝；尾组 ordinal 非连续后缀拒绝；尾组计数 ≥ 真实 valid window 数拒绝；terminal 位篡改/缺失仍 fail-closed。
- lifecycle fixture：尾截断 owner 的 open segment 在 stream 结束时不 commit、不 reset、committed 快照逐位不变；同 owner 无 reset 重新 admission → fail-closed。
- v0.11 §4 其余验收（wrapper attach/缺键、terminal 时序矩阵并入 v0.9 §3）不变。真实 manifest 重生成 + verifier PASS 仍归入 ⑪ GPU smoke Runbook 前置资产步骤。

## 3. 继承与范围

白名单扩增集合与 v0.11 §3 完全相同（root `tools/g0/build_r09_b2_stream_manifest.py`、`tools/g0/verify_r09_b2_stream_manifest.py`、child `cosmos_framework/data/generator/action/datasets/action_sft_dataset.py` 仅 `B2ManifestAwareIterableDataset.__iter__`、相邻测试）；`libero_lerobot_dataset.py` 明确不改。v0.11 被 ChatGPT 接受的全部条款与 v0.10 及其继承链逐条继承。本 v0.12 仍不授权实现之外的任何真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.12 为准；其余条款继承 v0.11–v0.1 及其引用的 C5A design v0.6、production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
