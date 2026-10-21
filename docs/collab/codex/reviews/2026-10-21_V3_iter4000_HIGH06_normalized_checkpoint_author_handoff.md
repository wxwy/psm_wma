# iter4000 HIGH-06：规范化 Model DCP 身份 / 作者交接

日期：2026-10-21。作者CPU Evidence与新Pair交接，**不是GPT增量验收或GPU授权**。

| 项目 | 精确版本 |
| --- | --- |
| Implementation Root | `950b2dbc6ad112205153a18dc0f733812db30706` |
| Child / Gitlink，未变 | `2d128ed5a07601cdd424974f99b67832eafeeb41` |
| 父 Root，含本轮集成审核及optim勘误 | `74d22d9c5a538da7684144d054e917c26146c503` |
| Queue Blob | `cb829cec0e43c09e8298e9d896a473b7b8285739` |
| 原集成Gate对象 | `6405c9dae02e81be5f267e79e27995c3df7fb988` / Queue `e56eaafe8276aa40cb9e2fbc1110515e8fa19c25` |

实现已非强推提交V3，并保留 `v3-iter4000-checkpoint-normalization-20261021`；后续证据/文档HEAD不代替Implementation。原HIGH-02、MEDIUM-05已闭CPU-static部分及HIGH-01撤销记录保留，不重新技术审核。此次只响应 `2026-10-21_V3_iter4000_DS_PRO_cpu_readiness_integration_gate_review.md` 的HIGH-06及其Owner勘误。

## 1. 生产修改：一个期望路径表达式

`scripts/eval_robocasa_18task_queue.py:87–91`：

```python
# CLI/manifest retain the requested root; the Child reports its selected model DCP.
for name, expected in (("checkpoint", (checkpoint / "model").resolve()), ("config_file", config_file)):
```

实际Child `inference/common/args.py:677–688` 对含model子目录的本地Checkpoint选择该目录；`inference/args.py:1437–1445` 使用它建立setup，`scripts/action_policy_server_robocasa.py:676–690,890–913` 将规范化路径回报到 `/info.checkpoint`。Queue原来比较父目录，误拒绝真正的iter4000/model。

本修复精确比较canonical模型目录；没有接受任意父目录、任意`/model`后缀、其它迭代或其它Job。请求/CLI/evaluation manifest仍绑定原Checkpoint根，模型metadata/hash/stat规则不改；Config/hash、采样、raw15/state/H16/64、Local required、端口/PID、Worker错误保全、锁、命令及Resume规则全部保持。

`scope_proof.json`机械证明：恢复这一处expected表达式后，**整个Queue AST与父版本一致**。身份模块字节和Child均未变。此入口仍要求CLI传入Checkpoint根（其中有model/），不新增直接传model目录的Queue CLI能力；Child自身直接传model不重复追加的行为只作为同源契约测试。

没有修改Child、Local-TTT、Optimizer、DCP、训练或锁；没有为推理补写/修复optim，也不停止正在运行的G1。原`complete.v1.json`与optim差异的训练恢复问题不进入本次model-only inference准入。

## 2. 测试不再手写伪造父目录回报

`tools/v3/eval_robocasa_queue_identity_test.py` 从固定Child源码解析并执行原始 `ConfigFileType`、`CheckpointType`、`CheckpointOverrides._build_checkpoint` 方法体。只隔离外部enum基类/类型注解和未用到的注册表依赖；真实临时Path目录、DCP后缀及.metadata存在检查按Child原码执行，不把规范化规则复制成另一个helper作为真值。源码/方法AST哈希见scope_proof。

每个集成HTTP stand-in的 `/info.checkpoint` 来自该方法的实际返回路径。独立正例也证明Child根目录与已选model目录分别得到同一个model路径，避免双重追加；所有fixture仅有model/config，没有optim。

| 场景 | 原Queue + 修正fixture（red） | 新Queue（green） |
| --- | --- | --- |
| 正确Child规范化Model DCP的直接契约 | checkpoint mismatch错误 | PASS |
| 正常1/2/4 Worker，各4Task×5条结果 | 三个子场景都RC1、zero sim calls，误拒正确/model | 全部RC0/COMPLETE/20条结果 |
| 错误iter3900/model、同iter4000其它Job/model | 仅作新代码负例 | RC1、zero sim calls、worker_errors保留 |
| 未规范化父目录、相似model_other、额外子路径、relative/缺失字段 | 仅作新代码负例 | 精确拒绝 |
| 原Config/采样/mode/端口/同身份旧Server/Worker初始化及异常退出 | 已有回归 | 继续PASS，没有放宽校验 |

## 3. 作者CPU实测

Evidence：`docs/collab/codex/evidence/2026-10-21_V3_iter4000_HIGH06_author_cpu/`。

- **32 passed**（17个定向方法 +15个既有Identity/Screening回归case），**47 subtests passed**，55无关项deselected，0fail/error/skip，34.879s。JUnit79为bookkeeping，不是79个独立方法。
- Python3.12.14、pytest9.0.2、Ruff0.12.7。新/改两文件Ruff check、format --check、语法及diff检查均PASS。
- 原代码red日志为2个方法、3个正常Worker数子场景fail和1个正向契约error，明确复现HIGH-06；不是新代码未解决的失败。最终16个Queue CPU集成场景包含1/2/4 Worker合成20条结果及严格负例，均无残留自有Worker/进程。
- `baseline.log`保留误拒原始输出；`pytest.log/xml`为最终运行；`regression_witnesses.json`提取前后JSON；`gate.json`含实际command/cwd/env/RC/source SHA，`implementation.patch`是精确最小diff，`manifest.json`绑定版本和产物hash。

边界：只执行stdlib HTTP/Git/临时模型文件名与元数据、合成结果/占位视频。没有导入真实Cosmos运行工厂或加载真实DCP权重，没有GPU/torchrun/真实Server/Simulator，没有可解码MP4或真实SR证据。同源方法体测试不冒称真实完整Pydantic/OmniInference模型加载。

## 4. 交GPT增量审核后，DS只做定向CPU复验

新Root/原Child的clean detached工作区，外置可写pycache/Evidence，`CUDA_VISIBLE_DEVICES=''`；不reset/clean/force、不修改源码、不重跑旧训练Gate。可用下列最小CPU选择（stdlib-only）：

```bash
python tools/v3/eval_robocasa_queue_identity_test.py \
  ServerIdentityTests.test_real_child_checkpoint_builder_model_path_passes_exact_identity \
  ServerIdentityTests.test_effective_info_exact_fields_and_malformed_values_fail_closed \
  QueueIntegrationTests.test_four_tasks_five_episodes_complete_on_one_two_or_four_workers \
  QueueIntegrationTests.test_wrong_checkpoint_config_and_mode_stop_before_simulator \
  QueueIntegrationTests.test_same_iteration_other_job_and_unnormalized_parent_are_rejected -v
```

另外对Queue/测试执行Ruff0.12.7 check、format --check；记录完整版本、Queue Blob、命令/RC、正负Witness及before/after clean状态。必要的扩展CPU命令已在gate.json，不要求重复全部旧30+41或旧GPU实验。不得使用历史6405c9da/ca936c8e的Root断言冒充新Pair。

DS可并行继续只读准备：实际Config的`dataloader_train.chunk_length/num_action_per_chunk`经真实resolver得到16（不能只看h_pred16），GPU/显存/端口/磁盘及四Task精确metadata集合。可用模型文件的推理前置只包括正确的 `iter_000004000/model/.metadata`、非空model shards、指定Config及真实模型canary等；**不要求optim、scheduler、trainer或dataloader sidecar齐全，不调用需要全组件的SafeLocal validate_checkpoint来阻塞模型推理**。这些附加训练状态的缺失不在本轮修复范围。

这项说明明确优先于旧 `2026-10-21_DS_PRO_V3_iter4000_HIGH02_CPU_readonly_preparation_ca936c8e.md` 中要求完整四组件/八份sidecar的metadata探针；旧probe不可原样作为本轮model-only inference门。保留旧文档不篡改历史；真实Server仍须Owner单独授权后加载并验证 `/info`，不能现在为获取runtime字段而启动GPU。

M03精确四Task、M04同身份完整Task-only Resume/partial新namespace、同用户/proc和采样/H16等既有严格边界继续适用。新Root改变evaluation digest，不复用旧Root输出；建议资源释放后使用两卡两Session Slot，先真实模型加载/info canary再4×5，全部取决于后续Gate与Owner授权。本批不发出或执行GPU命令，不操作G1训练。

**STOP：作者交付完成，等待新Formal Pair独立增量审核，随后DS定向CPU PASS，再由Owner明确释放资源和授权仿真。**
