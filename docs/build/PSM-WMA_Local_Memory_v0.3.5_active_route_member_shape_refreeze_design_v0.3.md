# Local Memory A2 Member Shape Refreeze v0.3 — Stable-Slot Synchronized Microbatch

日期：2026-09-18。状态：implementation-aligned refreeze。
本文件 supersede v0.2 中“先按 scalar scheduler 选择，再每 B_stream 个连续 segment 成组”及 repeated-slot dependency-wave 语义。
算法/训练总 authority 仍是 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`。

## 1. Canonical microbatch

- `B_stream` 是稳定 episode-stream slot 数；默认 8，可配置。
- `T = ttt_tbptt_steps = 16`。
- 每个 native microbatch **每个 stable slot 恰好贡献一个 next segment**。
- group row 顺序固定为升序 slot id；同一 group 禁止重复 slot。
- 默认 shape：`[B_stream,T] = [8,16]`，即 128 个 logical/valid consumers。
- 一个 optimizer update 默认 `GA=16` 个这样的 microbatch，即 2048 consumers。

## 2. TTT / Transformer execution

对一个 `[8,16]` microbatch：

1. 8 个 slot 分别装载自己的 `W_fast`；fresh episode 使用当前 `W_bar_0`。
2. `t=0..15` 严格串行；同一个 t 的不同 slot 并行执行独立 TTT update/read。
3. 得到 `M_local[8,16,K,D]`；stream-major flatten/gather。
4. 128 个 consumer + 128 个 Local Prefix 一次进入 native Transformer/MoT forward。
5. valid-consumer weighted outer backward 成功后，8 个 slot 的 candidate fast state 原子发布。
6. 下一 microbatch 再取这 8 个 slot 各自的 next segment。
## 3. Episode / catalog boundary

- episode continuity remains hard contract；不得为了凑 batch 中途切 episode。
- 某 slot 的 terminal segment 完成后，只能在**下一个 microbatch boundary** rebind fresh episode。
- fresh episode 必须从 cursor/step 0 开始，并清除旧 fast carry。
- 若该 slot 的当前 catalog 已完全耗尽，只允许在前一 episode terminal 后进入下一 slot-local reuse epoch。
- `SegmentIdentity` 不新增 epoch 字段；epoch reuse 首个 cursor0 identity 执行前，仅清该 slot 的旧 audit history，防止历史相同 identity 阻塞 commit。
- optimizer-window 内允许不同 slot 位于不同 episode/cursor；“同步”指每个 microbatch 每个 stable slot 各取一个 next T-block，不要求不同 episode 的 cursor 数值相同。

## 4. Superseded behavior

以下 v0.2 行为不再属于 active A2：

- scalar `freeze_window()` 先选择 `B_stream*GA` 个 member 再切片成 group；
- 同一 native group 出现同一个 slot 两次以上；
- 用 `dependency_waves > 1` 串行处理同组 repeated slot；
- 以 B=1 scalar member 顺序作为 A2 correctness authority。

B=1 只保留为吞吐/显存 control。梯度目标等价由同数据 grouped-vs-scalar native parity 与
`L_window = sum(valid consumer losses) / N_valid_window` 证明。

## 5. Required acceptance

- CPU：每个 group slot 唯一、固定稳定顺序、各 slot chronology 连续。
- CPU：terminal/rebind、slot-local epoch reuse、atomic commit、resume 均保持。
- geometry：至少覆盖 `B_stream=4/8/12`；默认 8×16=128、GA16=2048。
- CUDA：vectorized inner update / slow gradient 与独立 per-row 算法数值等价。
- Real GPU：每 update `native_forwards=16`、`valid_consumers=2048`。
- Real GPU telemetry：每个 128-consumer group 必须解析为 8 个 stream-major 16-consumer chunk，slot 顺序 0..7，`dependency_waves=[1]*16`。
## 6. Owner override / authority note

本 v0.3 是用户 2026-09-18 最新明确实现目标的 durable refreeze：
“所有 slot 同步计算；slot 内 TTT 沿 T 串行；8×16=128 samples 后一次 Transformer 前向”。
因此它显式覆盖 v0.2 的 scalar-order-preservation 过渡约束；DS_PRO 对旧批准边界的流程质疑成立，
但通过本 owner refreeze 解决，不回退到 scalar grouping。

当前适用范围仅为 LIBERO4IN1 canonical smoke 的 member packing；
未来 RoboCasa 等 task 数大于 B_stream 的通用 weighted-deficit scheduler 仍需独立 Gate，
不得把当前 static stable-slot/category allocation 解释为通用采样算法。

## 7. Final gradient acceptance after function-preserving zero initialization

implementation root `2a9df880` 内的早期 verifier 采用“每个 optimizer window、每个 D025 group 都必须 `nonzero_grad > 0`”的过强判据。真实 B=1 与 A2 fresh run 都证明该判据在 window 1 必然不成立：`local_memory2llm.weight` 采用 function-preserving exact-zero 初始化，因此首个 optimizer window 中 `dL/d(Local token) = grad_out @ W = 0`；`local_memory_runtime.evidence_encoder` 与 `local_memory_runtime.ttt_core` 虽在图中且 `with_grad > 0`，数值梯度应精确为 0。完成第一个 optimizer step 后 projector 离开零点，从 window 2 开始两组均应持续收到非零梯度。

最终 verifier 不采用“整段运行至少一次 nonzero”的宽松累计判据，而固定为逐 window 时序判据：

- 所有 D025 group 在每个记录 window 都必须 `finite=true` 且 `with_grad>0`；
- fresh `window_index==1` 时，仅 `local_memory_runtime.evidence_encoder` / `local_memory_runtime.ttt_core` 必须 `nonzero_grad==0`；其余 D025 group 仍必须 `nonzero_grad>0`；
- `window_index>1`（含 resume 恢复后的后续 window）时，上述两个 Local runtime group 也必须 `nonzero_grad>0`；
- optimizer membership tensor count 每个 window 仍必须与 requires-grad telemetry 完全一致。

该收紧只修正 acceptance/verifier 对 zero-init 的解释，不改变 `2a9df880/22acb13c` 的训练实现、loss 定义或任何 GPU evidence bytes。后续 root-only verifier/report commit 可以验证这个 immutable implementation pair，但必须同时证明目标 root 是当前 lineage 的 ancestor、其 `cosmos-framework` gitlink 精确等于目标 child，且 live child tracked source 与目标 child 一致。
