# 当前协作状态

更新时间：2026-08-27

## 2026-08-25~26 数据下载会话(sandbox,Codex)

- 用户授权"明早要见到数据 ready",但本沙箱到 `huggingface.co` 出网被掐死:直连 curl 测速 611 B/s、`hf-mirror.com` 480 B/s、HF XET 协议 0.05 MB/s、HF 默认 HTTP 30 秒字节零增长;SSH 到 bita 第一次测试单大文件 SFTP 1.99 MB/s(4.3GB ETA 36 min)看似可行,但 8 路并发 SSH 触发 bita `MaxSessions` 限流,后续单 SSH 连接也被拒,放弃 scp 路径。
- 创建 `/gemini/code/system_monitor.sh`(CgroupV1 适配版,与 bita `/disk/rl/system_monitor.sh` 口径一致但读取 `/sys/fs/cgroup/cpu,cpuacct,memory,cpuset` + sda 块设备 + SeaweedFS 14PB 挂载)。
- 下载切换到 tmux 后台脱离 Claude 管道:`tmux hf_download_libero` 拉 `nvidia/LIBERO_LeRobot_v3`(83 文件 → `/gemini/code/datasets/nvidia_LIBERO_LeRobot_v3`)、`tmux hf_download_latent` 拉 `MangoGoes/libero4in1_wan2.2vae_latent_cosmos_style`(→ `/gemini/code/datasets/MangoGoes_libero4in1_wan2.2vae_latent_cosmos_style`);命令仅 `env -u all_proxy -u ALL_PROXY` 保留 HTTP/HTTPS_PROXY 走 CONNECT 隧道,日志 `/tmp/hf_dl/libero_v3.log` / `latent.log`,不再前台测速或写监控脚本。
- 用户 SSH 端 `tmux attach -t hf_download_libero|hf_download_latent` 实时看进度。Claude 仅在阶段切换或异常时汇报,不占管道。
- 推送策略确认:父仓 V2 `79b1c54` = origin/V2 `79b1c54`,子模块 v2 `5b61762` = origin/v2 `5b61762`,**已完全同步无需 push**;本次 commit 同步 SESSION.md/TODO.md/MEMORY/DECISIONS.md D015 是为记录今晚会话。

## 当前最小步骤

- R07 最终审核结论（ChatGPT，APPROVE）：root 13af0e3 已正式关闭 G0-R07-RUNTIME-SMOKE；No-Memory exact parity、Local optimizer/update、fixed-weight Normal/Zero/Shuffle Future+Action sensitivity 均成立。raw sidecar 缺失已在 provenance 中诚实记录，不推翻 Gate；后续 R08/R09 Gate 必须在独立 review 完成前保留 raw sidecar 或文件级 SHA。

- R08 设计补充已冻结：开始任何 R08 代码前，Codex 必须先阅读 docs/build/PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md。新口径为 R08=Causal Local Evidence Stream（真实 history source/alignment/per-step evidence + stateless smoke readout），R09=Persistent Temporal Local Memory（A recurrent latent；B RoboTTT-style TTT fast weights）。R08 第一硬 Gate 是 Wan exact-window z0 suffix-invariance；Gate 未通过前禁止把 z0 当 causal historical feature。当前 LIBERO loader 尚未读取数据集已有的 observation.state 8D，必须先做 source audit 再接入。R08 不得实现 GRU/TTT/Global/Agent/RL。

- R07 provenance hygiene（Codex，DONE，无 GPU）：未能从真实 shell history、原始 `/opt/r07-smoke`/根 artifact 日志、现存 tmux pane 或 runner transcript 恢复 Gate C 精确启动命令，已在 `sensitivity_provenance.json` 诚实标记 `exact_command_recoverable=false`，未从当前配置或记忆重构。保留的 `sensitivity_ckpt5/iter_000000005` 实测完整：8 个 DCP 文件、18,132,791,947 B，model/optim/scheduler/trainer 与 metadata 的 SHA256 已回填。该 hygiene 不改变 R07 PASS；R08 GPU Gate 前置现已满足。

- R08 Step 0（Codex，DONE，只读）：`tools/g0/audit_r08_source.py` 已生成含 provenance 的 `artifacts/g0/r08/source_audit.json`。四 suite 的 `observation.state` 都是 float32 `[8]` 且有限；loader 当前仅读取 index/episode/task/timestamp/action，未读 state；state metadata 原样保留、未推断 8D 物理语义。target action 为 anchor `t` 的 `[t,t+16)`，R08 history 只能取 `j<t`。cache 为 `exact_window_v1`、17 frames、anchors `[0,4,8,12,16]`、latent `[5,48,12,20]` float32；concat 256×512 snap 至 192×320 pre-VAE canvas。mm APPROVE_TO_CLOSE、Kimi closure APPROVE，3 项审计 MEDIUM 已关闭。下一步仅可进入 R08 Gate-0 z0 suffix-invariance diagnostic；未修改模型/数据合同，未跑 GPU。

- R08 Gate-0 工具（Codex，REVIEW，无 GPU）：新增根仓 `tools/g0/verify_r08_z0_suffix_invariance.py`。它为每个 anchor 构造首帧 bitwise 相同、其余 16 帧来自另一有效 episode window 且 pixel-different 的 A/B 输入；复用 `exact_window_cache.py` 的 `to_training_uint8`/`encode_window`、当前 `VideoResize(resolution=None)` 和 Wan bf16 exact-duration 合同，只比较 latent temporal index 0。默认四 suite × `start_frame % 4` 四类 × 4 anchor = 64，对每条保存 JSON metrics 和未删的 raw z0 `.pt` sidecar/file SHA。`py_compile`、`--help` 导入、合成窗口 CPU smoke、`git diff --check` PASS；未加载 VAE、未解码真实数据、未跑 GPU。待 mm/Kimi/ChatGPT 审查工具；三方闭环前不得运行 Gate-0 GPU 或接入 LocalEvidenceEncoder/history/model/R09。

- `G0-R06/R07 override`（用户，DONE）：D017 生效：`iter_000002800` 冻结为 R06 No-Memory baseline，取消 canonical 400-episode acceptance，R07 UNBLOCKED；13-ckpt sweep 仅作趋势 evidence。未改 frozen 文档或历史 zero-shot FAIL 证据。

- `G0-R07-IMPLEMENTATION`（Codex，IN_PROGRESS）：预计修改子模块 `data_and_condition.py`、`sequence.py`、`packers.py`、`joint_dataloader.py`（`local_memory` optional collate）、`action/utils/transforms.py`（config-controlled `LocalDummyTransform` 注入 `local_memory` 与 `SequencePlan.has_local_memory`）、`omni_mot_model.py`、`cosmos3_vfm_network.py`、实际 Edge-4in1 config/test；只实现 dummy Local clean modality。A/B 比较 Vision/Action mRoPE 时按各自 modality indexes 取位置；多样本 global index 仅验证符合 packing offset，不硬编码统一 `+K_local`。Local 不进 noising/decoder/loss，不做 R08/R09；Flex disabled，legacy out-of-scope。

  - 第 1 步已完成：子模块 `0b48dae` 加入 `SequencePlan.has_local_memory`、`ActionTransformPipeline` 的默认关闭 local dummy payload、LIBERO dataset 参数透传和 `joint_dataloader` optional list/sparse collate；`py_compile` 与子模块 `git diff --check` PASS。未接 packing/network，默认关闭不会改变 baseline；下一步接 `GenerationDataClean`、packer 和 adapter。子模块已推送；根仓 Gitlink 已更新至 `0b48dae`。

  - Step 2 propagation 修复完成，ChatGPT 复审 APPROVE：ChatGPT 复核发现 `_get_velocity()` 的 `gen_data_for_packing` 重建与 `_slice_gen_data_clean()` 未传播 `x0_tokens_local_memory`。已仅修改 `omni_mot_model.py` 与既有 CPU test：重建直接保留 Local；slicing 对全 present 直接切片，对 mixed optional 则基于显式 `sequence_plans` 的 `has_local_memory` 映射选择 dense Local payload，缺映射时 fail-fast。5 项定向 CPU pytest、`py_compile`、`git diff --check` 均 PASS，ChatGPT 复审 APPROVE。未运行 GPU/checkpoint smoke，也不进入 R08/R09；下一步先盘点 iter2800 checkpoint 与既有 smoke 工具，再执行 load/no-memory parity、save/reload 与小步 sensitivity。

  - R07 runtime 首次单卡尝试（未通过完整 Gate）：系统盘副本 `/opt/Cosmos3-edge-generation-libero4in1/iter_000002800` 在 Local-enabled 新模型上成功 model-only warm-start（53.87s）；真实第 1 步 forward/backward 完成且 finite：`loss=0.854476`、vision=`0.069275`、action=`0.016173`、video global grad norm=`2.59375`。训练打印 `Done with training.` 后进程收到 `SIGKILL`，torchrun 退出码失败，疑似容器/宿主内存压力；未证实，不能判 R07 runtime PASS。未完成 No-Memory parity、Local 专项 grad、save/reload、3-10 步 sensitivity；用户决定换机器后再继续。临时 `artifacts/g0/r07/runtime_smoke/` 含日志/config/pickle，未提交。

  - R07 runtime 新机器系统盘复跑（进行中）：80 GiB GPU、64 GiB RAM 上，`/opt/Cosmos3-edge-generation-libero4in1/iter_000002800` 在 `PSM_LOCAL_DUMMY_ENABLED=1` 下 warm-start 成功；DCP 保留旧 549 个张量、新增 3 个 Local 张量新初始化。真实单步完成：`loss=0.854476`、vision=`0.069275`、action=`0.016173`、global grad norm=`2.60938`，无 NaN/OOM；`/opt/r07-smoke/local_80g_rerun/.../iter_000000001` 已于 88.11s 保存。该 checkpoint 再次从系统盘 DCP warm-start 成功（552 tensors，3.73s），随后为避免写入第二份临时模型主动终止。LIBERO 四 suite 均配置 exact-window latent cache，`latent_cache_verify_ratio=0.0`；不发生在线视频 VAE 编码。尚缺 Local 专项梯度、Local-disabled 数值/输出 parity 与 3--10 step Normal/Zero/Shuffle sensitivity；不进入 R08/R09。所有 runtime checkpoint 仅保留 `/opt/r07-smoke/`，不提交、不复制网络盘。

  - R07 runtime 收口实现（Codex，IN_PROGRESS）：预计仅改 `action/utils/transforms.py`、`action_sft_dataset.py`、`joint_dataloader.py`、Edge-4in1 config 及对应 CPU tests，并新增 `tools/g0` 的真实模型 Gate runner。runner 使用临时 worktree `cosmos-framework@5b61762` 作为 R06 old reference、当前 `c4557da` 作为 Local-capable reference，复用同一 cached LIBERO batch，写小型 JSON；不新建第二份 checkpoint。Zero dummy 必为严格全零，Shuffle 必在 collated batch 内仅置换 Local payload、绝不改变 plan/shape，也绝不在 model forward 内造数据。修改后先 CPU test/静态验证，再单卡 GPU Gate，最后交 mm 复审。

  - R07 runtime intervention 第 1 步完成：子模块 `af06827` 已推送。`LocalDummyTransform` 增加 `normal|zero|shuffle` mode；`zero` 为严格全零，`shuffle` 由 `IterativeJointDataLoader` 在 packed batch 内循环置换 present Local payload，plan/shape/None 占位不变；Edge recipe 通过 `PSM_LOCAL_DUMMY_MODE` 数据侧透传，默认 `normal`。三项定向 CPU pytest、5 文件 `py_compile`、`git diff --check` PASS；未运行 GPU。下一步新增真实跨 commit runtime runner。

  - R07 runtime optimizer Gate：ChatGPT 定位并经源码实证 Edge-4in1 深拷贝 Nano 的非空 `keys_to_select`，原先漏选 `local_memory2llm` 与 `local_memory_modality_embed`，导致三项 Local 参数冻结、真实 1-step checkpoint 仍全零。子模块 `55a9109` 仅在 Local 启用时向既有 allowlist 追加这两项，原生 7 项不变；CPU 配置合同 PASS。修复后同一 iter2800 的真实 Normal 1-step checkpoint 中 weight 65,536 个、bias/embed 各 2,048 个元素均为有限非零（`max_abs=5.002220859751105e-11`），证明 Local optimizer/update path PASS。临时 checkpoint 已删除；待 No-Memory old-vs-new parity 与 fixed-weight Normal/Zero/Shuffle sensitivity，仍不进入 R08/R09。

  - R07 No-Memory 输出级 parity（Codex，DONE）：在单卡 80 GiB GPU 上以 old `5b61762`（仅临时 capture-only instrumentation）与 Local-capable `62d77b8` 分别运行同一 `iter_000002800`、exact-window latent cache、`PSM_LOCAL_DUMMY_ENABLED=0`、`PYTHONHASHSEED=0`、`CUBLAS_WORKSPACE_CONFIG=:4096:8` 和 `--deterministic` 的一训练步。`artifacts/g0/r07/runtime_smoke/no_memory_parity.json` 为 `PASS`：8 项输入、6 项 packing/mRoPE 结构、Vision/Action prediction SHA256 均逐位相同，三项 loss 差均为 `0.0`（old/new 均 total=`1.3236993551254272`、vision=`0.10770943015813828`、action=`0.0246605072170496`）。两侧自动生成的 `iter_000000001` 临时 checkpoint 均已删除，保留 JSON/日志；这是 Local disabled 的 STRONG PASS。下一步仅为同一训练后 checkpoint 的 Normal/Zero/Shuffle sensitivity，仍不进入 R08/R09。

  - R07 fixed-weight sensitivity（Codex，IN_PROGRESS）：Gate A 已获 mm APPROVE 与 ChatGPT PASS。预计最小改动子模块 `r07_parity_capture.py`、其测试和 Edge-4in1 config，仅在显式 sidecar 环境变量下保存本步 Vision/Action velocity 与 Local payload；根仓新增比较工具。先用 Normal Local 训练 5 个 optimizer steps 保存唯一临时 checkpoint；随后从该 checkpoint 以相同 deterministic batch/noise 分别采集 Normal/Zero/Shuffle，比较 Action/Future velocity 的绝对/相对差与 Local payload 变更。训练不分别以 Zero/Shuffle 进行；所有临时 checkpoint 结束即删；不进入 R08/R09。
    - 实现/CPU 验证：sidecar 仅由 `PSM_R07_PARITY_TENSOR_OUTPUT` 显式开启，`r07_parity_capture_test.py` 4 passed；`compare_r07_sensitivity.py` synthetic Normal/Zero/Shuffle fixture PASS，`compare_r07_no_memory_parity.py` 已加 schema/field-presence fail-fast 后对原始 old/new JSON 仍 PASS；`py_compile` 与双仓 `git diff --check` PASS。待提交后由 mm 与 Kimi 同时独立审查，未启动 GPU。
    - 审查：mm 与 Kimi 均 APPROVE；Kimi 报告 `docs/build/PSM-WMA_REVIEW-R07-Gate-C-prep_2026-08-27.md`。比较器已同步对三模 invariant 加 key-presence fail-fast；GPU 结果须检查 `shuffle_present_local_count >= 2`。
    - GPU Gate C 已完成，待独立结果复核：Normal-only 5 个 optimizer update 后保存唯一 CKPT_5；三次独立重载该 checkpoint 的 Normal/Zero/Shuffle capture 均完成，临时 checkpoint 已删除。`artifacts/g0/r07/runtime_smoke/sensitivity.json` 为 PASS：14 项输入/packing/mRoPE 不变量 exact，shuffle present Local=128；Normal→Zero Vision/Action relative L2=0.010973/0.004952，Normal→Shuffle=0.009699/0.003958。mm 与 Kimi 已收到复核请求；不进入 R08/R09。
    - 结果独立复核：mm 结论 APPROVE；Kimi 结论 APPROVE（`docs/build/PSM-WMA_REVIEW-R07-Gate-C-runtime_2026-08-27.md`），无 BLOCKER/HIGH。Kimi 要求在 Gate C 正式 DONE 前补两项 MEDIUM：保留三模 raw sidecar 或记录 SHA256，及回填 provenance（commit、CKPT、命令/环境、数据/cache 路径）。用户要求本轮仅记录，未修复、未删除 `sensitivity_ckpt5/`、未启动任何新运行；R08/R09 仍禁止。
    - provenance 收口（Codex）：新增 `artifacts/g0/r07/runtime_smoke/sensitivity_provenance.json`，记录代码提交、基线/训练后 CKPT、固定权重三模重载、确定性环境、LIBERO cache、资源和验收量级。复核发现 raw sidecar 在先前临时清理时已删除，无法补文件 SHA 或离线重算；artifact 如实记录此复现限制与原路径。未运行 GPU、未改 Local 代码，待下一轮审核判定 Gate C 是否可 DONE。
    - closure review：mm `APPROVE_TO_DONE` 与 Kimi `APPROVE`（`docs/build/PSM-WMA_REVIEW-R07-Gate-C-provenance-closure_2026-08-28.md`）一致确认 R07 Gate C / runtime 可 DONE。raw sidecar 缺失保留为诚实的非阻塞复现限制；无需重跑 GPU。`G0-R07-RUNTIME-SMOKE` 已转 DONE；R08/R09 仍未启动。

  - 独立审查：`mm2` 对子模块 `0b48dae` / 根仓 `799dc91` 结论 APPROVE。默认关闭、shape/dtype、plan 标记、LIBERO 参数透传、mixed-None collate、序列化兼容与 baseline 无回归均通过；LOW：`SequencePlan.as_dict()` 当前未被业务入口调用，下一次触摸 `sequence.py` 时决定保留或删除，不阻塞 Step 2。

- `G0-R07-PRE-IMPLEMENT-REVIEW`（mm2，DONE）：对 `f238295` 只读复核结论 `APPROVE_TO_IMPLEMENT`。后续 runtime 实证已纠正其中 Edge-4in1「无 `keys_to_select`、整 backbone 训练」的旧判断：实际继承 Nano 非空 allowlist，遗漏 Local selector 已由 `55a9109` 修复；其余 D017、mRoPE、checkpoint、legacy/Flex 范围结论保持。Flex 默认 `enabled=false` 的继承证据已补齐。

- `EVAL-LIBERO-4IN1-ACCEPTANCE / PLAN`（SUPERSEDED BY D017，DO NOT EXECUTE）：driver 仅保留历史工具；禁止启动 canonical acceptance、iter2800/spatial smoke 或任何对应 GPU job。13-ckpt sweep 仅作趋势 evidence。

- 运行状态快照（2026-08-23 15:30）：训练 `tmux sft_4in1` iter ~2094/5000（loss≈1.20，~88s/步）；内存 113G/128.8G 正常；`eval_4in1` watcher 已停（用户明确不重启，200 倍数点无自动评测）；iter_000002000 上传 HF `MangoGoes/Cosmos3-edge-generation-libero4in1` 改在 `tmux hf_upload` 中运行（hf_transfer 多线程，带宽瓶颈 ~1MB/s，18.1GB 约 37% 起，日志 `artifacts/g0/hf_upload_iter2000.log`）；`plot_sft_loss.py` LR x 轴范围 2000→5000 以对齐实际 max_iter。

- `CLEANUP-20260822`（Codex/Kimi，DONE）：用户要求清理无用脚本/测试结果，先只读盘点并与 Kimi 对齐；双方确认当前 `sft_4in1`/`eval_4in1` 活跃，绝不碰子模块 `outputs/train`、`results/libero_closed_loop_4in1/iter_*`、checkpoint 或 tracked Gate 证据。已将根仓 14 个结束的临时 cache smoke/verify/first-loss 输出、旧 `artifacts/g0/online_vae_probe/`、指定 builder/smoke/verify 非追踪日志移至可恢复的同盘 `/disk/rl/psm_wma/.trash/20260822_cleanup/{outputs,artifacts_g0}/`；未永久删除。移动前后 `/disk/rl` `df` 均为 750T/611T used/140T avail（同盘移动不释放空间），trash 为 136G、根 `outputs/` 为 4KB、保留 `artifacts/g0/` 为 162MB。保留 `online_vae_probe_shared_contract/`、`latent_cache_route_probe/`、`latent_cache_mismatch_archive_20260820_v6/`、所有 tracked artifacts 与全部脚本；purge 时机由用户决定。未提交。

- `IMPLEMENT-ROBOCASA-OFFLINE-VAE-CACHE`（Codex，REVIEW）：用户已授权实现；Kimi 已审查计划 APPROVE。新增根仓 `tools/g0/exact_window_cache.py`（17 帧 shared VAE 编码、训练同顺序 uint8 转换、索引、原子写）、`tools/g0/build_cosmos_robocasa_latent_dataset.py`（atomic/composite 多根构建）、子模块 `cosmos_framework/data/generator/action/datasets/robocasa_lerobot_dataset.py`（单任务 LeRobot v2.1，三视角 float 拼接、原位 12D action/16D state 路径、四元 cache 键），并让 LIBERO windowed builder 委托 helper；runtime route probe 与 parity JSON 增加 suite/task_id。RoboCasa 视频固定 `wrist_top_agentview_lr_bottom`：腕部 256×256 顶部、左右 agentview 按 float `[0,1]` + bilinear `align_corners=False` 缩至 128×128 后底部拼为 `[T,C,384,256]`。`py_compile`（helper、两 builder、parity、Dataset、model）与双仓 `git diff --check` PASS；未启动 GPU、MP4 decode、cache build、训练或 watcher。待 Kimi 审查；随后先做 LIBERO tiny cache 重编码逐位 0 回归，之后才请求用户授权 RoboCasa tiny GPU parity。未提交。

- `EVAL-LIBERO-4IN1-PERIODIC-200`（Codex/Kimi，DONE）：按用户要求只修改 `cosmos-framework/examples/eval_libero_4in1_periodic.sh`，未触碰运行中的 `tmux sft_4in1`。已将评测 stride 250→200、每 suite `task0` 的 trial 3→1、`libero_10:2`→`libero_10:0`，并把首个 checkpoint 后轮询 10h→5h；顶部/循环注释同步为 `save_iter=50` 与 200 步。独立 server/eval 进程与 `.done` 去重不变。`bash -n`、双仓 `git diff --check` PASS，检索确认无旧 250/36000/3-trial/task2 引用；Kimi 复审 APPROVE，未启动 eval/GPU。运行侧：`iter_000000450` 保存途中受容器内存上限 SIGKILL，watcher 暂不启动；残缺 checkpoint 的清理/重启需用户明确授权。未提交。

- `UNIFY-SFT-LAUNCH`（Codex/Kimi，DONE）：用户要求统一 4in1 SFT 启动入口，未触碰运行中的 `tmux sft_4in1`。已修改 `examples/launch_sft_action_policy_libero_edge_all.sh`、`resume_sft_action_policy_libero_edge_all.sh`、`tmux_launch_sft_libero_edge_all.sh`、`tmux_resume_sft_libero_edge_all.sh` 与 `_sft_launcher_common.sh`：主入口按 checkpoints 下最大 `iter_*` 自动 resume，无 checkpoint 则冷启动，打印最近 3 项/选择项，`DISABLE_AUTO_RESUME=1` 强制冷启动；旧 resume 包装保留兼容；tmux 内联 cache root/verify/workers（默认 root、`0.001`、`36`）；`DRY_RUN=1` 只打印最终 torchrun 命令与 overrides。Kimi 审查 APPROVE；随后关闭 LOW：checkpoint 根从脚本相对 repo root 锚定，非 dry-run 在 cache root 缺失时快速失败。`bash -n`、双仓 `git diff --check` 及从 `/tmp` 调用的无 iter/有 iter/禁用自动恢复 dry-run 与缺失 cache 快速失败均 PASS（临时目录 `/tmp/tmp.XWkkMULWJS`，未启动 torchrun/GPU）。未提交。

- `OBSERVE-TRAIN-STEP-TIMING`（Codex/Kimi，DONE）：按用户要求仅增加下次 resume 生效的观测，绝不触碰运行中的 `tmux sft_4in1`，也不实现异步 prefetch。`trainer/__init__.py` 新增 `OptimizerStepTiming`，以 `time.monotonic()` 在主循环 `_fetch_data_batch` 前后记录主进程 dataloader wait，在每个 micro-batch `training_step` 前后记录 forward/backward/optimizer 的 host wall time；optimizer step 聚合总秒数、per-microbatch mean、other、step wall 与 wait/compute 占比。`StdoutLossLogger` 在 rank 0 输出 `perf/dataloader_wait_s`、`perf/model_compute_s`、mean/other/wall/pct/microbatches 的机器可解析 `key=value` 字段。无 CUDA synchronize、无 collectives、无数值路径修改。`.venv/bin/python -m py_compile`、双仓 `git diff --check` PASS；Kimi 审查 APPROVE。LOW：不做 CUDA synchronize，故这是 host wall-time 近似值，足以观测 dataloader wait 是否趋近零。未提交。

- `COMMIT-PUSH-EXACT-WINDOW-LATENT-CACHE`（Codex，BLOCKED）：本次 exact-window latent cache 已提交：子模块 `v2` 为 `dcd733b`（`feat: add exact-window LIBERO latent cache`），根仓库 `V2` 为 `23b6d7e`（`feat: add verified LIBERO latent-cache pipeline`）。静态验收 `py_compile` 与双仓 `git diff --check` PASS；未纳入训练输出、MP4/latent probe 张量和大量日志。推送先执行子模块 `git push origin v2`，被 `https://ghfast.top` 远端拒绝认证（`could not read Username`）阻断；为避免根仓库指向远端不存在的子模块提交，根仓库推送未执行。待用户提供该远端可写认证或 SSH push URL 后继续。 

- `FIX-CACHE-PARITY-RUNTIME-INSTRUMENT`（Codex/Kimi，REVIEW）：B-control 证明两次 online 首步逐位一致，而 online/cache 首步 loss 分别为 `15.709939/15.734109`，差异为真实训练在线 VAE 与 cache 的稳定信号。已仅修改 `cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py`：显式 verify 样本上从同一 raw uint8 分别计算 shared guard、训练在线等价路由和 cache，写入 `artifacts/g0/latent_cache_route_probe/` 的结构化 JSON（dtype/range/SHA256/三对 diff）；不改变 cache-only 默认路径或 fallback 行为。`cosmos-framework/.venv/bin/python -m py_compile cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py`、`git diff --check` PASS；待 Kimi 独立审查与最小 GPU 取证。未提交。

- `DIAGNOSE-CACHE-VAE-RUNTIME-CONTEXT`（Codex/Kimi，REVIEW）：1495 份训练 route probe 已证明 shared guard 与训练在线等价路由逐位一致，二者相对 cache 均差 `0.03125-0.0625`；spatial episode 0/start 0..19 亦复现，且 builder 对 start 0/1 的 raw uint8 SHA256 与训练逐位相同。已新增 `tools/g0/diagnose_vae_runtime_context.py`，在彼此隔离的子进程扫描 CUDA TF32、cuDNN deterministic/benchmark、`torch.use_deterministic_algorithms` 和 `CUBLAS_WORKSPACE_CONFIG`，以 cache 与可选训练 latent 为参照写 JSON；不修改模型、cache 或默认训练路径。`py_compile`、CLI help、`git diff --check` PASS；当前 route JSON 未保存训练 latent 张量，GPU 运行时需提供单个 b latent 给 `--online-latent` 以判定精确匹配 profile。未提交。

- `FIX-CACHE-CUDNN-BENCHMARK`（Codex/Kimi，DONE）：runtime context 扫描的 `cudnn_benchmark` profile 精确复现训练相对 cache 的 `max=0.03125/mean≈0.00172`，其余五个 profile 相对 cache 均为零；根因是框架默认 `CuDNNConfig.benchmark=True`，而训练 recipe 未覆盖。正式 `examples/toml/sft_config/action_policy_libero_edge_all.toml` 已增加 `[trainer.cudnn] benchmark=false`，并在 `configs/toml_config/sft_config.py` 增加默认保持 `benchmark=True` 的 SFT `CuDNNConfig` 与 `TrainerConfig.cudnn` 字段，使后续不带 `--deterministic` 的训练也与离线 builder 对齐；不重建 cache。`py_compile`、`git diff --check`、SFT pydantic schema 和最终 Hydra composed config 的 `trainer.cudnn.benchmark is False` 断言 PASS；Kimi 独立复审 APPROVE，训练内 1628 个 verify 样本逐位零 mismatch。未提交。

- `BUILD-LATENT-CACHE-4SUITE`（Codex/Kimi，DONE）：`/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1/` 四 suite 全量完成——Kimi 重启为 4×5 shard 并行（`tools/g0/launch_parallel_cache_build.sh`）并用 `merge_latent_cache_shards.py` 合并 manifest：432/454/428/379 episodes、246,377 窗口、54GB，契约（bf16 compute_dtype、exact_durations、chunk）齐全。未提交。

- `CACHE-TRAIN-EQUIVALENCE-TOOLS`（Codex/Kimi，DONE）：Kimi 已实跑 `cache_only_forward_smoke.py` PASS：`artifacts/g0/cache_only_forward_smoke.json` 的 3 步 forward 中 `_load_video`、TorchCodec decode、VAE interface encode、WanVAE encode 均为 0，耗时 9.49s；cwd 修复已验证有效。B 的 online/cache 首步 loss 工具不构成 latent 等价证据：固定 `--deterministic` 已令两侧 `cudnn.benchmark=False`，且 cache manifest 枚举与在线 iterable dataloader 不保证首 batch 键/顺序一致，观测到的 0.024 loss 差异不能归因 VAE。该限制已写入工具 docstring；权威等价证据为训练内 1628 样本三路逐位 0 的 `FIX-CACHE-CUDNN-BENCHMARK`。`py_compile`、`git diff --check` PASS。未提交。

- `FIX-CACHE-PARITY-VAE-CONTRACT`（Codex/Kimi，DONE）：新增 `cosmos_framework/model/generator/vision_vae.py`，作为唯一的 `uint8 RGB -> fp32[-1,1] -> VAE -> fp32 latent` 入口；模型 runtime guard、exact-window builder、probe、parity 均复用。训练 recipe 同样从该模块取得 exact-duration/chunk 配置。cache 模式默认 `LIBERO_LATENT_CACHE_VERIFY_RATIO=0.0`，dataloader 直接输出 latent，只有显式抽检才运行 VAE。manifest 新增并强校验 `vae_encode_contract`，不兼容/旧 cache 必须新建输出根重建。已通过共享入口内存测试、`py_compile` 和 `git diff --check`。2026-08-21 发现 `.venv` 内 CUDA 13 库未进入动态链接路径；为测试进程设置项目级 `LD_LIBRARY_PATH` 后，重建 `libero_spatial` episode 0（94 窗口）成功。20 窗口 GPU 证据：原始 `OmniMoTModel._normalize_uint8_vision_item -> _encode_vision_item` vs 公共入口 `max_abs_diff=0.0`，原始在线 vs 新 cache 亦为 `0.0`；`artifacts/g0/original_online_vae_vs_shared_contract.json` 与 `probe_vs_cache_parity_shared_contract.json` 均 PASS。Kimi 复审 APPROVE。未提交。

- `IMPLEMENT-ONLINE-VAE-LATENT-CACHE`（Codex，REVIEW）：Kimi 二次复审 `APPROVE`，HIGH/MEDIUM 均关闭；LOW-1 evidence 改为固定项目根 `artifacts/g0/latent_cache_mismatch/`，LOW-2 旧非窗口 R12 builder 分支已发 `FutureWarning` 禁止误用。`py_compile`、`diff --check`、layout/manifest reader PASS。GPU smoke 尚未运行：GPU 0 当前 `sft_4in1` 100%/54GiB 占用，避免冲突；待训练空闲后执行 cache 训练 3–5 步及在线路径 loss/shape 对照。未提交。

- `BUG-LIBERO-SAMPLE-STRIDE`（Codex，DONE）：用户确认改用 exact-window latent cache；训练采样保持 stride=1，不修改 `sample_stride` 实现。未提交。

- `BUG-R06-PRED-MP4`（Codex，REVIEW）：已确认 `results/libero_closed_loop_iter100/.../mp4_pred` 的 prediction JSON 每次返回 17 帧，而 MP4 仅 1 帧；根因是双视角输入帧为 512×256、模型预测帧尺寸不同，OpenCV 对后续尺寸不匹配帧静默拒写。已在 `cosmos-framework/cosmos_framework/simulation/libero/closed_loop_eval.py` 的预测视频导出循环中，将尺寸不同的预测帧双线性缩放到输入帧尺寸后再写入。`.venv/bin/python` 临时导出验证 PASS：512×256 MP4 共 17 帧；`py_compile`、`git diff --check` PASS。`uv run` 未执行，因已有 `pyproject.toml` 的 `[tool.uv.audit]` 字段不被当前 uv 识别。当前子模块含来源不明的既有未提交修改，且本修复与其处于同一代码块，未提交；待独立审查。

## 当前阶段

G0 Foundation。先完善并执行 R01-R06，建立可复现的 `Cosmos3-Edge-Policy-DROID -> LIBERO` 无 Memory baseline；R06 PASS 前不进入 Memory 算法实验。

## 当前事实

- 正式设计主线为 Temporal Local Memory 与 Spatial Global Memory 两个独立 optional clean modalities。
- 项目以 `cosmos-framework` 为工程母体；优先新增项目模块，只对 `SequencePlan`、`PackedSequence`、packer 和 Generator adapter 等必要扩展点做集中最小修改。
- 双仓库分支基线已切换，当前为「父仓库 `V2` + 子模块 `v2`（官方代码）」组合，详见下文「双仓库分支基线（2026-08-18）」；原 fork 研究线保留为「父仓库 `main` + 子模块 `main`」。
- `docs/build/log/kimi_operation.log` 是 Kimi 的执行日志，已确认纳入版本控制；其他 Agent 只追加自己的真实操作，不覆盖已有记录。
- 已拉取另一 Agent 的文档一致性修改。该交付修改了 5 份现有正式文档，但没有新增或完善可执行的 R01-R06 Runbook。
- Kimi 记录 `/gemini/code/models/Cosmos3-Edge-Policy-DROID` 已于 2026-08-12 16:08 下载完成；Codex 已按权重索引完成完整性预检，全部引用文件存在且非空。
- 项目 Python 环境已安装到 `/root/venvs/psm_wma`（Python 3.13.13）；大包优先从 `/gemini/code/packages/` 本地安装，Megatron-LM 与 lerobot 使用本地源码快照 override，已规避 Git TLS 中断。当前 GPU 已可见，CUDA 最小张量运算通过。
- 所有 Agent 执行代码、测试、训练、推理或评测前，必须先向用户展示目的、完整命令、工作目录、环境变量、资源/外网需求、输入、产物和判据。
- arXiv:2608.11246 已纳入后续 W10/W11 Agent Harness 高优先级参考，详细记录见 `docs/build/PSM-WMA_Agent_Harness_reference_addendum_v0.1.md` 与 `MEMORY/DECISIONS.md` D007；该参考不改变当前 G0/R01-R09 执行顺序。

### 双仓库分支基线（2026-08-18）

为「保持与 fork 官方代码一致」新建 `v2` 分支并切换，两个仓库当前状态如下。

**psm_wma（根仓库，`/disk/rl/psm_wma`）**
- `origin` → `https://github.com/wxwy/psm_wma.git`
- 分支：`main` 与 `V2` 均在 `5a7bfd3`（`main` 跟踪 `origin/main`）
- 当前检出：`V2`（由 `git branch V2` 创建，未切换当前分支的历史已并入本次切换）
- 树内 `cosmos-framework` 子模块指针：`927e147`（与 `main` 相同）
- ⚠️ `927e147` 当前**无法从任何远程取回**（fork 上已无此 ref/对象），无法把子模块工作区恢复到该 commit。

**cosmos-framework（子模块，`/disk/rl/psm_wma/cosmos-framework`）**
- `origin` → `https://ghfast.top/github.com/wxwy/cosmos-framework.git`（fork）
- `upstream` → `https://ghfast.top/github.com/NVIDIA/cosmos-framework.git`（官方，2026-08-18 新增，与 fork 同走 ghfast.top）
- 分支：
  - `main` = `69f2260`，跟踪 `origin/main`（fork 研究线：regular episode latent plan 等）
  - `v2` = `326b399`，跟踪 `upstream/main`（官方 NVIDIA 代码，创建自官方 main）
- 当前检出：`v2`（`326b399` "Add guidance interval to RoboLab policy server (#202)"）
- 同步官方更新：`git checkout v2 && git pull upstream main`

**组合与后续操作**
- 官方基线 = 父 `V2` + 子模块 `v2`（当前）；fork 研究线 = 父 `main` + 子模块 `main`。
- 父仓库 `git status` 会显示 `M cosmos-framework`：父树记录 `927e147`，子模块工作区为 `326b399`（官方 v2），差异是预期现象，非误改。
- 若要把父 `V2` 的 gitlink 固定到官方 `326b399`：`git add cosmos-framework && git commit`（需用户确认，勿自动提交）。
- 子模块 `v2` 尚未 push 到 fork `origin`。

### 本机执行环境（2026-08-18，新机 `/disk/rl/psm_wma`）

与旧机器（`/root/venvs/psm_wma`、`/gemini/code/models`）不同，本机为全新环境，2026-08-18 已就绪：

- 环境：uv 0.12.5 + Python 3.13.7，`cosmos-framework/.venv`（uv sync `--extra train --group=cu130-train`，395 包）→ torch 2.10.0+cu130，A100-SXM4-80GB，CUDA 13.0，`cosmos_framework` 导入 OK。
- 视频解码依赖 torchcodec：运行前需 `export LD_LIBRARY_PATH=<venv>/lib/python3.13/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH`（否则报 `libnppicc.so.13` 缺失）。
- 数据：`/disk/data/libero.zip`（1.86G，LeRobot v2.1 布局，`stats_gr00t.json`）**无法被官方 v2 代码读取**（官方要求 v3.0 布局：`data/chunk-*/file-*.parquet` + `meta/episodes/chunk-*/*.parquet` + `meta/tasks.parquet`）。已改下官方 `nvidia/LIBERO_LeRobot_v3/libero_10`（602M，内容与 libero.zip 相同：379 集/101469 帧/20FPS/7D action）→ 官方 `LIBEROLeRobotDataset` 验证通过（`action (16,10)` rot6d + quantile_rot，视频 256×512 concat，9.1s 加载 375/379 集）。`LIBERO_ROOT=/disk/data/LIBERO_LeRobot_v3/libero_10`。
- action 语义实证：存储 action 即逐帧 delta（命令空间），`state_delta ≈ action × 0.012`（sim 内部 action_scale），gripper 绝对 0/1；**无需绝对→差分转换**，官方 `_build_frame_wise_action` 仅重编码旋转（axis-angle→rot6d）。
- 存储：`/disk/data` 在 30G overlay（余 ~8G）；`/disk/rl` 挂载 `/bitahub-member`（750T，余 124T）；`/localdisk-tmp` 全新 100G nvme（0 使用）。**权重勿放 `/disk/data`，放 `/disk/rl/psm_wma/.../examples/checkpoints/` 或 `/localdisk-tmp`。**
- 权重缺口：本机**无任何模型权重**（旧机器 `/gemini/code/models` 有 Cosmos3-Edge 6.3G / Edge-Policy-DROID 8.6G）。HF 可直连：Edge-Policy-DROID 9.17G、Cosmos3-Nano 34.99G 均可下。
- 官方 v2 LIBERO SFT 仅支持 Nano（`action_policy_libero_nano.py`，HSDP 2×8）；Edge 仅 `edge_model_config.py` 无 LIBERO 动作配置——Edge→LIBERO 需自建配置（SESSION 底部 D006 已预告）。

### Edge-Policy-DROID -> LIBERO 新确认

- NVIDIA 官方 LIBERO recipe 是从 bare `Cosmos3-Nano` 做 LIBERO SFT，不是从 `Cosmos3-Nano-Policy-DROID` 继续微调；因此不能把 Nano-Policy-DROID 当作官方 LIBERO 起点。
- Nano LIBERO 的数据/动作/闭环评测合同可作为 Edge 迁移基线：20 Hz、`agentview+wrist` concat、10D `frame_wise_relative` rot6d、`quantile_rot`、action chunk 16，并保留官方 gripper / 图像朝向 / normalization parity 检查。
- `action_policy_libero_nano.py` 直接基于 `NANO_MODEL_CONFIG`，不能只替换 checkpoint 路径用于 Edge。Edge 版本应以 `EDGE_MODEL_CONFIG` 为模型基线，再迁移 LIBERO-specific dataset/action/eval 设置。
- 官方公开的 Nano DROID recipe 属于 Generator-side Full SFT，而不是 action-head-only。公开 selector 包括 `moe_gen`、`time_embedder`、`vae2llm`、`llm2vae`、`action2llm`、`llm2action`、`action_modality_embed`。
- 结合 Cosmos3 policy post-training 论文、官方 cookbook 与 Nano DROID recipe，可高置信推断 `Cosmos3-Edge-Policy-DROID` 也经历了大规模 Generator-side policy specialization；但 NVIDIA 未公开 Edge-Policy-DROID 发布 checkpoint 的 exact `keys_to_select`，不得把 Nano selector 写成 Edge 官方事实。
- 若仅把公开 Nano selector 映射到 Edge 参数结构，derived estimate 约为 1.423B trainable、约占 4B 的 35.6%。这是项目估算，不是 NVIDIA 官方 Edge 数字。
- 默认保留 `Edge-Policy-DROID` 已学到的 shared Generator / world-action coupling。R03/R04 的核心待决策项是 DROID `action2llm` / `llm2action` / `action_modality_embed` 与 embodiment domain 在 LIBERO 10D action space 下如何继承、新建 domain 或部分重初始化。
- R02 先做零大权重下载的 metadata/config/index audit；只有仍存在会改变 R04 初始化策略的关键未决问题时，才按需下载 bare Edge 的必要 transformer shard 做 Edge vs Edge-Policy-DROID tensor diff。`Cosmos3-Nano-Policy-DROID` 完整权重不作为当前依赖。
- bare `Cosmos3-Edge` 已位于 `/gemini/code/models/Cosmos3-Edge`（仅 `transformer/` 权重，约 6.3GB）；`Cosmos3-Edge-Policy-DROID` 为完整 HF 推理包（约 8.6GB，含 VAE/vision encoder/tokenizer/scheduler）。两库用途分工见 `MEMORY/DECISIONS.md` D009。

## 正在进行

| 任务 | 负责人 | 状态 | 预计修改文件 | 备注 |
|---|---|---|---|---|
| DOC-R01 | Codex | DONE | `docs/build/PSM-WMA_G0_R01_implementation_runbook_v0.1.md`、`tools/g0/collect_r01_gate_json.py` | Kimi 二轮复审 APPROVE，已关闭全部审查项 |
| G0-R01 | Codex | DONE | `artifacts/g0/r01/`、`tools/g0/`、`cosmos-framework` 最小 guardrail 开关 | Gate JSON `PASS`；用户批准 RoboLab 基础设施豁免，已放通 R02/R03 |
| DOC-R02 | Codex | DONE | `docs/build/PSM-WMA_G0_R02_checkpoint_audit_runbook_v0.1.md` | Kimi 独立审查 APPROVE；MEDIUM-1 与 LOW-1/2/3/4 已关闭，Runbook 状态 `reviewed` |
| G0-R02 | Codex | DONE | `tools/g0/audit_r02_checkpoints.py`、`artifacts/g0/r02/R02_edge_policy_checkpoint_audit.json` | metadata/config/index audit PASS；provenance 完整，warm-start 边界已冻结 |
| DOC-R03 | Codex | DONE | `docs/build/PSM-WMA_G0_R03_action_contract_runbook_v0.1.md` | Kimi 独立审查 APPROVE；2 MEDIUM + 3 LOW 已关闭或按范围转交，Runbook 状态 `reviewed` |
| G0-R03 | Codex | DONE | `tools/g0/audit_r03_action_contract.py`、`artifacts/g0/r03/R03_action_contract.json`、`cosmos-framework@3b4a929` | 真实 LIBERO runtime contract、参数拆分与 stats provenance PASS，并通过独立审查 |
| DOC-R04 | Codex | IN_PROGRESS | `docs/build/PSM-WMA_G0_R04_forward_loss_runbook_v0.1.md` | 独立版本化 Runbook；不与 R03 混入同一提交 |
| G0-R04 | Codex/Kimi | DONE | `tools/g0/r04_step_metrics.py`、`tools/g0/verify_domain_rows.py`、`artifacts/g0/r04/adamw_nonfused_20step/` | 非 fused AdamW 连续 20 步 PASS；机器可读 loss/资源/domain 行保护证据和末次 checkpoint 完整 |
| DOC-R05 | Codex | DONE | `docs/build/PSM-WMA_G0_R05_tiny_overfit_runbook_v0.1.md` | 已经独立审查与实执验收，状态 `reviewed` |
| G0-R05 | Codex/Kimi | DONE | `artifacts/g0/r05/R05_libero_tiny_overfit.json`、R05 审查报告 | Gate `PASS`；100 步训练、两次 reload、checkpoint 完整性和独立验收全部通过 |
| DOC-R06 | Kimi | REVIEW | `docs/build/PSM-WMA_G0_R06_closed_loop_baseline_runbook_v0.1.md` | 已创建并经实执验证；两处偏差（RLinf venv、TRITON_LIBCUDA_PATH）待升 v0.2 |
| G0-R06 | Kimi | REVIEW | `artifacts/g0/r06/`、`docs/build/PSM-WMA_REVIEW-G0-R06_closed_loop_2026-08-15.md` | Gate `FAIL_SR_ZERO`：链路全绿、逐位可复现，但 zero-shot SR=0/3；待用户决策 baseline |
| G0-R06-SFT-E4 | Kimi | DONE | `artifacts/g0/r06/gradient_flow_probe/probe.py` | E4 PASS：vae2llm/early moe_gen action/vision grad ratio 1.6-2.3，信号能回流，非结构性阻断；产物 `result.json`；恢复训练至 1000 步后复测 |

## 最近完成

- 阅读 `docs/build` 五份核心文档及 `cosmos-framework/AGENTS.md`。
- 核对 `SequencePlan`、`PackedSequence`、Cosmos3 Generator adapters 和 LIBERO dataset/config 的现有扩展基础。
- 完成 `COLLAB-BOOTSTRAP`，建立根目录协作协议、会话状态、任务队列和长期决策文件。
- 拉取并审查 `c428d46`、`42c6a13`；Local/Global 配置、代码结构和 runtime import 核对方向正确。
- 审查 `82892f3`：RoboTTT 被限制在 R06 PASS 后的 R09 backend 候选，未侵入 G0 Foundation 顺序；独立 Local compressor 的集成边界合理。
- 完成 `/root/venvs/psm_wma` 全量依赖安装；uv 解析 431 个包，本轮安装 286 个包，无新的未落地 >100MB 组件。
- 将 `cosmos-framework` 从 `5d6dedc` fast-forward 到 `upstream/main@103c5d1`；上游变更不包含 `pyproject.toml` 或 `uv.lock`，无需重装环境。
- 根据 Kimi `REVIEW-R01` 首轮 `REQUEST_CHANGES` 修订 Runbook：补齐 Reasoner warmup/steady timing、Reasoner/Policy VRAM 采样、RoboLab 响应证据契约、真实产物层级、preflight 日志、commit 自动断言及 provenance 字段；新增独立 Gate JSON 汇总脚本。
- Kimi `REVIEW-R01` 二轮结论 `APPROVE`；追加 LOW N1/N2 已修复为独立请求数不足标签和可配置 port/seed/num_steps provenance，N3 通过定向暂存排除 `__pycache__`。
- 确认 Nano LIBERO official recipe 与 Nano/Edge model config 的边界，并收敛 Edge-Policy-DROID -> LIBERO warm-start 原则；详见 `MEMORY/DECISIONS.md` D006。
- 新增 arXiv:2608.11246 Agent Harness 参考增补并登记 D007；其作用域限定为 W10/W11，不提前影响 G0 或 Memory Gate。
- 完成 G0-R02 metadata/config/index audit：复用支持入口对旧 Edge 导出 K-Norm 根索引的既有兼容逻辑，冻结 Edge-Policy-DROID -> LIBERO warm-start 与数据契约边界。
- Kimi 对 G0-R02 独立审查结论 `APPROVE`；关闭 MEDIUM-1（Gate provenance）与 LOW-1/2/3/4（LIBERO 证据锚点、vision extra keys、R01 load 证据复用措辞、Runbook 状态）。

## 验证记录

- R01 checkpoint 完整性预检 PASS：`cosmos_framework_model.safetensors`、两个 Transformer 分片和 `vision_encoder/model.safetensors` 均存在且非空；另确认 VAE 权重存在。
- 环境验收 PASS：PyTorch `2.10.0+cu130`，CUDA 可用，GPU 小张量运算结果正确；LIBERO、robosuite、lerobot、Megatron Core、Ray、OpenCV 和 OpenPI 导入通过。
- cuDNN 路径根因已定位：`nvidia/cu13/lib` 会命中不兼容的 cuDNN 9.0；将 `/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cudnn/lib` 放在 `LD_LIBRARY_PATH` 首位后，PyTorch 报告 cuDNN `91501`，Policy server CLI 导入及参数解析 PASS。
- 已知例外：`openpi-client==0.1.2` 元数据要求 `numpy<2.0`，而项目 `[tool.uv].override-dependencies` 为 LIBERO/numba 要求 `numpy>=2.0,<2.3`，实际安装 `numpy==2.2.6`；`uv pip check` 因此报 1 条元数据不一致，OpenPI 运行时导入已通过，未修改项目配置。
- Gate JSON 汇总脚本最小验证 PASS：`py_compile` 通过；空证据生成 `BLOCKED`，完整有效伪证据生成 `PASS`，peak VRAM、cuDNN `91501`、warmup/steady latency 与请求级 latency 映射断言通过。Ruff 未执行，原因是环境和 uv 缓存均无 Ruff，未为文档任务新增依赖；`git diff --check` 通过。
- 追加 LOW 复测 PASS：空证据为 `BLOCKED`，完整证据为 `PASS`，仅 1 个 timed request 为 `FAIL_INSUFFICIENT_REQUESTS` 且不再误报 nonfinite；自定义 port/seed/num_steps 准确写入 `run_config`。
- G0-R01 Phase A PASS：checkpoint 索引及 VAE 资产完整，固定 `cosmos-framework@103c5d1`，PyTorch `2.10.0+cu130`/cuDNN `91501`/CUDA 可用。
- G0-R01 Reasoner PASS：实际输入为 `Describe a modern robotics research laboratory in one sentence.`；warmup `14.59s`，3 次稳态 `13.23/13.38/13.40s`，平均 `13.34s`，显存采样峰值约 `6.76GiB`，输出非空且无 NaN/Inf。
- G0-R01 Policy/World PASS：4090 24GB 上加载本地 `Wan2.2_VAE.pth`；1 warmup + 2 timed 请求均返回 finite action `[32,8]` 和 uint8 world video `[33,528,640,3]`，稳态 latency `5961.4/6002.9ms`，峰值显存 `13.69GiB`。Gate JSON 状态 `PASS`、无 blocker/exception；预览视频为 `artifacts/g0/r01/policy_world_preview.mp4`。
- G0-R01 runtime drift：当前云 GPU 只在实际使用时向监控接口报告占用，因此新增 PyTorch CUDA 显存采样器；Policy server 默认 guardrails 改为关闭，显式 `--guardrails` 才启用；checkpoint training config 缺 `_type`，server 回退到 `ActionTransformPipeline(format_prompt_as_json=True)`。
- G0-R01 RoboLab override：真实 `BananaInBowlTask` 启动到 Isaac Sim，但 Orion 虚拟 GPU 的 CUDA/Vulkan/PhysX 设备无法一致映射，报 `No device could be created`，未进入闭环。2026-08-14 用户明确批准 R01 按 Reasoner、Policy action、shared Generator/world smoke 放通；该决定不等同 RoboLab PASS，R06 LIBERO closed-loop 门槛保持不变。
- RoboTTT 文档审查保留项：独立 compressor 下的 TTT-KVB objective、multimodal evidence 到 K/V token 的构造、官方代码/许可证/依赖复用边界尚未冻结；R09-A/B 还需 matched 参数量、训练步数、token budget 和计算预算，不能仅凭“primary candidate”提前选择。
- RoboTTT 文档治理问题：继续直接修改 `frozen/locked` 文件，虽增加 Addendum，但版本号未升级；后续正式冻结应生成新版本，而不是继续累积覆盖。
- 文档审查发现：R01-R06 只有目的、检查和 PASS 摘要，缺少精确命令、完整前置资产、源码入口、逐 Gate 修改文件、统一断言、失败分流和回填清单，不能直接执行。
- 文档治理发现：提交直接修改 `frozen/locked` 文件但未升级版本或增加对应修订记录。
- 一致性残留：技术调研第 10 章仍写“Local/Goal persistent state”；Static Audit 仍保留 `K_local/K_goal/K_psm` 旧字段。
- Edge->LIBERO warm-start 事实分级已明确：官方事实、项目高置信推断、derived estimate、待 R03/R04 实证项分开记录。
- arXiv:2608.11246 当前仅按后续 Agent 参考记录；W10/W11 启动前要求重新核验一手论文/代码，不把当前概括当作冻结实现事实。
- 已确认工作目录：`/gemini/code/psm_wma`。
- DOC-R01 主提交：`dde7621`。
- Edge vs Edge-Policy-DROID 对比（Codex 结构+分层抽样，2026-08-13；Kimi header 级复核，2026-08-14；R02 索引复核，2026-08-14）：base Transformer 为 549 个规范键；Policy-DROID 原始根索引含 56 个 K-Norm 条目（28 个错误旧别名 + 28 个 overlay 条目），项目支持入口会全部移除并从 transformer 子索引补回 28 个规范 K-Norm，最终有效 Transformer 键集同为 549。共同张量 0 shape 不匹配，仅 4 个 `time_embedder` 张量 BF16→FP32（约 +9.4MB），`action_proj_in/out`、`action_modality_embed` 两边都有。Codex 数值变化结论（`moe_gen`/action 模块已改写、`embed_tokens`/普通 norm 未变）仍为分层抽样证据，未宣称全量数值 diff。
- G0-R02 验证 PASS：审计产物 `status=PASS`，原始根索引 1014 键、支持入口有效索引 986 键、有效缺失 0；原始 K-Norm 56 = 错误旧别名 28 + overlay 28，合并 transformer 子索引后规范 K-Norm 28。`py_compile`、JSON 关键断言和 `git diff --check` 均通过；Policy 实际加载/推理证据复用 G0-R01。限制：`cosmos_framework.inference.model` 已兼容该旧导出，`inference2/_model_io.py` 尚未同步，当前不得用后者加载此 checkpoint。
- G0-R02 审查收尾复测 PASS：JSON 增加 UTC 时间、repo/cosmos commit、脚本 SHA-256、argv/run_config；LIBERO 契约逐项带官方 recipe 行号；vision encoder 6 个未索引 projector header 键完整列名。`py_compile`、provenance/契约/extra-key JSON 断言与 `git diff --check` 通过。
- G0-R03 本地 LIBERO schema 兼容：现有 20Hz 数据使用 `tasks.jsonl` / `episodes.jsonl` / `episode_*.parquet`，与 loader 原先只接受的 parquet metadata / `file-*.parquet` 布局不一致；`cosmos-framework@59653c5` 增加原格式优先、JSONL/per-episode fallback，并给 `video_path.format` 补 `episode_index`，未改变 action/video 语义。
- G0-R03 真实 LIBERO SFT 样本 PASS：本地 `libero_10_no_noops_1.0.0_lerobot` 加载 379 episodes、95,405 个有效窗口；样本 video `[3,17,192,320]` uint8，action `[16,64]`、`action_raw` `[16,10]`，`raw_action_dim=10`、`domain_id=5`、20Hz、finite、WAM `SequencePlan`。TorchCodec 需在启动命令中把环境内现有 `nvidia/cudnn/lib` 与 `nvidia/cu13/lib` 加入 `LD_LIBRARY_PATH`；无需下载或修改系统配置。
- G0-R03 正式审计 PASS：真实 action 链为 parquet `[16,7]` → rot6d `[16,10]` → `quantile_rot` `[16,10]` → model `[16,64]`；DomainAwareLinear shape smoke 为 64→2048→64 且 finite。按 Policy-DROID header 与官方 selector 实算 trainable `1,423,379,648`；纯 Transformer 为 `3,369,657,024`，selected 占 42.24%；含 vision encoder `412,649,712` 后 model 总计 `3,782,306,736`，selected 占 37.63%。
- R03 warm-start 冻结：LIBERO 使用独立 domain 5，DROID 为 domain 8；继承 shared Generator/time/vision adapters 与 `action_modality_embed`，保留其他 domain 权重，仅重初始化并更新 action projection 的 domain 5 行。R04 必须验证 optimizer step 前后其他 domain 行不变，避免 AdamW weight decay 漂移。
- R03 已知语义限制：LIBERO dataset 已完成 `quantile_rot` 后，通用 transform 将该 10D 张量保存为 `action_raw`；训练输入没有重复归一化，但字段名并非 parquet 原始 7D，R04 前需决定修正文档还是接口。
- Kimi 对 G0-R03 独立审查结论 `APPROVE`：MEDIUM-1 已通过参数分母拆分关闭；MEDIUM-2 已记录 stats 路径与 SHA-256，并转为 G0-R05 前置分布 sanity check；LOW-1 新增 JSONL/per-episode fallback 单测（`cosmos-framework@3b4a929`，1 passed）；LOW-2 Runbook 转 `reviewed`；LOW-3 provenance 语义已显式记录。
- G0-R04 配置阶段：Policy-DROID 已离线转换为 `/gemini/code/models/Cosmos3-Edge-Policy-DROID-dcp`（2026-08-14 自 `/root/models/psm_wma/` 迁入，与源 checkpoint 同级；R04 TOML 经 `BASE_CHECKPOINT_PATH` 环境变量引用，无硬编码路径），包含两个 DCP shard、总计 6.3GB；首次转换因 processor 指向 HF repo 在 offline 模式失败，改用 R01 已验证的本地 processor override 后成功，未修改 checkpoint。
- G0-R04 新增 `action_policy_libero_edge_warmstart` 与单步 TOML（`cosmos-framework@1c0c691`）：复用 Nano LIBERO 数据合同，模型切换为 `EDGE_MODEL_CONFIG`，保留 Policy-DROID action heads，关闭 EMA/compile，并对两个 domain-aware action projection 禁用 weight decay。配置解析、`compileall`、定向 Ruff 与 `git diff --check` PASS。
- 当前 CUDA runtime 仅暴露 1 张 `B4.gpu.large`、25.24GB；R04 将先尝试 1 sample/1 step，若 OOM 记为资源 BLOCKED，不归为代码 FAIL，并在可用 A100/多卡上续跑正式 20–50 steps。
- G0-R04 4090 单卡真实训练诊断：本地 processor、Wan2.2 VAE、LIBERO train split（375/379 episodes、94,250 valid indices）和 DCP 549/549 keys 均加载成功；optimizer 实测选中 294 tensors / 1,423,379,648 elements，其中两个 domain-aware projection 的 4 tensors / 8,456,192 elements 正确进入 `WD=False` 组。forward 与 backward 已完成，finite global grad norm 为 `52.75`；首次 `optimizer.step()` 创建 FP32 Adam 二阶状态时 OOM（23.45/23.51GiB 已用、仅余 58.05MiB、再申请 72MiB 失败）。该结果判定为 4090 资源 BLOCKED，不是代码 FAIL；完整 20–50 steps 需 A100 或多卡 FSDP。
- R04 启动中关闭了离线 smoke 不需要的 W&B basic callback（`cosmos-framework@321afc4`），保留 NaN/grad-clip/device-monitor；原因是当前 wandb 版本无 `wandb.util.generate_id`，且 `wandb_mode=disabled` 时上游 basic callback 仍无条件初始化 W&B。
- 切换 A100 节点后，用户指定将 `/root/venvs/psm_wma` 改为 Python 3.11 + PyTorch 2.7 cu128。旧 Python 3.13/cu130 环境完整备份于 `/root/venvs/psm_wma_py313_cu130_backup`；原路径已建立 Python 3.11.8 环境并从 `/gemini/code/packages/` / `uv-cache-robolab` 离线恢复 torch `2.7.0+cu128`、torchvision `0.22.0`、Triton `3.3.0` 和匹配 CUDA 12.8 运行库。Orion 的只读 NCCL 文件挂载残留在旧 `lib/python3.13` 子目录，不进入新 Python 3.11 site-packages。
- 新节点底层 PCI 为 A100，但 Orion 对当前进程暴露为 `P1.gpu.medium`、39.17GiB。Python 3.11 / torch `2.7.0+cu128` 在不手工设置 CUDA/NCCL `LD_LIBRARY_PATH` 时，最小 `.cuda()` 张量实测 PASS（`cuda:0`，`sum(x²)=14.0`）。此前 exit 151 / `not enough ratio` 与时变 GPU 配额未激活有关（调度层证据）；`LD_LIBRARY_PATH` 是否干扰 Orion 加载链未单独证实，当前成功路径为干净激活环境，后续不注入 CUDA/NCCL 路径。
- 新环境候选 `/root/venvs/psm_wma_py313_cu128` 已完成 Python 3.13.13 + PyTorch `2.10.0+cu128` + CUDA 12.8 核心安装；本地 25 个核心 wheel 哈希通过。`uv pip check` 通过，`torch/flash_attn/natten/megatron.core/transformer_engine/lerobot/datasets/pandas/pyarrow/wandb` 导入和 CUDA 张量验证通过。R04 TOML 在设置 `BASE_CHECKPOINT_PATH`、`WAN_VAE_PATH`、`EDGE_POLICY_CHECKPOINT`、`DATASET_PATH`、`LIBERO_ROOT`、`IMAGINAIRE_OUTPUT_ROOT` 后解析 PASS。配置预检过程中补齐了 `iopath`、MSC 纯 Python 包及其运行依赖、`qwen-vl-utils`、`webdataset` 等小依赖；未自动下载超过 50MB 的新包。当前仍未切换 `/root/venvs/psm_wma` 正式入口，待 R04 单步训练验证。
- G0-R04 py313/cu128 重试：从 `cosmos-framework/` 工作目录并使用实际 LIBERO 数据集根启动后，模型/VAE、DCP 549/549 keys、LIBERO 375/379 episodes、forward、backward 和 finite grad clip 均成功；在 FusedAdam 首次创建 optimizer 状态时再次收到系统 `SIGKILL (-9)`。关闭 DataLoader worker（`num_workers=0`, `prefetch_factor=null`）后仍复现，GPU 约 8.5GiB/40GiB，判定为当前主机内存/资源 BLOCKED，不是代码或 CUDA OOM。日志：`artifacts/g0/r04/py313_cu128_r04_retry_final.log`。
- Kimi R04 中期复核确认容器 `memory.max=34359738368`（32GB）；后续可选缓解包括申请更大容器内存、让 optimizer 状态直接在 GPU 创建，或采用 8-bit optimizer，具体方案待 R04 续跑时决定。

## 下一交接

1. G0-R04 已完成：非 fused AdamW 连续 20 步 PASS；后续若扩展训练，优先接入 R12 latent 缓存或启用 `num_workers>=2`，避免 CPU 视频解码瓶颈。
2. R04 执行器必须在 DCP load 后重初始化 domain 5 行，并验证 optimizer step 前后其他 domain 行不变；`action_raw` 当前按“已归一化的原始维度 action”记录，不在 R04 改公共接口。
3. 后续分别新建版本化 R04-R06 Runbook，不扩写 frozen/locked 文档；同时修复两处残留旧口径，并用新版本/修订记录处理 `frozen/locked` 文档治理问题。
4. G0-R05 启动前完成本地 action 分位数与内置 stats q01/q99 的分布 sanity check。
5. W10/W11 启动时读取 `PSM-WMA_Agent_Harness_reference_addendum_v0.1.md`，复核 arXiv:2608.11246 后再决定 scene/context 与 execution-evaluation 接口是否进入实现。

### G0-R04 正式验收（2026-08-15，Kimi 执行，Codex 验收）

- 产物：`artifacts/g0/r04/adamw_nonfused_20step/{step_metrics.jsonl,domain_row_guard.json,R04_gate.json,train_20step.log}`；终审报告 `docs/build/PSM-WMA_REVIEW-G0-R04_final_nonfused_2026-08-15.md`。
- Codex 复核：`R04_gate.status=PASS`、20 行 metrics 且 iteration 1–20 连续、loss/grad 全 finite、`domain_row_guard.pass=true`、冻结行 bitwise diff=0、domain 5 均更新、末次 checkpoint `iter_000000020` 的 model/optim/scheduler/trainer 四目录齐全；两个新增工具 `py_compile` 通过。
- 数值：loss `16.4969→13.6540`，grad norm（clip 后）最大 `1.00498`；GPU 分配峰值 `34270.6 MiB`，RSS 峰值 `19,954,976 KB`，无 OOM/SIGKILL。
- 结论：G0-R04 正式 Gate `PASS`，任务状态 `DONE`。后续扩展建议使用 R12 latent 缓存或 `num_workers>=2`，当前瓶颈为 CPU 视频解码。
### G0-R04-ADAMW（单步完成，Kimi APPROVE）

- 最小修改：`cosmos-framework/cosmos_framework/utils/generator/optimizer.py` 仅对标准 `Adam`/`AdamW` 允许 `fused=False`；`FusedAdam`、Muon/Dion2 等 fused-only 路径仍拒绝非 fused。
- 验证：`python -m py_compile`、`git diff --check` 通过；R04 单步从 DCP load、forward/backward、grad clip 到 `optimizer.step()` 均完成，日志出现 `Done with training.`。
- 结果：loss/梯度路径未出现 NaN/Inf；checkpoint 已保存至 `/gemini/code/psm_wma/artifacts/g0/r04/adamw_single_step_retry2/psm_wma/g0_r04/edge_libero_forward_loss/checkpoints/iter_000000001`（约 12GB）。
- 资源：GPU 峰值约 `40192/40488 MiB`（99.3%）；训练进程 RSS 峰值约 `16,497,588 KB`（约 15.7GiB）。此前 32GB 容器 SIGKILL 未复现。
- 限制：这是 1 step 诊断，不等同 R04 20–50 steps PASS；正式审查报告为 `docs/build/PSM-WMA_REVIEW-G0-R04_adamw_nonfused_review_2026-08-15.md`。
- Kimi 审查保留：MEDIUM-1 资源峰值尚未写入机器可读产物；LOW-1 单步 loss 未记录；LOW-2 已在本次记录中清理过时的暂停 PID 口径。三项均不阻止本次单步 APPROVE。

### G0-R12-CACHE（已完成，Kimi 核验通过）

- 任务状态：DONE；实际修改 `tools/g0/build_cosmos_rgb_latent_cache.py`、`MEMORY/DECISIONS.md`、`SESSION.md`、`TODO.md`。
- 设计事实：离线 RGB 编码严格复用 Cosmos `OmniMoTModel._encode_vision_item`，按 camera clip 独立 VAE encode，使用 uint8→[-1,1] 归一化，camera-major temporal 拼接；禁止逐帧独立编码。
- 全量完成（Kimi，2026-08-15）：379/379 episode 成功、零错误；产物 `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_latent` 约 1.2G；`dataset_manifest.json` 为 `episode_count=379`、`image_size=256`、`script_revision=8c9b443`。
- 独立核验：抽查 12 个 episode 的 latent 全部 finite；379 个 episode 全部满足 `latent_frames = 1 + ceil((video_frames - 1) / 4)`；日志 `artifacts/g0/r12/full_dataset_cosmos_image256.log`。编码进程两次被外部 SIGSTOP，均 SIGCONT 无损恢复并正常退出。
- 验证结果：真实 LIBERO RGB `[3,17,192,384]` → latent `[48,5,12,24]`，finite；工具路径与 Cosmos 直接 batch 路径 `max_abs=0.0`、shape 完全一致。Kimi 审查发现并已修复 image_size 默认值、manifest 续跑丢失、非原子写入、uint8 rounding、provenance 和完整 instruction 保存。修复后用 `--image-size 256` 完成 1 个 episode：原始 `[3,214,256,512]`，按 Cosmos `4n+1` 规则补到 217 帧，得到 `[55,48,16,32]` FP16 latent，源帧映射 `[55]`，原文指令已保存；产物位于 `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_latent/episodes/episode_000000.pt`。`py_compile` 与 `git diff --check` PASS；全量 379/379 已完成并由 Kimi 核验。

### G0-R05（DONE，Kimi 终审 APPROVE）

- stats 前置审计：扫描本地 379 个 parquet、101,469 帧，按 Cosmos axis-angle→rot6d 路径比较内置 `global_raw` q01/q99；10D 全 finite，最大 `[-1,1]` 外尾比例 `0.0306892 < 0.10`，`artifacts/g0/r05/R05_action_stats_sanity.json` 为 PASS。
- 新增确定性 tiny subset：训练 flat index `[0,1,2,3]` 循环，held-out index `4`；索引实测五个窗口均为 episode 0/task 0，互不重叠且不随机 shuffle。
- 新增 R05 分项指标：每步 total/action/vision loss、由 rectified-flow 恒等式推导的 detached `action_x0_reconstruction_mae`、grad、GPU peak、RSS；第 100 步和完整 checkpoint reload 后各记录一次 held-out。
- 新增 `action_policy_libero_edge_tiny_overfit` 与 R05 TOML；100 steps、EMA off、AdamW `fused=false` 由命令 override，checkpoint `iter_000000100`。
- 轻量验证：所有新增/修改 Python `py_compile` PASS；固定 subset 循环、x0 MAE 公式、TOML 生效配置和 `git diff --check` PASS。pytest 未执行，原因是当前 py313/cu128 环境未安装 pytest；已保留对应单测供 Kimi 审查环境执行。
- Runbook：`docs/build/PSM-WMA_G0_R05_tiny_overfit_runbook_v0.1.md`，包含 stats、100-step、reload consistency、Gate collector 的完整命令和判据。
- Phase B 实行：100/100 步 loss/grad 全 finite、趋势阈值全部达标，`iter_000000100` 四件 checkpoint 完整；步后 held-out 验证暴露 `OmniMoTModel.validation_step` 空桩，Kimi 标记 HIGH-1 / REQUEST_CHANGES。
- HIGH-1 修复：`cosmos-framework@fbe85a0` 在既有 `@torch.no_grad()` 下复用 `training_step` 的完整前向/损失路径，返回 trainer 要求的 `(output_batch, total_loss)`；未新增损失实现或改动训练语义。
- 修复验证：`py_compile`、dummy 返回值透传/无梯度断言、`git diff --check` 全部 PASS；真实 GPU reload 未由 Codex 重复执行，交 Kimi 复审后从 Phase C 续跑。
- HIGH-1 复审：Kimi 结论 APPROVE；Phase C 首次 reload 已成功读取 model 549 keys / optimizer 4410 keys，但暴露 HIGH-2：单进程 NCCL 对非 capturable AdamW 的 CPU `step` 标量做多余 broadcast 而崩溃。
- HIGH-2 修复：`cosmos-framework@8421e41` 在 `_broadcast_state_dict` 入口对 `world_size == 1` 直接返回；单 rank 是所有叶子唯一 reader，DCP 已读全状态，因此无需任何补全广播，多卡分支未改动。
- HIGH-2 定向验证：`py_compile` PASS；mock world size 1 且将 tensor/object broadcast 设为调用即失败，含 CPU AdamW `step` 的嵌套状态原样保留且零 collective；`git diff --check` PASS。真实 checkpoint reload 交 Kimi 复审后续跑。
- 最终验收：`artifacts/g0/r05/R05_libero_tiny_overfit.json` 为 `PASS`、`failures=[]`；100/100 步全 finite，total/action/action-x0/vision ratio 分别为 `0.705/0.745/0.735/0.285`；GPU 峰值 16653.5 MiB，RSS 峰值 12.3 GiB，checkpoint 四件齐全。
- Phase C 两次独立 reload 均恢复 iteration 100，held-out 四项逐位一致，`max_abs_diff=0.0`；Codex 独立解析 Gate/JSONL 并核对 DCP metadata/shard，结论 PASS。
- 已记录 deviation：实跑使用 `max_samples_per_batch=1` / `grad_accum_iter=32`；Phase B held-out 因 HIGH-1 未产出，Gate 以两次 iteration-100 确定性 reload 做一致性比对。
- 非阻塞遗留 MEDIUM-3 已转 `DCP-MULTIRANK-RELOAD` 并写入 `MEMORY/DECISIONS.md` D011：正式多卡 reload 前必须修复 CPU optimizer 叶子与 NCCL backend 不匹配。

### G0-R06（Gate FAIL_SR_ZERO，2026-08-15，Kimi 执行）

- 端到端闭环链路验证 PASS：RLinf venv(py3.11, mujoco 3.8.1, robosuite 1.4.1, libero 0.1.0 editable)+ EGL 离屏渲染；policy server(py313/cu128）直载 Edge-Policy-DROID 原始 HF checkpoint,domain_name="libero"(domain 5),10D frame_wise_relative rot6d,chunk 16。
- 两处环境修复已记录：`.r06_sim_pkgs` wheel 版 libero 遮蔽 editable 且缺 assets（已改名禁用，`/root/.libero/config.yaml` 指向 RLinf 资产）;server 端 triton `libcuda.so.1` 缺失，用 `TRITON_LIBCUDA_PATH=/opt/orion/orion_runtime/gpu/cuda` 修复（首轮 BLOCKED 证据归档 `artifacts/g0/r06/eval_task0_failed_triton/`)。
- 正式结果：libero_10 task 0 × 3 episodes，全部 520 步满 rollout、error=null、action 全 finite(3×520×7D)，但 SR=0/3；同 seed 0 重跑逐位一致（max_abs_diff=0.0)。server 193 次 /predict 稳态中位 1714ms/chunk,GPU 观测 9544 MiB。GIF 目视：机械臂悬停移动，未抓取任何物体。
- Gate JSON `artifacts/g0/r06/R06_libero_closed_loop.json`:status=FAIL,failures=[FAIL_SR_ZERO]；报告 `docs/build/PSM-WMA_REVIEW-G0-R06_closed_loop_2026-08-15.md`。
- 判读：zero-shot baseline 在 domain 5 未经 LIBERO 训练的发布 checkpoint 上不成立；SR>0 需用户重新决策 baseline（正式 LIBERO SFT checkpoint)。
- 用户决策（2026-08-15 晚）:R06 改为正式 LIBERO SFT baseline（新任务 G0-R06-SFT);zero-shot SR=0 作为诊断记录保留，其 Gate 证据 `R06_libero_closed_loop.json` 与 `eval_task0*/` 不得修改；SFT baseline 另出新 Gate JSON/报告，与 zero-shot 明确区分。

### G0-R06-SFT 探针(2026-08-16 凌晨,Kimi 执行)

- Probe 1(5 步显存,在线 VAE)PASS:5/5 步,GPU 步峰值 33.1 GiB,RSS 8.6 GB,稳态 75-130 s/step,loss 15.6→13.7 正常。
- Probe 2(latent parity)FAIL:latent max_abs_diff=4.625;连 start%4==0 对齐窗口 diff 仍有 1.79,证明 R12 整段因果编码切片≠17 帧独立窗口编码。cache 不启用,正式训练走在线 VAE。
- 正式 500 步训练预计 10-18 小时,待用户授权后启动。产物:`artifacts/g0/r06/sft_baseline/{probe,parity}/`,详见 `docs/build/PSM-WMA_REVIEW-G0-R06-SFT_code_review_2026-08-16.md`。

### 文件认领(2026-08-16,Kimi)

已全部提交并解除认领(根仓 `efed1ff`、cosmos `3e44d15`)。历史认领文件：`tools/g0/build_cosmos_libero_latent_dataset.py`、`cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py`(仅 cache 注入 dtype)、`docs/build/PSM-WMA_RGB_representation_and_memory_encoding_plan_v0.1.md`(新增)、`MEMORY/DECISIONS.md`、`SESSION.md`、`TODO.md`。

### G0-R06-SFT 口径切换(2026-08-16 下午,Kimi 第一技术审查者)

- 探针结论:Probe1 显存 PASS(在线 VAE,33.1GiB/75-130s每步);Probe2 parity FAIL,R12 整段因果编码≠17帧窗口独立编码(diff 4.625,对齐窗口仍1.79)。
- 契约核查:mowa 主线也是整段因果(其推理用流式 encoder 自洽);Cosmos LIBERO 在线/推理是单 vision item concat_view [3,17,256,512]→5 latent,从不启用 per-camera 路径。Codex 的 f7fe84c/19e0bd3 双视角复制版对新旧契约都不成立,REQUEST_CHANGES 后**暂停**(降级为回退路径)。
- 新方向:冻结文档 `cosmos-framework/docs_zh/psm_wma/REGULAR_EPISODE_LATENT_OVERFIT.md`(8fb48a9/69f2260),Kimi 评审 APPROVE,风险点=视觉 token 网格变化、闭环 oracle O(t) 成本、Codex 周额度 9%。
- 当前:Codex 按 §13 第 1 步实现 regular_episode_latent reader + 单测,Kimi 待复审。

### exact-window cache 阶梯验证(2026-08-16 晚,Kimi 执行)

- 方向确认:主线 = Cosmos-native exact-window offline cache(plan v0.1 + D013);REGULAR_EPISODE 降级历史候选;Codex regular_episode 工作已停止并清理。
- 代码修复(Kimi,未提交):builder 补 uint8→[-1,1] 归一化;cache 注入保持 fp32;parity 改独立在线参照;latent_cache 缺 episode 文件回退在线;schema_version=exact_window_v1。
- 阶梯1 parity:diff=0.0 逐位一致(5 窗口覆盖 start%4 全类);阶梯2 单 episode 构建 198 窗口 97.5MB;阶梯3 对齐 198/198 全对;阶梯4 cached forward 3步 PASS(iter1 与在线逐位一致,iter2/3 ~3e-5 漂移记 LOW);阶梯5 多 worker loader PASS(RSS 1.5GB)。
- 产物:`/gemini/code/data/libero/exact_window_v1_smoke/`、`artifacts/g0/r06/exact_window_v1/`。

### DS/Codex 第二审查跟进与阶梯4b(2026-08-16 深夜,Kimi 执行)

- DS 第二审查 APPROVE,附 MEDIUM-1/2、LOW-1/2;Codex 对修复 diff 复审 APPROVE。
- MEDIUM-1:builder 与 parity 参照从 `torch.round` 改为截断,逐位对齐在线 `base_dataset.py:214`;smoke cache 重建(705 窗口)后 parity ep0/ep18 重跑 diff=0.0。
- MEDIUM-2:阶梯4 表述更正为"混合 batch 全批在线回退的重现";补阶梯4b 全批 cache 命中 forward(tiny_overfit_num_samples=16):16/16 命中、3/3 finite、~50s/步(在线 ~120s),PASS。
- LOW-1:REGULAR_EPISODE_LATENT_OVERFIT.md 加 SUPERSEDED BY D013 横幅;LOW-2:外层 ActionLatentCacheDataset 跳过重复查询。
- 启动方式记录:torchrun 直启脚本路径会被 `cosmos_framework/scripts/hydra.py` 遮蔽 hydra 包,必须 `-m cosmos_framework.scripts.train`。
- 提交:cosmos-framework `3e44d15`,根仓 `efed1ff`(未 push)。
- 方案A(已完成):libero_10 task0 全量 exact-window 编码完成,产物 `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_exact_window_v1/`(命名约定 `<源数据集名>_cosmos_exact_window_v1`;38 ep / 9199 窗口 / 4.3GiB fp32,script_revision=a9c5a90);Kimi 核验 PASS,DS(Claude 监督)开箱检查 PASS(与 smoke3 ep0 逐位一致 198/198);smoke3 已按约定删除;训练侧经 `LIBERO_LATENT_CACHE_ROOT` 引用,不硬编码。下一步:500 步正式 SFT 待用户授权启动。
- 文件认领解除:本轮 Kimi 编辑文件均已提交,无持锁文件。

### G0-R06-SFT 训练/评测任务错位发现与 iter300 闭环(2026-08-17 上午,Kimi 执行)

- **任务错位(重要偏差)**:训练侧 `task_index=0` 是 LeRobot `tasks.jsonl` 顺序(马克杯/盘子:"put the white mug on the left plate and put the yellow and white mug on the right plate");仿真侧 `--task_ids 0` 是 LIBERO benchmark map 顺序(soup+sauce→basket, LIVING_ROOM_SCENE2)。证据:`/gemini/code/RLinf/.venv/libero/libero/libero/benchmark/libero_suite_task_map.py:38` 的 libero_10 列表第 5 项(index **4**)才是马克杯任务。**之前 zero-shot R06 评测(FAIL_SR_ZERO)与 iter300 首测测的都是模型未训过的 soup 任务;zero-shot 的 SR=0 结论受此偏差影响,但其"发布 checkpoint 在 LIBERO domain 5 无零样本能力"的定性不变。**
- iter300 对齐重测(task_ids 4,3 episode,seed 0):**SR=0/3**;3 episode 均 520 步满 rollout、error=null、action 全 finite(520×7D);GIF 目视机械臂有目的性移动、逼近目标马克杯区域,但未完成抓取/放置。判读:链路正确、任务对齐后行为明显改善(对比 soup 任务的盘旋),iter300(~8.5 epoch)欠训练,非错位或管线问题。产物 `artifacts/g0/r06/eval_task4_iter300_sft/`;错配首测留档 `eval_task0_iter300_sft/`。
- 1000 步正式训练已恢复(tmux r06sft,same-job 从 iter 301 续训,最新完整 checkpoint iter_000000300);计划到 1000 步后用 `--task_ids 4` 复测,中途可在 400/500 checkpoint 加测。
- 评测口径冻结:后续所有 R06-SFT 闭环评测必须使用 `--task_ids 4`(与训练 task_index 0 对齐),并在报告中注明该映射证据。

### G0-R06-SFT iter500/600 评测、OOM 与视觉输入错位修正(2026-08-17 下午,Kimi 执行)

- iter500 闭环评测(task_ids 4×3,seed 0):SR=0/3,链路全通、action finite;与 iter300 同 seed 行为类别一致(悬停不抓取)。zero-shot 原版 DROID 对照:SR=0/3,行为=远离桌面大幅游荡(mean|a|=0.82 vs SFT 0.24),证实 SFT 有效拉向任务。产物 `eval_task4_iter500_sft/`、`eval_task4_zeroshot_droid/`。
- 14:28 训练遭 memcg 32GB OOM SIGKILL(dmesg 实锤:shmem-rss 10.5GB + checkpoint 写网络盘 page cache 叠加);按用户条件删除 iter100-400(释放 48GB,保留 500/600);加 sync 守护每 180s flush 脏页。
- **视觉输入错位(重要修正)**:此前全部闭环评测(zero-shot/iter300/iter500)用 `--camera agentview` 单视角 256×256,而训练是 `camera_mode: concat_view`(agentview|wrist 横拼 256×512,latent [5,48,16,32])。iter600 起评测口径改为 `--camera agentview,wrist` 双视角对齐。
- iter600 双视角评测:**SR=0/3**,3 episode 均 520 步满 rollout、error=null、action finite(mean|a|=0.207);初判"抓取+举起"经用户质疑后**复核更正**:iter600 vs iter500 执行动作 mean|diff| 仅 0.062-0.073、前 60 步逐维均值几乎一致,同帧抽图(200/450 步)两臂姿态相同——均为**悬停在红色花纹马克杯上方未抓取**,双视角对齐后行为无显著变化;且红杯不在任务指令内(指令=白杯→左盘、黄白杯→右盘),疑似 fixation 错误目标。判读:输入错位与训练量均非已证实根因;iter1000 复测若仍 SR=0 立即转契约排查(open-loop 专家动作回放+目标对象核验),不再加步数。产物 `eval_task4_iter600_sft/`(含 comparisons 对比 MP4)。
- 评测后以 4 workers × prefetch_factor 1 从 iter_000000600 same-job 续训(tmux r06sft):实测 48s/步≈2×2 速度,RSS 仅 3.4GB(较 4×2 的 13GB 大降,memcg 安全);resume 从 trainer 保存态 iteration 603 起,loss/grad 连续正常,GPU 36.9GB/100%。
- iter700 horizon=4 诊断(用户假设:只执行前4步):**SR=0/3,与 horizon=16 相同且复跑一致,开环漂移非主因,坐实策略内容问题**;动作 finite,mean|a|=0.157。产物 `eval_task4_iter700_sft_h4/`(384 个逐窗口 17 帧预测 MP4,双编号 win+step,采集时渲染 GT=蓝框/PD=红框)。评测后从 iter700 续训(21:09)。结论更新:horizon、视觉视角均已排除,iter1000 复测仍 0 则转 open-loop 专家回放契约排查。

### G0-R06-SFT E4 梯度流探针交接(2026-08-17,Kimi)

- 训练已暂停在 iter811(前次完整 checkpoint iter800)。
- E2 teacher-forced 探针结论：真实视觉 vs 黑帧 action 单步去噪 MAE 几乎无差异(0.3146 vs 0.2768)，排除推理采样问题，指向训练侧 vision→action 信号未学会。
- DS 提议 E4「双分支梯度流探针」：分别 backward action-only 和 vision-only loss，比较 action2llm / vae2llm / early moe_gen 的 grad norm 比值。
- 自行实现 `artifacts/g0/r06/gradient_flow_probe/probe.py`；已修复 CheckpointOverrides 字符串路径和 `action_processing_record` collate 问题。
- 最新运行(PID 3933871,日志 `run2.log`)失败于 `pack_text_tokens`：`shifted_text_ids` 是 `int` 而非 `list`，根因为 `_load_and_tokenize_text_data` 期望 `text_token_ids` 为 `[[tensor]]`，而 `custom_collate_fn([item])` 只给出 `[tensor]`，嵌套层级少一层。
- 修复方案：把 `_collate_one` 改为用 `torch.utils.data.DataLoader` 取 batch，并手动把 `text_token_ids/video/action/action_raw` 从 `list[Tensor]` 重包为 `list[list[Tensor]]`，完全复现训练 JointDataLoader 输出格式。
- 运行结果（iter800 checkpoint，单 sample，teacher-forced）：
  - action_loss=0.699，vision_loss=0.131
  - action-only 总 grad norm=10.74，vision-only=5.31
  - action2llm 阳性对照非零（0.58），llm2action 非零（2.27）
  - **vae2llm ratio=1.61，layers.0/1/2 *moe_gen ratio=2.29/2.25/1.77，layers.0 全层 ratio=2.23**
- 判读：按 DS 矩阵，ratio ~1 → **信号能回流到视觉编码层与早期 gen tower，非结构性阻断**；问题指向优化/先验/loss 曲面。
- 决策：**暂不恢复训练**；等待 DS 对 E4 结果做进一步判读，共同完成问题定位后再决定是否继续训练/调整 LR/schedule/改配置。
- 产物：`artifacts/g0/r06/gradient_flow_probe/result.json`
- 交接文件：`docs/build/PSM-WMA_HANDOFF_R06_E4_gradient_flow_probe_2026-08-17.md`。

### 新机环境准备：Edge-Policy-DROID → DCP 转换（VAE 本地化，2026-08-18）

- 任务：简化 SFT 方案。不预编码训练数据，用原始官方 cosmos 代码 + 原始 libero 数据 + 在线 VAE + 在线 action transform。基座 = 本地 `/disk/rl/models/Cosmos3-Edge-Policy-DROID`（9.2G，Edge 官方 HF 包）。
- 关键障碍：DCP 转换时 `Wan2pt2VAEInterface` 经 `download_checkpoint_v2`（checkpoint_db.py:461）把 `vae_path="pretrained/tokenizers/video/wan2pt2/Wan2.2_VAE.pth"` 解析进 registry → 走 HF 下载 `Wan-AI/Wan2.2-TI2V-5B/Wan2.2_VAE.pth`。本机 HF 受限（socksio/hf_transfer 缺失），且用户要求不下载、直接用已有的。
- 已有的 VAE 只有 Edge 包里的 diffusers 布局 `vae/diffusion_pytorch_model.safetensors`（AutoencoderKLWan，`encoder.conv_in`/`down_blocks.*`/`norm_out`/`conv_out`… 196 keys），而原生 `WanVAE_` 要 Wan-native 布局（顶层 `conv1/conv2`=quant/post_quant，`encoder.conv1`/`downsamples.*`/`head`…，同为 196 keys，与 diffusers 0% 键名重叠）。
- 解决：`tools/g0/convert_vae_diffusers_to_native.py` 纯键重映射（不做权重转换、不下载）。规则全按阶段位置对应（encoder 4 downsample 14/18/18/12、decoder 4 upsample 22/22/22/20、mid 17），末级无 downsampler/upsampler 用存在性守卫跳过。校验：映射与 native 键集双向全等 + 全部 196 shape 一致 + `load_state_dict(strict)` 0 missing / 0 unexpected。
- 产物：`examples/checkpoints/wan22_vae/Wan2.2_VAE.pth`（1.4G，196 keys）——恰为官方 launcher 默认 `WAN_VAE_PATH`（`_sft_launcher_common.sh:52`），后续训练直接可用。
- 转换用相对路径短路：临时在 repo 根建 `pretrained/tokenizers/video/wan2pt2/Wan2.2_VAE.pth` 软链（4 级上溯到上面产物），`download_checkpoint_v2` 的 `os.path.exists` 分支直接返回本地路径，完全绕过 registry/HF。转换后已 `rm -rf pretrained` 清理。
- DCP 产物：`examples/checkpoints/Cosmos3-Edge-Policy-DROID-dcp/`（6.3G，2 分片 `__0_0.distcp`/`__0_1.distcp` + config.json + .metadata + checkpoint.json），`convert_model_to_dcp.py` exit 0。
- 关于「为什么旧机器 codex 没遇到 VAE 布局问题」的核查（fork main vs v2 完全一致）：
  - `edge_model_config.py` 两分支同为 `bucket_name=""`（L128）+ `vae_path="pretrained/tokenizers/video/wan2pt2/Wan2.2_VAE.pth"`（L137）；launcher 默认 `WAN_VAE_PATH=examples/checkpoints/wan22_vae/Wan2.2_VAE.pth` 也一致。
  - 旧机器 `/gemini/code/models/Wan2.2-TI2V-5B/` 有原生 Wan2.2_VAE.pth，R01-R06 的编码/训练/转换全部命中本地文件；Edge 包里的 diffusers VAE 只在 fork main 的 inference 侧（`inference/common/checkpoints.py` AVAE shim 只针对 **audio** VAE，与 Wan 视频 VAE 无关）被消费。原生 cosmos 代码从不读 Edge 包的视频 VAE → 布局不一致从未暴露。
  - 本机无原生文件且禁止下载，唯一来源是 Edge diffusers VAE，故需转原生布局。转换产物落在 launcher 默认路径，与旧机器走的是同一条代码路径。

### LIBERO 数据源核查：v2.1 vs v3.0 内容同源但布局不同，框架只认 v3.0（2026-08-18）

- 背景：`datasets/libero` 软链原指向老 `/disk/data/LEROBOT_LIBERO_DATA`（v2.1，四套），发现问题后核查两数据源。
- **数据内容逐位一致**：老 v2.1 与新 v3.0 的 libero_10 同 episode action/state `np.array_equal` 全等（ep0/10/378，max|Δ|=0），同为 379 episodes / 101,469 帧 / 10 tasks / fps 20；本质同一份 LIBERO 数据。
- **封装布局不同**：老 v2.1 = `meta/tasks.jsonl` + 每 episode 一个 parquet/mp4；新 v3.0（gr00t 风格）= `meta/tasks.parquet` + `meta/episodes/` + 分块 `file-*.parquet`/`file-*.mp4`。
- **当前框架 loader（v2/326b399）只支持 v3.0 布局**：`base_dataset.py:73` 读 `meta/tasks.parquet`、`_episodes` 读 `meta/episodes/chunk-*/file-*.parquet`、`libero_lerobot_dataset.py:146` 帧索引 glob `data/chunk-*/file-*.parquet`；老 v2.1 实例化报 `FileNotFoundError: meta/tasks.parquet`。注释明示同时兼容 v2.x/v3.0 的 task 列形态（v2.x 在 "task" 列、v3.0 在 DataFrame index），但文件布局仅 v3.0。
- 动作表示：两份 parquet 的 7D action 均为逐帧增量 `[dpos(3), drot_axisangle(3), gripper(1)]`（**不是 rot6d**）；loader 在线把 axis-angle 转 rot6d → 10D `[pos(3), rot6d(6), gripper(1)]`（`_build_frame_wise_action` + `libero_pose_utils`），归一化用内置 `libero_native_frame_wise_relative_rot6d.json`。v3 实测：`video (3,17,256,512) uint8` + `action (16,10)` 完整样本通过（含视频解码）。
- 处置：`datasets/libero` 软链 → `/disk/data/LIBERO_LeRobot_v3/libero_10`（实测经软链加载 375/379 episodes / 94250 窗口 OK）；README 已同步。v3 目前仅 libero_10 一套，缺 object/spatial/goal（老 v2.1 目录四套留作同源备查）。


### G0-R06-SFT 最新状态（2026-08-20，Kimi 复核）

- **训练已切换为 4-suite 联合 SFT** (`action_policy_libero_edge_all`)，不再使用 exact-window offline cache 单任务路线。当前在 `tmux sft_4in1` 中运行，从 `iter_000000275` resume，已跑到 **iter 290**（日志最新 12:40:56）。
- **首次非零闭环 SR**：iter 250 对 4 个 suite 的固定任务评测，`libero_spatial` task 0（black bowl → plate）**1/3 = 33.3%**；`libero_object`、`libero_goal`、`libero_10` 仍为 0。产物 `cosmos-framework/results/libero_closed_loop_4in1/iter_000000250/`。
- **iter 275 曾崩溃**，resume 后 num_workers 从 36 降到 30，速度从 ~144 s/iter 降至 ~170 s/iter，目前稳定。
- **loss 未记录问题（ds 反馈）**：根因是 `action_policy_libero_edge_all`/`action_policy_libero_edge_warmstart` 为避免 W&B 初始化而移除了 `basic` callback group，导致 `train/loss` 及子 loss 未写入日志。已新增 `StdoutLossLogger` callback 并接入这两个实验配置；`py_compile`、config smoke、functional smoke 均 PASS。
- **当前未提交改动**：
  - `cosmos_framework/callbacks/stdout_loss_logger.py`（新增）
  - `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py`
  - `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_warmstart.py`
  - 4 个 launch 脚本中的 `LIBERO_ROOT` 路径从 `/disk/data/...` 改为 `/disk/rl/...`（环境路径调整）
- **生效前提**：代码修改对正在运行的训练进程不生效，需 stop 当前 `sft_4in1` 并重新 resume 才能从后续迭代开始记录 loss。iter 0–290 的 loss 已无法恢复。
- **下一步**：待用户决定是否立即 restart/resume；若继续跑到 iter 300 checkpoint 再重启，可保留当前进度并减少中断。

- **BUG-4IN1-LOSS-LOG 修复验证（2026-08-20）**：13:18 从 iter_000000300 resume 后，`StdoutLossLogger` 已生效。首次 loss 日志（iter 301）：`iteration=301 | train/loss=1.731282 | flow_matching_loss_vision=0.108888 | flow_matching_loss_action=0.064241`。后续每 iter 都会记录 total/vision/action loss。相关代码修改尚未提交。

- **num_workers 恢复为 36（2026-08-20）**：用户要求将 dataloader workers 从 30 调回 36（prefetch_factor 保持 3），并重新从 iter_000000300 resume。实测 iter 301→302 耗时约 168s，与崩溃前速度接近；loss 记录正常：`iteration=301 | train/loss=1.653492 | ...`、`iteration=302 | train/loss=1.620743 | ...`。训练继续运行。

- **在线 VAE 探针设计文档已提交 Codex 审查（2026-08-20）**：文档位于 `docs/build/PSM-WMA_REVIEW-online_vae_probe_design_2026-08-20.md`，TODO 中新增 `REVIEW-ONLINE-VAE-PROBE` 任务，状态 `REVIEW`，负责人 Codex。待 Codex 批准后再进入实现。

---

## 🔔 Handoff to Codex

@Codex：请审查 `docs/build/PSM-WMA_REVIEW-online_vae_probe_design_2026-08-20.md`（在线 VAE 探针设计方案）。对应 TODO 任务 `REVIEW-ONLINE-VAE-PROBE` 已分配给你，状态 `REVIEW`。

审查重点：
1. Hook 点 `OmniMoTModel._encode_vision_item` 是否是在线路径的正确黄金基准；
2. callback 包装方式是否优雅、是否应避免 core model 修改；
3. 采样策略（200 样本、覆盖 `start_frame % 4`）是否足够；
4. 对比指标 `max_abs_diff < 1e-4` 是否严格；
5. 集成后的运行时校验开关设计是否合理。

请按项目审查惯例给出 `APPROVE` / `REQUEST_CHANGES` / `REJECT` 结论，并附 `file:line` 级意见。审查通过后我会进入实现。

- **Codex 审查通过 online VAE probe / latent cache 设计（2026-08-20）**：Codex 通过 tmux 回传确认，结论 APPROVE。关键决议：采用方案 A（dataloader 输出 `video_latent` `[5,48,16,32]`，模型检测到后跳过 `_normalize_video_databatch_inplace` + `_encode_vision_item`）；`source_frame_indices` 改名为 `window_frame_indices`（完整 17 帧），5 个 latent 锚点另存 `latent_source_frame_indices`；probe 在 batch-start 捕获归一化前 uint8；离线构建验收 `max_abs_diff<=1e-6`，runtime guard `verify_ratio=0.01`、阈值 `<=1e-5`；失配单样本 fallback 并写结构化证据到 `artifacts/g0/latent_cache_mismatch/`。当前状态：设计冻结，等待用户授权进入实现。

### Kimi 对 IMPLEMENT-ONLINE-VAE-LATENT-CACHE 二次审查（2026-08-20）

- **结论**：`REQUEST_CHANGES`。当前实现不能启用真实 cache 训练；修复前禁止切换 `sft_4in1` 到 cache 路径。
- **审查产物**：`artifacts/g0/REVIEW_IMPLEMENT_ONLINE_VAE_LATENT_CACHE_2026-08-20.md`。
- **关键缺陷**：
  - **HIGH-1**：`libero_lerobot_dataset.py:356` cache-hit 占位视频形状为 `[T,C,H,W]`，与在线路径 `[C,T,H,W]` 不一致，会导致 `_get_temporal_positions_vision` 读取错误的 `num_pixel_frames`。
  - **HIGH-2**：`omni_mot_model.py:3891-3897` 消费 cache latent 时只 `unsqueeze(0)`，未把 dataset 输出的 `[5,48,16,32]` permute 成在线路径的 `[1,48,5,16,32]`，会直接抛 `ValueError`。
  - **HIGH-3**：runtime guard / 单样本 online fallback / 结构化失配证据完全未实现，与设计决议不符。
  - **MEDIUM-1**：`cosmos-framework/tools/g0/verify_latent_cache_parity.py` 与 `build_cosmos_libero_latent_dataset.py` 不存在（目录仅 `.gitkeep`）。
  - **MEDIUM-2**：manifest 未显式包含 `suite`，且未校验 `chunk_length/camera_mode/sample_stride/fps`。
  - **MEDIUM-3**：`online_vae_probe.py` 在 cache 命中时因 `video` 已被替换为零占位，无法捕获真实 uint8 做 parity。
- **当前训练**：`tmux sft_4in1` 仍在跑在线 VAE，未受工作区改动影响；cache 路径因上述缺陷尚不可启用。
- **下一步**：Codex 修复 HIGH/MEDIUM 后，Kimi 复审并跑最小 GPU smoke（cache 训练 3-5 步，与在线路径比对 loss/shape）。

### Kimi 对 IMPLEMENT-ONLINE-VAE-LATENT-CACHE 二次复审（2026-08-20）

- **结论**：`APPROVE`，附 2 项 LOW。
- **已确认修复**：
  - HIGH-1 系 Kimi 首轮误判：`_build_result()` 会把输入 `[T,C,H,W]` permute 成 `[C,T,H,W]`，Codex 保留 `[T,C,H,W]` 占位并加注释，定向合同 PASS；Kimi 关闭该审查项。
  - HIGH-2：`omni_mot_model.py:3893-3897` 对 cache `[5,48,16,32]` 做 `permute(1,0,2,3).unsqueeze(0)` 得到 `[1,48,5,16,32]`，与在线路径一致。
  - HIGH-3：dataset 新增 `latent_cache_verify_ratio`（recipe 默认 0.01），抽样样本保留真实 RGB；model 在线 encode、比较 shape/dtype/finite/max_abs_diff<=1e-5；失配单样本 fallback 并写 JSON 到 `artifacts/g0/latent_cache_mismatch/rank_xx`。
  - MEDIUM-1：builder / parity 工具位于项目根 `tools/g0/`（非子模块 `cosmos-framework/tools/g0`），文件存在且 `py_compile` PASS。
  - MEDIUM-2：manifest 写入并校验 `suite/chunk_length/camera_mode/sample_stride/fps/latent_shape`。
  - MEDIUM-3：`online_vae_probe.py` 仅采集 `verify_cached_latent=True` 的真实 RGB 样本。
- **LOW-1**：mismatch evidence 路径 `Path("artifacts/g0/latent_cache_mismatch")` 相对 cwd；训练从 `cosmos-framework/` 启动，证据会落在 `cosmos-framework/artifacts/g0/...`，建议改为项目根 `artifacts/g0/...`。
- **LOW-2**：builder 非 `--windowed` 分支仍沿用旧 R12 schema 且无 `schema_version`，建议显式 deprecated/移除或加警告，避免误用于 exact-window recipe。
- **静态检查**：`py_compile` 与 `git diff --check` 均 PASS。
- **下一步**：可安排不与 `sft_4in1` 冲突的最小 GPU smoke（cache 训练 3-5 步，与在线路径比对 loss/shape）。

### Kimi 确认 Codex 关闭 LOW-1/2（2026-08-20）

- LOW-1 已关闭：`omni_mot_model.py:3925-3926` 使用 `Path(__file__).resolve().parents[4] / "artifacts/g0/latent_cache_mismatch"`，固定到项目根。
- LOW-2 已关闭：`tools/g0/build_cosmos_libero_latent_dataset.py:184-189` 对非 `--windowed` 分支发出 `FutureWarning`，明确禁止用于 exact_window_v1 cache 训练。
- `py_compile` / `git diff --check` 复测 PASS。
- GPU 0 当前被 `tmux sft_4in1` 占用（100%/54GiB），GPU smoke 待训练空闲后再执行。

### 4-suite exact-window latent cache 构建启动（2026-08-20）

- **任务**：后台串行构建 `libero_spatial`、`libero_object`、`libero_goal`、`libero_10` 的 exact_window_v1 latent cache。
- **后台任务 ID**：`bash-3fiaxclu`（已因 tiny-subset smoke 被 Kimi 中断，后续会重启）
- **工作目录**：`/disk/rl/psm_wma/cosmos-framework`
- **环境**：`.venv` (Python 3.13.7 + torch 2.10.0+cu130)
- **命令**：`.venv/bin/python ../tools/g0/build_cosmos_libero_latent_dataset.py --dataset-root /disk/rl/data/LIBERO_LeRobot_v3/<suite> --output-root /disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_v1/<suite> --vae-path examples/checkpoints/wan22_vae/Wan2.2_VAE.pth --windowed --suite <suite> --device cuda:0`
- **资源**：cuda:0 剩余 27GB VRAM，预计峰值 2-4GB，不与 `sft_4in1` 冲突。
- **日志**：`/disk/rl/psm_wma/artifacts/g0/cache_build_*.log`
- **产物**：`/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_v1/<suite>/{dataset_manifest.json,episodes/episode_*.pt}`
- **状态**：因用户要求 immediate tiny-subset smoke 而暂停；已完成 `libero_spatial` 104/432 episodes。

### tiny subset cache 与 GPU smoke 启动（2026-08-20）

- **动作**：Kimi 中断 `sft_4in1` 训练进程（原已跑到 iter 375 checkpoint，但进程仍在 GPU 100% 运行），释放整卡。
- **tiny cache**：已为 4 suite 各建 2 episodes，位于 `/disk/rl/data/LIBERO_4suites_exact_window_v1_smoke/<suite>/`。
- **后台任务 ID**：`bash-h6g6k2g2`
- **内容**：
  1. cache smoke：从 iter 375 resume，启用 tiny cache，临时输出 `/disk/rl/psm_wma/outputs/smoke_cache`，跑 3 步到 iter 378。
  2. online smoke：从 iter 375 resume，不启用 cache，临时输出 `/disk/rl/psm_wma/outputs/smoke_online`，跑 3 步到 iter 378。
- **日志**：`/disk/rl/psm_wma/artifacts/g0/smoke_cache.log`、`smoke_online.log`
- **判据**：两次均完成、loss finite、cache/online loss 差距可接受。

### G0-R06-SFT exact-window cache parity 验证（2026-08-20，Kimi 执行）

- 停止训练 smoke 与训练 probe（均因 `max_episodes=2` + IterableDataset + 36 workers 导致 DataLoader 狂取样本不推进）。
- 新增 `LIBERO_MAX_EPISODES` 环境变量支持（`cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py`、`action_sft_dataset.py`、`action_policy_libero_edge_all.py`），用于 future smoke 对齐 tiny cache 与 dataset 选择。
- 用轻量脚本 `tools/g0/save_online_vae_probe_from_cache.py` 直接对 cache 窗口走训练同一条 `_encode_vision_item` 路径编码，生成 probe 格式产物。
- **产物**：`artifacts/g0/online_vae_probe/rank_00/sample_000000..000019/{raw_uint8.pt, online_latent.pt, meta.json}`。
- **对比**：`artifacts/g0/probe_vs_cache_parity.json` 对比 online latent 与 tiny cache `libero_spatial/episode_000000.pt` 同窗口。
- **结果**：`status=PASS`，20 个窗口（start=0..19，覆盖 `start%4` 全类），`max_abs_diff=0.0`，shape/dtype/finite 全部一致。
- 结论：tiny cache 与 online VAE 输出逐位一致，可重启全量 4-suite cache 构建。未提交。

### BUILD-LATENT-CACHE-4SUITE 全量构建重启（2026-08-20）

- 已清理此前 `libero_spatial` 104/432 的部分输出。
- 4 个 suite 并行构建，全部使用 `--windowed` exact_window_v1 schema。
- 资源：单卡 A100-80GB + 13 CPU cores，4 个 builder 进程共享 cuda:0。
- 输出：`/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_v1/<suite>/`
- 日志：`artifacts/g0/cache_build_<suite>.log`
- 后台任务：`bash-d30rxw98`。

### BUILD-LATENT-CACHE-4SUITE 增加 resume 能力（2026-08-20）

- 用户要求保留之前进度、具备 resume 能力；此前 `libero_spatial` 104/432 部分输出已被清理，无法恢复。
- 已修改 `tools/g0/build_cosmos_libero_latent_dataset.py` 的 `_build_windowed`：
  - 允许已存在输出目录；
  - 读取现有 `dataset_manifest.json`，跳过已有且格式正确的 `episode_*.pt`；
  - 缺失 episode 重新编码；
  - 结束后再写完整 manifest。
- `py_compile` PASS。
- 4-suite 并行构建已重启（任务 `bash-76m7upd3`），从头开始，但后续中断可安全 resume。

### Codex 审查问题修复（2026-08-20）

Codex 审查结论 `REQUEST_CHANGES`，已按 HIGH/MEDIUM/LOW 修复：

1. **HIGH**：runtime guard shape mismatch 根因是 verify 路径把 float32 placeholder 直接喂给 `_normalize_uint8_vision_item`。修复：在 `omni_mot_model.py` verify 块内用 `*255+round+uint8` 从 float32 像素重建 uint8，再走 `_normalize_uint8_vision_item` + `_encode_vision_item`。
2. **MEDIUM-1**：evidence JSON 中 shape mismatch 时 `max_abs_diff`/`mean_abs_diff` 改为 `null`，不再写 `Infinity`。
3. **MEDIUM-2**：evidence 增加 `cache_shape`、`online_shape`、`cache_dtype`、`online_dtype`。
4. **MEDIUM-3**：`libero_lerobot_dataset.py` 与 `omni_mot_model.py` 在 `.float()` 前断言 cache latent dtype 必须为 `float32`。
5. **LOW**：`LIBERO_MAX_EPISODES` 在 dataset 与 config 两处校验必须为正整数。

`py_compile` PASS。正在运行 `verify_ratio=1.0` 的真实 cache 训练 1 步（任务 `bash-tv96xd16`），验证零 mismatch。

### BUILD-LATENT-CACHE-4SUITE 暂停（2026-08-20）

- 为优先跑 `verify_ratio=1.0` 的真实 cache 训练验证，已暂停全量 4-suite cache 构建（任务 `bash-76m7upd3`）。
- builder 已支持 resume，验证通过后可随时重启。

### verify_ratio=1 训练验证切换 num_workers=0（2026-08-20）

- 首次 `verify_ratio=1.0` cache 训练（36 workers）在 "Starting training..." 后 90 秒无进展，判断为 `max_episodes=2` + IterableDataset + 36 workers 同样的 DataLoader hang。
- 新增 `LIBERO_NUM_WORKERS` 环境变量支持，切换为 `LIBERO_NUM_WORKERS=0`。
- 已重启验证（任务 `bash-il15rrvr`）。

### verify_ratio=1 训练验证剩余 diff 根因定位与修复（2026-08-20）

- 验证结果：shape/dtype 均匹配，但 `max_abs_diff≈0.11`，远超 1e-5 阈值，持续 fallback。
- 根因：`tools/g0/build_cosmos_libero_latent_dataset.py` 先把 `_load_video` 的 float [0,1] 视频 permute 后喂给 `VideoResize`（在 float 域做 bicubic resize），再转 uint8；而训练路径 `_build_result()` 先 `(video*255).clamp().to(uint8)`，然后 `ActionTransformPipeline.video_resize` 才在 uint8 域做 resize。两个域的 bicubic 结果不同，导致 latent 有 0.11 级 diff。
- 修复：cache builder 改为先按 `_build_result()` 的方式转 uint8 并 permute，再调用 `VideoResize(resolution=None)`，与在线训练路径逐位对齐。
- 已修改：`tools/g0/build_cosmos_libero_latent_dataset.py:119-125`。
- 下一步：重建 tiny cache，重跑 `verify_ratio=1.0` 训练验证，确认零 mismatch 后再恢复 BUILD-LATENT-CACHE-4SUITE。

### verify_ratio=1 训练验证第二轮：pixel 一致但 VAE diff 仍在（2026-08-20）

- 验证结果：uint8 pixel 逐位一致（`pixel_max_abs_diff=0.0`），但 latent `max_abs_diff≈0.03-0.05`，2048 个样本全部 fallback。
- 根因：`tools/g0/build_cosmos_libero_latent_dataset.py` 创建 `Wan2pt2VAEInterface` 时传了 `encode_exact_durations=[17]`；在线训练路径使用默认配置（未设置该参数）。这导致 VAE 对 T=17 输入的内部 chunking 不同：exact 模式直接分 4 个 4 帧 chunk；默认模式先 pad 到 21 帧再分 5 个 chunk，最后 trim 回 5 个 latent 帧。因果卷积的浮点累加顺序不同，产生 ~3e-2 级 latent diff。
- 证据：`tools/g0/diagnose_vae_exact_duration.py` 对同一段 uint8 用 exact vs default 编码，`max_abs_diff=0.03125`。
- 修复：cache builder 去掉 `encode_exact_durations=[17]`，与在线训练路径使用完全一致的默认 VAE 配置。
- 已修改：`tools/g0/build_cosmos_libero_latent_dataset.py:231`。
- 下一步：再次重建 tiny cache，重跑 `verify_ratio=1.0` 训练验证。

### exact-window latent cache 全量构建 + 数值等价闭环（2026-08-21，Kimi/Codex）

- **全量 cache**：4×5 shard 并行构建（`tools/g0/launch_parallel_cache_build.sh`，单卡 GPU 为瓶颈 ~10 ep/min），`merge_latent_cache_shards.py` 合并。产物 `/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1/{libero_spatial,libero_object,libero_goal,libero_10}`：432/454/428/379 episodes、246,377 窗口、54GB，manifest 契约齐全。
- **根因定案**：训练 recipe 默认 `cudnn.benchmark=True`（`utils/config.py:248`，`trainer/__init__.py:156` 应用），cudnn autotune 选的 bf16 卷积算法与 builder 进程不同 → latent 偏 0.03。证据链：训练内三路 instrument 1495 样本 a-b 全 0（guard 路由无罪）、builder/训练像素 SHA256 逐位一致（输入无罪）、`diagnose_vae_runtime_context.py` 六 profile 中仅 cudnn_benchmark 复现 0.03125/0.00172（`artifacts/g0/vae_runtime_context_ep0_start0.json`）。
- **修复**：recipe TOML 显式 `[trainer.cudnn] benchmark=false`（`action_policy_libero_edge_all.toml:53-55` + `sft_config.py` CuDNNConfig schema），Kimi 端到端断言 composed config PASS。不重建 cache。
- **验收**：A-nobench（verify_ratio=1.0 真实训练）1628 样本 guard/真在线/cache 三方逐位为 0，零 mismatch（`artifacts/g0/latent_cache_route_probe/rank_00/`）；C cache-only forward 四项 decode/encode 计数全 0（`artifacts/g0/cache_only_forward_smoke.json`）；cache-only 3 步训练 smoke loss finite。
- **B 工具判据失效记录**：`compare_online_cache_first_loss.py` 固定 `--deterministic`，双侧本就 benchmark=False；0.024 loss diff 为两种 dataloader 模式首 batch 组成差异，不是 latent 差异。latent 等价以训练内 guard 为权威判据。
- **过程产物**：8-20 旧 mismatch 证据归档 `artifacts/g0/latent_cache_mismatch_archive_20260820_v6/`；B-control（online 重跑逐位一致）证明训练在 deterministic 配置下完全可复现。
- **未提交**：cosmos-framework 工作区改动（vision_vae.py、omni_mot_model.py guard/instrument、dataset cache reader、stdout_loss_logger、TOML/schema、启动脚本）与 tools/g0/ 工具均未 commit，待用户决定。
- **下一步**：正式 4in1 SFT 可启用 `LIBERO_LATENT_CACHE_ROOT`（省在线 VAE 编码）；建议保留小比例 `LIBERO_LATENT_CACHE_VERIFY_RATIO`（如 0.01）做在线抽检。

### 13 ckpt 1-trial smoke 评测 + 跨结果治本（2026-08-25/26，Kimi 执行）

- **目标**：把 13 个 ckpt × 4 suite 1-trial smoke 跑完，**仅**用作 checkpoint selection / 趋势筛选，**不**作为最终 R06 canonical baseline；8 个父目录按角色标注防再查错 SR；R06 口径由 runtime plan v0.6 §6 + 用户 2026-08-26 纠偏决定（见下"canonical R06 baseline 口径冻结"段）。
- **driver**：`cosmos-framework/examples/eval_libero_4in1_acceptance_4090.sh`（task #15，4090 24G，5 worker/suite，跨 suite 并发，stop_server/start_server 三重保险：trap+port probe+CHECKPOINT_PATH 显式 export）。
- **进度**（2026-08-26 15:51 快照）：**5/13 已 .done**，剩余 7 个 iter (1600/1400/1200/1000/800/600/400/200) 串行。
  - iter_000002400：spatial 1.0 / object 1.0 / goal 0.5 / libero_10 0.4 → 4in1-avg **0.725**
  - iter_000002200：1.0 / 0.8 / 0.9 / 0.4 → **0.775**
  - iter_000002000：1.0 / 0.6 / 0.7 / 0.8 → **0.775**
  - iter_000001800：1.0 / 0.7 / 0.8 / 0.2 → **0.675**
  - iter_000002600：1.0 / 0.9 / 0.8 / 0.4 → **0.775**
- **iter_2800 验收数据定位（历史证据 / 能力证据，**非** canonical baseline）**：10-trial `libero_closed_loop_4in1_acceptance_4090` g=1.0 按 MP4 后缀：spatial **0.96** / object **0.99** / goal **0.76** / libero_10 **0.58** → 4-suite mean **0.82**。**这套是 closed-loop capability 已成立的历史证据**，因为 spatial summary.json 0.48 是脏数据（已按 MP4 后缀修正为 0.96）；object/goal/libero_10 summary.json 可信。**不**作为 R06 canonical baseline 来源——该整套旧目录有 success aggregation bug 历史，且 trial 数 / 任务对齐均不是为后续 +Local matched baseline contract 设计的。
- **1-trial 局限**：spatial 全 100%（撞天花板）、libero_10 波动 0.2–0.8（stdev≈50%）；趋势区间 0.7–0.78 仅供 ckpt 选择参考。
- **完成时间预估**：剩 7 iter × 1h ≈ 22:30 完成；完成后 driver 自动触发 libero_90 cache build (#31) → HF upload (#32)。
- **server 加载 ckpt 三重保险已验证**：stop_server→start_server 时显式 `CHECKPOINT_PATH=$ckpt` 传入 launch 脚本；启动前 `curl localhost:8000/` 探活（旧进程未退则拒绝启动）；driver 任何路径退出 `trap stop_server EXIT INT TERM`；逐 iter server log 第一行 `loading model: ... checkpoint_path='.../iter_*/model'` 与 ps 启动时间双确认。
- **iter_2800 spatial 0.48 → 0.96 真相**：worker_task_001.log 显示 ep1-8 `success=False steps=0 elapsed=522s`，但 task_001/mp4/ 下 episode_000-009 全是 `_success.mp4` —— MP4 文件后缀是仿真环境 success 信号直接写入，summary.json success 字段在合并时被污染。**bug 只影响 spatial suite**，object/goal/libero_10 summary.json 与 MP4 后缀一致。
- **HF README 2B → 3B/3.4B 修正**（commit 0088c7ba）：基于 DCP metadata 实算 `language_model.model 3.087B + lm_head 0.268B + 小模块 ~14M = 3.37B`，bf16 存储 6.74GB ≈ DCP shard 6.28GB；改为 `Nemotron-3 3B reasoner` + 表格注明 `3B backbone + lm_head ≈ 3.4B total`。
- **MEMORY/ 6 个新文件已建**：cache-5suite-merge-build、cache-builder-script-location、eval-result-directory-roles、idea-input-robot-state-to-policy、iter2800-spatial-sr-dirty-data、mp4-suffix-is-truth（type=project/reference 混合，frontmatter 风格；用于项目级长期事实/索引/治本）。

### canonical R06 baseline 口径冻结（2026-08-26，用户纠偏）

- **R06 真实目的**：不是为每个 suite 调到最高 SR，而是冻结一个**统一、单一、可复现**的 no-memory baseline，作为后续所有 +Local 实验的**唯一 matched 对照**。见 runtime plan v0.6 §6。
- **canonical baseline 协议（冻结）**：
  - 单一 checkpoint（按 13-ckpt sweep + 已有稳定性证据选定）
  - `guidance=1.0`（**不**用 suite-specific CFG）
  - `denoise steps=30`，`max_episode_steps=700`
  - 同一 prediction/execution/query cadence
  - 4 suites × 10 tasks × 10 trials = 400 episodes
  - no memory / no agent / no RL
  - 其余训练/推理配置保持一致
- **三类证据严格区分**（**不**混用、**不**互相替代）：
  1. **historical evidence**：`acceptance_4090`、`acceptance`、`libero_closed_loop_4in1`、`iter100`、`steps12` —— 用于证明 closed-loop capability 已成立，**不**作 baseline
  2. **CFG sensitivity diagnostic**：`spatial_cfg_4090` (g=1.5/2.0/2.5) + `cfg_4090/g2_0` —— 用于研究 guidance 对 SR 的影响，**不**作 baseline（suite-specific inference tuning 会破坏 matched baseline contract）
  3. **checkpoint screening**：`smoke_v1` 13 ckpt × 1 trial —— 选 ckpt 用，**不**作 baseline
  4. **canonical R06 baseline**：待 13-ckpt sweep 完成后做一次 clean 400-episode acceptance；`summary.json == MP4 _success/_fail 后缀 == task-level episode success` 三者一致；冻结 checkpoint / config / eval contract 后 R06 → DONE
- **R06 当前状态（2026-08-26 纠偏后）**：
  - closed-loop capability = **PASS**（3 个 suite 已有非零 SR，链路全通；iter_2800 历史验收 4-suite mean ≈ 0.82 是 capability 证据）
  - canonical baseline freeze = **TODO**（待 clean 400-episode acceptance）
  - **不**提前把 G0-R06 标记 DONE；不进入 R07-R09 实质 Memory 实验
- **MEMORY/eval-result-directory-roles.md 已重写"治本约束"**：取消"spatial 用 spatial_cfg_4090 / goal 用 cfg_4090/g2_0"的旧写法，明确三类证据不能拼成 baseline。

### smoke 跑完后自动触发（2026-08-27 用户要求）

- 用户原话："smoke 跑完后的计划要自动触发"
- 实现：driver 末尾追加 `auto-post-smoke hook`，调用 `tools/g0/auto_post_smoke.sh`
- `tools/g0/auto_post_smoke.sh` 依次：
  1. 校验 13 个 smoke .done 全部存在（否则 abort exit 2）
  2. 汇总 SR 趋势 → `artifacts/g0/13ckpt_smoke_summary.{json,md}`（PHASE=summary 单跑已验证）
  3. 触发 `tools/g0/launch_parallel_cache_build_libero_90.sh`（5 shard 串行等）
  4. 打印 #32 / #21 待办提示（**不自动**：HF upload 待仓库拍板，R06 canonical 待用户授权）
- 幂等：`artifacts/g0/.post_smoke_done.lock` + 子 sentinel `.libero_90_cache_build_done`
- **本次 driver 实例**（pid=713227, 14h30m+）已跑完，新加 hook 对本次不生效；
  用户跑 `bash tools/g0/auto_post_smoke.sh` 即可触发本次后续计划
- **未来 driver 重跑**：自动走 hook（`AUTO_POST_SMOKE_HOOK=0` 可关）

### 治本约束（强制）

- 查 SR 必须先看 8 个 results 父目录之一 + 参数（guidance/trials/steps），且先判定角色类别（historical / diagnostic / screening / canonical）。
- spatial 真值必须按 MP4 后缀重算，**不**信 acceptance_4090 的 summary.json success 字段。
- server 加载新 ckpt 必须验证 ps 启动时间 + log checkpoint_path + 端口探活三件套。
- **canonical R06 baseline 必须**由 clean 400-episode acceptance 冻结，**不**用 suite-specific CFG、**不**用 1-trial sweep、**不**用历史 evidence 目录。

### 双仓库 commit/push 完成（2026-08-27）

- 用户原话："提交 推送"
- **子模块 cosmos-framework**：`7826483`（v2 ahead 1）已 push 成功
  - commit: `feat(examples): driver auto-post-smoke hook + launch script 防御性变量`
  - 改：3 files（driver + server launch + eval launch）
- **主仓库 psm_wma**：`d77a9fb`（V2 ahead 2）已 push 成功
  - `8036d75`: `feat(tools/g0): auto_post_smoke + libero_90 build + 13ckpt summary`
  - `d77a9fb`: `chore(submodule): bump cosmos-framework 7826483 driver hook + launch 变量`
- **rebase 流程**：
  1. 子模块 rebase origin/v2（19 R07 commits → fast-forward 到 af06827 → pick 9c9ddb1 重放成 7826483）
  2. 主仓库 rebase origin/V2（19 R07 commits + 2 my commits），submodule pointer conflict 由 9c9ddb1→7826483 手动 resolve
  3. amend 修正 message（9c9ddb1 已 rebase 替代为 7826483）
  4. push 后 `git rev-list --left-right --count HEAD...origin/V2` 必须 0/0
- **踩坑**（已写入 MEMORY）：
  - amend 误带 Codex 无关文件 → `git reset HEAD -- <files>` 撤
  - 子模块 rebase 后旧 hash 不可达 → 主仓库 submodule pointer 需手动 resolve
  - commit message 含 hash 与实际不一致 → amend 修正
- 见 `MEMORY/cross-repo-rebase-submodule-pointer.md`
