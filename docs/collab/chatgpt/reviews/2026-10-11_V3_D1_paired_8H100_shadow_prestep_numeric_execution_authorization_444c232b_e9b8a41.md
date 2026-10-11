# DS_PRO — V3 D1 成对 8×H100 Shadow Pre-step Numerical Parity 执行授权

**Date:** 2026-10-11
**Scope:** `D1_PAIRED_8H100_SHADOW_PRESTEP_ONLY` — 两条模式 sequential，各最多启动一次，不允许并发第二个 GPU 作业。
**Frozen Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`; **Child+Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Prior C1:** `C1_RESTORE_PASS / C1_CLOSED`.
**Review and source:** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_J1_J2_prelaunch_closure_444c232b_e9b8a41.md`; `docs/collab/chatgpt/evidence/2026-10-11_V3_D1_prelaunch/DS_PRO_2026-10-11_J1_J2_final_CPU_remediation_owner_relay.md`.
**Official Formal30k:** `formal_verified_index_30k` remains **STOPPED**, no official Resume/Fresh/job file writes.
**Target:** Shadow `iter_000000800`; full digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`.

## A. 一次性 CPU Guard（不是新独立 Gate）

1. 检查 Formal Root/Child/Gitlink/Child cleanliness；区分当前 V3 docs HEAD 与冻结实现 Root；原 Formal30k 无写进程。C1 Shadow Root **固定**为 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/`，Job **固定**为 `formal_verified_index_30k_shadow`；该 Job 自己的 `checkpoints/latest_checkpoint.txt → iter_000000800`。禁止 Original Formal30k 根目录作为 Trainer OutputRoot。每种模式的进程均从同一个 Shadow checkpoint **重新**加载，严格 `source.warm_start=False`、五组件、iteration800、实际 full config digest 相同。
2. 在 DS 主机逐文件核对外部脚本 SHA256：
   - `h3/launcher.py`: `9b615b01e9025f6925da50d5f70bd4448dbb7020f364e3212e876ff8990e49cd`;
   - `h1/no_step_harness.py`: `e854f7a4df27372863387b8706739601f16f44d1e68fb93e59755719815c50c5`;
   - `h2/pre_step_comparator.py`: `3e84d2c676903bd471b38af6e04df3df4b18208f04c534cef91f19b2dcd06b60`.
   Missing/different => `BLOCKED`，不得在现场修改后继续 GPU。
3. CPU `--static-preflight` (both env modes) 和 Launcher `--static-accept` 复用已有检查，要求无实际 CUDA 初始化。验证 torchrun positional 是 `no_step_harness.py`，实际 executable 来自正确 venv，CWD 为 pinned Child root，`--max-restarts=0`，没有额外 python positional，正确 shell argv quoting。原 launch 所依赖外部 Script/Asset path 和 /tmp 充足磁盘空间必须满足；不能再出现 C1 错误启动路径。
4. 首先取得**owner 对共享 8×H100 与现有 robotwin_server 并行的明确许可**，并验证外部进程稳定且各张 H100 当前 free≥25,000MiB；若任何卡不足、GPU 共享未批准/进程不稳或不能保证日志持久化 => `RESOURCE_BLOCKED`。不能杀掉/暂停其他任务。CUDA allocator / torch/FSDP runtime env 必须与冻结 Formal 比较且记录，不得静默删除/增加标志。
5. 先建立 mode attempt=1 专属不可覆盖证据目录，准备 per-rank stdout/stderr、异常和 result JSON 落盘策略；如 torchrun 使用统一输出，必须保留可追溯 rank/错误的原始日志与 torch elastic stderr 或既有每 rank 日志，不能让失败覆盖前一次证据。确保 Original DCP、Shadow DCP/Latest、原 Job config 的前置静态快照/小文件 hashes 可回验。

## B. GPU 主执行：只允许 Launcher 统一顺序调用两个模式

1. 使用固定外部 `/tmp/ds_pro_v3_d1_r1/h3/launcher.py` 和 `/tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py`。以其经过验证的 `--allow-gpu-run`，`--gpu-sharing-approved`，`--robotwin-stable` Guard 标志执行，**仅当真实许可和资源 Guard 满足**。不要直接手工重复运行两条独立 `torchrun` 命令。使用 venv 的 torchrun，`--max-restarts=0`。完整 CLI 是 DS J1 报告中展示的、由 H3 Launcher 构建的参考→优化参数组合，其他 all frozen numeric config不变（raw15、left_wrist、use_state、H_pred16、T16/B8/GA2/K4、CFG dropout0.1、world8、num_workers0、max_iter30000/warmup500/save_iter100）。
2. Reference `PSM_V3_COMPACT_CACHED_VIDEO=0`，`PSM_V3_SHARED_EPISODE_CACHE=0`；完成、8/8 rank 成功并保存 Evidence 后，才允许 Optimized `1/1` 启动。Flag 在新进程启动之前设置，不能在 dataset factory 之后改。每条都从相同 iter800 独立完整 DCP 恢复，同 rank RNG/fast-state/frontier/plan identities/valid counts 一致。
3. 每模式只跑一个完整 grouped GA Window (GA0+GA1)，走固定 **`window.begin() → run_member(GA0) → run_member(GA1) → capture → abort()`**。必须调用生产 SegmentProducer/Scan/native Loss & weighted Backward、真实 FSDP2 shard，且选中 all four w0 Fast gradients 必须 present。真实 `model.training_step(...,_local_memory_prefixes=prefixes)` 与原 callbacks/hook/GradScaler disabled 语义一致。GA weight `len(batch.payloads)/plan.n_window`，数据/frontier必须从 iter800 恢复，不允许 Initial Frontier fallback。
4. 捕获全量 Loss、每 rank/FQN selected **真实 `.grad`** 与 Local Candidate 的四种 fast tensors、identity/provenance/slots、RNG、params/optimizer/scheduler pre/post fingerprint 等；保存真正完整 tensor payload（CPU/offload tensor files），可用全 SHA 或分块数值比较，不能以只256 sampled grad 判 PASS。写入前应检查 /tmp 空间与目录权限/互不覆盖。区分 `.grad=None`、zero-grad、weight-value 差异。Output `optimizer_step_executed=False`，最终状态 `abort` 后未发布且无参数更新。
5. 与 P4 同时进行**CPU-only NVML resource monitor**（不是另一个 GPU 模型作业），记录 8 H100 GPU global used/free（含 robotwin）、外部 PID/变化；Harness rank 记录自己 `torch.cuda.max_memory_allocated/reserved` 和 staged timing（load/H2D/local scan/FWD/BWD/capture/abort）。C1 Load-only ~6.5GiB 是 NVML 差分估计，forward/backward 10.5–13.5GiB 仍估算，必须实测。事先约定 reserve>24GiB/整卡used>78,000MiB 的退出 guard只作告警/触发，不保证防 OOM。OOM/NaN/Inf/NCCL/外部资源变化 => 首异常+停止且不得重试；若 Reference 出错，不启动 Optimized。
6. 对本次实验**禁止** `trainer.train`、完整最后一个 `trainer.training_step`、`window.finish`、`optimizer.step`、`scheduler.step`、`grad_scaler.step/update`、`checkpointer.save`、新 DCP 和 Formal Job Resume。只证明 *pre-step* gradient numerical parity，不代表 optimizer-step parity 或 full training throughput。

## C. 一次性比较（Reference 和 Optimized 都成功后执行）

- H2 frozen Comparator v2 读取各 rank 结果，先要求每 rank DCP source/digest/RNG/Local live/segment request/GA membership/CFG decisions/visibility 等输入身份完全匹配，否则 `INPUT_MISMATCH`，不能拿不同样本与不同 RNG 的 loss/grad 做数值比较。
- 按 `rank → FQN → local shard dtype/shape` 检查每个 selected gradient。全张量 SHA 完全相等才 `BIT_EXACT`；hash 不同时必须 **全量**分块比较，按照冻结 tolerance 输出 `WITHIN_TOLERANCE` / `FAIL`；Tensor payload 缺失 `UNVERIFIED`，哈希证据不一致 `BLOCKED`；不得将 sample256 一致冒充 full parity。四 w0 gradient 必须真实源 `param.grad`，局部 candidate 四 fast tensors 需全量比对，所有 native outer/action/vision/inner 字段按实际生产模型返回及权重对齐比较。
- 保留 `P0 bitwise` 与 `P1 numeric` 的不同强度；任何 `FAIL/BLOCKED/UNVERIFIED` 不得作为 D1 PASS。未执行 optimizer-step/full-training-throughput 列 `NOT_TESTED`。可在本轮结束根据实测中实际差异的既定标准裁决，不得事后调容差。

## D. 停止条件及报告

每个模式最多**一次 torchrun launch**，不自动 restart/retry，不改代码或参数后重跑；把出现的首异常、每 rank log 和原始 JSON/Tensors 持久化，不得用后续成功覆盖。如果外部 robotwin 压力上升、GPU free 不足或 Owner 未许可：`BLOCKED` 并不启动。Comparator 原始输入内容不满足则 `FAIL/BLOCKED`，需报告，不准借口技术验收绕过限制。

完成后对照 Original Formal30k 及 Shadow `latest_checkpoint.txt`/iter800 目录的前后小文件 SHA、manifest/mtime（允许仅 Shadow config.pkl/yaml 被 Trainer constructor 更新）。**Original Formal30k 必须仍 STOPPED。**

提交单份 `DS_PRO_V3_D1_PAIRED_8H100_SHADOW_PRESTEP_2026-10-11.md`，包含：
- execution permission/resource guard/date，frozen pair/full config digest；
- 两模式独立 attempt, rank0–7结果、DCP source、RNG/Local/GA/window identities、所有必需 Loss 和 full Grad/Candidate 比较；
- `BIT_EXACT` vs `WITHIN_TOLERANCE`/FAIL/UNVERIFIED统计，第一失败及每 Rank traceback；
- per-rank CUDA process peak allocated/reserved and nvidia-smi global+robotwin peaks, stage timing scopes, evidence file hashes;
- 原 Formal30k 与 Shadow DCP/Latest 不变性；
- `D1_PRESTEP_PASS / FAIL / BLOCKED / UNVERIFIED`（仅证明 frozen single GA window pre-step Parity，不泛化 30k）、Optimizer Step与完整吞吐 `NOT_TESTED`。
DS 不修改生产代码、不提交 GitHub。**STOP after this paired diagnostic.** GPT 将独立审阅并决定 D1 closure 与原 Formal30k iter800 Resume 是否可另行放行；后续 E/F/HOLD 不受影响。
