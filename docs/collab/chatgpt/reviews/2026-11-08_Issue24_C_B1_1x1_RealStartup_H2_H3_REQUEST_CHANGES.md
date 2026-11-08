# Issue24 Stage3A — 真实 1 Policy Server × 1 RoboCasa Sim / C-B1 启动 Gate：REQUEST_CHANGES（H2/H3）

**Formal verdict: `REQUEST_CHANGES_REAL_C_B1_1X1_STARTUP`**，当前 **C-B1 真实 Sim 闭环 NOT_RUN / BLOCKED**。这是继此前 Stage3A CPU `APPROVE_CODE`、H1 OmegaConf CPU Gate PASS 和真实 H100 固定输入 Wan/DCP Visual96/FastState/Prefix/Action parity PASS 之后，**下一道独立生产拓扑硬件 Gate**。不撤销前述 PASS，也不得把本次未启动 Sim 当作任务失败或 SR0。

日期：2026-11-08；独立 reviewer：GPT；Owner 当前授权执行单个真实 C-B1 1×1 Gate。Codex 负责小范围修复，GPT 负责新 Pair 审核。

## 1. 冻结 Formal Pair、物理资源与实验范围

- **Root Formal**：`ea64c26f7738f2efba5c33c78f18eab475230a61`
- **Child+Gitlink Formal**：`90ac5e91c5919cdb1d228aebd797e40327900981`
- PR：Root `wxwy/psm_wma#25` / Child `wxwy/cosmos-framework#7`，仍为 Draft/unmerged。所有文档后续 Root HEAD **不是**新的 implementation SHA。
- 真实 checkpoint L `iter_000015000` + 真实 Wan2.2 BF16；独立新 Run：**Policy Server GPU6 ×1、实际 Sim GPU4 ×1、Wan VAE Worker GPU4 ×1，C-B1/wait0**；`CloseFridge` 仅 1 episode，raw15/state15、horizon16、NVIDIA-only EGL 实际 PCI 映射；不启动 A/B/C SR或 900EP。
- 原始证据留在授权 `data` 主机隔离目录：
  `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_stage3a_c_b1_1x1_real_egl_20261108/`。
- 汇总 JSON `stage3a_c_b1_1x1_preflight_h2_h3_independent_evidence.json`，SHA256 **`6eefae77600f910050d0078b947f078e7879ae8ddfae2e69bd3eaf9c221c213a`**；每次 Run 日志/Worker Trace、配置、隔离脚本与前置资源证据均在该目录，模型/图片不外传。

## 2. 环境预检（不是产品代码问题，已关闭）

首个 `fresh` 在运行前 Vendor Code Audit 拦截 14 个 Numba 生成的 `.nbc/.nbi` 未跟踪缓存，并且需要供应商的**已批准正式资产清单**。该清单确切位于 `/mnt/data1/data_v2_0617/robocasa_vendor_build_20261023/asset_manifest.json`，已作为本试验配置只读输入；14 个仅为编译缓存的文件在不修改任何受 Git 跟踪的 robosuite/robocasa 源码或原始资产的情况下按原路径/SHA256备份至 `vendor_numba_cache_quarantine/quarantine_manifest.json`，而非删除源码、生成新资产清单、跳过严格认证。**后续两个 fresh 均通过供应商、资产、源代码和 checkpoint 的正式身份预检**，创建了合法隔离 Run。

## 3. H2 — Root 传入允许的浮点超时，Worker 私有协议只接受严格整数 JSON

- **真实证据** 第二次 `fresh`：GPU6 Policy真实加载成功；但 Root 汇总报 `shared Worker actual READY identity mismatch`。实际 Child Worker 日志是 `robocasa_vae_protocol.ProtocolError: float/non-finite JSON token forbidden` / `invalid strict JSON`，在 `run_daemon -> _read_private` 时发生，**Worker 尚未加载/证明模型，因此这一外层 READY 文案不是实际 CUDA/模型身份错误**。
- **Root 位置**：`scripts/robocasa_eval_v2/shared_vae.py:593–606`，`public["drain_timeout_s"] = cfg["terminate_grace_s"]`，通过 `canonical_json` 写入启动私有 FD。试验配置 `terminate_grace_s=15.0`；Root `config.py` 允许 int/float，默认也为 `10.0`。Child `robocasa_vae_protocol.strict_json` 明确拒绝所有浮点 JSON token。原生 CPU 对照：`{"drain_timeout_s":15.0}` 失败，`{"drain_timeout_s":15}` 通过。
- **隔离 config-only 复验**：将全新 Run 的 `terminate_grace_s` 以合法整数 `15` 表示（保持完整超时时长不变；另开不同 output_dir/port，未修改正式生产源码），Worker **成功解析启动输入、载入真实 Wan 和通过模型 loaded Identity 比对，进一步走到 CUDA 物理设备检查**。这证明 H2 是实际存在且局部可恢复的配置序列化兼容缺口。
- **Codex 最小整改**：只为 C Worker 私有 bootstrap 序列化成严格整数 schema 的真实等价时长。对原来允许的正**整数秒**数（包括 Python `10.0`、`15.0`）保留原值但在 Root/Worker wire 中写 `10`、`15`；非整数浮点例如 `10.5` 如不新增审过的纳秒合同，则必须**配置阶段 fail closed，不能四舍五入延长/缩短原截止时间**。在 C profile 的 preflight 提前校验，A/B/default Resume 不改变。**不得放宽 Child 全局 strict_json，亦不得把超时字段偷偷删除。** 增加 Root 正向与负向 CPU 合同（default 10.0、显式15.0、10.5 fail）及真实私有 FD/READY 测试。

## 4. H3 — PyTorch 2.10 CUDA UUID 缺 `GPU-` 前缀，生产校验误拒绝正确物理卡

- **真实证据** 第三次 `fresh`（整秒 bootstrap 配置后）：GPU6 Policy与 GPU4 真 Wan Worker均已加载；Child Worker `robocasa_vae_daemon.py:228–266` `_physical_device` 在比较 `str(torch.cuda.get_device_properties(device).uuid)` 与 Root 的 `expected["uuid"]` 时抛 `ValueError: actual Worker CUDA UUID differs from assigned physical GPU`，Root按严格 fail-closed 停止 Run：`native Worker requested safe stop`。
- **独立真实 PyTorch+NVML物理证明**：GPU4 环境 `CUDA_VISIBLE_DEVICES=4`，唯一可见 H100。实际 `str(torch._C._CUuuid)` 返回 `545d3c6f-e60e-dad5-cb58-b0fd6aceb33b`；Root/唯一物理 NVIDIA UUID是 `GPU-545d3c6f-e60e-dad5-cb58-b0fd6aceb33b`。两者 **UUID 128bit 内容完全一致，仅表示前缀不同**。`nvidia-smi -i GPU-545d... --query-gpu=index,uuid,pci.bus_id` 真实返回 **index4 / 同UUID / PCI 0000:98:00.0**，实际没有错误设备选择。完整证据保存在 `cuda_uuid_probe.json`。
- **Codex 最小整改**：只在**实际 CUDA 硬件身份校验入口**将 PyTorch raw `uuid` 作**严格格式/128bit 内容校验**，允许完整标准 UUID 无前缀时加标准 `GPU-`，允许已标准化 `GPU-` 本身；**仍必须逐字节对照 Root expected UUID，再用实际 `nvidia-smi -i canonical_UUID` 反查并严格核对物理 GPU index、UUID、PCI**。非法/缺失/错误 CUDA UUID、不同物理卡/PCI、多个可见 CUDA 设备、权重不在同 GPU、NVML不可用都保持 fail closed。禁止用 `CUDA_VISIBLE_DEVICES` ordinal 对齐、跳过 UUID 或 PCI 校验、信任 config 代替实际 CUDA property。增加 CPU 仿真单元测试覆盖裸UUID、有前缀、错误UUID、错误PCI、设备数错误和真实 negative cases。

## 5. Gate verdict 与 Codex 交付要求

**`REQUEST_CHANGES_REAL_C_B1_1X1_STARTUP`**：本次闭环**没有出现 Sim env.reset 完成/成功 post-step、没有 Action Chunk、没有 Worker IPC 产出 History Feature、没有 Session ACK/End 证明**。评测 Run 在模型/Worker 启动期间 fail-closed，生成的 `invalid=1` 是环境/系统运行阻断，**不是机器人任务失败（SR0）**。没有权限对本次 C 真实闭环、真实时延或SR宣布通过。

Codex只针对 **H2 Root 私有 FD超时整数规范化**、**H3 Child CUDA UUID strict canonicalization** 两处窄范围修复+正负向CPU/进程回归，保留此前 H1、15+1 数值 Gate 和 Legacy A/B NoTTT行为。新代码需提交**新完整 Root/Child formal implementation Pair/Gitlink**（Root/Child Draft PR25/7可增量维护，不能修改官方 V3）、原始 JUnit/Ruff/source unchanged、RED->GREEN及端到端 Worker READY synthetic CPU证明，追加 canonical Inbox 等 GPT 独立 Code Gate。**新 Gate 没有通过前不能用测试私自屏蔽真实 UUID/Deadline 验收并重试 GPU。**

完成记录：三个隔离 fresh log 均保留；CPU 证明 + nvidia-smi H100物理测量保留；模型/Checkpoint/正式 V3从未修改；GPU4–7 **全部0MiB、无残留 Policy/Worker/Sim 进程**。后续仍先是单个 C B1 真实 post-step / Worker Unix IPC / Native Transaction / ACK/End Smoke，P0 A/B/C paired SR、Stage3B B8、V3合并另立 Gate。
