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