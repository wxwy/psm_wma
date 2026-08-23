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
| G0-R06 | REVIEW | Kimi | G0-R05 PASS | zero-shot 诊断已封存：Gate `FAIL_SR_ZERO`(SR=0/3，逐位可复现），证据 `artifacts/g0/r06/R06_libero_closed_loop.json` 不得修改；报告 `docs/build/PSM-WMA_REVIEW-G0-R06_closed_loop_2026-08-15.md`；**注意偏差：该评测用的仿真 task_ids 0(soup) 并非后续 SFT 训练的马克杯任务(仿真 task_ids 4)，定性结论不变但 SR 数值受任务错配影响** |
| G0-R06-SFT | IN_PROGRESS | Kimi/Codex | 用户已决策正式 LIBERO SFT baseline；G0-R06 zero-shot 诊断完成 | 当前主线已切换为 4-suite 联合 SFT(`action_policy_libero_edge_all`):Edge-Policy-DROID warm-start、在线 VAE、单卡 A100-80GB、grad_accum=16;训练在 `tmux sft_4in1` 中运行,当前 iter 302(从 iter 300 resume);iter 250 4-suite 闭环评测首次出现非零 SR:libero_spatial task0 **1/3=33.3%**,其余 suite 仍为 0;**num_workers 恢复为 36**(prefetch_factor=3),iter 301→302 耗时约 168s,loss 记录正常;验收:1000+ 步后多 seed 闭环 SR>0 且可复现 |
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
| EVAL-LIBERO-4IN1-ACCEPTANCE | TODO | Kimi/Codex | 用户拍板 ckpt 范围/任务数/启动时机后，与 Codex 对齐脚本参数 | 4 suite × 每任务 10 trials，denoise=30、上限 700 步；每 ckpt 400 episodes；SR 结果落盘并与历史 200 倍数点对比；训练期间并发受 GPU/内存水位限制，不得诱发训练 OOM |
| G0-R07-R09 | BLOCKED | 待认领 | G0-R06 PASS | Local/Global packing 与 Local Memory Gate 分别满足 Runtime Plan |
| G0-R12-CACHE | DONE | Codex/Kimi | Cosmos RGB 编码契约已确认；本地 Wan2.2_VAE.pth | 379/379 episode 全量编码成功、零错误；manifest、finite 抽查和全量时序映射校验通过 |
| DOC-RGB-REP | DONE | ChatGPT | 用户确认 Policy/Memory RGB 表征不应过早绑定 | 新增项目级 RGB/Memory 编码规划，记录到 D014，并将 regular-episode latent 从当前主线降级为候选实验 |

## 新增任务规则

- 一个任务只对应一个可独立验证的结果。
- 编码前先认领并列出预计修改文件。
- 验证完成后先转 `REVIEW`，独立检查通过后才转 `DONE`。
- 阻塞必须写明缺少的资产、权限或上游结果，不使用笼统描述。
