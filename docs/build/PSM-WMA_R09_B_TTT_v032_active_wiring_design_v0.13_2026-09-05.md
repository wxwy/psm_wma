# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.13

**状态**：v0.12 superseded（仅 tail 认证措辞；v0.10 已批准范围与 v0.11 被接受条款不受影响并保持有效）；待三方同 SHA 设计审核。仅冻结尾组认证的序列域修正，不授权实现、GPU 或训练。
**基线**：v0.12（root `2309d69`）获 MM、Kimi 双方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`（v0.12 tail 政策整改部分）与 ChatGPT（review=`7cb418c`）`REQUEST_CHANGES`。唯一阻塞 HIGH-1：v0.12 §1.2 把尾组 ordinal 连续定义为全局 ordinal 连续整数，但实际 builder 按 micro-batch suite round-robin 分配、全局 ordinal 跨 suite 递增，同一 suite 的同一 episode 合法地横跨多个 micro-batch，其全局 ordinal 本就非连续整数——合法尾组会因此被 verifier 误判。ChatGPT 接受 v0.12 其余全部条款（真实 terminal 不伪造、固定条数不变、单一认证尾组方向、single-pass end-of-stream 语义、v0.11 wrapper/model fail-closed 与白名单），本 v0.13 原样保留，仅按 ChatGPT 指定措辞修正认证序列域。

## 1. 尾组认证修正（ChatGPT HIGH-1 整改，采用其指定措辞）

v0.12 §1.2(a) 替换为以下冻结措辞，其余四条（builder 不变、verifier fail-closed 矩阵、end-of-stream 语义、lifecycle 零新增）逐字继承：

**尾组认证（certified tail group）**：将 record 按 `(suite, epoch)` 过滤并按全局 `ordinal` 升序排列，得到该 suite 的过滤序列。一个 `(suite, epoch, episode_index)` 组允许零 `is_episode_end=true` 当且仅当同时满足——

- (a) 该组等于上述**过滤序列的最后一个连续组**（同一 owner 的 record 在过滤序列末尾连续出现；连续性的定义域是过滤序列的位置序，不是全局 ordinal 整数的相邻性）；且该组包含该过滤序列的**最大全局 ordinal**；
- (b) 组内 record 数 < 该 episode 的 valid window 计数（verifier 经 dataset 独立重算）；
- (c) 组内无 `is_episode_end=true`。

每 `(suite, epoch)` 至多一个尾组。其余每个组仍必须**恰好一条** `is_episode_end=true` 且位于该组最大 `start_frame`。

## 2. 验收增补（CPU/static，并入 v0.12 §2）

新增 verifier fixture（ChatGPT 指定）：一个合法尾 episode 横跨多个 suite round-robin micro-batch、全局 ordinal 非连续——必须 **PASS**；计数相同的非末尾组（过滤序列中不在末尾）——必须 **FAIL**。v0.12 §2 其余 fixture（builder 截断无伪造、非尾组缺 terminal/尾组含 terminal/计数达标拒绝、terminal 位篡改/缺失、lifecycle 尾截断 open segment 不 commit/重 admission fail-closed）全部保留。

## 3. 继承与范围

白名单扩增集合与 v0.11 §3 完全相同（root `tools/g0/build_r09_b2_stream_manifest.py`、`tools/g0/verify_r09_b2_stream_manifest.py`、child `cosmos_framework/data/generator/action/datasets/action_sft_dataset.py` 仅 `B2ManifestAwareIterableDataset.__iter__`、相邻测试）；`libero_lerobot_dataset.py` 明确不改。v0.12 被 ChatGPT 接受的全部条款、v0.11 被接受条款与 v0.10 及其继承链逐条继承。本 v0.13 仍不授权实现之外的任何真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.13 为准；其余条款继承 v0.12–v0.1 及其引用的 C5A design v0.6、production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
