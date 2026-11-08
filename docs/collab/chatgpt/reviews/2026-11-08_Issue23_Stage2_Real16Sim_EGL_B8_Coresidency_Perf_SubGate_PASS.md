# Issue #23 Stage2 — 真实 16 RoboCasa Sim + 同卡共享 Wan VAE Worker：独立性能子门审核

**Formal verdict: `PASS_STAGE2_REAL_16SIM_EGL_CORESIDENCY_PERFORMANCE_SUBGATE`（仅 Stage2 资源共存 / 真实性能子门）**

**Overall Issue23 Stage2: PARTIAL / NOT CLOSED**。之前的 B4/B8 与 B1 **逐位数值一致性 Gate 未通过**；Owner 对 B8 RGB 重建视觉质量已验收 PASS；真实 Local-TTT 的 Prefix/Action 误差非零且 SR 未验证。本报告既不改写既有确切数值合同，也不批准 Stage3、PR6/V3 合并。

日期 2026-11-08（Asia/Shanghai）。
- **冻结形式配对**：Root `3ab4578475d8df5ce93b7bde6c4f2073a46f777e`；Child/Gitlink `0a2119782fb5078fee3359f9ef7383d788744458`。使用独立 clean checkout。Root 官方 V3 验后 `7b8b733e1f585bb44a0eac7c14ad545c29355a86`，仍指向 Child `1ca308055fc41fb69efaeb9efaa23808f164a18e`；PR6 Draft/unmerged。
- **真实物理资源**：data GPU4 H100 80GB，UUID `GPU-545d3c6f-e60e-dad5-cb58-b0fd6aceb33b`，PCI `0000:98:00.0`。单卡 16 独立 EGL OS Sim 进程，VAE 情况另加一份独立 CUDA Worker 进程。Sim 子进程强制 `CUDA_VISIBLE_DEVICES=''` + `MUJOCO_GL=egl` + NVIDIA-only `__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json`，以已加入 `render` 用户组启动；原生 `render_devices.configure` 和 `verify_current` 严格证实每个 Sim 的 GPU4 PCI / 当前 EGL Context，未跳过或修补生产代码。
- **任务与观测**：真正 RoboCasa `CloseFridge` 环境，种子 `41233 + physical_slot_index`，`target` 物体 split 和 Atomic-Seen 环境 layout/style，20Hz 控制配置、256×256 双摄像头，`native.compose` 生成 `left | wrist` 256×512 RGB。统一执行**零动作**每步 `env.step`，原始 raw15 证据为 all-zero，**不是训练 Policy 的 raw15 动作**。不测任务 SR。
- **阶段路径**：各 16 Sim 同时 reset/ready 后由 Barrier 放行，Sim 一边真实 stepping 一边将当步 RGB+raw15 封装成 immutable Frame 经 Unix Data IPC submit 给 GPU4 Worker（非同步等待完整特征），所有 steps 完毕后分别 poll / 接收 / ACK / End。单独的可信外部控制器验证 HMAC、源步和完整 Session 身份，Sim client 不持有 signing key，Owner control 与 Session cap 分离。由于 Stage1 尚无真实 `env.step` 因果认证，Controller 在确认 Sim 重置完成后预置合法 source frontier：`owner_complete` **明确为 MOCK、不能声称实际事后因果证明**。这是隔离硬件并行性能测试，不是生产 Action Path。
- **实际 VAE**：真实加载 Wan2.2 BF16 eager Encode1，权重 SHA256 `20eb789667fa5e60e7516bf509512f6cb61f01b0aa0695eadaea930c13892b36`；Stage1 `LoadedWanEncode1`、`SharedVAEWorker`、`UnixVAEServer`、`LocalVAEClient`。B1/wait0、B4/wait5ms、B8/wait5ms。正式预热实验在接收 Sim 数据之前，对各自真实 B shape 使用真 RoboCasa RGB **三轮**模型编码（独立脚本证据，预热 Frame 不算入 Sim 处理帧数）。输入、签名与 worker End 均按实际生产模块执行。

## A. 16 Sim × 4 步：短测与预热效应（64 帧）

| 模式 | Barrier→全部特征完成 wall | 完成帧/s | Step P50 ms | Step P95 ms | Worker 实际批次 |
|---|---:|---:|---:|---:|---|
| Sim-only | 1.147s | 55.798 | 68.584 | 99.736 | 无 VAE |
| Sim+B1, 未预热 | 3.8617s | 16.573 | 63.273 | 100.740 | `1×64` |
| Sim+B4, 未预热 | 3.5057s | 18.256 | 60.156 | 96.915 | `4×15,2×2` |
| Sim+B8, 未预热 | 3.0723s | 20.831 | 60.672 | 101.137 | `8×7,7×1,1×1` |
| Sim+B1, **预热** | 3.2350s | 19.784 | 60.073 | 105.422 | `1×64` |
| Sim+B4, **预热** | 2.8211s | 22.686 | 60.140 | 123.012 | `4×15,3×1,1×1` |
| Sim+B8, **预热** | 1.8779s | 34.081 | 59.552 | 96.927 | `8×7,6×1,2×1` |

初期 Worker 首个真实编码 batch 曾消耗约 1.4–1.7s；**先预热再测量**避免把这部分算成持续请求的服务时间。上述数据各配置仅单次受控执行，不能由四步负载直接外推真实长 Episode 的吞吐。

## B. 16 Sim × 16 步：较长真实同卡压力测试（256 帧，主判据）

| 模式 | Barrier→全部特征完成 wall | 完成帧/s | `env.step()` P50 | `env.step()` P95 | 观测 GPU4 总显存峰值 |
|---|---:|---:|---:|---:|---:|
| **Sim-only** | **1.8687s** | **136.994** | 60.232ms | 91.704ms | 19043 MiB |
| Sim+B1，预热 | 9.1262s | 28.051 | 59.479ms | 97.567ms | 22481 MiB |
| Sim+B4，预热 | 5.0957s | 50.238 | 58.797ms | 95.087ms | 22483 MiB |
| **Sim+B8，预热** | **4.6955s** | **54.520** | 55.646ms | 93.527ms | 22602 MiB |

**定量比较：** B8 相对 B1 同卡处理吞吐 **1.9436×**；B8 相对 B4 **1.0852×**；B8 相对 B1 barrier→全部特征完成 wall 缩短 **48.55%**。B8 相对 Sim-only 的 `env.step()` P95 变化 **+1.822ms**，GPU4 总峰值显存 **+3559 MiB**。**Sim-only 基线 136.994 step/s 不等价于加入 VAE 后的工作量**，不能据此说「整体策略变慢」或「整体策略已经加速」；真实 P0 单 Server×单 Sim / MultiSim SR+Policy throughput 尚未运行。

256 帧实际 Worker batch histogram：
- B1：`{"1":256}`
- B4：`{"4":63,"2":2}`（252+4=256）
- B8：`{"8":31,"6":1,"2":1}`（248+6+2=256）

**每组 16/16 真 Sim 进程完成 reset+step+EGL PCI+context 验证、全部 256 个真实后观测 RGB 特征签名验证、ACK、End，Worker quiescent，队列 items/bytes 归零。模拟框架和 CUDA Worker 均已退出，验证结束 GPU4–7 全 0MiB，无 CUDA/SIM 残留/OOM。**

## C. Worker 实际排队/计算分解（16×16 预热）

Worker `info().trace` 最多2048，本轮256 job轨迹 `trace_overflow=0`；按同一个 job 的 monotonic event 定义（不是推测分解）：

| 时段，P50 | B1 | B4 | B8 |
|---|---:|---:|---:|
| **READY → ENCODE_START** | 4017ms | — | **1738ms** |
| ENCODE_START → ENCODE_END | 26.49ms | — | 77.44ms |
| RESULT_READY → ACK | 4.27ms | — | 7.14ms |
| Sim frame step→feature ack 完成（P50） | 4077ms | — | 1844ms |

B8 READY→ENCODE_START P95 **2379ms**，frame→feature P95 **2475ms**。这主要显示**本次 16 Sim 同时突发提交 256 帧后的有限队列/并发调度成本**，不表示正常 Pipeline 每个单步都会等待1.8s。VAE 计算只占部分成本，优先开展真实 Replan arrival / streaming overlap、Unix base64/CPU admission及网路排队测量，而不是仅盯 GPU Kernel。无需先过度重构。

## D. 边界与 Gate verdict

- **此 Gate 可以通过的范围**：在 GPU4 同卡 **真实 16 独立 RoboCasa EGL+一份真实 Wan BF16 VAE B8 Worker 并行** 的物理可行性、能聚 B8、吞吐优势相对 B1、显存/尾部步时、严格 cleanup，全部实际硬件证据。原先 `BLOCKED_OS_DRM_PERMISSION` + 双 EGL vendor重复条目已经按最小环境方案解决：将 Sim 进程 EGL 限定 NVIDIA-only、通过物理 PCI 上下文校验，无需改产品 `render_devices.py`。
- **不能宣布通过的范围**：Stage0 默认**逐位 exact0 数值等价**对于 B4/B8 未通过；Owner 已验收8张 B8 reconstruct 视觉 PASS，但非 FastState/Action/SR 不变性。先前真实 iter15000 Local-TTT 输入差异传播至 Action，最大绝对差异 `0.0301193`、相对 RMS `0.49–0.60%`（3个固定 synthetic raw15 案例），且 **SR NOT_RUN**。此处**没有真实 Policy Server**，也没有源步后验因果认证（mock Owner完成前沿）、15+1 sparse future 当前帧缓存/复用、TTT FastState事务入 Action Path、P0 A/B/C single 1×1 latency与SR/CI、16Sim×2GPU/正式批 Bpolicy8 端到端 throughput、PR6 merge/V3 Gitlink promotion。
- **正式判定**：`PASS_STAGE2_REAL_16SIM_EGL_CORESIDENCY_PERFORMANCE_SUBGATE`；`FULL_STAGE2=PARTIAL`，`STAGE3_POLICY_INTEGRATION=NOT_AUTHORIZED`。若实施 launcher 环境变化、生产 Worker管理、Protocol Action admission，须新的提交/审核 Gate。数据单轮观测，不可声称 SR 或具有统计置信区间的生产吞吐结论。

## E. 原始证据及过程隔离

**精确数据主机目录**（非 sandbox，本轮未外传训练权重/用户数据）：

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/v3_issue23_stage2_real16_egl_sharedvae_20261108/`

- 机器可读汇总：`stage2_real16_egl_final_evidence.json`，由独立证据校验脚本读回11组真实 run + actual Worker traces + 16 Sim slot reports，并逐一断言128/256合法 source steps、本地授权身份、原始 Frozen SHA、模型 job/count、签名验证、GPU post0、无非生产进程存留及临时凭据文件已删除。
- 隔离执行器：`run_16sim_contended.py`, `real_sim_slot.py`, `real_vae_worker_process.py`；只读项目权重及官方源文件，不改正式运行生产代码。
- 每个 `actual_16sim_*` / `long_16sim_16steps_*` 下含 `run_report.json`, `slot_XX.json`, （VAE方案）`vae_worker_state.json`, `slot_XX_receipts.json`, `sim_XX.log`, `vae.log` 和独立 Exit code。测试生成的 Worker signing / Owner / Session 原始 secret 配置仅暂存权限0600，结束后已移除，不在公开 review/issue 中存储。
- 同一 GPU4 出现过 `NVIDIA+Mesa` 交叉枚举（17索引，两组同物理GPU），仅 NVIDIA EGL ICD 后为8个物理GPU，单 Sim 严格 native Code Gate 已单独 PASS（Issue23旧评审证据）。所有实际 Sim 使用此不影响系统全局配置的环境变量隔离策略。

Issue23 新证据沟通后由 GPT 附加链接。正式记录与 canonical Inbox 的docs-only 后续提交不是 implementation SHAs。
