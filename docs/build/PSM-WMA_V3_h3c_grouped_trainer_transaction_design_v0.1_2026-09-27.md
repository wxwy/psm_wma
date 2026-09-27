# PSM-WMA V3 H3-C — grouped trainer transaction CPU/static 设计 v0.1

- 日期：2026-09-27；责任：cx 技术 owner 与实现，ds 后续 GPU 执行；ChatGPT 为非在线审核者。
- 基线：H3-A joint autograd、H3-B 8 rank×8 stable slot×GA2 candidate producer；此设计仅覆盖 CPU/static H3-C，不启动 GPU 或正式训练。

## 冻结目标

8×H100 正式路径使用普通 autograd 从官方 native policy flow outer loss 穿过 Local K/V prefix，同时更新既有 Edge generation/action 范围及全部 Local slow 参数。禁止借用 4090 detached-leaf relay。固定 T16、K4、raw15、model action64、policy chunk32/33 帧；每 rank 每窗口两个 member，各有 8 stable slots。有效 consumer 总数 `N_window` 精确取 H3-B `GroupedWindowPlan.n_window`；同 index 的有效 slot 组成一个 native microbatch，loss 权重为该 batch 大小除以 `N_window`，不得再除 GA2。

## 事务与接线

1. live 状态统一为单个对象：catalog frontier、每 slot sidecar 及 scheduler。规划与物化两个 member 只读 live；候选状态使用私有 overlay。任何 forward/backward/预检失败，丢弃 overlay，live 对象身份和内容不变。
2. 每 member 为 8 个单 row B1 `SegmentBatch` 各用一个 B0 adapter，复用 `model.net.local_memory_runtime.encoder/core` 和已注册的 `model.net.scan_local_memory`。adapter 读取 overlay；同 slot member2 看到 member1 的候选 detached fast state，terminal 后下个 episode S0 无 Local。跨段只 detach fast state，不 detach token→native outer graph。
3. 每个 index 只收集该 index 的有效 payload 与 graph-connected prefix，传入一次 native `OmniMoTModel.training_step(..., _local_memory_prefixes=prefixes)`；batch slot 顺序固定。16 个 index 的加权 native loss 执行 backward 后才把该 member 的 8 个结果提交到 overlay；第二 member 重复。Local inner 更新仅产出 candidate fast state，不增加 outer loss。
4. 进入 optimizer 前必须完成两 member、检查 finite loss 与全部已选参数梯度；GradScaler enabled 时先 unscale、判定 inf/NaN，并用 scale 更新判断是否 skip。调用现有 trainer callback/optimizer/scheduler 顺序；只有真实 optimizer step 成功才将完整 overlay 以单次 live 状态引用替换发布。失败时禁止 frontier/sidecar/scheduler 发布；optimizer 异常则终止该窗口，不能在未知部分更新后继续。
5. H3-C CPU tests 必须覆盖 GA 几何 `128+128=256`、terminal remainder 的实际 `N_window`、host+Local 联合梯度、S0/continuation/rebind、回调异常、非有限 loss/grad、GradScaler skip、optimizer 异常与成功一次提交。须有使用真实 `ImaginaireTrainer` 生命周期入口的测试，不能只测独立事务类。

## 边界与后续

child 优先新增 grouped window 模块和 tests；对 trainer 仅作可审查的局部 subclass/hook，不重排 upstream 训练循环。H3-D 单独负责 model/optimizer/scheduler/fast sidecar/frontier/RNG 的严格 DCP resume；H3-E 才由 ds 做 8×H100 短跑与恢复证据。H3-C CPU PASS 不等于正式训练就绪。
