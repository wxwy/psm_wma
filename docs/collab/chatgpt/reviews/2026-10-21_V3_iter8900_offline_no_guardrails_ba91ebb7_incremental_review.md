# PSM-WMA V3 — iter8900 offline Guardrail1 bootstrap blocker: 一行 Queue 修复 + 新 Pair 增量审核

日期：2026-10-21
当前任务：`iter_000008900` required Local-TTT RoboCasa 4 underlying tasks × 5 episodes；**不是旧 iter4000 评测结果**。

## Exact implementation pair

- 原正式技术 Pair Root：`306d235046fe5d578503beb17a56f5c0eb0f5634`；Child/Gitlink：`35b0ea1ccee9ee26653ed6589c484f0997d1c586`；Queue Blob：`4916918aca412a0abc6cb00e28f6053a351e07d8`。
- 本轮提交前 latest V3 docs HEAD：`2f75ed0ced577fab75a08a89343f202003f7445b`（文档 SHA，不代替旧正式实施 Root）。
- **修复后的新 Root Implementation SHA：`ba91ebb7de2555cd1ff2a290d0af5ee43a8a3ee6`**。
- **Child/Gitlink `35b0ea1ccee9ee26653ed6589c484f0997d1c586`**，未变。
- **新 Queue Blob `72ad7e2b94b31cbfd7a8af0a1eaff92127ffa7ae`**。
- **新 Queue test Blob `d6a52d35b79e1d8636f36583c4122c483a3b3afa`**。
- 本轮两个非强推源码提交：Root `116cada3373625362a24f8005f2c4976559941c5`（生产一行）、最终 Root `ba91ebb7de2555cd1ff2a290d0af5ee43a8a3ee6`（测试一行）。V3 exact re-fetch/tree/diff证实相对最新旧docs HEAD **仅这两个文件各 +1行**，不改 Child。

## New finding: HIGH-08 — offline inference guardrails startup dependency

- **Severity: HIGH**（目标机真实模型进程启动阻断）。
- **file:line**：`scripts/eval_robocasa_18task_queue.py:353-379`，Root Queue `server_command` 原缺 `--no-guardrails`；Child `cosmos_framework/scripts/action_policy_server_robocasa.py:479,565,603-630` 的 `ActionServerArgs.guardrails: bool=True` / `base.guardrails=self.guardrails`；`cosmos_framework/inference/common/inference.py:142-151` 的 `GuardrailRunners.create` 由布尔 flag 触发。
- **Root cause**：正式离线 Action Server 默认为创建附属 Guardrail1 组件；DS 报告目标机无 `nvidia/Cosmos-Guardrail1` 模型缓存与外网，下载失败导致真实 `ActionModelService` 初始化抛出 `CalledProcessError`。DS 手工 CLI 加 `--no-guardrails` 后，GPU2/port8900 实测模型加载并可读取匹配 `/info`；**这是 DS 提交的现场日志摘录，不是 GPT 已直读其本机原始日志**。
- **Frozen contract**：此任务是内部离线 RoboCasa 评测，Required Local-TTT / raw15-state15 / chunk16/H_pred16 / 20fps / checkpoint id / config SHA / self-owned loopback /info；正式 Queue 在既定允许的 `--no-guardrails` smoke 策略下必须无需下载附属模型即可启动，且不全局改变 Child guardrail 默认策略。

## 修复与源码核查

- **Production diff 精确一行**：Root Queue 每个 Worker server CLI 在 `--http-400-on-error` 前增加 `"--no-guardrails",`。用户明确要求最小变更；未更改 Root protocol manifest、Output format、Child、Checkpoints、freeze G1 config或任何训练逻辑。新的 Root SHA 自带新 Evaluation identity digest，旧 output 不能混用。
- **Test diff 精确一行**：`tools/v3/eval_robocasa_queue_identity_test.py:526-536` 在已有 1/2/4 Worker 合成正常场景内增加 `self.assertEqual(command.count("--no-guardrails"), 1)`，因此可以证明每个 Worker 启动命令恰有该 flag；既有 `--action-chunk-size 16`、H_pred/R16、全 4 task×5 合成结果及错误语义断言保留。
- 新完整源码经 GitHub V3 精确 SHA 回读：生产 Queue/测试各一行加法，Root Gitlink精确新 Child，Child ActionServer bool 默认 True 与 build_setup overrides 原代码一致；`Inference.create` 在 `guardrails=False` 时令 guardrail runner `None`，不进入附属下载路径；参数本身已被 DS 手工真实 canary 的命令验证是 Child 可识别 CLI。
- 本轮只是内部离线 RoboCasa 评测，不意味着允许在任何面向公众的 serving/default safety 配置中全局关闭 guardrails。仍保留全部 /info/checkpoint/config/port PID 严格身份校验、Local required、H16、已有 HIGH-02、MEDIUM-05、HIGH-06、HIGH-07 防护逻辑。
- **作者即 ChatGPT 使用 GitHub connector 直接修改并回读了本轮两行源码**。这不是独立开发者提供的执行测试。**GPT未运行完整 Python CPU 集成测试，也未执行 GPU/canary/真实仿真**；不能把结构比对当作 1/2/4 Worker runtime PASS。

## Verdict / evidence gate

**`REQUEST_CHANGES` — EVIDENCE-ONLY（新 Pair 的 targeted CPU 执行以及真实正式 Queue canary 仍待 DS_PRO 完成）；目前直接审查生产源码无未修复的 HIGH-08 scope 内 code blocker。**

接收门槛不是让 Codex/GPT再修改生产源码，而是让 DS 在**新 exact Pair** 下执行一项 `QueueIntegrationTests.test_four_tasks_five_episodes_complete_on_one_two_or_four_workers` CPU 试验与 Ruff check/format、语法；输出新 Pair、Command/RC/正例 Worker argv `--no-guardrails` 和错误日志。CPU失败即停止并给出可复核证据，不直接开GPU。

在 Owner 已将GPU2分配该仿真任务且实际仍释放的前提下，CPU绿后按 **`docs/collab/chatgpt/requests/2026-10-21_DS_PRO_iter8900_no_guardrails_new_pair_CPU_then_real_canary.md`** 的 runbook：
1. Stage A 使用新代码/真实 iter8900 Config/Checkpoint 运行 **1 Task ×1 Episode**，验证真实 Model load、/info、required Local-TTT真实predict/仿真动作、完整结果和可解码MP4。DS手工旧canary /info绿不等同新版 Queue E2E绿。任意 Infra Error/RuntimeError/OOM/启动失败/视频无效则 STOP；
2. 若 Stage A 真实 E2E全绿且有足够已分配GPU，Stage B 在全新输出路径串行 GPU2 运行 **4 Task×5真实 Episode**，保留manifest/summary/JSON/logs/MP4和逐task成功率；不得伪报 synthetic SR，也不得跨 Root/Checkpoint/digest复用旧Episode。
3. **不要求本轮 nvidia-smi/GPU inventory、不要求 optim/**，不修改仍在运行的G1冻结Config/Checkpoint或其它进程。Owner控制资源分配，DS只处理自有 server/simulator PID。

正式 CPU+真实执行 Gate completion 仍需 DS 的新 Pair 原始 log/结果，经 GPT/Owner复核后记录；本 review **不宣称已经重新启动模型、仿真成功或真实 SR**。

**Scope：本次一行补丁已上V3；尚未关闭新正式执行 Evidence Gate。**
