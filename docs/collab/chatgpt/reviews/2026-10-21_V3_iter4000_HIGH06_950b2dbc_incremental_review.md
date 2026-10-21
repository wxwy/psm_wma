# PSM-WMA V3 — iter4000 HIGH-06 Checkpoint normalization 独立增量复审

日期：2026-10-21
Gate：V3 iter4000 4 tasks × 5 episodes queue — HIGH-06 CPU/static integration remediation
Scope：**root Queue / pinned Child path semantics / CPU synthetic Evidence**；不授权 GPU、真实 Cosmos Action Server/Simulator、训练或生产 DCP 修改。

## Formal pair（精确）

- Implementation Root：`950b2dbc6ad112205153a18dc0f733812db30706`
- Child/Gitlink：`2d128ed5a07601cdd424974f99b67832eafeeb41`，未变
- Implementation parent（含前轮记录）：`74d22d9c5a538da7684144d054e917c26146c503`
- 上一个技术对象：`6405c9dae02e81be5f267e79e27995c3df7fb988` + 同 Child
- Queue 新 Blob：`cb829cec0e43c09e8298e9d896a473b7b8285739`
- 当前作者 docs HEAD `c15e57b1da9b0747f31874894153597aca25c4cc` 只是 Evidence/bookkeeping，不替代 Implementation SHA。
- 先前 Integration review：`docs/collab/chatgpt/reviews/2026-10-21_V3_iter4000_DS_PRO_cpu_readiness_integration_gate_review.md`（含 optim/ 非评测前置条件的 ERRATUM）。
- 作者交接：`docs/collab/codex/reviews/2026-10-21_V3_iter4000_HIGH06_normalized_checkpoint_author_handoff.md`；Evidence：`docs/collab/codex/evidence/2026-10-21_V3_iter4000_HIGH06_author_cpu/`。

## Formal Verdict

**`APPROVE` — 关闭 HIGH-06 的 CPU/static remediation Gate，仅此 scope。**

HIGH-06 **CLOSED**：当前 Queue 将 `/info.checkpoint` 与 `(requested_checkpoint_root / "model").resolve()` 精确比较，匹配 Child 实际本地 DCP 规范化结果；错误迭代、其他 Job、父目录、不正确的任意路径被拒绝。当前 Pair 未发现新的 scope 内 production blocker。此前 HIGH-02、MEDIUM-05 已 CLOSED，HIGH-01 曾撤销为 FALSE POSITIVE；不因新提交重复审查或要求重新修改。

**本 verdict 不放行 GPU/真实推理/仿真。** 实际迭代 4000 模型加载、真实 /info、目标 GPU/Config/H16/端口/存储、20 条 rollout 仍属于后续独立执行 Gate；当前 GPU_RELEASE 维持 BLOCKED，直至 Owner 单独授权。

## Production 实际 diff 和契约

- `scripts/eval_robocasa_18task_queue.py:83-91`：唯一的生产行为变化为将 `validate_server_info()` 的 checkpoint 期待值从 `checkpoint` 改为 `(checkpoint / "model").resolve()`。保持 `--checkpoint-path` 和 `evaluation_manifest` 指向用户请求的根目录、Hash/身份等契约不变。
- Child `cosmos_framework/inference/args.py:1437-1445` 的 `OmniSetupOverrides.build_setup()` 调用 `_build_checkpoint`；`cosmos_framework/inference/common/args.py:677-688` 把存在 `model/` 的本地 DCP 根变为 `root/model`；`cosmos_framework/scripts/action_policy_server_robocasa.py:676-690,890-913` 将归一化的 `setup_args.checkpoint_path` 返回给 `/info.checkpoint`。
- Root 其他 Checkpoint/Config/path 真实性检查继续执行 `Path(value).is_absolute()` 和 `.resolve()==expected`，因此没有放宽到任意 `model/` 目录、其他根或相同 iteration 名称。
- 新 root commit 中生产变动仅 1 条 expected 表达式与注释；附带聚焦 CPU 测试和 SESSION/TODO 追加。Gitlink/Child、`scripts/v3_evaluation_identity.py`、server/simulator 命令、PID/port、采样、required-mode、worker 错误及锁作用域未变。作者 `scope_proof.json` 与实际 diff 一致。

## Direct behavioral Evidence

GPT 直接读取 GitHub 新测试源码（`tools/v3/eval_robocasa_queue_identity_test.py`）与作者提交的 `gate.json`、`scope_proof.json`、`manifest.json`、`baseline.log`、`pytest.log/xml`、`regression_witnesses.json`，并与 pinned Child 源码对照。**没有在执行服务器独立重跑 CPU，也没有加载模型或 GPU**。

- 新 fixture 使用 AST 解析并执行 pinned Child 源文件中的 `ConfigFileType`、`CheckpointType` 及 `CheckpointOverrides._build_checkpoint` 原方法体（仅隔离无需执行的外部依赖），在真正临时 `model/.metadata` 和 `*.distcp` 文件上执行实际本地路径探测，而非复制写死的路径逻辑。
- RED：修复前 Queue 遇到正确 Child `root/model` 回报时，1/2/4 Worker 合成任务全部 `rc=1`、`sim_calls=0`，日志中的失败理由为 expected 根目录与得到的 `root/model` 不同。
- GREEN：修复后 1/2/4 Worker 分别 `rc=0`、`status=COMPLETE`、`total_trials=20`、`sim_calls=4`；正向同源路径校验通过；错误 iteration、其他 job、父目录等 0 sim + nonzero RC，旧 Server/Config/Worker 负例回归仍成立。
- 作者终态：`32 passed, 55 deselected, 47 subtests passed in 34.88s`，`pytest.xml` 的 79 是计入 subtests 的 bookkeeping case 数，不是 79 个独立方法。Ruff check/format、`py_compile` 与 `git diff --check` RC0。对应源 SHA/证据 hash 见作者 manifest/gate。
- 合成 HTTP、临时 DCP 结构和视频占位不是实际推理 I/O、视频文件或 SR；未用作者 PASS 取代生产代码与 pinned Child 的直接复核。

## 后续执行 Gate 与禁止事项

1. **DS_PRO 仅 CPU 定向独立复验**：在 clean detached Root `950b2dbc...` / Child `2d128ed5...` 执行作者列出的五项定向 CPU 验证及 Ruff，提交带 SHA/命令/RC/正反例 witness 的独立日志；此前 30+41 的已闭 CPU 案例不需要无意义整套重复。
2. **目标机只读配置检查**：Action Server 使用 `_extract_chunk_length_from_config` 从真实 `dataloader_train` 解析 `action_chunk_size=16`，不能只引用 `h_pred=16`；必要时单独报告。四任务 `dataset_meta.json` exact name set、`iter_000004000/model/.metadata`/nonempty shards、Config 及 /proc/port/GPU/memory/disk 新鲜状态，输出新 namespace。
3. **Owner GPU release 之后** 才能按新 Pair 申请真实模型加载及 `/info` canary；canary 通过后还需按明确授权范围执行 4任务×5 Episode，并保留真实 JSON、可解码 MP4、错误/SR分类证据。无自由 GPU 不执行、不抢占正在运行的 G1 训练。
4. 推理不读取 optimizer：`optim/` 不属于这个 model-only Gate，不得因此阻止或修改推理 DCP。whole-task-only `--resume` 边界继续有效；不允许拼接不同 Root/旧 digest 的 partial 结果。

**此 formal verdict 只关闭当前 HIGH-06 CPU/static remediation Gate，不代表授权真实 GPU 或其它 Gate。**
