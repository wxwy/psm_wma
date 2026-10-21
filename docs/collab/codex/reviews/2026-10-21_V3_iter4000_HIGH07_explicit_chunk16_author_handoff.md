# HIGH-07 — iter4000 explicit chunk16 / author CPU handoff

日期：2026-10-21。作者CPU自测，不是独立验收或GPU授权。

- **Implementation Root `320fda57c2cf450fbf0042183d7761a70b56f215`**；父Root `271984989dfd1151180905084c72817f74477e57`。
- **Child/Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41` 未变**；Queue Blob `4916918aca412a0abc6cb00e28f6053a351e07d8`。
- 已非强推发布V3及隔离源分支 `v3-iter4000-action-chunk16-20261021`。后续文档HEAD不替代实现SHA。独立Config-truth候选不在此Pair。

## 最小生产修改及契约

仅 `scripts/eval_robocasa_18task_queue.py:275,365`：各Worker命令显式 `--action-chunk-size 16`；immutable Evaluation Identity protocol增加 `server_action_chunk_size=16`。`H_pred=16`和执行`R`语义独立，仍保留。新协议字段进入原有manifest digest；必须使用新输出namespace，不把旧Root/旧manifest结果冒充同身份Resume。

真实Child已支持CLI > Config > fallback，不改Child。旧G1 Config32保留原bytes，指定模型/root-model路径、config SHA、raw15/state/H16/required/64/fps/采样、端口/PID、Worker异常、锁、Local-TTT、Optimizer、DCP及运行中G1均不动。`scope_proof.json`证明删除新增CLI两元素和manifest键后整个Queue AST与父版本相同，共享Identity模块与Child未改。

## CPU Red/Green Evidence

目录：`docs/collab/codex/evidence/2026-10-21_V3_iter4000_HIGH07_author_cpu/`。

测试直接解析固定Child的 `_extract_chunk_length_from_config`、真实初始化的CLI/config/fallback `if` 分支和fallback常量原AST并执行，仅隔离DictConfig类型/日志；未导入真实服务工厂或模型。每个合成HTTP `/info.action_chunk_size`来自真实分支对Queue实际CLI和合成Config32的运行结果，非写死16。

- Red：旧Queue没有override；1/2/4 Worker各RC1、zero sim calls，strict info expected16/got32，三个预期回归失败；直接CLI16覆盖32/缺CLI32负例本身PASS。
- Green：**33 passed（18定向方法+15既有回归）+50 subtests passed**，55无关项deselected，0failure/error/skip，37.631秒。JUnit83为包含subtests的bookkeeping数。Ruff0.12.7 check/format、syntax、diff PASS。
- 17个集成场景包括1/2/4 Worker命令全部显式16、Manifest16、各4任务×5合成结果；Config32文件bytes前后不变；强制错误/info32仍RC1/zero sim calls。原错误Checkpoint/Config/mode、监听者冒充、启动/中途退出、mkdir/log-open异常回归保持PASS。
- `gate.json`记录完整command/cwd/env/RC/source哈希；baseline/final日志、JUnit、原始argv/结果witness、scope proof、diff及manifest哈希齐全。
- 测试仅CPU临时Git、模型metadata占位、stdlib HTTP与合成结果/视频占位。未启动真实Action Server/模型/Simulator或GPU，没有真实SR/MP4/模型加载证据；没有访问G1工区/Config/Checkpoint或停止其进程。

## GPT/DS 下一步与停止边界

请GPT只对新Pair HIGH-07做独立增量审核，不重复已关闭HIGH-02/MEDIUM-05/HIGH-06。后续DS在clean detached新Root/原Child可仅执行：

```bash
CUDA_VISIBLE_DEVICES='' python tools/v3/eval_robocasa_queue_identity_test.py \
  ServerIdentityTests.test_real_child_explicit_chunk16_overrides_config32_and_missing_flag_fails_strict_info \
  ServerIdentityTests.test_effective_info_exact_fields_and_malformed_values_fail_closed \
  QueueIntegrationTests.test_four_tasks_five_episodes_complete_on_one_two_or_four_workers \
  QueueIntegrationTests.test_wrong_checkpoint_config_and_mode_stop_before_simulator -v
```

外置pycache/log；两改动文件Ruff0.12.7 check/format；记录新Pair和命令/RC/witness。DS仅CPU/真实Config只读，不检查GPU占用，不启动模型/仿真，不要求optim。不改旧G1 config.yaml/config.pkl/v3_job_identity.json或任何历史资产。Owner决定G1停止/释放GPU及以后canary/4×5授权。

本次HIGH-07代码完成。Owner另外授权的未来新Job Config-truth只在另一隔离分支实现/提交，不合入本HIGH-07或V3训练路径；两项各自等待GPT独立审核，不自动执行后续GPU。
