# R09-B2 P2 非变异 Capture 设计 v0.1

**状态**：DRAFT；仅请求方案审核。禁止实现、模型加载、训练、GPU、评测与推理。

## 目标

为未来 matched training 的 Normal/Zero/Shuffle 采集定义一条只读观察路径。Capture 必须从同一已消费 batch 的深拷贝输入和 Local runtime state 副本计算，绝不推进 canonical dataloader cursor、训练 RNG、模型参数、optimizer、scheduler 或真实 runtime state。

## 冻结合同

1. observer 只能在 `on_training_step_end` 读取已经产生的 `data_batch`/`output_batch`；不得调用 `next(dataloader)`、`training_step`、backward、optimizer step 或 checkpoint save。
2. callback 禁止对 canonical training model 或 canonical Local runtime 做第二次 forward。Normal/Zero/Shuffle 只能运行于纯函数 helper 或显式 functional/cloned module/state 路径，输入为 detached 已产出 feature 与 clone；不得触发 canonical hook/counter/buffer。
3. capture 进入时保存 CPU/CUDA RNG states，并在 `finally` 无条件恢复；异常也必须先恢复 RNG 再写 FAIL。扰动只作用于 clone，不写回原 batch/state。
4. cursor 证据只取已消费 batch 的 P1 immutable `b2_stream_ordinal`、epoch、microbatch metadata；禁止检查、clone、推进、回绕或查询 live dataloader iterator。TTT 覆盖冻结五成员 state；recurrent 覆盖完整 recurrent state representation。
5. capture 前后分别记录并比较：模型 parameters **及 buffers**、optimizer state、scheduler state、CPU/CUDA RNG states、batch ordinal metadata、完整 Local runtime state SHA。任一变化即 FAIL。
6. 输出为 JSON + 可选 detached CPU tensor sidecar；每条带 root/submodule/Gitlink、manifest ordinal、mode、输入/输出 hash 和 before/after hash。
7. verifier 要求三模式的 non-history input/packing/mRoPE 字段逐位一致；只允许 Local payload 改变，并记录 future/action sensitivity。

## 实现面与验收

- 最小新增 callback 与 CPU unit tests；复用 R07 sidecar 的 tensor 摘要，但不得复用其写入语义来改变训练路径。
- CPU test 必须覆盖：正常 capture、全零/置换 clone、canonical model/runtime second-forward 或 mutation 拒绝、RNG 消耗后异常仍逐位恢复、parameter/buffer/optimizer/scheduler/runtime/batch ordinal mutation 检出、unsupported mode 与 malformed Local payload 拒绝。
- 任何 runtime/GPU capture 均需 P2 实现 closure 后另行运行审批。

## 禁止范围

本方案不授权 P3-P5、B2-T、训练、模型/VAE/optimizer 加载、GPU、eval/inference/closed-loop/SR/backend freeze。
