# Issue #35 — Prefix K 数值修复后 Cosmos Native Generation 性能：GPT 独立实测

**日期** 2026-11-10。**证据审核类型**：同一正式Pair的新增性能实测，**不重新做代码审核**。已有限域 `APPROVE_CODE` 数值正确性结论保持。

- Formal Root：`55b74ab461fda27e4ff6490023c828db0abc0a9f`；Child / Gitlink：`bf707810f573e885f0966d65c232dc2a610d6a93`。
- 对比前一实现：Root `18be4a80a5ae4d97bc7d287034d24efab847c496` / Child `193627f42f4cd1ba6d563aefb8fa8f9428ecb56d`。
- 指标仅为 **Cosmos model native generation，包括当前帧VAE，不含历史Worker/FW更新、Policy HTTP网络、Sim执行**。不比较Episode总体耗时。使用原生B1、guidance1、30 UniPC、Local iter15000、GPU6 H100，人工GPU负载保持关闭，未重跑NoTTT。

## 1. 同一个冻结真实请求，精确隔离数值修复成本

GPT在GPU6 H100使用前后两个**精确 clean formal pair**加载同一Local iter15000 DCP，各选择已冻结的真实 `K1/source32`、`K16/source64`，仅启用Stage2 Prefix-aware Text-KV + Pack。每种模式每个K **warmup4 + measured30**；GPU事件覆盖完整原生模型生成（含当前帧VAE）。每次生成的Action/Vision通过本代码版本对应的真实保存输出严格校验（数值修复前参考旧Stage2，数值修复后参考旧原Local）。分别在同一卡上串行运行，次序K1 old→new、K16 new→old。

| 固定请求/指标 | 修复前 Stage2 | 修复后 Stage2 | 变化 |
|---|---:|---:|---:|
| K1/source32 GPU P50 | **774.532 ms** | **810.472 ms** | **+35.940 ms，+4.64%** |
| K1 GPU mean | 775.310 ms | 811.122 ms | +35.813 ms |
| K1 GPU P95 | 781.424 ms | 815.723 ms | +34.299 ms |
| K16/source64 GPU P50 | **759.777 ms** | **798.868 ms** | **+39.091 ms，+5.15%** |
| K16 GPU mean | 760.129 ms | 799.387 ms | +39.257 ms |
| K16 GPU P95 | 763.949 ms | 805.612 ms | +41.663 ms |

上述约36–39ms可归因于**本次数值修复实施前后**这一实测配置差异，但不能仅凭整体计时确定其中 `torch.all/where`、存储、归一化、GPU同步各自的毫秒份额；不为加速设固定百分比门槛。

**独立服务器证据目录**：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_kv_norm_performance_20261110/`。四份 `old_k1,new_k1,new_k16,old_k16/result.json` 各30条测量和原始命令日志、四个exit0。独立聚合 `model_only_independent_summary.json` SHA256 `6a7c73dcf595c3e0f7bcf9b456608d9e3ebc4d4c180853c1786833f4e4fb19a6`。首次launcher preflight的`benchmark.log`文件存在性断言失败已留存记录，**当时模型尚未加载**；修正的是隔离诊断脚本预检，不是生产代码，不冒充GPU Gate。

## 2. 连续真实观测下的模型生成速度——同种子55次稳定Replan

为避免固定输入低估现实变化，GPT在**修复后Formal Pair**上只运行Local K1与K16各一条RoboCasa CloseFridge/seed4603轨迹以采集动态模型输入，不运行NoTTT；GPU6 Policy、GPU4 Sim/SharedVAE、无人工GPU模拟负载。两条运行各57个replan，底层执行/采样/Prefix证据全部有效，无代码异常；本报告**仅分析replan index2..56的55次 `native_generation_ms`**（排除index0首次无Prefix及index1首次Prefix编译）。两条任务均未成功，**本轮不用于成功率/SR判断**。

| 指标 | 历史NoTTT seed4603 | 修复后Local K1 | 修复后Local K16 |
|---|---:|---:|---:|
| 55个稳定replan平均 | **664.654 ms** | **1,035.182 ms** | **1,088.085 ms** |
| P50 | **736.752 ms** | **1,146.950 ms** | **1,163.912 ms** |
| P95 | 约750.177 ms | 1,172.468 ms | 1,230.022 ms |
| Replan 2–27 P50 | — | 862.10 ms | 870.27 ms |
| Replan 28–56 P50 | — | 1,163.19 ms | 1,184.61 ms |

**历史NoTTT 五种子**：280次非首次Replan模型原生生成 `mean=616.258 ms`（同样包含当前帧VAE）；这是不同的统计人群与口径，不能替换单seed55次的P50。NoTTT与Local使用**不同训练checkpoint**，历史NoTTT运行时GPU4–7仍有 `gpu_load_sim.py`，这次新的Local没有；因此上表差异是**描述性实际观察，不是控制条件严格一致的因果加速比**。不应把`+410ms/+427ms`等同于KV残余Attention开销。

**另一项重要正确性证据**：修复后K1与K16各自57/57次模型Action和原始RGB SHA，均与先前原Local（KV关闭）的真实轨迹**逐元素/哈希完全相同**；前一未修复Stage2在较早Replan已经偏离旧轨迹。因此，未修复Stage2与修复后连续真实轨迹的时延差值还混入了轨迹/观测分布的变化，不能当成36–39ms修复开销。可信的修复成本以第1节的同冻结输入模型内对照为准。

## 3. 后半段生成变慢：VAE不是主因，下一步需专门定位

两个K都发生了replan28附近之后的显著时间上升。Raw trace按GPU事件拆分后：

| 时延项的阶段P50 | K1前半 | K1后半 | K16前半 | K16后半 |
|---|---:|---:|---:|---:|
| `current_frame_vae` GPU | 5.871 ms | 8.821 ms | 5.394 ms | 6.800 ms |
| `policy_native_generate` GPU（**包含**上行） | **846.077 ms** | **1,143.510 ms** | **856.052 ms** | **1,162.988 ms** |

因此主要延迟变化在模型主体/调度而不是VAE。现有服务端Trace不足以区分是CUDA kernel时间、CPU launch/synchronization、Attention varlen、Graph/compile cache形状或系统干扰；作者源码没有足够证据证明其中任一是根因。**禁止盲目改Attention或声称仅凭输入Prefix就应与NoTTT绝对等速。**

## 4. 结论与Gate

- 本轮 **性能证据实测 PASS（计时/原始数据/源身份与输出校验可复核）**；不是“性能达成某个预设提升率”的Gate。
- 原限域数值 `APPROVE_CODE` **仍有效且formal pair未变**，不重复技术审核；本次发现修复成本约36–39ms及连续轨迹中可复现的约300ms后半段上升，需作为新性能问题持续调查。
- 后续若要优化，优先在相同Localcheckpoint/真实输入、可控图/Attention执行下定位replan28前后GPU kernels和CPU发射差异，专门做最小instrumentation再决定修复。**不重跑NoTTT、不直接合并V3、不自动关闭Issue35的Attention性能任务**。
- 所有原始帧、FastState、模型输出、checkpoint、profiling数据均只留在授权服务器，没有外传；两个Repo tracked工作树无修改，GPU4–7清理后0MiB，GPU0–3其他任务未操作。