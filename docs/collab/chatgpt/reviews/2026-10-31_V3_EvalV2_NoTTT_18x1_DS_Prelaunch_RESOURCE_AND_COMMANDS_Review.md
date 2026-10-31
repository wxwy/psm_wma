# PSM-WMA V3 EvalV2 No-TTT 18×1 — DS_PRO 启动准备 / 资源状态 / 手动启动命令独立审核

**日期：2026-10-31；审核类型：运行准备与启动命令，不是新源码 Code Gate。Verdict：`PREPARATION_REPORTED_READY; FRESH_LAUNCH_BLOCKED_PENDING_OWNER_RESOURCE_DECISION_AND_COMMAND_FIX`。**

## 正式源码身份与范围

- DS在相同共享训练/仿真代码树只读核对：Root detached `cee6f53eef345579c3db1124148f350fd2edc618`，Child/Gitlink `6c83596d6a259e89c4cd3e79424024983426ac3d`；DS未拉取/切分支或修改源码，符合Owner两DS共享代码要求。
- GPT从GitHub独立读现行V3最新HEAD `ec9d7b26391821d0eed34977e8d45ae90b346ba3`、Child正式branch 6c、实际EvalV2 `config.py`、`resources.py`、`identity.py`、`cli.py`、`store.py`及历史 Owner accepted 4-episode OSMesa review。当前源Formal无新的生产代码修改，本轮**禁止重复技术Code Gate**；本Review只审DS报告的Prelaunch命令和资源解释。GitHub后续仅docs相对DS检出Root cee6的进展不代表其运行source失配。
- 实际服务器的GPU进程、原12200 DCP、YAML/外部shell/cache路径均只来自Owner转交DS报告，GPT未直接访问训练服务器或逐字节校验这些原件。

## DS报告已满足的准备项（DS_REPORTED）

- 18个RoboCasa Target Atomic-Seen task的数据根路径含各自`extras/dataset_meta.json`；正式目标18 tasks×1 episode / seed0；NoTTT `phase_b/off`、M2/B2、OSMesa、全部rollout MP4；原正式iter12200完整DCP由DS报告、不要用AB实验12220替代。
- 实际YAML与服务/仿真Python、Numba cache和vendor paths按DS报告准备完成；未调用dry-run/fresh、未启动Sim/Server或修改正式NoTTT训练。
- 历史 NoTTT OSMesa 4-episode有效/4个行为失败、batch B2 2/244及GPU7的Canary已经Owner以`PASS — DS_PRO_REPORTED / OWNER_ACCEPTED`采信（Review `2026-10-31_V3_EvalV2_NoTTT_OSMesa_Owner_Accepted_Report_Gate_PASS.md`）。不得重新以原始Evidence缺失阻塞该旧Gate。注意旧Canary用iter11000，不能冒充新iter12200的筛查结果。

## 当前阻断与启动命令修订

### RUN-01 HIGH — 启动命令含无条件删除Fresh目录

- **位置：** DS交付`§5.2 FRESH`，`rm -rf "$BASE/out"`。生产依据 `scripts/robocasa_eval_v2/config.py:190-192` 的Fresh输出目录不可已存在，以及Child `evaluation/robocasa_v2/store.py:create()`独占`mkdir()`与原子记录。
- **根因：** unconditional rm -rf会销毁历史/部分完成的Run及其证据，绕过既有Fresh fail-closed/Resume独立语义。
- **违反合同：** 旧Owner D3/D5持久化有效Episodes不可重做/覆盖；此次18×1新namespace和Owner手动运行，不授权破坏任意原输出。
- **立即可验收：** 从Owner可复制的最终启动命令中**删除该行**；用`test ! -e "$BASE/out" || { echo ...; exit 2; }`启动前fail-closed，或选择全新唯一输出目录并同步修改YAML。发现旧Run应走显式Resume或由Owner独立决策，不自动删除。此项仅修DS外部启动指令，无需Codex修改任何生产源码。

### RUN-02 RESOURCE / POLICY — GPU全部有作业，不等于全部代码硬阻塞

- **DS实况（以现场报告为准，启动时须重新确认）：** GPU0–3外部LibreRO训练每卡62253MiB used、训练占满；GPU4–7正式NoTTT Resume每卡约35GiB、66–100% GPU util。
- **生产代码核对：** Root`scripts/robocasa_eval_v2/resources.py` docstring明确`allow GPU sharing without managing foreign processes`，`check(...before_models=True)`只按**总显存的`max_gpu_fraction=0.85`与20GiB reserve**检查（不是GPU util=0或独占）。对于81559MiB total，85%≈69325MiB≈67.7GiB；GPU0–3 used62253MiB +20480MiB>budget，会`BLOCKED_RESOURCE`；GPU4–7 used≈35GiB +20GiB <67.7GiB，内存Gate可能通过，**但并不保证训练+仿真并发的时延/吞吐/长程稳定性**。
- **准确判定：** 按Owner先前“评测不得抢占训练GPU”的**当前无冲突运行约束**，目前没有可不干扰训练的GPU，故`FRESH_RESOURCE_WAIT`成立；不应称GPU4–7由代码独占而无条件BLOCKED_RESOURCE。允许共享须由Owner明确知悉性能影响后单独授权，并核实际GPU当时峰值/HostRAM/IO/端口；不暂停别人的任务、不擅自动正式NoTTT。
- **最小减配：** 18 underlying tasks不需要18并发/9张GPU。`physical_slots(cfg,task_count)`是有界Slot调度，`--gpus <一张空闲卡> --sims-per-gpu 2`同样能分批执行18×1，只会更慢。GPU编号务必统一于CLI和`CUDA_VISIBLE_DEVICES`；更新YAML/命令前先dry-run核计划。GPU0–3现有负载明显不满足预算。

### RUN-03 MEDIUM (Owner已采信的遗留风险，仅运行注意) — Numba缓存异步注入竞态

- **位置：** DS交付`§4/§5.2` 的外部`inject_numba_cache.sh`背景等待`out/_internal/.run.lock`并symlink至预热cache。冻结Root`identity.py`的 runtime_environment在真正创建Run后指向`out/_internal/cache/numba`，Child`store.create()`在exclusive mkdir后创建`.run.lock`。`fresh`在同一次运行自行创建Run/初始化Runtime，因此独立后台注入在首次Sim import前存在时序竞态。
- **此前Owner裁决：** OSMesa方案采纳、4集报告采信、缓存竞态仅作为正式长跑时运行注意，不因缺原件重复取证/重跑旧Canary，也不要求本轮Codex重构。
- **最小验收：** DS在新可复制启动脚本中确认`${BASE}/evidence`存在（背景重定向失败不可静默）、注入脚本确实运行且其成功/失败可以观察与收尾、确认缓存link在启动Sim之前可见；任何注入失败/OSMesa崩溃必须保留日志并停止，不自动清理out或带同一Fresh重试。外部`&`不应留下无人回收的后台脚本。这里不要求额外性能实验、源码修复或新的旧Evidence包。

## 可执行状态与建议

1. **Owner可手动执行`dry-run`**：根据现有`scripts/robocasa_eval_v2/cli.py:33-73`仅做任务/Slots/Manifest计划CPU预览，不启动Server/Sim/GPU，不受目前GPU忙阻断；DS之前尚未运行。它也不能证明GPU可用。
2. **真实`fresh`暂不直接执行当前脚本**，直到修改上述破坏性rm -rf并就GPU资源作Owner明示选择（等待非冲突GPU或允许一张4–7的受控共享）。执行瞬间重新查看`nvidia-smi`，核负载阈值、输出路径必须不存在、注入依赖；所有GPU IDs以当前资源而非原固定0,1,2,3为准。
3. **手动启动不变：** DS只读/准备/生成两条可复制命令→Owner亲自dry-run与fresh→DS监控提交18任务每项valid/success/error/MP4及真实资源情况→本会话按新Runtime Evidence增量验收；不能误把Valid Episode当Success，不能以此授权900或LocalTTT Canary。

**本次不产生新Formal Code verdict，不更新或修改正在运行的共享PSM-WMA V3代码、训练进程、Checkpoint、子模块、数据与已有评测Run。**