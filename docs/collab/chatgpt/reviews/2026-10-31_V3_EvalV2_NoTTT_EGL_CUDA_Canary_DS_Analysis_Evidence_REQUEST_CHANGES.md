# V3 EvalV2 PhaseB NoTTT GPU Canary：DS 同卡 EGL/CUDA 崩溃报告独立审核

- 日期：2026-10-31（CST）。角色：ChatGPT **新增真实执行 Evidence** 独立审核，非重复 Production Code Gate。
- **Formal implementation Root** `d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163` / **Child+Gitlink** `2f7334c4ada6ace1d21185985aae90539052bf18`；同 Pair 的增量代码 `APPROVE_CODE` 保持不变，本轮新增真实 DS 运行报告并不改变 Formal Pair。
- **当前真实 Canary 状态**：`BLOCKED_NATIVE_SIM_SIGABRT`；**Evidence verdict `REQUEST_CHANGES`**，不接受“NoTTT PhaseB 真实 B=2/4 Episode Canary PASS”或“已证实 NVIDIA 驱动内存churn毁损EGL context”。原已审 Code Gate 未撤回。
- Evidence 输入：Owner 粘贴的 DS_PRO《EvalV2 Phase B Canary 崩溃根因分析（NoTTT）》、其中报告的重复 SIGABRT 与同卡/异卡隔离矩阵。所有 `evidence/iso_*.log` / `out/logs/GPU7_S0_simulator.log` 仍是 DS 服务器本地路径，本轮 GPT **未能访问原始字节**，服务器远端设备离线，故现场事实均标为 `DS_REPORTED/RAW_NOT_INDEPENDENTLY_VERIFIED`。本轮独立核对 GitHub 精确源码和上游文档。

## 1. 结论等级：有力的定位线索 ≠ 已证明的具体机制

- DS称同卡 closed-loop（Solo/dual）均SIGABRT于 `mujoco.mjr_readPixels` 附近，异卡（Sim GPU4或5，Server GPU7）可完整完成20/32次预测；纯 EGL600迭代、随机真实 RoboCasa200步、Server idle200步可稳定。这些实验支持 **concurrent same-device render/inference 或其资源压力是重要诱因**，并且设备分离是合理的避险路线。
- 现有结果**不足以断言**“每次推理的大量CUDA alloc/free破坏EGL context”“必然的已知NVIDIA驱动bug”或“肯定不是Sim/驱动调用错误”。`SIGABRT at mjr_readPixels` 不能独立识别来自GL error、MuJoCo fail-fast、原生C异常、context/资源不足/错误设备映射等哪个机制；须看Fatal前的stderr/NVRM/EGL error、对照推理/渲染时序、显存峰值。
- **EGL设备序号 ≠ CUDA/nvidia-smi 序号的风险**：上游 MuJoCo EGL通过 `eglQueryDevicesEXT` 枚举，不能单靠 `MUJOCO_EGL_DEVICE_ID=5/7` 就认定物理GPU5/7；容器内映射尤其可能偏移。请 DS 在运行侧确认实际EGL设备和CUDA物理UUID/PCI bus id并核实训练/推理/渲染进程对应设备。上游：`https://github.com/google-deepmind/mujoco/blob/main/python/mujoco/egl/__init__.py`、`https://rlinf.readthedocs.io/en/latest/rst_source/resources/faq.html`。
- NVIDIA官方文档支持CUDA/OpenGL图形互操作（并非“同GPU必然冲突”的通用规则），但不保证这台机器、该 MuJoCo/driver/内存压力组合稳定：`https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/graphics-interop.html`。

## 2. DS 推荐的“无改码 shell sim_python 包装脚本”不满足当前身份合同 — HIGH

- Root `scripts/robocasa_vendor.py:244-278` 把 `sim_python` 当**真实的Python解释器二进制**：Hash `sha256_file(sim_python.resolve())`，在它上面启动`-B probe`，验证被调用解释器 `sys.executable == str(sim_python)`、`interpreter.binary_sha256==sha256_file(sim_python.resolve())`。把 `sim_python` 配成shell wrapper再 `exec python`，实际 `sys.executable`/binary hash对应真实Python而非shell脚本，通常会在 `collect_runtime` 直接失败。任何蓄意绕过probe不被授权。
- Root `scripts/robocasa_eval_v2/runtime.py:327-332` 在 Sim spawn 时**覆盖** `MUJOCO_EGL_DEVICE_ID=str(gpu)`；事先从shell导出该变量会被覆盖。配置 `config.py:10-43,77-80` 也不支持render_gpu_id选项，额外 YAML key fail-closed。
- 所以 **方案A的“无需GPT复审、立即在原批准Pair用wrapper重跑”不成立**。对于实际EGL/计算分离应由Codex完成**窄、显式、可审计**的真实 launcher/config 接线，然后新精确Pair Code Gate；不得在原Pair脏补丁、混淆真实解释器身份或静默更改设备。

## 3. 先测不改码的最小替代路径

### D0 首选：关闭可选生成视频解码，保留 rollout MP4

- Child `simulation/robocasa/eval_v2_transactions.py:115-117`：`save_generated_video=first` 仅 Episode **首个replan** 追加 `media` 请求；并非每一次预测都做VAE decode。
- Child `inference/robocasa_batch_transactions.py:229-242,327-339`：只有请求 `media` 且加入spool时才走 decode；Child `scripts/action_policy_server_robocasa.py:1313-1318` 的 `model.decode` 是此**可选**路径。Sim rollout MP4 由 `save_rollout_mp4` 独立控制。
- 因此可在新的独立试验输出目录，维持同GPU 1Server+2Sim、B2、正在运行的训练原样不动，只把 Eval YAML 的 `save_generated_video: none`，保留 `save_rollout_mp4: true`。先核DS的 `iso_closed_loop.py` 是否原本已经不请求media；若原本无media，这项对照应跳过。若稳定，可保留无需新增GPU分离代码的配置；若仍崩，排除可选VAE解码这一触发因素，但不能归因于全部CUDA动态内存。
- 测试仍需已有Owner真实执行范围和新`fresh`输出，不能在失败历史namespace`resume` 或偷换checkpoint；稳定需真实B2与4Core/MP4/owned cleanup记录。

### D1 零源代码候选：软件OSMesa渲染（仅先CPU/headless快速兼容预检）

- 官方MuJoCo Linux支持 `MUJOCO_GL=osmesa` 的CPU offscreen rendering；Root `scripts/eval_robocasa_18task_queue.py:244-254` 会继承已有 `MUJOCO_GL`，而 `runtime.py` 覆盖的`MUJOCO_EGL_DEVICE_ID`对OSMesa一般不适用。故无需替换 `sim_python`，可以先原生Python不改 source 用 `MUJOCO_GL=osmesa`（并确保正确的PyOpenGL backend）做兼容试验。
- 这条路线以目标机器是否安装 `libOSMesa`、robosuite后端能否正确创建context、CPU吞吐和画面差异为条件；**不是已验证直接可用的正式配置**。若使用必须记录render backend并创建新Run；切勿把软件渲染和原EGL结果静默混为一个实验。上游：`https://github.com/google-deepmind/mujoco/blob/main/python/mujoco/rendering/classic/gl_context.py`。

### D2 保守长期解法：单独指定Sim EGL渲染设备（需要窄生产改动）

- DS异卡成功是较强证据，因此若D0/D1无法满足稳定性/性能，建议Codex只在 Root `config.py` + `runtime.py` + 已有 execution identity/资源检查与定向 tests 增加一个显式 `sim_render_gpu_id`（或者对应slot映射）字段。**Server CUDA设备不动**；Sim实际 `MUJOCO_EGL_DEVICE_ID` 由显式、已校验的渲染设备设定，严禁改`sim_python`；GPU UUID/device mapping 和相应显存预算应核查。支持NoTTT与LocalTTT同一设置，避免重复两套框架。
- 可先选 DS已报告验证的 Server7 / 两 Sim 的 EGL5 布局；**必须先实测 EGL5确实等于目标物理GPU5**，以及GPU5在训练并行下有足够显存。保留原1Server/2Sim/NativeB2、IPC/Session/Checkpoint/MP4契约。
- 不建议用全局NVIDIA driver调整、停训练、取消模型Batch或通过锁把两个Sim完全串行化来冒充B2 Canary。

## 4. 当前请求的最小 DS 追加 Evidence

1. 只读交付崩溃日志中 **SIGABRT 前至少几十行真实stderr**、相关driver/NVRM/Xid日志（若有）、每次原始sim/server PID和物理设备UUID映射，说明“确实同一/不同物理卡”。
2. 检查 `iso_closed_loop.py` 是否请求了 `media`、生成视频decode究竟执行几次；给出同卡同 checkpoint/同任务/同训练负载下 `save_generated_video=none` 的短对照（必要时已有授权范围内）或者指出该对照已由已有iso证据覆盖。
3. 原报告须把机制从“**已证实CUDA churn破坏EGL context**”改为“**同卡真实CUDA推理+EGL渲染并发高度相关，具体触发机制未证，异卡规避有初步验证**”。

## 5. Gate 状态与边界

- 双模式生产源码旧 `APPROVE_CODE` 维持，formal implementation Pair未变，不重复代码 Gate。
- `REAL_GPU_Canary=BLOCKED_NATIVE_SIM_SIGABRT`，**Evidence Gate `REQUEST_CHANGES`**。
- NoTTT 真实 4Episode/B2/MP4 尚未通过；LocalTTT 真实GPU尚未通过。
- 此为审查/最小诊断建议，**不自动授予额外GPU实验、NoTTT正式900、代码合并或驱动更新**。如选择D2需新精确源码Pair增量fresh review。
