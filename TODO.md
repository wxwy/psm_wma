# PSM-WMA 任务队列

状态：`TODO`、`IN_PROGRESS`、`BLOCKED`、`REVIEW`、`DONE`。

| ID | 状态 | 负责人 | 前置条件 | 验收条件 |
|---|---|---|---|---|
| COLLAB-BOOTSTRAP | DONE | Codex | 无 | 根目录协作协议、会话状态、任务队列和长期决策文件可供所有 Agent 使用 |
| DOC-R01 | DONE | Codex | G0 Runtime Plan v0.6 | REVIEW-R01 的 H1/H2、M1-M3、L1/L2/L4 已修订并完成最小行为验证 |
| DOC-R02 | DONE | Codex | DOC-R01 完成 | Kimi 独立审查 APPROVE；MEDIUM-1 与 LOW-1/2/3/4 已关闭，Runbook 状态 `reviewed` |
| DOC-R03 | DONE | Codex | DOC-R02 完成 | Kimi 独立审查 APPROVE；2 MEDIUM + 3 LOW 已关闭或按范围转交，Runbook 状态 `reviewed` |
| DOC-R04 | IN_PROGRESS | Codex | DOC-R03 完成 | 建立 Edge-Policy-DROID × LIBERO forward/loss 独立 Runbook，覆盖精确命令、资产、Schema、断言、判据与失败分流 |
| DOC-R05 | DONE | Codex | G0-R04 PASS | R05 Runbook 已升为 `reviewed`，stats、tiny subset、loss/reload/checkpoint 判据已通过实执验收 |
| DOC-R06 | REVIEW | Kimi | G0-R05 PASS | Runbook v0.1 已创建并经实执验证；两处偏差（RLinf venv、TRITON_LIBCUDA_PATH）与 §7.3 措辞待升 v0.2，待 Codex 审查 |
| REVIEW-R01 | DONE | Kimi | DOC-R01 已重新进入 REVIEW | 二轮复审 APPROVE，首轮 8 项全部关闭，N1/N2/N3 已于收尾处理 |
| G0-R01 | DONE | Codex | REVIEW-R01 DONE；环境和 checkpoint 就绪 | Gate JSON PASS；用户批准 RoboLab 基础设施豁免，Reasoner/Policy/World smoke 与独立复核完成 |
| G0-R02 | DONE | Codex | G0-R01 PASS | metadata/config/index audit JSON PASS；有效索引 0 缺失、provenance 完整，warm-start 与 LIBERO 数据契约已冻结并通过独立审查 |
| G0-R03 | DONE | Codex | G0-R01 PASS | 真实 LIBERO 7→10→64 action pipeline、domain 5/8、shape/mask、projection smoke、参数拆分与 stats provenance 已落盘并通过独立审查 |
| G0-R04 | DONE | Codex/Kimi | G0-R02、G0-R03 完成；40GB GPU 与非 fused AdamW 路径可用 | 连续 20 步 PASS：loss/grad 全 finite、domain 行保护 PASS、末次 checkpoint 四件齐全、无 OOM/SIGKILL；机器可读 Gate JSON 已落盘 |
| G0-R04-ADAMW | DONE | Codex/Kimi | G0-R04 单步诊断；框架当前硬编码拒绝 `fused=False` | 标准 Adam/AdamW 的非 fused 优化器路径已通过单步验证和 Kimi 独立 APPROVE；FusedAdam 行为不变 |
| G0-R05 | DONE | Codex/Kimi | G0-R04 PASS | Gate JSON `PASS`；100/100 步、两次 reload 逐位一致、checkpoint 四件齐全；HIGH-1/2 复审 APPROVE |
| DCP-MULTIRANK-RELOAD | TODO | 待认领 | R06 或任何正式多卡训练启动前；不阻塞单卡 R05 | CPU optimizer 叶子在 NCCL 多 rank DCP reload 中可正确广播；至少 2 rank 恢复真实 AdamW 状态与定向单测 PASS |
| G0-R06 | DONE | Codex/Kimi | G0-R05 PASS | 用户 D017 override：`iter_000002800` 冻结为 R06 No-Memory baseline；历史 zero-shot `FAIL_SR_ZERO` 证据保留且不改写 |
| G0-R06-SFT | DONE | Kimi/Codex | 用户 D017 | 4-suite SFT 产出 `iter_000002800`，作为冻结 No-Memory baseline；不再以 canonical 400-episode acceptance 为前置 |
| BUG-R06-PRED-MP4 | REVIEW | Codex | 已定位 `--save_pred_mp4` 双视角帧尺寸不一致 | 单个预测 MP4 保留 1 帧输入与全部预测帧；定向导出验证的帧数为 17，待独立审查 |
| BUG-4IN1-LOSS-LOG | DONE | Kimi | ds 反馈 4in1 训练 log 未记录 loss | 新增 `StdoutLossLogger` callback 并接入 `action_policy_libero_edge_all`/`action_policy_libero_edge_warmstart`;2026-08-20 13:18 从 iter_000000300 resume 后生效;验证日志:`iteration=301 | train/loss=1.731282 | flow_matching_loss_vision=0.108888 | flow_matching_loss_action=0.064241`;代码尚未提交 |
| BUG-LIBERO-SAMPLE-STRIDE | DONE | Codex | 用户确认改用 exact-window latent cache | 不修改训练采样；正式路径保持 `sample_stride=1`，cache 覆盖全部合法窗口并按精确窗口键读取 |
| REVIEW-ONLINE-VAE-PROBE | DONE | Codex/Kimi | Kimi 方案与 Codex 审查完成 | 采用方案A(dataloader输出video_latent,模型跳过normalize+VAE);`source_frame_indices` 改名为 `window_frame_indices`(完整17帧),5个latent锚点另存 `latent_source_frame_indices`;probe在batch-start捕获归一化前uint8;离线构建<=1e-6,runtime guard<=1e-5;失配单样本fallback并写结构化证据；用户已授权转 IMPLEMENT |
| IMPLEMENT-ONLINE-VAE-LATENT-CACHE | REVIEW | Codex/Kimi | Kimi 二次复审 APPROVE；LOW-1/2 已关闭；tiny cache parity 已 PASS | exact-window cache reader、video_latent 契约、模型 bypass、runtime guard、离线构建/parity 工具均已实现；静态验证 PASS；tiny cache vs online VAE `max_abs_diff=0.0`（20 窗口，覆盖 start%4 全类）；待 Codex 独立审查后关闭 |
| BUILD-LATENT-CACHE-4SUITE | DONE | Codex | 用户已批准新独立全量构建根 | 4 suite 全量完成（Kimi 重启为 4×5 shard 并行 + merge）：432/454/428/379 episodes、246,377 窗口、54GB；manifest 契约齐全（bf16 compute_dtype、exact_durations、chunk 配置） |
| FIX-CACHE-RESIZE-ORDER | DONE | Kimi | verify_ratio=1 训练验证仍 mismatch | cache builder 先转 uint8 再 VideoResize，与训练路径 `_build_result`+`ActionTransformPipeline` 完全一致；pixel diff 降为 0 |
| FIX-CACHE-VAE-EXACT-DURATION | DONE | Kimi | pixel diff=0 但 latent diff ~0.03-0.05 | 已由 FIX-CACHE-PARITY-VAE-CONTRACT 取代；统一 VAE contract 后 tiny cache 与在线路径 parity=0 |
| FIX-CACHE-PARITY-VAE-CONTRACT | DONE | Codex/Kimi | 公共入口静态/GPU parity PASS | Kimi 复审 APPROVE；训练 recipe、builder、probe、parity、runtime guard 复用 `vision_vae.py`；`libero_spatial` episode 0 20 窗口 original online vs shared contract/cache 均 `max_abs_diff=0.0`；parity 工具 PASS |
| FIX-CACHE-PARITY-RUNTIME-INSTRUMENT | DONE | Codex/Kimi | B-control PASS，确认真实训练在线 VAE 与 cache 存在稳定差异 | 在显式 verify 样本上记录同一 raw uint8 的 shared guard、训练在线等价路由、cache 三路摘要/diff 到 `artifacts/g0/latent_cache_route_probe/`；不改变 cache-only 默认路径；`py_compile`、`git diff --check` PASS，待 Kimi 独立审查与最小 GPU 取证 |
| DIAGNOSE-CACHE-VAE-RUNTIME-CONTEXT | DONE | Codex/Kimi | route probe 已证实同像素同路由下 builder/训练进程 latent 仍不同 | Kimi 审核 APPROVE 并实跑：6 profile 中仅 cudnn_benchmark 复现 0.03125/0.00172 偏移，其余全 0（`artifacts/g0/vae_runtime_context_ep0_start0.json`），锁定根因 |
| FIX-CACHE-CUDNN-BENCHMARK | DONE | Codex/Kimi | runtime context 扫描锁定训练 `cudnn.benchmark=True` 为唯一数值分叉 | 正式 recipe 显式 false；SFT schema、最终 Hydra composed config 与 Kimi 独立复审 PASS；训练内 verify 1628 个样本逐位零 mismatch，不重建 cache |
| CACHE-TRAIN-EQUIVALENCE-TOOLS | DONE | Codex/Kimi | C 实跑 PASS；B 限制已写入 docstring | C 工具 PASS（四项计数全 0）；B 的固定 `--deterministic` 使双侧本就 `benchmark=False`，且两种 dataloader 模式不保证首 batch 样本组成相同，故其 0.024 loss diff 不可作为 latent 等价判据；该限制已在工具 docstring 明确，latent 等价以训练内 guard 为权威判据 |
| CACHE-ONLY-FORWARD-SMOKE | DONE | Kimi | 4 suite 全量 cache 完成 | PASS：`artifacts/g0/cache_only_forward_smoke.json` 四项计数（_load_video/torchcodec decode/interface encode/WanVAE encode）全 0，3 步 forward 9.5s；另 cache-only 3 步训练 smoke loss finite 零 mismatch |
| OBSERVE-TRAIN-STEP-TIMING | DONE | Codex/Kimi | Kimi 审查 APPROVE；不干扰正在运行的 `sft_4in1` | trainer 主循环以 micro-batch 记录 `next(dataloader)` 等待与 `training_step` 主机墙钟耗时，按 optimizer step 聚合；StdoutLossLogger 输出机器可解析秒数/占比；不改数值、不实现异步 prefetch；`py_compile`、双仓 `diff --check` PASS；Kimi 核对计时点、StopIteration、None guard 和无数值改动后 APPROVE；下次 resume 生效 |
| UNIFY-SFT-LAUNCH | DONE | Codex/Kimi | Kimi 审查 APPROVE；不得干扰运行中的 `sft_4in1` | 主 launcher 自动扫描最大 `iter_*`，支持 `DISABLE_AUTO_RESUME=1` 冷启动、最近 3 项提示和 `DRY_RUN=1`；旧 resume/tmux-resume 为 deprecated 转发；tmux 内联 cache root/verify ratio/workers；`bash -n`、双仓 diff-check、无 iter/有 iter/禁用自动恢复三种 dry-run 均 PASS；Kimi 审查 APPROVE，已关闭从非 repo cwd 误 Fresh 与 cache root 延迟报错两个 LOW |
| EVAL-LIBERO-4IN1-PERIODIC-200 | DONE | Codex/Kimi | Kimi 复审 APPROVE；不得干扰运行中的 `sft_4in1` | 4in1 watcher 已改为 stride=200、每 suite task0 一次 trial、后续轮询 5h；`bash -n`、双仓 diff-check PASS，旧 250/10h/3-trial/task2 引用已清除；Kimi 复审 APPROVE；未启动 eval |
| GPU-SMOKE-LATENT-CACHE | DONE | Kimi | tiny cache 可用；用户同意用直接 parity 替代训练 smoke | 用 `save_online_vae_probe_from_cache.py` + `verify_latent_cache_parity.py` 完成 cache vs online VAE 直接对比；`artifacts/g0/probe_vs_cache_parity.json` status=PASS，max_abs_diff=0.0；原训练 smoke 因 `max_episodes=2`+IterableDataset+36 workers 不兼容取消 |
| IMPLEMENT-ROBOCASA-OFFLINE-VAE-CACHE | TODO | Codex/Kimi | 用户决定暂缓 cache，需要时再启动；代码实现与静态验收已完成 | 代码复审两轮收敛（REQUEST_CHANGES→APPROVE，遗留 1 个非阻塞 nit：builder :98 死代码残留旧 shape）；未跑 GPU；启动时需依次完成：LIBERO tiny helper 回归 0-diff、RoboCasa tiny parity（单进程限资源、水位准入）、用户授权后 full build；build 期间须停 eval watcher |
| REVIEW-CACHE-IMPLEMENTATION | TODO | Codex | IMPLEMENT-ONLINE-VAE-LATENT-CACHE 实现与 parity 证据就绪 | Codex 独立审查 exact-window cache 实现、parity 证据与新增 `max_episodes` 支持；按项目审查惯例给出 APPROVE/REQUEST_CHANGES/REJECT 并附 file:line 级意见 |
| EVAL-LIBERO-4IN1-ACCEPTANCE | DONE | Codex | D017 override | 已 superseded：driver 保留但不再作为 R06 Gate，禁止启动 canonical acceptance 或 iter2800/spatial smoke GPU job；13-ckpt sweep 仅作趋势 evidence |
| G0-R07-SOURCE-AUDIT | DONE | Codex | 详细设计 v0.1、Runtime Plan v0.6 与官方 v2 代码基线 | 二轮独立复核 APPROVE；D017 已解除 R06 canonical blocker，审计产物已补 native mRoPE/checkpoint parity Gate |
| G0-R07-IMPLEMENTATION | DONE | Codex | G0-R06 DONE、G0-R07-SOURCE-AUDIT DONE、D017 | Local dummy clean modality、A/B/C/D、native mRoPE parity、iter2800 load/no-memory parity/save-reload、optimizer/update 与 fixed-weight sensitivity 均已通过独立审查；R07 implementation 与 runtime Gate 均关闭，不实施 R08/R09 |
| G0-R07-PRE-IMPLEMENT-REVIEW | DONE | mm2 | D017 与 source audit 完成 | `APPROVE_TO_IMPLEMENT`；D017、mRoPE parity、checkpoint/no-memory parity、Edge-4in1 scope、legacy/Flex 范围通过；LOW 措辞已回填 |
| G0-R07-STEP1-REVIEW | DONE | mm2 | 子模块 `0b48dae`、根仓 `799dc91` | APPROVE：Local dummy 注入、optional collate、默认关闭无回归与 serialization 兼容通过；`SequencePlan.as_dict()` 未被业务调用为 LOW，不阻塞 |
| G0-R07-STEP2-REVIEW | DONE | mm2 | R07 Step 2 子模块实现与 CPU 合约测试 | APPROVE：首轮 HIGH（测试漏传必填 `SequencePlan.has_text`）仅修 fixture 后关闭；mm2 复跑 3 项 pytest（3 passed）、`py_compile`、`diff --check` PASS。`GenerationDataClean → PackedSequence/packer → adapter/GEN routing`、Edge config 注入、native mRoPE parity 与 Local clean/no-loss 边界均通过 |
| G0-R07-STEP2-PROPAGATION-REVIEW | DONE | ChatGPT | ChatGPT 发现 `_get_velocity`/`_slice_gen_data_clean` 漏传 Local | APPROVE：仅修重建传播与 all-present/mixed-optional slice 映射；5 项 CPU pytest、`py_compile`、`diff --check` PASS；禁止 R08/R09 |
| G0-R07-RUNTIME-SMOKE | DONE | Codex | Step 2 propagation review DONE | mm `APPROVE_TO_DONE` 与 Kimi `APPROVE`（provenance closure report）一致确认可关闭。provenance 记录提交、CKPT、三模固定权重、确定性环境、cache、资源与验收量级；raw sidecar 已清理且如实记录为复现限制，不推翻 Gate。`sensitivity.json` PASS：同一 5-step Normal CKPT 下三模 14/14 输入/结构不变量 exact，shuffle present=128；Normal→Zero Vision/Action relative L2=1.097%/0.495%，Normal→Shuffle=0.970%/0.396%。R08/R09 尚未启动。 |
| G0-R07-PROVENANCE-HYGIENE | DONE | Codex | G0-R07-RUNTIME-SMOKE DONE；保留 sensitivity_ckpt5 | 无 GPU 完成：原始 shell/log/tmux/runner transcript 均未保留 Gate C 精确启动行，`exact_command_recoverable=false` 已如实记录，未猜测重构；CKPT_5 实测 8 文件、18,132,791,947 B，model/optim/scheduler/trainer 及 metadata SHA256 全部回填。R07 PASS 不变，R08 GPU Gate 前置已满足。 |
| G0-R08-STEP0-SOURCE-AUDIT | DONE | Codex | R07 provenance hygiene DONE；R08 supplement v0.1 已完整阅读 | `artifacts/g0/r08/source_audit.json` 实证 loader/state/action/cache 合同，含真实 provenance；mm APPROVE_TO_CLOSE 与 Kimi closure APPROVE，审计 MEDIUM 全关闭。未改模型/数据合同、未跑 GPU；下一步 Gate-0 z0 suffix-invariance diagnostic，先完成后独立 review。 |
| G0-R08-GATE0-Z0-SUFFIX-INVARIANCE | DONE | Codex | R08 Step 0 DONE；R07 provenance hygiene DONE；工具三方批准 | ChatGPT `APPROVE_TO_CLOSE_SANITY_CHECK`、mm2/Kimi `APPROVE_TO_CLOSE`。GPU attempt2 的 128 A/A-repeat/B encode 为 `PASS_STRICT_BITWISE`：128/128 z0/repeat bitwise、max_abs=0、input/coverage/determinism/sidecar SHA 全核验；attempt1 仅 torchcodec 动态库环境失败、未进 encode。按 5188a5a 关闭为一次 Wan wrapper causal-contract sanity check，不再扩展 z0 实验；raw sidecar/log 继续本地保留。 |
| G0-R08-STEP2-CAUSAL-HISTORY-CONTRACT | DONE | Codex | G0-R08-GATE0 DONE；`31983c5` 首轮 REVIEW | ChatGPT/mm2/Kimi 三方复审通过：`local_history_action*` 避开原生 `history_action`，真实 CPU evidence 覆盖 H=0/1/3/16、causal/state/raw+normalized action/z0 visual、pipeline isolation；未接 runtime/model/GPU。 |
| G0-R08-STEP3-ALIGNMENT-LEAKAGE | DONE | Codex | G0-R08-STEP2-CAUSAL-HISTORY-CONTRACT DONE | ChatGPT/mm2/Kimi 三方通过：CPU-only 17/17 PASS，history/current target source-row 集合不相交、same episode、精确 dt、padding inertness、H=0 default-off、provenance 均关闭；未接 runtime/GPU。 |
| G0-R08-STEP4-LOCAL-EVIDENCE-ENCODER | DONE | Codex | G0-R08-STEP3-ALIGNMENT-LEAKAGE DONE | ChatGPT/mm2/Kimi 三方通过：stateless adapters 分离、mask exact-zero、finite grad、state stats fail-fast 均 PASS；无 readout/Cosmos/runtime/recurrent/TTT/Global/R09。state runtime 保持 `DISABLED_PENDING_TRAIN_SPLIT_STATS`。 |
| G0-R08-STEP5-STATELESS-LOCAL-REPLAY-READOUT | DONE | Codex | G0-R08-STEP4-LOCAL-EVIDENCE-ENCODER DONE | 三方复审 APPROVE_TO_ADVANCE_STEP6；子模块 `f249566` 的 stateless `masked_mean + latest_valid → MLP → [B,1,D_local]`、all-mask exact-zero、finite/grad CPU 合约 8/8 PASS；不含 recurrent/TTT/temporal Transformer/Cosmos/GPU/R09。 |
| G0-R08-STEP6-RUNTIME-INTEGRATION | DONE | Codex | ChatGPT `d810b37`、mm、Kimi 独立复审均通过 | `89b421b` 的 runtime `reset_parameters()` 由 network `init_weights()` 调用；meta→to_empty(cpu)→fixed-seed init 全参数 finite/逐元素确定，定向 pytest 12 passed、py_compile、双仓 diff-check PASS。trace root `7440342` / submodule `89b421b` PASS，mRoPE 与两项 condition-index 不变量均保持。仅获单卡 Gate A 准入；R09/多卡未获批。 |
| G0-R08-GATE-A-SINGLE-GPU | DONE | Codex | ChatGPT、mm、Kimi 独立审核通过 | `artifacts/g0/r08/gate_a_single_gpu.json` PASS：2-step loss finite，R08 gradient/update finite/nonzero，完整 model/optim/scheduler/trainer DCP，fresh process restore 至 iteration 2 并结束；root `f05085a`、Gitlink/子模块 `c66ade0`、tracked clean 由 verifier 记录。 |
| G0-R08-GATE-B-HISTORY-SENSITIVITY | DONE | Codex | Gate A DONE；ChatGPT/MM/Kimi runtime closure 均通过 | `gate_b_history_sensitivity_final.json` PASS，`expected_runtime_valid=true`；三模式均固定 root `2ad910a`、Gitlink/submodule `860f532`；clean alternate runtime 三模式负例 FAIL，pytest 9/9 PASS。ChatGPT `APPROVE_TO_CLOSE_GATE_B`，MM/Kimi `APPROVE_TO_CLOSE`。后续进入 R09 前先完成独立 runbook/范围复核。 |
| G0-R09-RUNBOOK-PREFLIGHT | IN_PROGRESS | Codex | R09 Runbook 三方 APPROVE_TO_ADVANCE_A0 | 仅实施 R09-A0 CPU contract：minimal recurrent backend、state/reset_mask、mixed presence、partial-reset、segment equivalence、meta-init regression、JSON verifier；禁止 GPU、A1、TTT、多卡与 backend freeze。 |
| G0-R12-CACHE | DONE | Codex/Kimi | Cosmos RGB 编码契约已确认；本地 Wan2.2_VAE.pth | 379/379 episode 全量编码成功、零错误；manifest、finite 抽查和全量时序映射校验通过 |
| DOC-RGB-REP | DONE | ChatGPT | 用户确认 Policy/Memory RGB 表征不应过早绑定 | 新增项目级 RGB/Memory 编码规划，记录到 D014，并将 regular-episode latent 从当前主线降级为候选实验 |
| D015-LOCAL-MEMORY-GATE | DONE | Codex | D013/D014 已生效，Runtime Plan R07-R09 已对齐 | MEMORY/DECISIONS.md 新增 D015：Local/Global 必须为独立 optional clean modality；R07-R09 顺序与冻结边界；未冻结项不得在实现前写成既定事实 |
| DATA-DOWNLOAD-TMUX | IN_PROGRESS | Codex | 用户要求 2026-08-26 早数据 ready；本沙箱到 huggingface.co 出网被掐 | `tmux hf_download_libero` 拉 `nvidia/LIBERO_LeRobot_v3`、`tmux hf_download_latent` 拉 `MangoGoes/libero4in1_wan2.2vae_latent_cosmos_style`，仅清 SOCKS5 保留 HTTP_PROXY 走 CONNECT 隧道；Claude 不前台测速 |
| ACCEPT-13CKPT-SMOKE | IN_PROGRESS | Kimi | EVAL-LIBERO-4IN1-ACCEPTANCE driver 已就绪 | **角色：checkpoint screening / 趋势筛选，**不**作为最终正式 SR**。13 ckpt × 4 suite 1-trial smoke：5/13 已完成（iter_2600/2400/2200/2000/1800 4in1-avg = 0.775/0.725/0.775/0.775/0.675），剩 7 iter 串行至 22:30；1 trial 局限（spatial 撞天花板、libero_10 stdev≈50%）已在 SESSION 标注。**验收：sweep 完成后给出 ckpt 选型建议（top-N + 稳定性证据），但**不**写 frozen baseline SR** |
| ACCEPT-CANONICAL-R06-BASELINE | DONE | Kimi | 用户 D017 override | 已取消：不执行额外 400-episode canonical acceptance；13-ckpt sweep 保留为趋势 evidence，不阻塞 Local |
| FIX-EDGE-3B-PARAM-COUNT | DONE | Kimi | 用户质疑 README 描述与 DCP shard 体积不符 | HF README `MangoGoes/Cosmos3-edge-generation-libero4in1` 改 `2B` → `3B reasoner` + Architecture 表注明 `3B backbone + lm_head ≈ 3.4B total`；commit 0088c7ba 已推送；DCP metadata 实算 3.087B + 0.268B + 14M = 3.37B，bf16 6.74GB ≈ DCP 6.28GB |
| ROOT-CAUSE-ITER2800-SPATIAL | DONE | Kimi | 用户两次质疑 acceptance_4090/iter_2800 spatial 0.48 是错的 | 按 MP4 _success/_fail 后缀重算 → **0.96**（95/99）；bug 仅影响 spatial suite，object/goal/libero_10 summary.json 可信；MEMORY/mp4-suffix-is-truth.md + iter2800-spatial-sr-dirty-data.md 已固化 |
| VERIFY-SERVER-LOADS-NEW-CKPT | DONE | Kimi | 用户要求确认 server 切 ckpt 正确性 | 6 个 server log 全部 `checkpoint_path=iter_*/model` 与 ps 启动时间、端口探活、driver trap+stop_server 三重保险对得上；不留残留 |
| ROOT-CAUSE-EVAL-DIR-ROLES | DONE | Kimi | 多次查 SR 数据错位 | MEMORY/eval-result-directory-roles.md 固化 8 个父目录的角色/参数/启动时间全景表 + 查 SR 强制流程（先父目录 → 再参数 → 再判定可靠性）|

## 新增任务规则

- 一个任务只对应一个可独立验证的结果。
- 编码前先认领并列出预计修改文件。
- 验证完成后先转 `REVIEW`，独立检查通过后才转 `DONE`。
- 阻塞必须写明缺少的资产、权限或上游结果，不使用笼统描述。
