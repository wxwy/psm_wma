# iter12000 评测参数语义复核：采样步数、预测长度、执行长度与 Episode 上限

日期：2026-10-23。
类型：Owner 转交 DS 参数说明后的源码事实纠正；不是新代码整改或 Gate 审核，不修改生产代码、脚本、运行中评测/G1，不启动模型或仿真。
本轮读取的远端 V3 HEAD：72d3155667604db668dea3343f2f09388534d548；对应已知实现测试 Root ee53cbe1c25ff174f0d92a92e51e901ec6436c18，Child c9f21040f462a114d597fc83773cb9b6a9e96214。以下 Root 源码读取固定前述 V3 HEAD，Child 源码固定 c9f21040；不是目标机新运行结果。

## 一、复核结论

DS“num-steps=预测30步未来动作”“action-horizon=模型输出chunk”“当前没有receding horizon开关”三种表述需要纠正。

- `--num-steps 30` 是每次生成时的去噪/采样迭代数，不是生成30个未来动作，不是每Episode上限，也不是30次重规划。Root别名 `--prediction-steps`/配置 `prediction_steps` 仍映射到这个采样参数；名字不能代替底层语义。
- 模型预测动作长度由 Server `--action-chunk-size 16` 控制；当前统一Queue固定传16，与G1 H_pred=16一致。
- `--action-horizon R` 是每次拿到预测后实际执行多少个动作，然后重新获取观测并预测。当前统一入口及required Local-TTT契约均已接受整数1..16。设置2/4/8不改变Server预测长度16。
- 每个Episode的动作预算由已固定RoboCasa registry的官方horizon决定，与前三者独立。任务跑5个Episodes不代表5集共用这一预算。

不需要为“预测16、只执行k再预测”新增 `--replan-interval`，也不需要改循环。禁止把参数理解错误变成无必要生产改动。

## 二、实际源码依据

### 1. 采样步数与预测长度分别设置

Child `cosmos_framework/scripts/action_policy_server_robocasa.py` 的 `ActionServerArgs`（约485–505行）：

```python
num_steps: int = 30
# Number of denoising steps.
action_chunk_size: int | None = None
# Number of action steps to predict.
```

该文件约985–1024行 `_prep_policy_item`/`_build_action_input` 用 `self.cfg.action_chunk_size` 构造video/action时间长度，有state时动作输入加一个条件token；serial `predict_policy` 约1169–1203行把 `self.cfg.num_steps` 传入 `self.model.generate_samples_from_batch`，生成后去掉state条件行。返回日志分别记录采样 `steps` 和 `action_steps=len(pred_action_list)`，二者不是一个量。

DS引用的 `cosmos_framework/inference/inference.py` 约1690–1754行，是在FSDP场景对去噪迭代数进行collective步序对齐，并转交sampler生成；不能据此推论为未来动作帧数。当前串行Policy路径直接调用model生成，亦已独立核对。

### 2. 现有执行截断就是 receding horizon

Root `scripts/eval_robocasa_18task_queue.py` 的 `server_argv`（约281–309行）固定 `--action-chunk-size 16`，而 `simulator_argv`（约315–329行）传入 `--action-horizon str(args.action_horizon)`。两端参数分离。

Root `scripts/robocasa_eval_config.py:224–253` 要求action_horizon正整数且<=16；Child `cosmos_framework/inference/robocasa_local_memory_contract.py::validate_local_memory_eval_contract` 同样要求 `1 <= action_horizon <= H_pred=16`，不是只准16。

Child `cosmos_framework/simulation/robocasa/closed_loop_eval.py::run_policy` 约291–341行：

```python
if not queue:
    result = predict(...)  # Server仍生成16步
    acts = result['action']
    queue = acts[:action_horizon]
a = queue.pop(0)
```

当R=4：第一次预测16步，仅前4步入执行队列；执行4步后queue空，基于新观测重规划。后12步未进入执行队列，不会在下一轮继续执行。原来的“必须等队列清空”恰好实现这个逻辑，不是缺少功能的证据。

Local-TTT `record_completed` 位于真实env.step成功后，记录实际执行的canonical raw15；未执行的预测尾部不应进入completed evidence。此处仅确认源码调用流程，不声称已在现场实测R=4的策略表现或延迟。

### 3. Episode预算及修改边界

Child `official_horizon`/`verify_runtime`（约163–245行）读取或验证registry horizon；main约531–536行：

```python
h = runtime['protocol']['official_horizons'][task_name] if runtime is not None else official_horizon(task_name)
eff_max_steps = h if h else args.max_steps
```

统一入口提供runtime并要求每任务有效正整数horizon；因此底层legacy `--max-steps`只是fallback，不是当前统一入口中的有效覆盖开关。
DS和已交dry-run记录的本固定环境值为CloseFridge900、NavigateKitchen450、PickPlaceSinkToCounter900、TurnOnSinkFaucet600。实际运行可因成功、异常或wall-time超时提前结束；这些是单Episode最多env.step次数，不是去噪次数，不是重规划次数。

“只能修改vendor registry才能改上限”不成立：将来若Owner确需诊断性自定义上限，可在Root/Child增加显式覆盖并记录official/effective horizon和非默认协议，无需篡改第三方registry。这只是设计可选项，本次不授权/不实施，也不把自定义时长结果混称默认协议评测。

## 三、给DS/Codex的处理

1. DS纠正报告中的概念，保留官方horizon结论，但明确为单Episode上限。不要基于错误描述申请新增replan-interval。
2. 当前R16运行不为此中止、修改或覆盖。Owner决定尝试短执行窗口时，只需把新运行参数改为 `--num-steps 30 --action-horizon 4 --save-generated-video all`，或者R=2/8；其余模型chunk保持16。
3. 先dry-run核对 `H_pred=16`、`server_action_chunk_size=16`、`R=4`、`num_steps=30`。新R写入manifest身份，须新run_name，不能以不同R resume旧目录。
4. Owner后续实际运行可从已有日志确认Server `action_steps=16`、相邻正常重规划发生于source_step 0/4/8/...；最后一段、成功提前退出、错误等另算。没有授权DS额外启动GPU。
5. 相同已执行步数下R4对比R16大致需要4倍预测调用，也生成更多预测MP4；这是次数估算，不是精确墙钟耗时保证，更不保证SR改善。20Hz下4步为0.2秒仿真时间，不代表模型0.2秒返回或实时5Hz。

本文只新增解释记录；不重新开启C01/C02或夹具Gate，不更改训练/模型/解码/增益/Vendor，保留暂停iter8900深入诊断的Owner决定。